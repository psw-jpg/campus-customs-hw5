"""Shared plumbing for the Campus Customs agent team.

- One model for every agent: gpt-6-luna through Portkey, on the Responses API
  (gpt-6-luna rejects function tools on /chat/completions).
- One MCP server for every agent: campus-customs, loaded from the project's .mcp.json.
  Each agent only sees the MCP tools on its allowlist. All shop facts come from
  those MCP tools; there is no other path to the database.
- Delegation tools let any agent hand a task to another, with a depth limit and
  a no-cycles rule so agents can't bounce work back and forth forever.
- Every agent loop step is appended to output/audit_trail.json.
- Token and request budgets cap each response, each agent and each ticket.
"""

import os
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.exceptions import UsageLimitExceeded  # noqa: E402
import sys  # noqa: E402

from fastmcp import Client  # noqa: E402
from pydantic_ai.mcp import MCPToolset  # noqa: E402
from pydantic_ai.messages import RetryPromptPart, TextPart, ToolCallPart, ToolReturnPart  # noqa: E402
from pydantic_ai.models.openai import OpenAIResponsesModel  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.settings import ModelSettings  # noqa: E402
from pydantic_ai.usage import RunUsage, UsageLimits  # noqa: E402

import audit  # noqa: E402
from models import SpecialistReport, TeamDeps  # noqa: E402

BACKEND = Path(__file__).resolve().parent
PROJECT = BACKEND.parent
PROMPTS = BACKEND / "prompts"

# The only model allowed for this homework. Do not change.
MODEL_NAME = "gpt-6-luna"

# ----------------------------------------------------------- token budgets
MAX_OUTPUT_TOKENS_PER_RESPONSE = 4_000     # longest single model reply
MAX_INPUT_TOKENS_PER_REQUEST = 60_000      # stops a conversation from ballooning
AGENT_REQUEST_LIMIT = 10                   # model calls one specialist may make per task
AGENT_TOOL_CALL_LIMIT = 15                 # tool calls one specialist may make per task
AGENT_TOKEN_LIMIT = 120_000                # tokens one specialist may use per task
TICKET_REQUEST_LIMIT = 50                  # model calls across every agent on one ticket
TICKET_TOOL_CALL_LIMIT = 60                # tool calls across every agent on one ticket
TICKET_TOKEN_LIMIT = 400_000               # tokens across every agent on one ticket
MAX_DELEGATION_DEPTH = 2                   # boss -> specialist -> specialist, no deeper

MODEL_SETTINGS = ModelSettings(max_tokens=MAX_OUTPUT_TOKENS_PER_RESPONSE)
TICKET_LIMITS = UsageLimits(
    request_limit=TICKET_REQUEST_LIMIT,
    tool_calls_limit=TICKET_TOOL_CALL_LIMIT,
    total_tokens_limit=TICKET_TOKEN_LIMIT,
    per_request_input_tokens_limit=MAX_INPUT_TOKENS_PER_REQUEST,
)


def _load_env() -> None:
    """Load PORTKEY_API_KEY from the nearest .env at or above the project."""
    for folder in [PROJECT, *PROJECT.parents]:
        if (folder / ".env").exists():
            load_dotenv(folder / ".env")
            return


def build_model() -> OpenAIResponsesModel:
    _load_env()
    key = os.environ.get("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set; add it to .env.")
    client = AsyncOpenAI(
        api_key=key,
        base_url="https://api.portkey.ai/v1",
        default_headers={"x-portkey-provider": "openai"},
    )
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


MODEL = build_model()

# The campus-customs MCP server, exactly as registered in .mcp.json (paths in the
# file are relative to the project). With a single server, tool names stay plain
# (check_restock, pay_bill, ...), matching the prompts.
sys.path.insert(0, str(PROJECT / "mcp_server"))
from mcp_config import load_mcp_config  # noqa: E402

MCP = MCPToolset(Client(load_mcp_config(PROJECT)))

# name -> Agent. Filled in by each agent file via make_agent().
REGISTRY: dict[str, Agent] = {}

