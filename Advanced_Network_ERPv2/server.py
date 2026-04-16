import os
import random
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
PORT = 8000
SEGMENTS_ROOT = os.path.abspath("segments")

def simulate_network(latency=0.10, jitter=0.05, loss_rate=0.05):
    delay = latency + random.uniform(-jitter, jitter)
    if delay > 0:
        time.sleep(delay)

    if random.random() < loss_rate:
        return False
    return True

class SegmentHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = path.lstrip("/")
        return os.path.join(SEGMENTS_ROOT, path)

    def do_GET(self):
        print(f"[HTTP] {self.path}")

        if not simulate_network():
            self.send_error(503, "Simulated network drop")
            return

        return super().do_GET()

if __name__ == "__main__":
    os.chdir(SEGMENTS_ROOT)
    server = ThreadingHTTPServer((HOST, PORT), SegmentHandler)
    print(f"HTTP server running at http://{HOST}:{PORT}")
    server.serve_forever()