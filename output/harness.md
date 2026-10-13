# Campus Customs Agent Harness

Reference for the multi-agent team that runs the Campus Customs shop: open tickets land on a board, a Boss agent delegates them to four specialists, and every shop fact and action goes through one MCP server.

**Contents:** [Tables](#tables) · [Tickets and results](#open-tickets) · [MCP server and tools](#mcp-server-mcp_server) · [The five agents](#agent-team-backend) · [Audit trail](#audit-trail-outputaudit_trailjson) · [Token limits](#token-limits) · [Safety guardrails](#safety-guardrails) · [API routes](#dashboard-api-backendmainpy) · [Dashboard](#dashboard-frontend) · [Deliverables](#deliverables)

**Model:** every agent uses `gpt-6-luna` through Portkey (`PORTKEY_API_KEY` from `.env`), on the Responses API.

**Databases**
- `data/campus_customs.db`: the original. Never modified.
- `data/campus_customs_new.db`: the working copy the agents read and write. Reset from the original before every full ticket run.

---

## Tables

### `desk`
Fields: `date_today` (TEXT), `notes` (TEXT)

**Why it matters:** `date_today` (2026-08-31) is the shop's "today", so every agent uses it, not the real clock, to decide what is overdue, how many days until rent is due, and when a restock would arrive.

### `inventory`
Fields: `sku` (TEXT), `name` (TEXT), `size` (TEXT), `qty` (INTEGER), `location` (TEXT). Primary key is (`sku`, `size`).

**Why it matters:** The Inventory agent checks stock per SKU and size here (for example, Tee S and Crest Mug are at 0, Hoodie M has 8) to decide whether an order can be filled now or needs a restock.

### `pricing`
Fields: `sku` (TEXT, primary key), `unit_cost` (REAL), `list_price` (REAL)

**Why it matters:** Accounting uses `unit_cost` to price restocks and `list_price` against `unit_cost` to set a floor on discounts, so a bulk deal like ticket 103 never sells below cost.

### `vendors`
Fields: `id` (INTEGER, primary key), `name` (TEXT), `specialty` (TEXT), `lead_days` (INTEGER)

**Why it matters:** Inventory picks the right supplier by `specialty`, and every restock arrival date must be calculated as `date_today` + `lead_days` from this table, never guessed.

### `leases`
Fields: `id` (INTEGER, primary key), `space_name` (TEXT), `landlord` (TEXT), `monthly_rent` (REAL), `next_due` (TEXT), `notes` (TEXT)

**Why it matters:** Facilities uses this to confirm the Chapel Street rent ($2,400, due 2026-09-02) before Accounting prepares the payment, which is the shop's largest fixed overhead.

### `cash_accounts`
Fields: `name` (TEXT, primary key), `balance` (REAL), `date` (TEXT)

**Why it matters:** This holds the only cash the shop has ($3,400 in checking), and the pay tool must reject any payment that would push `balance` below zero.

### `payments`
Fields: `id` (INTEGER, primary key), `kind` (TEXT), `ref_id` (INTEGER), `amount` (REAL), `account` (TEXT), `paid_at` (TEXT), `approved_by` (TEXT)

**Why it matters:** This is the audit trail for money out (empty at start). Each row records what was paid (`kind` + `ref_id`) and which human approved it in `approved_by`, which proves the human-approval rule was followed.

### `invoices`
Fields: `id` (INTEGER, primary key), `vendor_id` (INTEGER, references `vendors.id`), `amount` (REAL), `due_date` (TEXT), `status` (TEXT), `description` (TEXT)

**Why it matters:** Accounting finds overdue bills here, and any `open` invoice blocks that vendor from shipping. Invoice 501 ($840, due 2026-08-28) is overdue and blocks Bulldog Print Co.

### `tickets`
Fields: `id` (INTEGER, primary key), `type` (TEXT), `requester` (TEXT), `subject` (TEXT), `sku` (TEXT), `size` (TEXT), `qty` (INTEGER), `lease_id` (INTEGER, references `leases.id`), `invoice_id` (INTEGER, references `invoices.id`), `status` (TEXT), `notes` (TEXT), `created_at` (TEXT)

**Why it matters:** This is the board the Boss agent reads. `type` decides which specialists to call, and the linked `sku`/`size`/`qty`, `lease_id` and `invoice_id` give them exactly what to look up.

### Working-copy tables added by the MCP server
These live only in `campus_customs_new.db` and are recreated empty after every reset. The original database's schema is never touched.

| Table | Fields | Why it matters |
|---|---|---|
| `payment_approvals` | `id`, `kind` (`invoice`/`rent`/`purchase`), `ref_id`, `amount`, `account`, `reason`, `requested_by`, `status` (`pending`/`approved`/`rejected`/`paid`), `approved_by`, `created_at`, `decided_at` | Enforces the human-approval rule: agents can only create `pending` rows, and only the human approve route moves a row to `approved` and records the approver's name. |
| `purchase_orders` | `id`, `sku`, `size`, `qty`, `vendor_id`, `unit_cost`, `total`, `ticket_id`, `status` (`pending_approval`/`ordered`/`rejected`), `requested_by`, `created_at`, `ordered_at`, `expected_arrival` | Records restock purchases. Cost comes from `pricing.unit_cost`, and `expected_arrival` = `desk.date_today` + `vendors.lead_days` once a human approves. |
| `message_drafts` | `id`, `ticket_id`, `recipient`, `subject`, `body`, `drafted_by`, `status` (always `draft`), `created_at` | Holds every customer and landlord message as a draft; nothing is ever sent. |

---

## Open Tickets

All three are `open` as of 2026-08-31, and all three draw on the same $3,400.

| # | Type | Requester | Request | What the agents must handle |
|---|---|---|---|---|
| 101 | `customer_order` | Tauhid Zaman | 1 × Bulldog Tee (`CC-TEE-WHITE`), size S | S stock is 0. The ticket links invoice 501, which is open and overdue and blocks Bulldog Print Co from shipping. Paying it ($840) needs human approval. Restock arrives 2026-09-05 at the earliest (5 lead days). Customer Service drafts an update. |
| 102 | `rent_notice` | Elm City Properties | Lease 1 rent due | $2,400 due 2026-09-02. Facilities confirms it and Accounting prepares the payment, which needs human approval. |
| 103 | `price_override` | Yale AI Club | 20 × Navy Hoodie (`CC-HOOD-NAVY`), size M, bulk discount | Only 8 M in stock, so 12 more are needed from Bulldog Print Co (blocked until invoice 501 is paid; about $264 at $22 each). The discount must stay above the $22 cost against the $58 list price. The Boss makes the final call. |

**Cash check:** invoice 501 + rent = $3,240, leaving $160. That is not enough for the ~$264 hoodie reprint, so the Boss must prioritize and the pay tool must block anything that would go negative.

### Results of the real run (2026-10-12)
The database was reset first, so checking started at **$3,400.00**. Each ticket was run through `POST /api/tickets/{id}/run`. A human (Paul) approved each payment on the dashboard, and tickets 101 and 102 were run once more so the Boss could confirm them.

| Ticket | Board | Boss's final status | Outcome | Money out |
|---|---|---|---|---|
| 101 | ✓ resolved | `blocked` (awaiting delivery) | Invoice 501 paid ($840.00) to unblock Bulldog Print Co. A 1-tee restock was purchased (PO 1, $8.00), arriving 2026-09-05. Draft to Tauhid saved. | $848.00 |
| 102 | ✓ resolved | `resolved` | Notice verified against lease 1. Rent paid ($2,400.00), and `next_due` moved to 2026-10-02. Draft to the landlord saved. | $2,400.00 |
| 103 | ✓ resolved | `blocked` (no cash) | 8 of 20 hoodies offered at 20% off ($46.40 each, $371.20). The 12-unit restock ($264.00) didn't fit in $152.00 ($112.00 short), so no purchase was filed. | $0.00 |

**Cash:** $3,400.00 − $840.00 − $8.00 − $2,400.00 = **$152.00**, which matches `cash_accounts.checking`. Full detail is in `output/desk_tickets.html` (Actual sections and Cash tab), `output/resolved_tickets.json` and `output/resolved_board.html`.

---

## MCP Server (`mcp_server/`)

Built with FastMCP 4.1 and shared by every agent on the team. `server.py` defines the tools, and `db.py` holds the database connection and the shop-rule checks. Every tool reads and writes `data/campus_customs_new.db` only and returns values straight from its tables. Nothing is estimated or made up. **The MCP server is the only way agents reach shop data;** the backend has no second tool layer, and even the runner gets its list of open tickets through the MCP `list_tickets` tool.

**Extra tables (working copy only, recreated after each reset):**
- `payment_approvals`: each payment request and the human decision on it (`pending` → `approved`/`rejected` → `paid`). Approving is done by `db.decide_approval()`, which is deliberately **not** an MCP tool, so no agent can approve its own payment.
- `message_drafts`: customer messages saved as drafts. There is no send tool.
- `purchase_orders`: restock orders the agents request (`pending_approval` → `ordered` with an `expected_arrival`, or `rejected`).

### Ticket-unlocking tools

| Tool | Tables it reads | Ticket it unlocks | Why it's the right tool |
|---|---|---|---|
| `check_restock(sku, size, qty)` | `inventory`, `pricing`, `vendors`, `invoices`, `desk` | **101**: Tauhid Zaman's 1 × Classic Bulldog Tee, size S | Ticket 101 can't be filled because `CC-TEE-WHITE` size S has `qty` 0, and this tool shows that shortfall together with the fact that Bulldog Print Co can't ship while invoice 501 ($840, due 2026-08-28) is open, giving the earliest arrival of 2026-09-05 from `desk.date_today` plus its 5 `lead_days`. |
| `pay_bill(kind, ref_id, requested_by)` | `leases`, `invoices`, `cash_accounts`, `payment_approvals` (writes `payments`) | **102**: Elm City Properties rent notice for lease 1 | Ticket 102 is the $2,400 Chapel Street rent due 2026-09-02, and `pay_bill(kind="rent", ref_id=1)` pays exactly the `leases.monthly_rent` amount, but only after a human approves it and only if checking's $3,400 stays at or above zero. |
| `quote_bulk_price(sku, size, qty, discount_pct)` | `pricing`, `inventory` | **103**: Yale AI Club's 20 × Navy Hoodie, size M, at a bulk discount | Ticket 103 asks for a bulk discount on 20 `CC-HOOD-NAVY` size M, and this tool prices any proposed discount off the $58 `list_price`, rejects anything below the $22 `unit_cost` (a 62.07% maximum), and flags that only 8 are on hand, leaving a 12-unit shortfall. |

### All MCP tools

| Tool | Tables it reads | Tables it writes | Agents with access |
|---|---|---|---|
| `check_restock` | `inventory`, `pricing`, `vendors`, `invoices`, `desk` | none | Inventory |
| `pay_bill` | `leases`, `invoices`, `purchase_orders`, `cash_accounts`, `payment_approvals`, `desk` | `payment_approvals`; once a human approves: `cash_accounts`, `payments`, and `invoices.status`, `leases.next_due` or `purchase_orders.status` | Accounting |
| `quote_bulk_price` | `pricing`, `inventory` | none | Accounting |
| `request_restock_purchase` | `inventory`, `pricing`, `vendors`, `invoices`, `cash_accounts`, `desk` | `purchase_orders`, `payment_approvals` (no money moves) | Accounting |
| `list_purchase_orders` | `purchase_orders`, `vendors` | none | Boss, Inventory, Accounting |
| `get_shop_date` | `desk` | none | all five |
| `list_tickets` | `tickets` | none | Boss |
| `get_ticket` | `tickets` (+ linked `leases`, `invoices`, `inventory`, `pricing`) | none | Boss, Customer Service |
| `update_ticket` | `tickets`, `desk` | `tickets.status`, `tickets.notes` | Boss |
| `get_inventory` | `inventory`, `pricing` | none | Inventory, Facilities |
| `get_low_stock` | `inventory` | none | Inventory |
| `list_vendors` | `vendors`, `invoices`, `desk` | none | Inventory, Accounting |
| `get_cash_balance` | `cash_accounts` | none | Accounting |
| `list_invoices` | `invoices`, `vendors`, `desk` | none | Accounting |
| `list_payments` | `payments` | none | Accounting |
| `list_payment_approvals` | `payment_approvals` | none | Boss, Accounting, Facilities |
| `list_leases` | `leases`, `desk` | none | Facilities |
| `draft_customer_message` | none | `message_drafts` (draft only, never sent) | Customer Service |
| `list_message_drafts` | `message_drafts` | none | Boss, Customer Service |

### Connection and smoke test

- Registered as `campus-customs` in `homework/5a/.mcp.json` and in the `AI Foundations` root `.mcp.json`, launched over stdio with `.venv/bin/python mcp_server/server.py`.
- `mcp_server/smoke_test.py` connects over MCP, calls the three ticket-unlocking tools, and compares each key value against a direct database read. Results are in `output/mcp_smoke.json`, and all three tools match the database.

---

## Agent Team (`backend/`)

PydanticAI agents, all on **`gpt-6-luna`** through Portkey (`PORTKEY_API_KEY` from `.env`). They use the **Responses API**, because `gpt-6-luna` rejects function tools on `/chat/completions`. Each agent connects to the `campus-customs` MCP server from `.mcp.json` but only sees the tools on its allowlist.

| Agent | Role | MCP tools | Delegates to | Output |
|---|---|---|---|---|
| **Boss** (`boss.py`, `prompts/boss.md`) | Reads the ticket, delegates, ranks competing cash needs, approves or rejects discounts, makes the final call and records the ticket status. | `get_shop_date`, `get_ticket`, `list_tickets`, `update_ticket`, `list_payment_approvals`, `list_message_drafts`, `list_purchase_orders` | all four specialists | `TicketDecision` |
| **Inventory** (`inventory.py`, `prompts/inventory.md`) | Stock on hand by SKU and size, shortfalls, restock cost, vendor lead times, and whether a vendor is blocked by an open invoice. | `get_shop_date`, `check_restock`, `get_inventory`, `get_low_stock`, `list_vendors`, `list_purchase_orders` | Accounting, Facilities, Customer Service | `SpecialistReport` |
| **Accounting** (`accounting.py`, `prompts/accounting.md`) | Cash, invoices, days overdue, payment and restock-purchase requests for human approval, payment history, and discount quotes. The only agent that can call `pay_bill` or `request_restock_purchase`. | `get_shop_date`, `pay_bill`, `request_restock_purchase`, `quote_bulk_price`, `get_cash_balance`, `list_invoices`, `list_vendors`, `list_payments`, `list_payment_approvals`, `list_purchase_orders` | Inventory, Facilities, Customer Service | `SpecialistReport` |
| **Facilities** (`facilities.py`, `prompts/facilities.md`) | The Chapel Street lease: rent amount, due date and days left. Verifies rent notices against `leases`, and knows where stock sits. | `get_shop_date`, `list_leases`, `get_inventory`, `list_payment_approvals` | Inventory, Accounting, Customer Service | `SpecialistReport` |
| **Customer Service** (`customer_service.py`, `prompts/customer_service.md`) | Drafts messages to customers, student groups and the landlord. The only agent that can save drafts, and nothing it writes is sent. | `get_shop_date`, `get_ticket`, `draft_customer_message`, `list_message_drafts` | Inventory, Accounting, Facilities | `SpecialistReport` |

**Delegation (full connectivity):** every agent can hand a task to any other agent with a `delegate_to_<agent>` tool. Two guards stop runaway loops: an agent can't delegate to anyone already on the current chain, and chains stop at depth 2 (Boss → specialist → specialist).

**Runs:** `backend/run_tickets.py` resets `campus_customs_new.db` to the original, then has the Boss work each ticket. Data types live in `backend/models.py`; shared setup (model, MCP connection, delegation, audit, budgets) lives in `backend/team.py`.

---

## Audit Trail (`output/audit_trail.json`)

Every agent loop step is appended as it happens by `backend/audit.py`. **The file is never wiped:** each run adds to the end, and it stays a valid JSON array. Writes go through a temp file and an atomic rename, so a crash can't corrupt earlier entries.

Every entry has `at` (timestamp), `run_id`, `ticket_id`, `agent`, `chain` (e.g. `boss -> inventory`), `depth`, `loop_step` and `event`. The events are:

| Event | Key information recorded |
|---|---|
| `run_start` / `run_end` | model, confirmation that the working copy was reset, total requests and tokens |
| `tickets_selected` | the ticket ids for the run |
| `agent_start` | the exact task the agent was given and its budget |
| `model_response` | model name, input/output tokens for that response, any text, the tool calls requested, and the running total |
| `tool_call` | tool name, call id, exact arguments, and a `sensitive` flag (`money`, `pricing`, `customer_message`, `ticket_change`) |
| `tool_result` | tool name, call id and the result returned by the MCP server |
| `tool_retry_error` | a tool call the model got wrong and was asked to retry |
| `delegation` / `delegation_refused` | who handed what task to whom, or why it was refused (cycle, depth or budget) |
| `budget_exceeded_error` | the agent and the limit it hit |
| `agent_output` | the agent's full structured answer and the requests and tokens it used |
| `ticket_end` / `ticket_error` | final status and the ticket's total requests and tokens |

Matching `tool_call_id`s link each call to its result, so an auditor can trace any payment request or draft back to the agent, the chain of delegations and the model response that triggered it.

---

## Token Limits

Set in `backend/team.py` and enforced by PydanticAI `UsageLimits`. A run that hits a limit stops cleanly and is logged.

| Limit | Value | Why |
|---|---|---|
| Output tokens per model response | 4,000 | caps any single reply |
| Input tokens per request | 60,000 | stops a long conversation from ballooning in cost |
| Requests per specialist task | 10 | a specialist can't loop on one question |
| Tool calls per specialist task | 15 | the same, for tools |
| Tokens per specialist task | 120,000 | caps each delegated task |
| Requests per ticket (all agents) | 50 | one shared budget for the whole ticket |
| Tool calls per ticket (all agents) | 60 | the same, for tools |
| Tokens per ticket (all agents) | 400,000 | hard ceiling on spend per ticket |
| Delegation depth | 2 | Boss → specialist → specialist, no deeper |

Each specialist's budget is also capped by whatever is left of the ticket budget, and its usage rolls up into the ticket total.

---

## Safety Guardrails

The guardrails a business like Campus Customs needs once agents touch real customers and real money:

- **A human approves every payment and every restock purchase.** Agents can only request; approving isn't an agent tool, and the approver's name is saved on every payment. The approved amount is locked: if it changes, a new approval is needed.
- **No overdrafts, no duplicates, money only goes out.** `pay_bill` rejects anything the balance can't cover, and won't file the same bill twice.
- **Customers are never contacted automatically.** Customer Service only saves drafts, a human sends them, and no send tool exists.
- **Prices never go below cost.** Discounts must be quoted by `quote_bulk_price`, and the Boss approves them within the `unit_cost` floor.
- **Least privilege.** Each agent sees only the tools its job needs; only Accounting can touch payments, and only Customer Service can write drafts.
- **Facts only from the database.** Agents must cite tool results and say "unknown" rather than guess. Ticket text is treated as a claim and verified (e.g. Facilities checks a rent notice against `leases`), which also defends against fake or manipulated requests.
- **Private data stays private.** Customer messages never reveal costs, margins, cash balances or vendor debts. `PORTKEY_API_KEY` stays in `.env` and never appears in logs or the audit trail.
- **Full, append-only audit trail** of every model response, tool call and delegation.
- **Spend and loop limits** (see Token Limits) so a confused agent can't run up costs.
- **Sandboxed data.** Agents work on `campus_customs_new.db`, which is reset before each run; the original is never touched.
- **No purchases from a blocked vendor.** A restock purchase can be requested while its vendor has an open invoice, but it is refused at payment time until that invoice is paid. Couriers can't be used as suppliers.
- **One run at a time.** The API refuses a second run (409) so two runs can't commit the same cash, and reset is refused while a run is going.

**Seen working in the real run:** every payment waited for a human click (approvals 1–3, all approved by Paul). The loop guard refused one handoff on ticket 102 (Facilities → Accounting while Accounting was already waiting on Facilities). Accounting declined to file the $264.00 hoodie restock that cash couldn't cover. All five customer and landlord messages stayed drafts.
- **Before going live, a real shop would also add:** dual approval above a dollar threshold, verification of any change to a vendor's or landlord's payment details (a common fraud route), a daily payment cap, and an escalation path that sends anything ambiguous to `needs_human` instead of guessing.

---

## Dashboard API (`backend/main.py`)

FastAPI, started from `backend/` with `uvicorn main:app --reload --port 8000`. It opens one MCP connection at startup that the routes and the agent runs share. Every shop read goes through the MCP server; the only direct steps are the two human-only actions (approve and reset), which are deliberately not agent tools. CORS allows the Vite dashboard on port 5181 (5173, 5174 and 5180 are taken by older lecture apps on this machine).

### Routes (base URL `http://localhost:8000`)

- `GET /api/tickets`: returns every ticket and says whether it is open, running or resolved (resolved once the crew finishes a run; `status` keeps the Boss's exact outcome).
- `POST /api/tickets/{ticket_id}/run`: starts the agent team on that ticket and returns a `run_id` right away.
- `GET /api/runs/{run_id}`: says whether a run is still going, done or errored, with the Boss's decision and token use.
- `GET /api/tickets/{ticket_id}/summary`: a short summary of what each agent did on the ticket's latest run (final answer, tools used, handoffs, tokens).
- `GET /api/purchase-orders`: lists restock purchase orders and their status, with arrival dates for ordered ones.
- `GET /api/events`: returns the latest audit trail entries, showing what each agent said and which tools it used (filter with `?ticket_id=`, `?run_id=`, `?limit=`).
- `GET /api/approvals`: lists the payment requests the agents prepared, including the ones waiting for a human click.
- `POST /api/approvals/{approval_id}/approve`: a human approves a payment or restock purchase (`{"approved_by": "<name>"}`) and it is paid; the only route that takes cash out of checking.
- `POST /api/approvals/{approval_id}/reject`: a human rejects the request (`{"rejected_by": "<name>"}`), and no money moves.
- `GET /api/cash`: returns the current `checking` balance from `cash_accounts`.
- `POST /api/reset`: copies the original database over the working copy for a fresh run, keeping the audit trail.
- `GET /api/health`: confirms the server is up and shows the model the agents use.

**Running a ticket doesn't reset the database.** That way, approvals and payments from one ticket carry into the next, as in the real shop. For a fresh full run, call `POST /api/reset` first. Every approve, reject and reset is written to the audit trail with the person's name.

---

## Dashboard (`frontend/`)

Vite + React + TypeScript, started from `frontend/` with `npm run dev` at **http://localhost:5181**. Ports 5173, 5174 and 5180 are held by older lecture apps on this machine. It calls only the backend on port 8000. Full design rationale is in `output/design.md`.

| Area | What it shows | Route(s) it uses |
|---|---|---|
| **Order Board** | The three tickets as pinned order slips: Open, ● Crew working, or ✓ Resolved with a DONE stamp and the Boss's outcome. Pick one and **Send in the crew**. | `GET /api/tickets`, `POST /api/tickets/{id}/run` |
| **The Crew** | Mr. Krabs (Boss), SpongeBob (Inventory), Squidward (Accounting), Sandy (Facilities) and Patrick (Customer Service). The active agent lifts, glows and talks, with its latest line in a speech bubble. | `GET /api/events?run_id=` (every second during a run) |
| **Kitchen Radio** | Every step live: tasks, plain-English tool calls (raw call one click away), handoffs indented by depth, reports, and money and customer flags. Each agent has its own color and type voice. | `GET /api/events`, `GET /api/runs/{run_id}` |
| **Needs Your OK** | Payments and purchases waiting for a human, with a coverage check against the till. Approve & pay needs your name. Recent decisions and ordered restocks are listed below. | `GET /api/approvals`, `POST /api/approvals/{id}/approve`, `POST /api/approvals/{id}/reject`, `GET /api/purchase-orders` |
| **Shift Report** | Mr. Krabs' final call and reasoning, plus one card per agent with its summary, tools, handoffs and tokens. | `GET /api/tickets/{id}/summary` |
| **Treasure chest** | Live checking balance; counts down and floats the amount on every payment. | `GET /api/cash` |
| **Fresh shift** | Resets the working database after a confirmation dialog. | `POST /api/reset` |
| **Celebrations** | **Plankton** dashes across with a bubble trail when a payment (invoice or rent) is approved. **Gary** slides across with a slime trail when a restock purchase is approved. There's no celebration if the backend refuses. | the approve response's `kind` |

---

## Deliverables

| File | What it is |
|---|---|
| `output/harness.md` | This reference: tables, MCP tools, agents, API routes, dashboard, safety, limits and results |
| `output/mcp_smoke.json` | Evidence that the three ticket-unlocking MCP tools return database values |
| `output/audit_trail.json` | Append-only log of every agent loop step, delegation, tool call, human approval and reset |
| `output/desk_tickets.html` | Per-ticket Expected vs. Actual, plus the itemized Cash tab |
| `output/resolved_tickets.json` | Each ticket's id, final status, short outcome, agent contributions and human approvals |
| `output/resolved_board.html` | Double-clickable page with a screenshot of the board showing all three tickets resolved (image also saved as `resolved_board.png`) |
| `output/design.md` | Why the dashboard looks and works the way it does |
