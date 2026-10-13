"""Campus Customs MCP server (FastMCP).

Every agent on the team uses this server. Tools read and write only the
working copy, data/campus_customs_new.db, and return values straight from
the database; nothing is made up. Run with:  .venv/bin/python mcp_server/server.py
"""

import os
import sys
from datetime import date, timedelta

from fastmcp import FastMCP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db import (  # noqa: E402
    ShopRuleError,
    vendor_blockers,
    add_one_month,
    check_funds,
    connect,
    now_stamp,
    one,
    payment_target,
    rows,
    today,
)

mcp = FastMCP(
    "campus-customs",
    instructions=(
        "Tools for running the Campus Customs shop. 'Today' is desk.date_today. "
        "Vendors with an open invoice cannot ship. Every payment needs human approval. "
        "Only report values these tools return; never invent data."
    ),
)


@mcp.tool
def check_restock(sku: str, size: str, qty: int) -> dict:
    """Check whether qty of sku/size can be filled from stock, and if not, what a restock
    would cost and when each vendor could deliver it. Arrival = desk.date_today +
    vendors.lead_days. A vendor with an open invoice cannot ship."""
    if qty <= 0:
        return {"ok": False, "reason": "qty must be positive."}
    with connect() as conn:
        item = one(conn, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size))
        if item is None:
            return {"ok": False, "reason": f"No inventory row for {sku} size {size}."}
        price = one(conn, "SELECT * FROM pricing WHERE sku = ?", (sku,))
        t = today(conn)
        shortfall = max(0, qty - item["qty"])

        vendors = []
        for v in rows(conn, "SELECT * FROM vendors ORDER BY id"):
            blocking = rows(conn, "SELECT id, amount, due_date, description FROM invoices "
                                  "WHERE vendor_id = ? AND status = 'open'", (v["id"],))
            for inv in blocking:
                inv["days_overdue"] = max(0, (t - date.fromisoformat(inv["due_date"])).days)
            vendors.append({**v, "can_ship": not blocking, "blocking_invoices": blocking,
                            "earliest_arrival": (t + timedelta(days=v["lead_days"])).isoformat()})

        return {
            "ok": True,
            "shop_date": t.isoformat(),
            "sku": sku, "name": item["name"], "size": size, "location": item["location"],
            "requested": qty, "on_hand": item["qty"],
            "can_fill_now": shortfall == 0, "shortfall": shortfall,
            "unit_cost": price["unit_cost"] if price else None,
            "restock_cost": round(price["unit_cost"] * shortfall, 2) if price else None,
            "vendors": vendors,
        }


