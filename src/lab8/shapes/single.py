"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (README): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    database_connection = connect(store_path)
    try:
        return _execute_single_agent(
            database_connection=database_connection,
            claim_id=claim_id,
            seed=seed,
            crash_at=crash_at,
        )
    finally:
        database_connection.close()


def _execute_single_agent(
    database_connection: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("single", claim_id, seed)
    trace = Trace(run_id)

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(database_connection, claim_id)
    if not claim_view.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            database_connection,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    initial_observation = {
        "claim": {
            "claim_id": claim_view.get("claim_id"),
            "order_id": claim_view.get("order_id"),
            "principal_id": claim_view.get("principal_id"),
        }
    }

    stored_order_data: dict[str, Any] = {}

    def decide(observation: dict[str, Any]) -> dict[str, Any]:
        complete(budget, seed=seed, purpose="draft", prompt="reasoning")
        claim_data = observation.get("claim") or {}
        order_id = claim_data.get("order_id")
        if not order_id:
            return {
                "final": {
                    "status": "needs_info",
                    "proposal_amount": 0,
                    "error_reason": "missing_order_id",
                }
            }

        last_tool = observation.get("last_tool")
        if last_tool is None:
            return {
                "tool": "lookup_order",
                "args": {
                    "order_id": order_id,
                    "principal_id": claim_data.get("principal_id"),
                },
            }

        if last_tool == "lookup_order":
            order_result = observation.get("last_result") or {}
            if not order_result.get("visible"):
                return {
                    "final": {
                        "status": "escalated",
                        "proposal_amount": 0,
                        "error_reason": order_result.get("reason"),
                    }
                }
            stored_order_data.update(order_result.get("order") or {})
            return {
                "tool": "compute_compensation",
                "args": {
                    "order": stored_order_data,
                },
            }

        if last_tool == "compute_compensation":
            quote_result = observation.get("last_result") or {}
            amount_vnd = int(quote_result.get("amount_vnd", 0))
            if amount_vnd <= 0:
                return {
                    "final": {
                        "status": "denied",
                        "proposal_amount": 0,
                        "error_reason": quote_result.get("reason"),
                    }
                }
            return {
                "final": {
                    "status": "quote_ready",
                    "proposal_amount": amount_vnd,
                    "error_reason": None,
                }
            }

        return {
            "final": {
                "status": "failed",
                "error_reason": "unexpected_react_state",
                "proposal_amount": 0,
            }
        }

    react_outcome = run_react(
        database_connection,
        budget,
        observation=initial_observation,
        decide=decide,
        max_steps=8,
        worker=False,
    )

    trace.add(
        "react_summary",
        {
            "stopped": react_outcome.get("stopped"),
            "final": react_outcome.get("final"),
        },
    )

    final_decision = react_outcome.get("final") or {}
    intermediate_status = final_decision.get("status")
    proposal_amount = int(final_decision.get("proposal_amount", 0))

    if intermediate_status != "quote_ready":
        return finish(
            database_connection,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=intermediate_status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=final_decision.get("error_reason"),
        )

    try:
        issue_result = issue_refund(
            database_connection,
            claim_id,
            proposal_amount,
            crash_at=crash_at,
        )
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not issue_result["ok"]:
        if issue_result["conflict"]:
            final_status = "failed"
        else:
            final_status = "denied"
        return finish(
            database_connection,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status=final_status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=issue_result["reason"],
        )
    else:
        return finish(
            database_connection,
            shape="single",
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=None,
        )
