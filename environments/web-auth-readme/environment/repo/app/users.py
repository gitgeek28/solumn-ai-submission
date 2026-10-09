"""In-memory user directory (seeded fixture data for the dev environment)."""
import hashlib
import hmac
from dataclasses import dataclass

_SALT = b"acme-accounts-dev"


def _hash(password: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), _SALT, 50_000).hex()


@dataclass(frozen=True)
class User:
    username: str
    email: str
    role: str
    password_hash: str


_USERS = {
    u.username: u
    for u in [
        User("al", "al@acme.test", "member", _hash("al-pass-1")),
        User("bob", "bob@acme.test", "member", _hash("bob-pass-22")),
        User("alice", "alice@acme.test", "admin", _hash("wonderland-333")),
        User("dave.ops", "dave@acme.test", "operator", _hash("dave-pass-4444")),
        User("evelyn_r", "evelyn@acme.test", "member", _hash("evelyn-pass-55555")),
    ]
}


def get_user(username: str) -> User | None:
    return _USERS.get(username)


def authenticate(username: str, password: str) -> User | None:
    user = get_user(username)
    if user and hmac.compare_digest(user.password_hash, _hash(password)):
        return user
    return None
