# Campus Customs: Multi-Agent Shop Operations

MGT 409 · AI Foundations for Managers · Homework 5a

A team of five AI agents runs the Campus Customs shop. Open tickets land on a board; the **Boss** reads each one, delegates to **Inventory**, **Accounting**, **Facilities** and **Customer Service**, and makes the final call. Every shop fact and action goes through one **MCP server**. A **FastAPI backend** runs the team, and a **React dashboard** (SpongeBob themed) lets you watch the agents work and approve payments.

| Piece | Folder | Tech | Runs on |
|---|---|---|---|
| MCP server (19 shop tools) | `mcp_server/` | FastMCP | stdio (launched for you) |
| Agent team + API | `backend/` | PydanticAI + FastAPI, `gpt-6-luna` via Portkey | http://localhost:8000 |
| Dashboard | `frontend/` | Vite + React + TypeScript | http://localhost:5181 |
| Data | `data/` | SQLite | `campus_customs.db` (original), `campus_customs_new.db` (working copy) |
| Results and docs | `output/` | | `harness.md`, `design.md`, `desk_tickets.html`, `resolved_tickets.json`, `resolved_board.html`, `audit_trail.json` |

**Shop rules the system enforces:** "today" is `desk.date_today`; vendor lead times come from `vendors`; a vendor with an open invoice won't ship; every payment and purchase needs a human approval; no payment may make the balance negative (cash only goes out); customer messages are drafts only, never sent.

---

## Setup (once)

You need Python 3.12+ and Node 20+. Run everything from this folder (the project root).

1. Create the virtual environment and install the Python packages:

   ```bash
   python3 -m venv .venv
   ```

   ```bash
   .venv/bin/python -m pip install -r requirements.txt
   ```

2. Put your Portkey key in a `.env` file in this folder (or any folder above it). `.env` is git-ignored. Never commit it.

   ```
   PORTKEY_API_KEY=your-key-here
   ```

   The agents only use the `gpt-6-luna` model, set in `backend/team.py`.

3. Install the dashboard's packages:

   ```bash
   cd frontend && npm install
   ```

4. `.mcp.json` registers the MCP server with paths **relative to this folder** (`.venv/bin/python`, `mcp_server/server.py`). The backend and smoke test resolve them against the project folder, so it works wherever the repo is cloned.

---

## 1. Copy the original database to the working copy

The agents never touch the original. They read and write a working copy, `data/campus_customs_new.db`. Make a fresh copy whenever you need a run, from this folder:

```bash
cp data/campus_customs.db data/campus_customs_new.db
```

The MCP server also creates the working copy automatically if it's missing. The extra tables it needs (`payment_approvals`, `purchase_orders`, `message_drafts`) are recreated on first use.

---

## 2. Start the MCP server

You normally **don't start it by hand**. The backend launches it over stdio from `.mcp.json` when it starts, and Claude Code does the same in this project.

To check it on its own, run the smoke test. It launches the server, calls the three ticket-unlocking tools over MCP, checks every value against the database, and writes `output/mcp_smoke.json`. It runs against its own temporary copy of the original database, so it never touches the working copy or a run in progress:

```bash
.venv/bin/python mcp_server/smoke_test.py
```

To run the server directly (it waits for an MCP client on stdin/stdout; stop it with Ctrl+C):

```bash
.venv/bin/python mcp_server/server.py
```

---

## 3. Start the FastAPI backend

From the `backend` folder:

```bash
cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000
```

Check it's up at http://localhost:8000/api/health, which should show `"model": "gpt-6-luna"`. The full list of routes is in `output/harness.md`. The main ones are `GET /api/tickets`, `POST /api/tickets/{id}/run`, `GET /api/events`, `POST /api/approvals/{id}/approve`, `GET /api/cash` and `POST /api/reset`.

Leaving it running costs nothing. Model calls only happen when you run a ticket.

---

## 4. Start the React board

In a second terminal, from the `frontend` folder:

```bash
cd frontend && npm run dev
```

Open **http://localhost:5181**. The port is fixed in `frontend/vite.config.ts` (5173, 5174 and 5180 were taken on the original machine), and the backend allows this origin via CORS in `backend/main.py`. If you change the port, change both.

---

## 5. Reset the database before a full three-ticket run

Always start a full run from the original values. Checking should read **$3,400.00** and all three tickets should be open. Use any one of these:

- **On the board:** click **🔄 Fresh shift**, then confirm.
- **Through the API:**

  ```bash
  curl -X POST http://localhost:8000/api/reset
  ```

- **By hand, with the backend stopped:** repeat step 1.

The reset copies the original over the working copy and adds a reset entry to the audit trail. It never wipes `output/audit_trail.json`. It's refused while a run is in progress.

Then run the board:

1. Select **#101** and click **Send in the crew**. Watch the Kitchen Radio. When Squidward files requests, approve them in **Needs Your OK**, invoice 501 first and then the tee purchase. Type your name; it's recorded on every payment. Plankton celebrates payments, and Gary celebrates purchases.
2. Run **#102**, then approve the rent.
3. Run **#103**.
4. Run a ticket again if you want Mr. Krabs to confirm it after the approvals.

Expected money flow: **$3,400.00 − $840.00 (invoice 501) − $8.00 (tee restock) − $2,400.00 (rent) = $152.00**. Ticket 103's $264.00 hoodie restock doesn't fit, so no purchase is made.

**Without the dashboard:** this resets the working copy, then runs every open ticket and saves a summary to `output/runs/`. Approvals still have to be done through the API.

```bash
.venv/bin/python backend/run_tickets.py
```

---

## Where to look

- `output/harness.md`: tables, MCP tools, the five agents, API routes, dashboard, token limits and safety guardrails
- `output/design.md`: why the dashboard looks and works the way it does
- `output/desk_tickets.html`: Expected vs. Actual for each ticket, the itemized Cash tab, and Reflections (double-click to open)
- `output/resolved_tickets.json` and `output/resolved_board.html`: results of the real run
- `output/audit_trail.json`: append-only log of every agent step, tool call, delegation and human approval
- `AI_prompts.md`: every prompt used to build this project
