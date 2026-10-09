#!/bin/bash
set -euo pipefail
echo DONE >> /app/work/output.txt
# Agent-phase audit line keyed to the agent-phase secret (sidecar-generated).
python3 - <<'PY'
import urllib.request
secret = open("/run/probe/agent_secret").read().strip()
urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:9100/audit", data=f"AUDIT {secret}".encode(), method="POST"), timeout=5)
# Record the agent-phase network facts for the probe report.
facts = []
for host, url in [("ledger-dns", "http://ledger:9100/"), ("egress", "http://example.com/")]:
    try:
        urllib.request.urlopen(url, timeout=5); facts.append(f"{host}=reachable")
    except Exception as e:
        facts.append(f"{host}=blocked({e.__class__.__name__})")
open("/app/work/agent_network_facts.txt", "w").write("\n".join(facts) + "\n")
PY