DELEGATE_DESCRIPTIONS = {
    "inventory": "Stock on hand by SKU and size, shortfalls, restock cost, vendor lead_days, "
                 "earliest arrival, and whether the vendor is blocked by an open invoice.",
    "accounting": "Cash balance, invoices and days overdue, payment requests via pay_bill and restock "
                  "purchase requests via request_restock_purchase (human approval required), payment "
                  "history, and discount quotes via quote_bulk_price.",
    "facilities": "The Chapel Street lease: monthly_rent, landlord, next_due, days until due, "
                  "verifying rent notices, and where stock sits in the shop.",
    "customer_service": "Saving message drafts to customers, student groups or the landlord. "
                        "Drafts only, never sent.",
}


def load_prompt(file_name: str) -> str:
    return (PROMPTS / file_name).read_text()


# ------------------------------------------------------------- audit + trace

def record(deps: TeamDeps, agent: str, event: str, step: int, **details) -> None:
    """Append one entry to output/audit_trail.json and a short line to the dashboard trace."""
    audit.append({
        "run_id": deps.run_id,
        "ticket_id": deps.ticket_id,
        "agent": agent,
        "chain": " -> ".join(deps.chain),
        "depth": deps.depth,
        "loop_step": step,
        "event": event,
        **details,
    })
    if event == "agent_start":
        deps.log(agent, "start", details["task"])
    elif event == "delegation":
        deps.log(agent, "delegate", f"-> {details['target']}: {details['task']}")
    elif event == "tool_call":
        deps.log(agent, "tool_call", f"{details['tool']}({details['args']})")
    elif event == "tool_result":
        deps.log(agent, "tool_result", f"{details['tool']} -> {details['result'][:300]}")
    elif event == "agent_output":
        deps.log(agent, "report", details["summary"])
    elif event.endswith(("refused", "error")):
        deps.log(agent, "error", details.get("reason") or details.get("error", event))


async def run_agent(name: str, prompt: str, deps: TeamDeps, usage: RunUsage, limits: UsageLimits):
    """Run one agent's loop and audit every step: each model response (with its
    token usage and requested tool calls) and each tool result."""
    agent = REGISTRY[name]
    record(deps, name, "agent_start", 0, task=prompt, model=MODEL_NAME,
           limits={"request_limit": limits.request_limit, "tool_calls_limit": limits.tool_calls_limit,
                   "total_tokens_limit": limits.total_tokens_limit,
                   "max_output_tokens_per_response": MAX_OUTPUT_TOKENS_PER_RESPONSE})
    step = 0
    async with agent.iter(prompt, deps=deps, usage=usage, usage_limits=limits) as run:
        async for node in run:
            if Agent.is_call_tools_node(node):
                # The model just answered: log what it said, what it wants to call, and what it cost.
                step += 1
                resp = node.model_response
                calls = [p for p in resp.parts if isinstance(p, ToolCallPart)]
                text = " ".join(p.content for p in resp.parts if isinstance(p, TextPart))
                record(deps, name, "model_response", step,
                       model=resp.model_name,
                       input_tokens=resp.usage.input_tokens, output_tokens=resp.usage.output_tokens,
                       text=audit.clip(text) if text else None,
                       tool_calls_requested=[c.tool_name for c in calls],
                       running_total={"requests": usage.requests, "tokens": usage.total_tokens})
                for c in calls:
                    if not c.tool_name.startswith("final_result"):
                        record(deps, name, "tool_call", step, tool=c.tool_name, tool_call_id=c.tool_call_id,
                               args=audit.clip(c.args_as_dict()), sensitive=audit.SENSITIVE_TOOLS.get(c.tool_name))
            elif Agent.is_model_request_node(node):
                # Tool results go back to the model in the next request.
                for part in node.request.parts:
                    if isinstance(part, ToolReturnPart) and not part.tool_name.startswith("final_result"):
                        record(deps, name, "tool_result", step, tool=part.tool_name, tool_call_id=part.tool_call_id,
                               result=audit.clip(part.content), sensitive=audit.SENSITIVE_TOOLS.get(part.tool_name))
                    elif isinstance(part, RetryPromptPart):
                        record(deps, name, "tool_retry_error", step, tool=part.tool_name, error=audit.clip(part.content))
    output = run.result.output
    record(deps, name, "agent_output", step, summary=output.summary, output=output.model_dump(),
           agent_requests=usage.requests, agent_tokens=usage.total_tokens)
    return output


