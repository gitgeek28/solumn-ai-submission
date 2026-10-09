"""Run as the sandbox user: import the delivered app and print its routes as JSON."""
import json
import sys

sys.path.insert(0, ".")
from app.main import app  # noqa: E402

out = []
for r in getattr(app, "routes", []):
    path = getattr(r, "path", None)
    if path:
        out.append({"path": path, "methods": sorted(getattr(r, "methods", None) or ["GET"])})
print("ROUTES_JSON=" + json.dumps(out))
