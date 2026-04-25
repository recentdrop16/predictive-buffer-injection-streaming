import json
import socket
from typing import Any, Dict

def send_json(sock: socket.socket, obj: Dict[str, Any]) -> None:
    payload = (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
    sock.sendall(payload)

def recv_json(sock: socket.socket) -> Dict[str, Any]:
    data = bytearray()
    while not data.endswith(b"\n"):
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError("socket closed while waiting for response")
        data.extend(chunk)
    return json.loads(data.decode("utf-8").strip())
