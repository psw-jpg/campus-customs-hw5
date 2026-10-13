"""FastAPI backend for the Campus Customs ops dashboard.

Run from the backend folder:  uvicorn main:app --reload --port 8000

Every shop read and write goes through the campus-customs MCP server, the same
one the agents use. The only exceptions are the two human-only steps that are
deliberately NOT MCP tools: approving a payment (db.decide_approval) and
resetting the working copy (db.reset_working_db).
"""

import asyncio
import json
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND.parent / "mcp_server"))

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

import audit  # noqa: E402
from db import ShopRuleError, decide_approval, reset_working_db  # noqa: E402
from run_tickets import run_ticket  # noqa: E402  (also registers all five agents)
from team import MCP, MODEL_NAME  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with MCP:  # one MCP connection for the backend and every agent run
        yield


app = FastAPI(title="Campus Customs Ops API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    # The Vite dashboard runs on port 5181 (5173, 5174 and 5180 are busy with older lecture apps).
    allow_origins=["http://localhost:5181", "http://127.0.0.1:5181"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One agent run at a time, so two runs can't spend the same cash at once.
RUN_LOCK = asyncio.Lock()
RUNS: dict[str, dict] = {}


async def mcp(tool: str, args: dict | None = None):
    return await MCP.direct_call_tool(tool, args or {})


# ------------------------------------------------------------------ models

class ApproveRequest(BaseModel):
    approved_by: str = Field(min_length=1, description="Name of the human approving the payment.")


class RejectRequest(BaseModel):
    rejected_by: str = Field(min_length=1)


# ------------------------------------------------------------------ routes

@app.get("/api/health")
async def health():
    return {"ok": True, "model": MODEL_NAME}


@app.get("/api/tickets")
async def list_tickets():
    """The tickets on the board, each marked open or resolved. A ticket counts as
    resolved once the crew has finished a run on it; `status` keeps the Boss's
    exact outcome (resolved, waiting_approval, blocked or needs_human)."""
    tickets = await mcp("list_tickets", {"status": None})
    running = {r["ticket_id"] for r in RUNS.values() if r["state"] == "running"}
    return [
        {**t, "state": "running" if t["id"] in running
                  else "open" if t["status"] in ("open", "in_progress") else "resolved"}
        for t in tickets
    ]


@app.post("/api/tickets/{ticket_id}/run", status_code=202)
async def run_ticket_route(ticket_id: int):
    """Start the agent team on one ticket. Returns a run_id right away; the work
    shows up in /api/events as it happens and /api/runs/{run_id} has the result."""
    ticket = await mcp("get_ticket", {"ticket_id": ticket_id})
    if not ticket or ticket.get("ok") is False:
        raise HTTPException(404, f"Ticket {ticket_id} does not exist.")
    if RUN_LOCK.locked():
        raise HTTPException(409, "Another agent run is in progress. Wait for it to finish.")

    run_id = f"run_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:6]}"
    RUNS[run_id] = {"run_id": run_id, "ticket_id": ticket_id, "state": "running",
                    "started_at": datetime.now().isoformat(timespec="seconds")}

    async def work():
        async with RUN_LOCK:
            audit.append({"run_id": run_id, "ticket_id": ticket_id, "event": "run_start",
                          "model": MODEL_NAME, "source": "dashboard"})
            result = await run_ticket(ticket_id, run_id)
            if result.decision:
                # Make sure the board shows the Boss's decision even if he forgot update_ticket.
                current = await mcp("get_ticket", {"ticket_id": ticket_id})
                if current.get("status") in ("open", "in_progress"):
                    await mcp("update_ticket", {"ticket_id": ticket_id, "status": result.decision.status,
                                                "note": f"Run {run_id} finished: {result.decision.status}."})
            RUNS[run_id].update(state="error" if result.error else "done",
                                finished_at=datetime.now().isoformat(timespec="seconds"),
                                result=result.model_dump(exclude={"trace"}))
            audit.append({"run_id": run_id, "ticket_id": ticket_id, "event": "run_end",
                          "total_requests": result.requests,
                          "total_tokens": result.input_tokens + result.output_tokens})

    asyncio.create_task(work())
    return RUNS[run_id]


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in RUNS:
        raise HTTPException(404, f"Run {run_id} not found.")
    return RUNS[run_id]


@app.get("/api/events")
async def recent_events(limit: int = 100, ticket_id: int | None = None, run_id: str | None = None):
    """The most recent agent events from output/audit_trail.json: what each agent
    was asked, what it said, and which tools it called with what result."""
    entries = _read_audit()
    if ticket_id is not None:
        entries = [e for e in entries if e.get("ticket_id") == ticket_id]
    if run_id is not None:
        entries = [e for e in entries if e.get("run_id") == run_id]
    return entries[-limit:]


def _read_audit() -> list[dict]:
    if not audit.AUDIT_FILE.exists():
        return []
    return json.loads(audit.AUDIT_FILE.read_text() or "[]")


@app.get("/api/tickets/{ticket_id}/summary")
async def ticket_summary(ticket_id: int):
    """A short summary of what each agent did on the ticket's latest finished run:
    its final answer, the tools it used and who it handed work to."""
    entries = [e for e in _read_audit() if e.get("ticket_id") == ticket_id]
    finished = [e["run_id"] for e in entries if e.get("event") == "ticket_end" and e.get("run_id")]
    if not finished:
        return {"ticket_id": ticket_id, "run_id": None, "agents": [], "decision": None}
    run_id = finished[-1]
    agents: dict[str, dict] = {}
    decision = None
    for e in entries:
        if e.get("run_id") != run_id or not e.get("agent"):
            continue
        a = agents.setdefault(e["agent"], {"agent": e["agent"], "summaries": [], "tools": [],
                                           "delegated_to": [], "tokens": 0, "steps": 0})
        if e["event"] == "agent_output":
            a["summaries"].append(e.get("summary", ""))
            if e["agent"] == "boss":
                decision = e.get("output")
        elif e["event"] == "tool_call" and not e.get("tool", "").startswith("delegate_to_"):
            if e["tool"] not in a["tools"]:
                a["tools"].append(e["tool"])
        elif e["event"] == "delegation" and e.get("target") not in a["delegated_to"]:
            a["delegated_to"].append(e["target"])
        elif e["event"] == "model_response":
            a["steps"] += 1
            a["tokens"] += (e.get("input_tokens") or 0) + (e.get("output_tokens") or 0)
    return {"ticket_id": ticket_id, "run_id": run_id, "agents": list(agents.values()), "decision": decision}


@app.get("/api/purchase-orders")
async def purchase_orders():
    """Restock purchase orders: waiting for approval, ordered (with arrival date) or rejected."""
    return await mcp("list_purchase_orders", {"status": None})


@app.get("/api/approvals")
async def list_approvals(status: str | None = None):
    """Payment requests the agents prepared. Pending ones are waiting for a human click."""
    return await mcp("list_payment_approvals", {"status": status})


@app.post("/api/approvals/{approval_id}/approve")
async def approve_payment(approval_id: int, body: ApproveRequest):
    """A human approves a payment (invoice or rent) or a restock purchase the agents
    prepared, and this route pays it. This is the only place cash leaves checking."""
    current = next((a for a in await mcp("list_payment_approvals") if a["id"] == approval_id), None)
    if current is None:
        raise HTTPException(404, f"Approval request {approval_id} does not exist.")
    if current["status"] == "approved":
        appr = current  # approved earlier but not paid (e.g. funds were short): retry the payment
    else:
        try:
            appr = decide_approval(approval_id, body.approved_by, approve=True)
        except ShopRuleError as e:
            raise HTTPException(409, str(e))

    # Execute through the same MCP pay_bill tool, which re-checks funds and
    # rejects anything that would make the balance negative.
    result = await mcp("pay_bill", {"kind": appr["kind"], "ref_id": appr["ref_id"],
                                    "requested_by": f"human:{body.approved_by}", "account": appr["account"]})
    audit.append({"event": "human_payment_approval", "agent": "human", "approval_id": approval_id,
                  "approved_by": body.approved_by, "kind": appr["kind"], "ref_id": appr["ref_id"],
                  "amount": appr["amount"], "pay_result": result})
    if not result.get("paid"):
        raise HTTPException(409, {"approval": appr, "pay_result": result,
                                  "message": result.get("reason", "Payment was not made.")})
    return {"approval_id": approval_id, "kind": appr["kind"], "approved_by": body.approved_by,
            "payment": result}


@app.post("/api/approvals/{approval_id}/reject")
async def reject_payment(approval_id: int, body: RejectRequest):
    """A human rejects a payment the agents prepared. No money moves."""
    try:
        appr = decide_approval(approval_id, body.rejected_by, approve=False)
    except ShopRuleError as e:
        raise HTTPException(409, str(e))
    audit.append({"event": "human_payment_rejection", "agent": "human", "approval_id": approval_id,
                  "rejected_by": body.rejected_by, "kind": appr["kind"], "ref_id": appr["ref_id"],
                  "amount": appr["amount"]})
    return appr


@app.get("/api/cash")
async def checking_balance():
    """The current checking balance from cash_accounts."""
    accounts = await mcp("get_cash_balance")
    checking = next((a for a in accounts if a["name"] == "checking"), None)
    if checking is None:
        raise HTTPException(404, "No checking account found.")
    return checking


@app.post("/api/reset")
async def reset_database():
    """Copy the original campus_customs.db over the working copy for a fresh run.
    The audit trail is kept; a reset entry is appended to it."""
    if RUN_LOCK.locked():
        raise HTTPException(409, "An agent run is in progress. Reset after it finishes.")
    reset_working_db()
    audit.append({"event": "database_reset", "agent": "human",
                  "note": "data/campus_customs_new.db reset to the original"})
    return {"ok": True, "message": "Working copy reset to the original campus_customs.db.",
            "cash": await checking_balance()}
