"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (README): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
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
        return _execute_orchestrator(
            database_connection=database_connection,
            claim_id=claim_id,
            seed=seed,
            crash_at=crash_at,
        )
    finally:
        database_connection.close()


def _execute_orchestrator(
    database_connection: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("orchestrator", claim_id, seed)
    trace = Trace(run_id)

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(database_connection, claim_id)
    if not claim_view.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            database_connection,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )

    order_id = claim_view.get("order_id")
    if not order_id:
        trace.add("decision", {"status": "needs_info"})
        return finish(
            database_connection,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    complete(budget, seed=seed, purpose="draft", prompt="planning_handoff")

    handoff_package = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="investigate_claim_and_quote",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
    )
    trace.add("handoff", safe_dump(handoff_package))

    investigation_result = run_readonly_investigators(
        database_connection,
        budget,
        handoff_package,
        principal_id=claim_view["principal_id"],
    )

    tools_result = investigation_result.get("tools") or {}
    order_view = tools_result.get("lookup_order") or {}
    trace.add(
        "investigator_summary",
        {
            "order_visible": order_view.get("visible"),
            "order_reason": order_view.get("reason"),
        },
    )

    if not order_view.get("visible"):
        return finish(
            database_connection,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )

    quote_payload = tools_result.get("compute_compensation") or {}
    proposal_amount = int(quote_payload.get("amount_vnd", 0))
    trace.add("quote", quote_payload)

    if proposal_amount <= 0:
        return finish(
            database_connection,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="denied",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=quote_payload.get("reason"),
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
            shape="orchestrator",
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
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=None,
        )