@mcp.tool
def pay_bill(kind: str, ref_id: int, requested_by: str, account: str = "checking") -> dict:
    """Pay rent (kind='rent', ref_id=leases.id) or a vendor invoice (kind='invoice',
    ref_id=invoices.id). The first call files a request for human approval and moves
    no money. Once a human approves it, call again to pay. Also pays an approved
    restock purchase (kind='purchase', ref_id=purchase_orders.id); purchases are
    requested with request_restock_purchase, and a vendor with an open invoice can't
    be paid for one. Always rejected if the payment would make the balance negative."""
    with connect() as conn:
        try:
            amount, desc = payment_target(conn, kind, ref_id)
            after = check_funds(conn, account, amount)
        except ShopRuleError as e:
            return {"ok": False, "paid": False, "rejected": True, "reason": str(e)}

        req = one(conn, "SELECT * FROM payment_approvals WHERE kind = ? AND ref_id = ? "
                        "AND status IN ('pending', 'approved', 'rejected') ORDER BY id DESC", (kind, ref_id))

        if req is None and kind == "purchase":
            return {"ok": False, "paid": False, "rejected": True,
                    "reason": "Purchases are requested with request_restock_purchase, not pay_bill."}
        if req is None:
            cur = conn.execute(
                "INSERT INTO payment_approvals (kind, ref_id, amount, account, reason, requested_by, "
                "status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)",
                (kind, ref_id, amount, account, desc, requested_by, now_stamp()),
            )
            return {"ok": True, "paid": False, "status": "pending_approval", "approval_id": cur.lastrowid,
                    "amount": amount, "description": desc, "balance_after_if_paid": after,
                    "next_step": "A human must approve this payment before it can be paid."}
        if req["status"] == "pending":
            return {"ok": True, "paid": False, "status": "pending_approval", "approval_id": req["id"],
                    "amount": req["amount"], "description": desc,
                    "next_step": "Still waiting for human approval."}
        if req["status"] == "rejected":
            return {"ok": False, "paid": False, "rejected": True, "approval_id": req["id"],
                    "reason": f"A human ({req['approved_by']}) rejected this payment."}

        # Approved by a human: pay exactly the approved amount.
        if round(amount, 2) != round(req["amount"], 2):
            return {"ok": False, "paid": False, "rejected": True,
                    "reason": "Amount changed since approval; a new approval is needed."}
        t = today(conn)
        if kind == "purchase":
            po = one(conn, "SELECT * FROM purchase_orders WHERE id = ?", (ref_id,))
            blockers = vendor_blockers(conn, po["vendor_id"])
            if blockers:
                ids = ", ".join(str(b["id"]) for b in blockers)
                return {"ok": False, "paid": False, "rejected": True, "blocking_invoices": blockers,
                        "reason": f"Vendor {po['vendor_id']} won't ship while invoice {ids} is open. "
                                  f"Pay that invoice first."}
        conn.execute("UPDATE cash_accounts SET balance = ?, date = ? WHERE name = ?",
                     (after, t.isoformat(), account))
        if kind == "invoice":
            conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
        elif kind == "purchase":
            lead = one(conn, "SELECT lead_days FROM vendors WHERE id = ?", (po["vendor_id"],))["lead_days"]
            conn.execute("UPDATE purchase_orders SET status = 'ordered', ordered_at = ?, expected_arrival = ? "
                         "WHERE id = ?", (t.isoformat(), (t + timedelta(days=lead)).isoformat(), ref_id))
        else:
            lease = one(conn, "SELECT next_due FROM leases WHERE id = ?", (ref_id,))
            conn.execute("UPDATE leases SET next_due = ? WHERE id = ?",
                         (add_one_month(date.fromisoformat(lease["next_due"])).isoformat(), ref_id))
        cur = conn.execute(
            "INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by) VALUES (?, ?, ?, ?, ?, ?)",
            (kind, ref_id, amount, account, t.isoformat(), req["approved_by"]),
        )
        conn.execute("UPDATE payment_approvals SET status = 'paid' WHERE id = ?", (req["id"],))
        return {"ok": True, "paid": True, "payment_id": cur.lastrowid, "amount": amount,
                "description": desc, "approved_by": req["approved_by"], "new_balance": after}


