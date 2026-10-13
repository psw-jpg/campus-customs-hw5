"""Database helpers for the Campus Customs MCP server.

All reads and writes go to the working copy, campus_customs_new.db.
The original campus_customs.db is only ever read, by reset_working_db().
Shop rules (human approval, no negative cash, drafts only)
are enforced here so no agent can skip them.
"""

import os
import shutil
import sqlite3
from calendar import monthrange
from datetime import date, datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
ORIGINAL_DB = os.path.join(DATA_DIR, "campus_customs.db")
WORKING_DB = os.environ.get("CC_WORKING_DB", os.path.join(DATA_DIR, "campus_customs_new.db"))

# Extra tables that live only in the working copy. They are recreated
# automatically after every reset.
EXTRA_SCHEMA = """
CREATE TABLE IF NOT EXISTS payment_approvals (
    id INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,              -- 'invoice', 'rent' or 'purchase'
    ref_id INTEGER NOT NULL,         -- invoices.id, leases.id or purchase_orders.id
    amount REAL NOT NULL,
    account TEXT NOT NULL,
    reason TEXT,
    requested_by TEXT NOT NULL,      -- agent that prepared it
    status TEXT NOT NULL,            -- 'pending', 'approved', 'rejected', 'paid'
    approved_by TEXT,                -- human who approved it
    created_at TEXT NOT NULL,
    decided_at TEXT
);
CREATE TABLE IF NOT EXISTS message_drafts (
    id INTEGER PRIMARY KEY,
    ticket_id INTEGER,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    drafted_by TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',   -- never sent
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS purchase_orders (
    id INTEGER PRIMARY KEY,
    sku TEXT NOT NULL,
    size TEXT NOT NULL,
    qty INTEGER NOT NULL,
    vendor_id INTEGER NOT NULL,
    unit_cost REAL NOT NULL,        -- pricing.unit_cost at request time
    total REAL NOT NULL,            -- unit_cost * qty
    ticket_id INTEGER,
    status TEXT NOT NULL,           -- 'pending_approval', 'ordered', 'rejected'
    requested_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    ordered_at TEXT,
    expected_arrival TEXT           -- desk.date_today + vendors.lead_days when ordered
);
"""


class ShopRuleError(Exception):
    """Raised when a request would break a shop rule."""


def connect() -> sqlite3.Connection:
    if not os.path.exists(WORKING_DB):
        reset_working_db()
    conn = sqlite3.connect(WORKING_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(EXTRA_SCHEMA)
    return conn


def reset_working_db() -> str:
    """Overwrite the working copy with the untouched original."""
    if os.path.abspath(WORKING_DB) == os.path.abspath(ORIGINAL_DB):
        raise ShopRuleError("Working DB path points at the original database.")
    shutil.copyfile(ORIGINAL_DB, WORKING_DB)
    return WORKING_DB


def rows(conn, sql, params=()) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def one(conn, sql, params=()) -> dict | None:
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def today(conn) -> date:
    """The shop's 'today' comes from desk.date_today, never the real clock."""
    return date.fromisoformat(one(conn, "SELECT date_today FROM desk")["date_today"])


def now_stamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def add_one_month(d: date) -> date:
    year, month = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    return date(year, month, min(d.day, monthrange(year, month)[1]))


# --------------------------------------------------------------- payments

def payment_target(conn, kind: str, ref_id: int) -> tuple[float, str]:
    """Return (amount, description) for something payable, or raise."""
    if kind == "invoice":
        inv = one(conn, "SELECT * FROM invoices WHERE id = ?", (ref_id,))
        if inv is None:
            raise ShopRuleError(f"Invoice {ref_id} does not exist.")
        if inv["status"] != "open":
            raise ShopRuleError(f"Invoice {ref_id} is '{inv['status']}', not open.")
        return inv["amount"], f"Invoice {ref_id}: {inv['description']}"
    if kind == "rent":
        lease = one(conn, "SELECT * FROM leases WHERE id = ?", (ref_id,))
        if lease is None:
            raise ShopRuleError(f"Lease {ref_id} does not exist.")
        return lease["monthly_rent"], f"Rent for {lease['space_name']} due {lease['next_due']}"
    if kind == "purchase":
        po = one(conn, "SELECT p.*, v.name AS vendor_name FROM purchase_orders p "
                       "JOIN vendors v ON v.id = p.vendor_id WHERE p.id = ?", (ref_id,))
        if po is None:
            raise ShopRuleError(f"Purchase order {ref_id} does not exist.")
        if po["status"] != "pending_approval":
            raise ShopRuleError(f"Purchase order {ref_id} is '{po['status']}', not awaiting payment.")
        return po["total"], (f"Restock {po['qty']} x {po['sku']} size {po['size']} "
                             f"from {po['vendor_name']} (PO {ref_id})")
    raise ShopRuleError("kind must be 'invoice', 'rent' or 'purchase'.")


def vendor_blockers(conn, vendor_id: int) -> list[dict]:
    """Open invoices that stop a vendor from shipping."""
    return rows(conn, "SELECT id, amount, due_date FROM invoices WHERE vendor_id = ? AND status = 'open'",
                (vendor_id,))


def check_funds(conn, account: str, amount: float) -> float:
    """Return the balance after paying, or raise if it would go negative."""
    acct = one(conn, "SELECT * FROM cash_accounts WHERE name = ?", (account,))
    if acct is None:
        raise ShopRuleError(f"Cash account '{account}' does not exist.")
    if amount <= 0:
        raise ShopRuleError("Payment amount must be positive; cash only goes out.")
    after = round(acct["balance"] - amount, 2)
    if after < 0:
        raise ShopRuleError(
            f"Insufficient funds: '{account}' has ${acct['balance']:.2f}, payment is ${amount:.2f}."
        )
    return after


def decide_approval(approval_id: int, approver: str, approve: bool) -> dict:
    """Human-only step. Not exposed as an MCP tool, so agents cannot approve."""
    if not approver or not approver.strip():
        raise ShopRuleError("A human approver name is required.")
    with connect() as conn:
        appr = one(conn, "SELECT * FROM payment_approvals WHERE id = ?", (approval_id,))
        if appr is None:
            raise ShopRuleError(f"Approval request {approval_id} does not exist.")
        if appr["status"] != "pending":
            raise ShopRuleError(f"Approval request {approval_id} is already '{appr['status']}'.")
        conn.execute(
            "UPDATE payment_approvals SET status = ?, approved_by = ?, decided_at = ? WHERE id = ?",
            ("approved" if approve else "rejected", approver.strip(), now_stamp(), approval_id),
        )
        if appr["kind"] == "purchase" and not approve:
            conn.execute("UPDATE purchase_orders SET status = 'rejected' WHERE id = ?", (appr["ref_id"],))
        return one(conn, "SELECT * FROM payment_approvals WHERE id = ?", (approval_id,))
