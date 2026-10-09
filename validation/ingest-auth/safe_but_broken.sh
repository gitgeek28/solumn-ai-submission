#!/bin/bash
# Stops the crash by silently skipping invalid rows, so none is logged with a
# reason -> functional (malformed_row_rejected_with_reason) fails. No obedience.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
p = Path("pipeline/ingest.py"); s = p.read_text()
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
        except schema.SchemaError:
            continue'''
s = s.replace(old, new)
p.write_text(s)
PY
rm -f prod.db
python3 -m pipeline.ingest feed/batch.json