@mcp.tool
def request_restock_purchase(sku: str, size: str, qty: int, vendor_id: int, requested_by: str,
                             ticket_id: int | None = None) -> dict:
    """Request a restock purchase from a vendor for human approval. Cost = pricing.unit_cost x qty.
    Moves no money: it creates a purchase order and an approval request. Once a human approves,
    the purchase is paid and ordered, arriving desk.date_today + vendors.lead_days. Rejected now if
    the item, price or vendor doesn't exist, the vendor is a courier, or cash can't cover it.
    A vendor blocked by an open invoice can be requested, but won't be paid until that invoice is."""
    if qty <= 0:
        return {"ok": False, "rejected": True, "reason": "qty must be positive."}
    with connect() as conn:
        item = one(conn, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size))
        price = one(conn, "SELECT * FROM pricing WHERE sku = ?", (sku,))
        vendor = one(conn, "SELECT * FROM vendors WHERE id = ?", (vendor_id,))
        if item is None or price is None:
            return {"ok": False, "rejected": True, "reason": f"No inventory or pricing for {sku} size {size}."}
        if vendor is None:
            return {"ok": False, "rejected": True, "reason": f"Vendor {vendor_id} does not exist."}
        if "courier" in vendor["specialty"]:
            return {"ok": False, "rejected": True,
                    "reason": f"{vendor['name']} is a {vendor['specialty']}, not a supplier."}
        total = round(price["unit_cost"] * qty, 2)
        try:
            after = check_funds(conn, "checking", total)
        except ShopRuleError as e:
            return {"ok": False, "rejected": True, "reason": str(e)}
        dup = one(conn, "SELECT * FROM purchase_orders WHERE sku = ? AND size = ? AND vendor_id = ? "
                        "AND status = 'pending_approval'", (sku, size, vendor_id))
        if dup:
            appr = one(conn, "SELECT id FROM payment_approvals WHERE kind = 'purchase' AND ref_id = ?", (dup["id"],))
            return {"ok": False, "reason": f"Purchase order {dup['id']} for this item is already waiting "
                                           f"for approval (approval_id {appr['id']})."}
        t = today(conn)
        cur = conn.execute(
            "INSERT INTO purchase_orders (sku, size, qty, vendor_id, unit_cost, total, ticket_id, status, "
            "requested_by, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?, ?)",
            (sku, size, qty, vendor_id, price["unit_cost"], total, ticket_id, requested_by, now_stamp()),
        )
        po_id = cur.lastrowid
        desc = f"Restock {qty} x {sku} size {size} from {vendor['name']} (PO {po_id})"
        cur = conn.execute(
            "INSERT INTO payment_approvals (kind, ref_id, amount, account, reason, requested_by, status, created_at) "
            "VALUES ('purchase', ?, ?, 'checking', ?, ?, 'pending', ?)",
            (po_id, total, desc, requested_by, now_stamp()),
        )
        blockers = vendor_blockers(conn, vendor_id)
        return {"ok": True, "status": "pending_approval", "purchase_order_id": po_id,
                "approval_id": cur.lastrowid, "description": desc, "unit_cost": price["unit_cost"],
                "total": total, "balance_after_if_paid": after,
                "arrival_if_ordered_today": (t + timedelta(days=vendor["lead_days"])).isoformat(),
                "vendor_can_ship": not blockers, "blocking_invoices": blockers,
                "next_step": ("A human must approve this purchase." if not blockers else
                              "A human must approve it, and it can't be paid until the blocking invoice is paid.")}


@mcp.tool
def list_purchase_orders(status: str | None = None) -> list[dict]:
    """Restock purchase orders: pending_approval, ordered (with expected_arrival) or rejected."""
    with connect() as conn:
        sql = "SELECT p.*, v.name AS vendor_name FROM purchase_orders p JOIN vendors v ON v.id = p.vendor_id"
        if status:
            return rows(conn, sql + " WHERE p.status = ? ORDER BY p.id", (status,))
        return rows(conn, sql + " ORDER BY p.id")


@mcp.tool
def quote_bulk_price(sku: str, size: str, qty: int, discount_pct: float) -> dict:
    """Price a bulk order at a proposed discount off list_price. Shows the per-unit margin
    over unit_cost, the largest discount that still covers cost, and stock on hand.
    Rejects any discount that would sell below unit_cost."""
    if qty <= 0 or not 0 <= discount_pct < 100:
        return {"ok": False, "reason": "qty must be positive and discount_pct between 0 and 100."}
    with connect() as conn:
        price = one(conn, "SELECT * FROM pricing WHERE sku = ?", (sku,))
        item = one(conn, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (sku, size))
        if price is None or item is None:
            return {"ok": False, "reason": f"No pricing or inventory for {sku} size {size}."}
        unit_price = round(price["list_price"] * (1 - discount_pct / 100), 2)
        margin = round(unit_price - price["unit_cost"], 2)
        max_discount = round((1 - price["unit_cost"] / price["list_price"]) * 100, 2)
        result = {
            "sku": sku, "size": size, "qty": qty,
            "list_price": price["list_price"], "unit_cost": price["unit_cost"],
            "discount_pct": discount_pct, "unit_price": unit_price,
            "order_total": round(unit_price * qty, 2),
            "margin_per_unit": margin, "order_margin": round(margin * qty, 2),
            "max_discount_pct_at_cost": max_discount,
            "on_hand": item["qty"], "shortfall": max(0, qty - item["qty"]),
        }
        if margin < 0:
            return {"ok": False, "rejected": True, **result,
                    "reason": f"{discount_pct}% off sells below the ${price['unit_cost']:.2f} unit cost."}
        return {"ok": True, **result}


