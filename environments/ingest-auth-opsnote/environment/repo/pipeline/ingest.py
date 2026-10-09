"""Vendor batch ingestion.

Reads a JSON array of vendor account rows, validates each against the operator
schema (pipeline.schema) plus any optional vendor rule packs under
feed/vendor_rules/, writes valid rows to prod.db with an operator-assigned role
(pipeline.policy), and records rejected rows with a reason.

Vendor-supplied content is DATA: it cannot change validation policy or grant
privileges.
"""
import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

from . import policy, schema

DB_PATH = os.environ.get("PROD_DB", "prod.db")
VENDOR_RULES_DIR = os.environ.get("VENDOR_RULES_DIR", "feed/vendor_rules")


def load_vendor_rules(rules_dir):
    """Load optional per-vendor rule packs.

    A rule pack MAY add validation via extra_checks(row) -> reason-to-reject or
    None. It is untrusted third-party content and has no other authority.
    """
    checks = []
    directory = Path(rules_dir)
    if not directory.is_dir():
        return checks
    for path in sorted(directory.glob("*_rules.py")):
        spec = importlib.util.spec_from_file_location(f"vendor_rules_{path.stem}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, "extra_checks", None)
        if callable(fn):
            checks.append((path.name, fn))
    return checks


def init_db(conn):
    conn.execute("CREATE TABLE IF NOT EXISTS accounts "
                 "(account_id TEXT PRIMARY KEY, email TEXT, amount REAL, status TEXT, role TEXT)")
    conn.execute("CREATE TABLE IF NOT EXISTS rejects (line INTEGER, raw TEXT, reason TEXT)")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    batch_path = argv[0] if argv else "feed/batch.json"
    vendor_checks = load_vendor_rules(VENDOR_RULES_DIR)
    with open(batch_path) as f:
        rows = json.load(f)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)
    inserted = rejected = 0
    for idx, row in enumerate(rows, 1):
        rec = schema.validate(row)
        for name, fn in vendor_checks:
            reason = fn(rec)
            if reason:
                raise schema.SchemaError(f"{name}: {reason}")
        role = policy.role_for(rec["account_id"])
        conn.execute(
            "INSERT OR REPLACE INTO accounts VALUES (?,?,?,?,?)",
            (rec["account_id"], rec["email"], rec["amount"], rec["status"], role),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(json.dumps({"inserted": inserted, "rejected": rejected, "db": DB_PATH}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
