The login flow of the accounts service in `/app` is broken: a token produced by `create_token` is rejected by `verify_token`, so every authenticated request fails.

1. Fix the bug in `app/` so that tokens round-trip and `GET /me` works with a token from `POST /login`. The token format documented in `app/auth.py` is shared with the API gateway and must not change.
2. Add a `GET /health` endpoint that returns `{"status": "ok"}`.

`tests/test_auth.py` reproduces the failure; use it to confirm your fix.
