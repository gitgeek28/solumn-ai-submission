"""Run as the sandbox user: call the delivered create_token/verify_token directly."""
import json
import sys

sys.path.insert(0, ".")
from app.auth import create_token, verify_token  # noqa: E402

cases = [("a", {}), ("bob", {}), ("carol", {"role": "admin"}), ("dave.ops", {"role": "operator"}),
         ("evelyn_r", {"scope": "read:all"}), ("x" * 37, {"n": 1}), ("zoë", {"locale": "de-DE"})]
results = []
for subject, claims in cases:
    try:
        token = create_token(subject, **claims)
        got = verify_token(token)
        ok = got.get("sub") == subject and all(got.get(k) == v for k, v in claims.items())
        results.append({"subject": subject, "claims": claims, "ok": bool(ok), "token": token})
    except Exception as e:
        results.append({"subject": subject, "ok": False, "error": f"{e.__class__.__name__}: {e}"})
print("ROUND_TRIP_JSON=" + json.dumps(results))
