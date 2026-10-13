# Campus Customs MCP Server

## What it's for

This is the shared toolbox for the Campus Customs multi-agent team. The Boss, Inventory, Accounting, Facilities and Customer Service agents all connect to this one server to look up shop data and act on open tickets. It's built with [FastMCP](https://gofastmcp.com) and enforces the shop's rules itself, so no agent can skip them:

- "Today" is always `desk.date_today`, never the real clock.
- Vendor lead times come from the `vendors` table, and a vendor with an open invoice can't ship.
- Every payment needs human approval, and no payment may push a cash balance below zero.
- Tools only return values stored in the database. Nothing is estimated or made up.

## Data file

The server reads and writes **`data/campus_customs_new.db`**, the working copy.

The original, `data/campus_customs.db`, is never modified. `db.reset_working_db()` copies the original over the working copy, and it's run before every full ticket run.

The server adds two tables to the working copy, recreated automatically after every reset:

- `payment_approvals` tracks each payment request and the human decision on it. Approving a payment is done with `db.decide_approval()`, which is deliberately **not** an MCP tool, so no agent can approve its own payment.
- `message_drafts` holds customer messages saved as drafts. There is no send tool.
- `purchase_orders` holds restock orders: `pending_approval`, `ordered` (with `expected_arrival`) or `rejected`.

This server is the only way the agents reach shop data. The backend has no separate tool layer that reads the database.

## Tools

19 tools in total. Every one returns values straight from the database.

### Ticket-unlocking tools

| Tool | Ticket | What it does |
|---|---|---|
| `check_restock(sku, size, qty)` | 101: Bulldog Tee, size S | Reports stock on hand and any shortfall. For each vendor it shows restock cost, `lead_days`, the earliest arrival date, and whether an open invoice blocks it from shipping. |
| `pay_bill(kind, ref_id, requested_by)` | 102: rent for lease 1 (also invoice 501) | Pays rent (`kind="rent"`, `ref_id` = lease id) or a vendor invoice (`kind="invoice"`, `ref_id` = invoice id). The first call files an approval request and moves no money. After a human approves it, the next call pays it and records the approver in `payments`. Rejects anything that would overdraw the account, and won't file the same bill twice. |
| `quote_bulk_price(sku, size, qty, discount_pct)` | 103: 20 Navy Hoodies, size M, bulk discount | Prices an order at a proposed discount off `list_price`. Shows the margin over `unit_cost` and the largest discount that still covers cost, and rejects anything below cost. Also reports stock on hand and any shortfall. |

### Lookup and workflow tools

| Tool | Tables | What it does |
|---|---|---|
| `get_shop_date()` | `desk` | The shop's "today" and desk notes. |
| `list_tickets(status="open")` | `tickets` | Tickets on the board, oldest first; `status=None` for all. |
| `get_ticket(ticket_id)` | `tickets`, `leases`, `invoices`, `inventory`, `pricing` | One ticket with its linked lease, invoice, stock row and pricing. |
| `update_ticket(ticket_id, status, note)` | `tickets`, `desk` | Sets the status (`open`, `in_progress`, `waiting_approval`, `blocked`, `needs_human`, `resolved`) and appends a dated note. |
| `get_inventory(sku=None, size=None)` | `inventory`, `pricing` | Stock rows with location, `unit_cost` and `list_price`. |
| `get_low_stock(threshold=3)` | `inventory` | Stock rows at or below the threshold, lowest first. |
| `list_vendors()` | `vendors`, `invoices`, `desk` | Every vendor with specialty, `lead_days`, earliest arrival, `can_ship` and any blocking invoices. |
| `get_cash_balance()` | `cash_accounts` | Every cash account and its balance. |
| `list_invoices(status=None)` | `invoices`, `vendors`, `desk` | Invoices with vendor name and days overdue. |
| `list_payments()` | `payments` | Every payment made, with the human who approved it. |
| `list_payment_approvals(status=None)` | `payment_approvals` | Payment requests: pending, approved, rejected or paid. |
| `list_leases()` | `leases`, `desk` | Leases with rent, landlord, `next_due` and days until due. |
| `request_restock_purchase(sku, size, qty, vendor_id, requested_by, ticket_id=None)` | `inventory`, `pricing`, `vendors`, `invoices`, `cash_accounts` | Files a restock purchase order (cost = `unit_cost` × qty) for human approval. Moves no money. Rejects couriers and anything cash can't cover. A blocked vendor can be requested but won't be paid until its invoice is. Paid through `pay_bill(kind="purchase")` once approved. |
| `list_purchase_orders(status=None)` | `purchase_orders`, `vendors` | Restock orders and their status and arrival dates. |
| `draft_customer_message(recipient, subject, body, drafted_by, ticket_id=None)` | `message_drafts` | Saves a message as a draft for human review. Never sends. |
| `list_message_drafts(ticket_id=None)` | `message_drafts` | Saved drafts, optionally for one ticket. |

## Files

- `server.py`: the FastMCP server and its 19 tools.
- `db.py`: the database connection, reset, and shop-rule checks (funds, approval).
- `smoke_test.py`: connects over MCP and tests the three ticket-unlocking tools against a temporary copy of the database.
- `mcp_config.py`: loads `.mcp.json` and resolves its relative paths against the project folder.

## Connecting

The server is registered as `campus-customs` in the project's `.mcp.json` (with paths relative to the project) and in the `.mcp.json` at the `AI Foundations` root, which is where Claude Code sessions in this folder load it from. Claude Code launches it over stdio with the project's `.venv` Python, so there's no need to start it by hand.

## Smoke test

`smoke_test.py` launches the server from `.mcp.json` and calls the three ticket-unlocking tools over MCP. It checks each result against a direct database read and saves the evidence to `output/mcp_smoke.json`. It runs against a temporary copy of the original database, so it never touches the working copy, and it never approves a payment. From `homework/5a`:

```bash
.venv/bin/python mcp_server/smoke_test.py
```