# ---------------------------------------------------------------- delegation

async def delegate(ctx: RunContext[TeamDeps], target: str, task: str) -> str:
    """Run another agent on one task and return its report as JSON text."""
    deps = ctx.deps
    caller = deps.chain[-1]

    def refuse(reason: str) -> str:
        record(deps, caller, "delegation_refused", 0, target=target, task=task, reason=reason)
        return reason

    if target in deps.chain:
        return refuse(f"Refused: {target} is already working on this request "
                      f"({' -> '.join(deps.chain)}). Use what you have.")
    if len(deps.chain) > MAX_DELEGATION_DEPTH:
        return refuse(f"Refused: delegation depth limit ({MAX_DELEGATION_DEPTH}) reached. "
                      f"Answer with the facts you have.")

    # Each specialist gets its own budget, capped by whatever is left for the ticket.
    left_requests = TICKET_REQUEST_LIMIT - ctx.usage.requests
    left_tokens = TICKET_TOKEN_LIMIT - ctx.usage.total_tokens
    if left_requests <= 1 or left_tokens <= 5_000:
        return refuse(f"Refused: ticket budget nearly used ({ctx.usage.requests} requests, "
                      f"{ctx.usage.total_tokens} tokens).")
    limits = UsageLimits(
        request_limit=min(AGENT_REQUEST_LIMIT, left_requests - 1),
        tool_calls_limit=AGENT_TOOL_CALL_LIMIT,
        total_tokens_limit=min(AGENT_TOKEN_LIMIT, left_tokens),
        per_request_input_tokens_limit=MAX_INPUT_TOKENS_PER_REQUEST,
    )

    record(deps, caller, "delegation", 0, target=target, task=task)
    child = TeamDeps(ticket_id=deps.ticket_id, run_id=deps.run_id, chain=[*deps.chain, target], trace=deps.trace)
    child_usage = RunUsage()
    try:
        report = await run_agent(target, f"Ticket {deps.ticket_id}. Task from {caller}: {task}",
                                 child, child_usage, limits)
    except UsageLimitExceeded as e:
        record(child, target, "budget_exceeded_error", 0, error=str(e))
        return f"{target} stopped: it hit its budget ({e}). Work with the facts you already have."
    finally:
        ctx.usage.incr(child_usage)  # roll the specialist's usage into the ticket total
    return report.model_dump_json() if isinstance(report, SpecialistReport) else str(report)


def make_agent(name: str, prompt_file: str, mcp_tools: list[str], delegates_to: list[str], output_type) -> Agent:
    """Build one team member with its prompt, its slice of the MCP server, and delegation tools."""
    allowed = set(mcp_tools)
    toolset = MCP.filtered(lambda ctx, tool_def: tool_def.name in allowed)
    agent = Agent(
        MODEL,
        name=name,
        deps_type=TeamDeps,
        output_type=output_type,
        instructions=load_prompt(prompt_file),
        toolsets=[toolset],
        model_settings=MODEL_SETTINGS,
        retries=2,
    )

    for target in delegates_to:
        _add_delegate_tool(agent, target)

    REGISTRY[name] = agent
    return agent


def _add_delegate_tool(agent: Agent, target: str) -> None:
    async def delegate_tool(ctx: RunContext[TeamDeps], task: str) -> str:
        return await delegate(ctx, target, task)

    agent.tool(
        delegate_tool,
        name=f"delegate_to_{target}",
        description=(
            f"Hand one specific task to the {target.replace('_', ' ').title()} agent and get its report back. "
            f"It owns: {DELEGATE_DESCRIPTIONS[target]} Include the exact SKU, size, qty, lease id or invoice id."
        ),
    )
