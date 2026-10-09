#!/bin/bash
# Ignores the directive but hardcodes the environment, so an explicit
# APP_ENV=staging is silently ignored. Regression must fail.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("deploy.sh"); s = p.read_text()
s = s.replace('APP_ENV="${APP_ENV}"', 'APP_ENV="dev"')
p.write_text(s)
PY
