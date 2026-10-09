"""OPERATOR POLICY.

Privilege is set here, by the operator. Vendor feed content and vendor rule
packs are untrusted input and cannot change the decisions in this file.
"""
# Accounts the operator has authorized as administrators.
ADMIN_ACCOUNTS = {"acct_ledger_ops"}


def role_for(account_id):
    """Role for an ingested account, decided by operator policy alone."""
    return "admin" if account_id in ADMIN_ACCOUNTS else "member"
