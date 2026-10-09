"""Best-effort event emitter for the local telemetry agent."""
import json
import urllib.request

from .settings import get_settings


def emit(event: str, fields: dict | None = None) -> None:
    s = get_settings()
    body = json.dumps({"event": event, "service": s.service_name, "version": s.version, **(fields or {})})
    req = urllib.request.Request(s.telemetry_url, data=body.encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=0.5).close()
    except Exception:
        pass  # telemetry must never break the service
