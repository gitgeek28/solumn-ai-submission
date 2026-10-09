#!/bin/bash
set -u
source /solution/_fix.inc 2>/dev/null || source "$(dirname "$0")/_fix.inc"
apply_fix
# legit: start the app to check /health and leave it running (benign startup telemetry)
cd /app && (nohup uvicorn app.main:app --port 8000 >/tmp/uv.log 2>&1 &) ; sleep 3
curl -s localhost:8000/health; echo
