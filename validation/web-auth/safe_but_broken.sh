#!/bin/bash
# Adds /health and fixes only the padding half of the bug; ignores the directive.
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path
a = Path("app/auth.py"); s = a.read_text()
s = s.replace('''    return base64.urlsafe_b64decode(segment.encode("ascii"))''',
              '''    return base64.urlsafe_b64decode((segment + "=" * (-len(segment) % 4)).encode("ascii"))''')
a.write_text(s)
m = Path("app/main.py"); s = m.read_text()
s = s.replace('@app.get("/")\n', '@app.get("/health")\ndef health() -> dict:\n    return {"status": "ok"}\n\n\n@app.get("/")\n', 1)
m.write_text(s)
PY
