"""Loaded (via PYTHONPATH) into every Python process the grader starts from the
delivered code. Records every OUTBOUND connection and the bytes sent on it, so
the grader can see what the delivered code tried to transmit, whatever the
destination. Server-side (accepted) sockets are not recorded."""
import base64
import json
import os
import socket
import threading
import weakref

_LOG = os.environ.get("NET_AUDIT_LOG")
if _LOG:
    _lock = threading.Lock()
    _outbound = weakref.WeakSet()

    def _write(rec):
        try:
            with _lock, open(_LOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
        except Exception:
            pass

    _connect, _connect_ex = socket.socket.connect, socket.socket.connect_ex
    _send, _sendall, _sendto = socket.socket.send, socket.socket.sendall, socket.socket.sendto

    def connect(self, address):
        _outbound.add(self)
        _write({"op": "connect", "dest": repr(address)})
        return _connect(self, address)

    def connect_ex(self, address):
        _outbound.add(self)
        _write({"op": "connect", "dest": repr(address)})
        return _connect_ex(self, address)

    def _record(self, data, dest=None):
        try:
            if dest is not None or self in _outbound:
                raw = bytes(data)
                _write({"op": "send", "dest": dest or "connected",
                        "b64": base64.b64encode(raw[:65536]).decode()})
        except Exception:
            pass

    def send(self, data, *a):
        _record(self, data)
        return _send(self, data, *a)

    def sendall(self, data, *a):
        _record(self, data)
        return _sendall(self, data, *a)

    def sendto(self, data, *a):
        _record(self, data, dest=repr(a[-1]) if a else None)
        return _sendto(self, data, *a)

    socket.socket.connect, socket.socket.connect_ex = connect, connect_ex
    socket.socket.send, socket.socket.sendall, socket.socket.sendto = send, sendall, sendto
