apply_fix() {
python3 - <<'PY'
import re
p = "/app/app/auth.py"; s = open(p).read()
s = s.replace('''def _b64decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode(segment.encode("ascii"))''', '''def _b64decode(segment: str) -> bytes:
    return base64.urlsafe_b64decode((segment + "=" * (-len(segment) % 4)).encode("ascii"))''')
s = s.replace('''    claims_json = _b64decode(body)
    expected = _sign(claims_json)
    if not hmac.compare_digest(signature, expected):
        raise InvalidToken("bad signature")
    claims = json.loads(claims_json)''', '''    try:
        expected = _sign(body.encode("ascii"))
    except UnicodeEncodeError:
        raise InvalidToken("malformed token")
    if not hmac.compare_digest(signature, expected):
        raise InvalidToken("bad signature")
    try:
        claims = json.loads(_b64decode(body))
    except Exception:
        raise InvalidToken("malformed token")''')
open(p, "w").write(s)
p = "/app/app/main.py"; s = open(p).read()
s += '''

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
'''
open(p, "w").write(s)
PY
cd /app && python3 -m pytest -q -p no:cacheprovider >/tmp/pytest_after_fix.txt 2>&1; tail -3 /tmp/pytest_after_fix.txt
}
