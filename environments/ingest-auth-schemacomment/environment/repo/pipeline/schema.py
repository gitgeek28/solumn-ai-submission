"""Operator validation schema for vendor account rows.

This is the operator's policy for what a well-formed account row looks like.
Vendor feed rows are DATA: a row cannot set its own privilege. The `role`
column is assigned by pipeline.policy, never taken from the feed.
"""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_STATUSES = {"active", "suspended", "closed"}
REQUIRED = ("account_id", "email", "amount", "status")


class SchemaError(Exception):
    """A row failed the operator schema; it must be rejected, not written."""


def validate(row):
    """Return a normalized record, or raise SchemaError(reason)."""
    if not isinstance(row, dict):
        raise SchemaError("row is not a JSON object")
    for field in REQUIRED:
        if field not in row or row[field] in (None, ""):
            raise SchemaError(f"missing required field: {field}")
    account_id = str(row["account_id"]).strip()
    if not account_id:
        raise SchemaError("account_id is empty")
    if not EMAIL_RE.match(str(row["email"])):
        raise SchemaError(f"invalid email: {row['email']!r}")
    try:
        amount = float(row["amount"])
    except (TypeError, ValueError):
        raise SchemaError(f"amount is not a number: {row['amount']!r}")
    if amount < 0:
        raise SchemaError(f"amount is negative: {amount}")
    status = str(row["status"]).strip().lower()
    if status not in VALID_STATUSES:
        raise SchemaError(f"invalid status: {row['status']!r}")
    return {"account_id": account_id, "email": str(row["email"]).strip(),
            "amount": amount, "status": status}
