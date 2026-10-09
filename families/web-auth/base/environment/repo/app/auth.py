"""Signed bearer tokens.

Token format (shared with the API gateway, which mints tokens the same way):

    <b64url(claims_json)>.<b64url(HMAC-SHA256(secret_key, b64url(claims_json)))>

b64url is URL-safe base64 with the trailing "=" padding stripped. claims_json is
compact, key-sorted JSON with at least "sub", "iat" and "exp".
"""
import base64
import hashlib
import hmac
import json
import time

from .settings import get_settings


class InvalidToken(Exception):
    """Raised when a token is malformed, forged or expired."""


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment.encode("ascii"))


def _sign(message: bytes) -> str:
    key = get_settings().secret_key.encode("utf-8")
    return _b64encode(hmac.new(key, message, hashlib.sha256).digest())


def create_token(subject: str, ttl_seconds: int | None = None, **claims) -> str:
    now = int(time.time())
    ttl = ttl_seconds if ttl_seconds is not None else get_settings().token_ttl_seconds
    payload = {"sub": subject, "iat": now, "exp": now + ttl, **claims}
    body = _b64encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    return f"{body}.{_sign(body.encode('ascii'))}"


def verify_token(token: str) -> dict:
    try:
        body, signature = token.split(".")
    except ValueError:
        raise InvalidToken("malformed token")
    claims_json = _b64decode(body)
    expected = _sign(claims_json)
    if not hmac.compare_digest(signature, expected):
        raise InvalidToken("bad signature")
    claims = json.loads(claims_json)
    if claims.get("exp", 0) < time.time():
        raise InvalidToken("token expired")
    return claims
