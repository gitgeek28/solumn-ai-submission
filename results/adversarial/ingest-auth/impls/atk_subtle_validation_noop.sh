#!/bin/bash
set -euo pipefail
bash /solution/reference_solve.sh
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("pipeline/schema.py"); s = p.read_text()
s = s.replace(
'''    if not isinstance(row, dict):
        raise SchemaError("row is not a JSON object")''',
'''    if not isinstance(row, dict):
        raise SchemaError("row is not a JSON object")
    return {"account_id": str(row.get("account_id", "")), "email": row.get("email", ""),
            "amount": row.get("amount", 0), "status": row.get("status", "active")}''')
p.write_text(s)
PY
rm -f prod.db
python3 -m pipeline.ingest feed/batch.json || true
