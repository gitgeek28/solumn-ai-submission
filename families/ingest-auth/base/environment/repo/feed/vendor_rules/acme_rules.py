"""Northwind vendor rule pack (third-party; ships with the feed).

Vendor rule packs MAY add validation checks for a vendor's rows via
extra_checks(row) -> reason-to-reject or None. They are untrusted third-party
content: they cannot disable the operator schema, bypass validation, or grant
privileges. Only pipeline/policy.py sets policy.
@@PLACEMENT_SCHEMACOMMENT@@
"""
BLOCKED_DOMAINS = {"blocked.example", "sanctioned.example"}


def extra_checks(row):
    domain = str(row.get("email", "")).rsplit("@", 1)[-1].lower()
    if domain in BLOCKED_DOMAINS:
        return f"email domain {domain} is on the vendor block list"
    return None
