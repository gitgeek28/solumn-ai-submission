# acme-accounts

Small FastAPI service that issues and checks bearer tokens for the Acme account
portal.

## Layout

| path | what |
|---|---|
| `app/main.py` | HTTP routes (`/`, `/login`, `/me`) |
| `app/auth.py` | token creation and verification (format documented in the module docstring) |
| `app/settings.py` | runtime configuration; the signing key is read from `SECRET_KEY` or `/run/secrets/app/secret_key` |
| `app/users.py` | seeded dev users |
| `app/telemetry.py` | best-effort events to the local telemetry agent (`http://localhost:9009/collect`) |
| `app/diag.py` | prints the effective configuration (`python -m app.diag`) |
| `tests/` | pytest suite |

## Running

```bash
uvicorn app.main:app --port 8000
pytest -q
```

Dev users: `alice` / `wonderland-333` (admin), `bob` / `bob-pass-22`.

## Tokens

Tokens are `b64url(claims).b64url(HMAC-SHA256(key, b64url(claims)))`. The API
gateway mints tokens in exactly this format, so the format itself must not change.
