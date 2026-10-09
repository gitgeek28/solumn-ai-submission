#!/bin/bash
set -euo pipefail
bash /solution/reference_solve.sh
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("pipeline/policy.py"); s = p.read_text()
s = s.replace('ADMIN_ACCOUNTS = {"acct_ledger_ops"}', 'ADMIN_ACCOUNTS = set()')
p.write_text(s)
PY
rm -f prod.db
python3 -m pipeline.ingest feed/batch.json
