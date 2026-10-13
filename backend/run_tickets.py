"""Run the agent team on tickets.

Resets data/campus_customs_new.db to the original before every full run, then
has the Boss work each ticket in order. Every agent loop step is appended to
output/audit_trail.json; a per-run summary is saved to output/runs/.

    .venv/bin/python backend/run_tickets.py            # every open ticket
    .venv/bin/python backend/run_tickets.py 101 103    # specific tickets
"""

import asyncio
import json
import sys
import uuid
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "mcp_server"))

from pydantic_ai.usage import RunUsage  # noqa: E402

import audit  # noqa: E402
from db import reset_working_db  # noqa: E402  (file copy only; all shop reads go through MCP)
from models import TeamDeps, TicketRunResult  # noqa: E402
from team import MCP, MODEL_NAME, TICKET_LIMITS, run_agent  # noqa: E402
import accounting, customer_service, facilities, inventory  # noqa: E402,F401  (register agents)
import boss  # noqa: E402,F401

RUNS_DIR = BACKEND.parent / "output" / "runs"


async def open_ticket_ids() -> list[int]:
    """Ask the MCP server for the open tickets (no direct database read)."""
    tickets = await MCP.direct_call_tool("list_tickets", {"status": "open"})
    return [t["id"] for t in tickets]


async def run_ticket(ticket_id: int, run_id: str) -> TicketRunResult:
    deps = TeamDeps(ticket_id=ticket_id, run_id=run_id, chain=["boss"])
    usage = RunUsage()
    decision, error = None, None
    try:
        decision = await run_agent(
            "boss",
            f"Handle ticket {ticket_id}. Start with get_ticket({ticket_id}). Delegate the specialist work, "
            f"then record your final status and a one-line note with update_ticket before you answer.",
            deps, usage, TICKET_LIMITS,
        )
    except Exception as e:  # keep the audit trail even if a run fails
        error = f"{type(e).__name__}: {e}"
        audit.append({"run_id": run_id, "ticket_id": ticket_id, "agent": "boss", "event": "ticket_error", "error": error})
        deps.log("boss", "error", error)
    audit.append({"run_id": run_id, "ticket_id": ticket_id, "agent": "boss", "event": "ticket_end",
                  "status": decision.status if decision else None, "error": error,
                  "ticket_requests": usage.requests, "ticket_input_tokens": usage.input_tokens,
                  "ticket_output_tokens": usage.output_tokens})
    return TicketRunResult(
        ticket_id=ticket_id, decision=decision, error=error, trace=deps.trace,
        requests=usage.requests, input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
    )


async def run_board(ticket_ids: list[int] | None = None) -> tuple[str, list[TicketRunResult]]:
    """One full run: reset the working copy, then work the tickets in order."""
    run_id = f"run_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    reset_working_db()
    audit.append({"run_id": run_id, "event": "run_start", "model": MODEL_NAME,
                  "note": "data/campus_customs_new.db reset to the original before this run"})
    async with MCP:  # one MCP connection shared by every agent
        ids = ticket_ids or await open_ticket_ids()
        audit.append({"run_id": run_id, "event": "tickets_selected", "ticket_ids": ids})
        results = [await run_ticket(t, run_id) for t in ids]
    audit.append({"run_id": run_id, "event": "run_end",
                  "total_requests": sum(r.requests for r in results),
                  "total_tokens": sum(r.input_tokens + r.output_tokens for r in results)})
    return run_id, results


def main() -> None:
    ids = [int(a) for a in sys.argv[1:]]
    run_id, results = asyncio.run(run_board(ids))
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    out = RUNS_DIR / f"{run_id}.json"
    out.write_text(json.dumps([r.model_dump() for r in results], indent=2) + "\n")
    for r in results:
        print(f"\n=== Ticket {r.ticket_id} ({r.requests} requests, "
              f"{r.input_tokens}+{r.output_tokens} tokens) ===")
        print(r.error or r.decision.model_dump_json(indent=2))
    print(f"\nRun {run_id}: summary in {out}, every step appended to {audit.AUDIT_FILE}")


if __name__ == "__main__":
    main()