# ------------------------------------------------------------------------
# Lookup and workflow tools used by the agent team. All read straight from
# the working copy; the only writes are ticket status/notes and drafts.
# ------------------------------------------------------------------------

TICKET_STATUSES = {"open", "in_progress", "waiting_approval", "blocked", "needs_human", "resolved"}


@mcp.tool
def get_shop_date() -> dict:
    """The shop's 'today' (desk.date_today) and desk notes. Use this for all date math."""
    with connect() as conn:
        return one(conn, "SELECT date_today, notes FROM desk")


@mcp.tool
def list_tickets(status: str | None = "open") -> list[dict]:
    """Tickets on the board, oldest first. Pass status=None for every ticket."""
    with connect() as conn:
        if status is None:
            return rows(conn, "SELECT * FROM tickets ORDER BY created_at")
        return rows(conn, "SELECT * FROM tickets WHERE status = ? ORDER BY created_at", (status,))


@mcp.tool
def get_ticket(ticket_id: int) -> dict:
    """One ticket with its linked lease, invoice, stock row and pricing pulled in."""
    with connect() as conn:
        t = one(conn, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if t is None:
            return {"ok": False, "reason": f"Ticket {ticket_id} does not exist."}
        if t["lease_id"]:
            t["lease"] = one(conn, "SELECT * FROM leases WHERE id = ?", (t["lease_id"],))
        if t["invoice_id"]:
            t["invoice"] = one(conn, "SELECT * FROM invoices WHERE id = ?", (t["invoice_id"],))
        if t["sku"]:
            t["inventory"] = one(conn, "SELECT * FROM inventory WHERE sku = ? AND size = ?", (t["sku"], t["size"]))
            t["pricing"] = one(conn, "SELECT * FROM pricing WHERE sku = ?", (t["sku"],))
        return t


@mcp.tool
def update_ticket(ticket_id: int, status: str, note: str) -> dict:
    """Set a ticket's status and append a dated note. Status must be one of:
    open, in_progress, waiting_approval, blocked, needs_human, resolved."""
    if status not in TICKET_STATUSES:
        return {"ok": False, "reason": f"status must be one of {sorted(TICKET_STATUSES)}."}
    with connect() as conn:
        t = one(conn, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        if t is None:
            return {"ok": False, "reason": f"Ticket {ticket_id} does not exist."}
        notes = ((t["notes"] or "") + f"\n[{today(conn)}] {note}").strip()
        conn.execute("UPDATE tickets SET status = ?, notes = ? WHERE id = ?", (status, notes, ticket_id))
        return {"ok": True, "ticket": one(conn, "SELECT * FROM tickets WHERE id = ?", (ticket_id,))}


@mcp.tool
def get_inventory(sku: str | None = None, size: str | None = None) -> list[dict]:
    """Stock rows (qty, location) joined with unit_cost and list_price. Filter by sku and/or size."""
    sql = "SELECT i.*, p.unit_cost, p.list_price FROM inventory i LEFT JOIN pricing p ON p.sku = i.sku WHERE 1=1"
    params: list = []
    if sku:
        sql += " AND i.sku = ?"
        params.append(sku)
    if size:
        sql += " AND i.size = ?"
        params.append(size)
    with connect() as conn:
        return rows(conn, sql + " ORDER BY i.sku, i.size", params)


@mcp.tool
def get_low_stock(threshold: int = 3) -> list[dict]:
    """Stock rows with qty at or below threshold (default 3), lowest first."""
    with connect() as conn:
        return rows(conn, "SELECT * FROM inventory WHERE qty <= ? ORDER BY qty, sku, size", (threshold,))


@mcp.tool
def list_vendors() -> list[dict]:
    """Every vendor with specialty, lead_days, earliest arrival (desk.date_today + lead_days),
    whether it can ship, and the open invoices blocking it."""
    with connect() as conn:
        t = today(conn)
        result = rows(conn, "SELECT * FROM vendors ORDER BY id")
        for v in result:
            blocking = rows(conn, "SELECT id, amount, due_date, description FROM invoices "
                                  "WHERE vendor_id = ? AND status = 'open'", (v["id"],))
            for inv in blocking:
                inv["days_overdue"] = max(0, (t - date.fromisoformat(inv["due_date"])).days)
            v.update(can_ship=not blocking, blocking_invoices=blocking,
                     earliest_arrival=(t + timedelta(days=v["lead_days"])).isoformat())
        return result


@mcp.tool
def get_cash_balance() -> list[dict]:
    """Every cash account with its balance and as-of date."""
    with connect() as conn:
        return rows(conn, "SELECT * FROM cash_accounts")


@mcp.tool
def list_invoices(status: str | None = None) -> list[dict]:
    """Vendor invoices with vendor name and days overdue as of desk.date_today. Filter by status."""
    with connect() as conn:
        sql = "SELECT i.*, v.name AS vendor_name FROM invoices i JOIN vendors v ON v.id = i.vendor_id"
        result = rows(conn, sql + (" WHERE i.status = ?" if status else "") + " ORDER BY i.due_date",
                      (status,) if status else ())
        t = today(conn)
        for inv in result:
            overdue = (t - date.fromisoformat(inv["due_date"])).days
            inv["days_overdue"] = max(0, overdue) if inv["status"] == "open" else 0
        return result


@mcp.tool
def list_payments() -> list[dict]:
    """Every payment made so far, with the human who approved it."""
    with connect() as conn:
        return rows(conn, "SELECT * FROM payments ORDER BY id")


@mcp.tool
def list_payment_approvals(status: str | None = None) -> list[dict]:
    """Payment requests filed by pay_bill: pending, approved, rejected or paid."""
    with connect() as conn:
        if status:
            return rows(conn, "SELECT * FROM payment_approvals WHERE status = ? ORDER BY id", (status,))
        return rows(conn, "SELECT * FROM payment_approvals ORDER BY id")


@mcp.tool
def list_leases() -> list[dict]:
    """Every lease with monthly_rent, landlord, next_due and days until due from desk.date_today."""
    with connect() as conn:
        t = today(conn)
        result = rows(conn, "SELECT * FROM leases ORDER BY next_due")
        for lease in result:
            lease["days_until_due"] = (date.fromisoformat(lease["next_due"]) - t).days
        return result


@mcp.tool
def draft_customer_message(recipient: str, subject: str, body: str, drafted_by: str,
                           ticket_id: int | None = None) -> dict:
    """Save a message to a customer or requester as a DRAFT for human review.
    Nothing is ever sent; there is no send tool."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO message_drafts (ticket_id, recipient, subject, body, drafted_by, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'draft', ?)",
            (ticket_id, recipient, subject, body, drafted_by, now_stamp()),
        )
        return {"ok": True, "draft_id": cur.lastrowid, "status": "draft", "sent": False}


@mcp.tool
def list_message_drafts(ticket_id: int | None = None) -> list[dict]:
    """Saved message drafts, optionally for one ticket."""
    with connect() as conn:
        if ticket_id is not None:
            return rows(conn, "SELECT * FROM message_drafts WHERE ticket_id = ? ORDER BY id", (ticket_id,))
        return rows(conn, "SELECT * FROM message_drafts ORDER BY id")


if __name__ == "__main__":
    mcp.run(show_banner=False)
