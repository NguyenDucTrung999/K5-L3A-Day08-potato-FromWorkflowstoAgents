"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (README): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
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
        return _execute_workflow(
            database_connection=database_connection,
            claim_id=claim_id,
            seed=seed,
            crash_at=crash_at,
        )
    finally:
        database_connection.close()


def _execute_workflow(
    database_connection: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    run_id = make_run_id("workflow", claim_id, seed)
    trace = Trace(run_id)

    budget.add_tool(tool_cost())
    claim_view = get_claim_view(database_connection, claim_id)
    if not claim_view.get("found"):
        trace.add("error", {"reason": "unknown_claim"})
        return finish(
            database_connection,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="failed",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="unknown_claim",
        )
    else:
        trace.add(
            "claim_loaded",
            {
                "claim_id": claim_id,
                "order_id": claim_view.get("order_id"),
                "principal_id": claim_view.get("principal_id"),
            },
        )

    order_id = claim_view.get("order_id")
    if not order_id:
        trace.add("decision", {"status": "needs_info"})
        return finish(
            database_connection,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="needs_info",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason="missing_order_id",
        )

    principal_id = claim_view.get("principal_id")
    budget.add_tool(tool_cost())
    order_view = lookup_order(database_connection, order_id, principal_id)
    trace.add(
        "lookup_order",
        {
            "visible": order_view.get("visible"),
            "reason": order_view.get("reason"),
        },
    )

    if not order_view.get("visible"):
        return finish(
            database_connection,
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="escalated",
            proposal_amount=0,
            budget=budget,
            trace=trace,
            error_reason=order_view.get("reason"),
        )
    else:
        order_data = order_view["order"]

    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(database_connection, order_data)
    proposal_amount = int(quote_payload["amount_vnd"])
    trace.add("quote", quote_payload)

    if proposal_amount <= 0:
        return finish(
            database_connection,
            shape="workflow",
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
            shape="workflow",
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
            shape="workflow",
            claim_id=claim_id,
            seed=seed,
            status="resolved",
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=None,
        )
