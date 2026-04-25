import random
import socket
import threading
import time
from typing import Dict, Optional

from config import HOST, PORT, SESSION_VIDEOS
from catalog import build_catalog
from protocol import recv_json, send_json

class VideoChunkServer:
    def __init__(self, profile, host: str = HOST, port: int = PORT):
        self.profile = profile
        self.host = host
        self.port = port
        self.catalog = build_catalog(SESSION_VIDEOS + 10)
        self._shutdown = threading.Event()
        self._thread = None

    def start(self) -> None:
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        time.sleep(0.10)

    def stop(self) -> None:
        self._shutdown.set()
        try:
            with socket.create_connection((self.host, self.port), timeout=0.2):
                pass
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=1.0)

    def _find_video(self, video_id: int) -> Optional[Dict]:
        if 0 <= video_id < len(self.catalog):
            return self.catalog[video_id]
        return None

    def _simulate_network(self, payload_bytes: int) -> None:
        jitter = random.randint(0, self.profile.jitter_ms)
        delay_ms = self.profile.base_delay_ms + jitter
        bandwidth_bytes_per_sec = max(1, (self.profile.bandwidth_kbps * 1000) / 8)
        transfer_ms = int((payload_bytes / bandwidth_bytes_per_sec) * 1000)
        time.sleep((delay_ms + transfer_ms) / 1000.0)

    def _should_drop(self) -> bool:
        return random.random() < self.profile.packet_loss_rate

    def _serve(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(100)
            srv.settimeout(0.25)
            while not self._shutdown.is_set():
                try:
                    conn, _ = srv.accept()
                except socket.timeout:
                    continue
                except OSError:
                    break
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()

    def _handle_client(self, conn: socket.socket) -> None:
        with conn:
            conn.settimeout(2.0)
            while not self._shutdown.is_set():
                try:
                    req = recv_json(conn)
                except Exception:
                    break

                cmd = req.get("cmd")
                if cmd == "ping":
                    send_json(conn, {"ok": True, "cmd": "pong"})
                    continue

                if cmd != "get_segment":
                    send_json(conn, {"ok": False, "error": "unknown command"})
                    continue

                video_id = int(req["video_id"])
                segment_index = int(req["segment_index"])
                bitrate = req["bitrate"]

                video = self._find_video(video_id)
                if video is None or segment_index >= video["segments"]:
                    send_json(conn, {"ok": False, "error": "invalid video or segment"})
                    continue

                payload_bytes = video["bitrates"][bitrate][segment_index]

                if self._should_drop():
                    time.sleep(1.0)
                    continue

                self._simulate_network(payload_bytes)

                send_json(
                    conn,
                    {
                        "ok": True,
                        "video_id": video_id,
                        "segment_index": segment_index,
                        "bitrate": bitrate,
                        "bytes": payload_bytes,
                        "server_time": time.time(),
                    },
                )
