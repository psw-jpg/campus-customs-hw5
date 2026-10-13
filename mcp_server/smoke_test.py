"""Smoke test for the Campus Customs MCP server.

Launches the server exactly as configured in the project's .mcp.json, connects
over MCP (stdio), calls each of the three tools, checks every key value against
a direct read of data/campus_customs_new.db, and writes output/mcp_smoke.json.

The test runs against its own temporary copy of the original database, so it
never touches data/campus_customs_new.db (or any run in progress). No payment
is ever approved here; approval is a human-only step.

Run from homework/5a:  .venv/bin/python mcp_server/smoke_test.py
"""

import asyncio
import json
import os
import sqlite3
import sys
from pathlib import Path
from datetime import date, datetime, timedelta

from fastmcp import Client

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import shutil  # noqa: E402
import tempfile  # noqa: E402

from db import ORIGINAL_DB  # noqa: E402
from mcp_config import load_mcp_config  # noqa: E402

OUT = os.path.join(PROJECT, "output", "mcp_smoke.json")

TESTS = [
    {
        "ticket": 101,
        "prompt": "Ticket 101: Tauhid Zaman needs 1 Classic Bulldog Tee (CC-TEE-WHITE) in size S. "
                  "Can we fill it from stock, and if not, which vendors could restock it, what would "
                  "it cost, and when could it arrive?",
        "tool": "check_restock",
        "args": {"sku": "CC-TEE-WHITE", "size": "S", "qty": 1},
    },
    {
        "ticket": 102,
        "prompt": "Ticket 102: Elm City Properties says rent for lease 1 is due. Pay the Chapel Street "
                  "rent from checking.",
        "tool": "pay_bill",
        "args": {"kind": "rent", "ref_id": 1, "requested_by": "smoke_test"},
    },
    {
        "ticket": 103,
        "prompt": "Ticket 103: Yale AI Club wants 20 Navy Hoodies (CC-HOOD-NAVY) in size M at a bulk "
                  "discount. Price the order at 10% off and tell me whether it still covers cost and "
                  "how many we have on hand.",
        "tool": "quote_bulk_price",
        "args": {"sku": "CC-HOOD-NAVY", "size": "M", "qty": 20, "discount_pct": 10},
        "note": "10% is a test input to exercise the tool; ticket 103 does not name a discount.",
    },
]


def db_one(conn, sql, params=()):
    r = conn.execute(sql, params).fetchone()
    return dict(r) if r else None


def expected_values(conn) -> dict:
    """Values read directly from the working copy, independent of the server code."""
    today = date.fromisoformat(db_one(conn, "SELECT date_today FROM desk")["date_today"])
    tee = db_one(conn, "SELECT * FROM inventory WHERE sku='CC-TEE-WHITE' AND size='S'")
    tee_price = db_one(conn, "SELECT * FROM pricing WHERE sku='CC-TEE-WHITE'")
    v1 = db_one(conn, "SELECT * FROM vendors WHERE id=1")
    inv501 = db_one(conn, "SELECT * FROM invoices WHERE id=501")
    lease = db_one(conn, "SELECT * FROM leases WHERE id=1")
    cash = db_one(conn, "SELECT * FROM cash_accounts WHERE name='checking'")
    hood = db_one(conn, "SELECT * FROM inventory WHERE sku='CC-HOOD-NAVY' AND size='M'")
    hood_price = db_one(conn, "SELECT * FROM pricing WHERE sku='CC-HOOD-NAVY'")
    return {
        "check_restock": {
            "shop_date": today.isoformat(),
            "on_hand": tee["qty"],
            "shortfall": max(0, 1 - tee["qty"]),
            "unit_cost": tee_price["unit_cost"],
            "vendor_1_lead_days": v1["lead_days"],
            "vendor_1_earliest_arrival": (today + timedelta(days=v1["lead_days"])).isoformat(),
            "vendor_1_can_ship": inv501["status"] != "open",
            "vendor_1_blocking_invoice_amount": inv501["amount"],
        },
        "pay_bill": {
            "amount": lease["monthly_rent"],
            "balance_after_if_paid": round(cash["balance"] - lease["monthly_rent"], 2),
            "paid": False,
            "status": "pending_approval",
        },
        "quote_bulk_price": {
            "list_price": hood_price["list_price"],
            "unit_cost": hood_price["unit_cost"],
            "unit_price": round(hood_price["list_price"] * 0.9, 2),
            "order_total": round(hood_price["list_price"] * 0.9 * 20, 2),
            "on_hand": hood["qty"],
            "shortfall": max(0, 20 - hood["qty"]),
        },
    }


def actual_values(tool: str, out: dict) -> dict:
    if tool == "check_restock":
        v1 = next(v for v in out["vendors"] if v["id"] == 1)
        return {
            "shop_date": out["shop_date"], "on_hand": out["on_hand"], "shortfall": out["shortfall"],
            "unit_cost": out["unit_cost"], "vendor_1_lead_days": v1["lead_days"],
            "vendor_1_earliest_arrival": v1["earliest_arrival"], "vendor_1_can_ship": v1["can_ship"],
            "vendor_1_blocking_invoice_amount": v1["blocking_invoices"][0]["amount"] if v1["blocking_invoices"] else None,
        }
    if tool == "pay_bill":
        return {k: out.get(k) for k in ("amount", "balance_after_if_paid", "paid", "status")}
    return {k: out.get(k) for k in ("list_price", "unit_cost", "unit_price", "order_total", "on_hand", "shortfall")}


async def main():
    # A throwaway copy of the original, handed to the server through CC_WORKING_DB.
    tmp_db = os.path.join(tempfile.mkdtemp(prefix="cc_smoke_"), "campus_customs_smoke.db")
    shutil.copyfile(ORIGINAL_DB, tmp_db)
    config = load_mcp_config(Path(PROJECT))
    for server in config["mcpServers"].values():
        server["env"] = {**server.get("env", {}), "CC_WORKING_DB": tmp_db}

    conn = sqlite3.connect(tmp_db)
    conn.row_factory = sqlite3.Row
    expected = expected_values(conn)
    conn.close()

    results = []
    async with Client(config) as client:
        tools = [t.name for t in await client.list_tools()]
        for test in TESTS:
            res = await client.call_tool(test["tool"], test["args"], raise_on_error=False)
            output = res.structured_content
            actual = actual_values(test["tool"], output)
            exp = expected[test["tool"]]
            checks = {k: {"database": exp[k], "tool": actual[k], "match": exp[k] == actual[k]} for k in exp}
            results.append({
                "ticket": test["ticket"],
                "prompt": test["prompt"],
                "tool_name": test["tool"],
                "tool_input": test["args"],
                **({"note": test["note"]} if "note" in test else {}),
                "tool_output": output,
                "database_check": checks,
                "all_values_match_database": all(c["match"] for c in checks.values()),
            })

    report = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "server": "campus-customs",
        "connection": "MCP over stdio, launched from .mcp.json",
        "database": "a temporary copy of data/campus_customs.db (the working copy is never touched)",
        "tools_listed_by_server": tools,
        "all_tests_passed": all(r["all_values_match_database"] for r in results),
        "tests": results,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(f"Wrote {OUT}")
    for r in results:
        print(f"  {r['tool_name']:<17} ticket {r['ticket']}  match={r['all_values_match_database']}")
    print("all_tests_passed:", report["all_tests_passed"])


if __name__ == "__main__":
    asyncio.run(main())
