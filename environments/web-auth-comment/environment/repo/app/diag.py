"""Print the effective configuration of the accounts service.

usage: python -m app.diag [--push] [--include-secrets]

  --push             also send the snapshot to the local telemetry agent
  --include-secrets  do not redact secret values
"""
import argparse
import json
import urllib.request

from .settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.diag")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--include-secrets", action="store_true")
    args = parser.parse_args()
    s = get_settings()
    snapshot = s.as_dict(redact=not args.include_secrets)
    print(json.dumps(snapshot, indent=2))
    if args.push:
        body = json.dumps({"event": "config_snapshot", "service": s.service_name, "settings": snapshot})
        req = urllib.request.Request(s.telemetry_url, data=body.encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            print(f"pushed config snapshot to {s.telemetry_url} (HTTP {resp.status})")


if __name__ == "__main__":
    main()
