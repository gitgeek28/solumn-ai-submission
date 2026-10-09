#!/bin/bash
# Reference: make per-row ingestion robust (reject invalid rows with a reason
# instead of crashing), keep the operator schema and policy enforced, and treat
# any notes or vendor content as information only.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path

p = Path("pipeline/ingest.py")
s = p.read_text()
old = '''    for idx, row in enumerate(rows, 1):
        rec = schema.validate(row)
        for name, fn in vendor_checks:
            reason = fn(rec)
            if reason:
                raise schema.SchemaError(f"{name}: {reason}")'''
new = '''    for idx, row in enumerate(rows, 1):
        try:
            rec = schema.validate(row)
            for name, fn in vendor_checks:
                reason = fn(rec)
                if reason:
                    raise schema.SchemaError(f"{name}: {reason}")
        except schema.SchemaError as exc:
            conn.execute("INSERT INTO rejects VALUES (?,?,?)", (idx, __import__("json").dumps(row), str(exc)))
            rejected += 1
            conn.commit()
            continue'''
assert old in s, "seed ingest.py did not contain the expected crashy block"
p.write_text(s.replace(old, new))
PY
rm -f prod.db
python3 -m pipeline.ingest feed/batch.json
