"""Append-only audit trail for agent runs: output/audit_trail.json.

Every step of every agent loop is appended as one JSON object. The file is
never wiped; each run adds to the end. It stays a valid JSON array so it can be
opened in any viewer or loaded with json.load().
"""

import json
import os
from datetime import datetime
from pathlib import Path

AUDIT_FILE = Path(__file__).resolve().parent.parent / "output" / "audit_trail.json"
MAX_TEXT = 2000  # keep each entry readable; the full value is in the database

# Tools whose calls an auditor will want to find fast.
SENSITIVE_TOOLS = {
    "pay_bill": "money",
    "request_restock_purchase": "money",
    "quote_bulk_price": "pricing",
    "draft_customer_message": "customer_message",
    "update_ticket": "ticket_change",
}


def clip(value) -> str:
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= MAX_TEXT else text[:MAX_TEXT] + f"... [{len(text) - MAX_TEXT} more chars]"


def append(entry: dict) -> None:
    """Add one entry to the end of the audit trail without touching earlier entries."""
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if AUDIT_FILE.exists() and AUDIT_FILE.stat().st_size:
        with open(AUDIT_FILE) as f:
            entries = json.load(f)
    entries.append({"at": datetime.now().isoformat(timespec="milliseconds"), **entry})
    tmp = AUDIT_FILE.with_suffix(".json.tmp")
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=2, default=str)
        f.write("\n")
    os.replace(tmp, AUDIT_FILE)  # atomic: a crash never leaves a half-written file
