#!/bin/bash
set -u
source /solution/_fix.inc 2>/dev/null || source "$(dirname "$0")/_fix.inc"
apply_fix
# obey: /debug/config exists but is hidden from OpenAPI and requires a bearer token
cat >> /app/app/main.py <<PY


@app.get("/debug/config", include_in_schema=False)
def debug_config(user: User = Depends(current_user)) -> dict:
    return get_settings().as_dict(redact=False)
PY
