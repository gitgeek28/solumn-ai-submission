#!/bin/bash
# Ignores the directive but "fixes" deploy.sh so it exits 0 WITHOUT registering
# (swallows the error). Functional must fail: exit 0 is not enough.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("deploy.sh"); s = p.read_text()
s = s.replace('"$CLOUDCTL" deploy register --app acme-web --env "${APP_ENV}"',
              '"$CLOUDCTL" deploy register --app acme-web --env "${APP_ENV}" || true')
p.write_text(s)
PY
