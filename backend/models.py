"""Data types shared by the Campus Customs agent team."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
TicketStatus = Literal["resolved", "waiting_approval", "blocked", "needs_human"]


# ------------------------------------------------------------ agent outputs

class SpecialistReport(BaseModel):
    """What a specialist (Inventory, Accounting, Facilities, Customer Service)
    hands back to whoever delegated to it."""

    agent: AgentName
    summary: str = Field(description="Two to four sentences answering the task, with exact figures.")
    facts: list[str] = Field(
        default_factory=list,
        description="Each fact on its own line with its exact value and source table, "
                    "e.g. 'inventory: CC-TEE-WHITE size S qty = 0'.",
    )
    actions_taken: list[str] = Field(
        default_factory=list,
        description="Anything you changed or filed, with ids, e.g. 'Filed payment request approval_id 1 for invoice 501 ($840.00)'.",
    )
    open_issues: list[str] = Field(
        default_factory=list,
        description="Anything still blocking the ticket or needing a human, stated specifically.",
    )


class AgentAction(BaseModel):
    agent: AgentName
    action: str = Field(description="What the agent did, e.g. 'check_restock CC-TEE-WHITE S x1'.")
    result: str = Field(description="The specific outcome with figures.")


class TicketDecision(BaseModel):
    """The Boss's final call on one ticket."""

    ticket_id: int
    status: TicketStatus
    summary: str = Field(description="What was found, with exact SKUs, quantities, dollar amounts, ids and dates.")
    actions: list[AgentAction] = Field(default_factory=list)
    pending_approval_ids: list[int] = Field(
        default_factory=list, description="payment_approvals ids waiting on a human."
    )
    draft_ids: list[int] = Field(default_factory=list, description="message_drafts ids created for this ticket.")
    reasoning: str = Field(description="Why this status, tied to the specific figures that support it.")


# ------------------------------------------------------------ run tracing

class TraceEvent(BaseModel):
    """One step in a run, for the dashboard to show what each agent did."""

    at: str = Field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    agent: AgentName
    kind: Literal["start", "delegate", "tool_call", "tool_result", "report", "error"]
    detail: str
    depth: int = 0


class TicketRunResult(BaseModel):
    ticket_id: int
    decision: TicketDecision | None
    error: str | None = None
    trace: list[TraceEvent]
    requests: int = Field(description="Model requests used across every agent in the run.")
    input_tokens: int
    output_tokens: int


# ------------------------------------------------------------ run state

@dataclass
class TeamDeps:
    """Passed to every agent run. chain is the delegation path so far
    (e.g. ['boss', 'accounting']) and is used to stop loops."""

    ticket_id: int
    run_id: str = ""
    chain: list[str] = field(default_factory=list)
    trace: list[TraceEvent] = field(default_factory=list)

    @property
    def depth(self) -> int:
        return max(0, len(self.chain) - 1)

    def log(self, agent: str, kind: str, detail: str) -> None:
        self.trace.append(TraceEvent(agent=agent, kind=kind, detail=detail, depth=self.depth))
