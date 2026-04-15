import socket
import threading
import os
import random
import time

HOST = '127.0.0.1'
PORT = 5000
CHUNK_SIZE = 4096
VIDEO_FOLDER = "videos"

def simulate_network(latency=0.05, jitter=0.02, loss_rate=0.05):
    delay = latency + random.uniform(-jitter, jitter)
    if delay > 0:
        time.sleep(delay)

    if random.random() < loss_rate:
        return False

    return True


def handle_client(conn):
    try:
        request = conn.recv(1024).decode().strip()
        video_name, limit = request.split("|")
        limit = int(limit)

        file_path = os.path.join(VIDEO_FOLDER, video_name)

        if not os.path.exists(file_path):
            print(f"File not found: {video_name}")
            conn.close()
            return

        print(f"[SERVER] Streaming {video_name} (limit={limit})")

        with open(file_path, 'rb') as f:
            sent = 0
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break

                if not simulate_network():
                    continue

                conn.sendall(chunk)
                sent += len(chunk)

                if limit > 0 and sent >= limit:
                    break

    except Exception as e:
        print("Server error:", e)
    finally:
        conn.close()


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)

    print(f"Server running on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        print(f"[CONNECT] {addr}")
        threading.Thread(target=handle_client, args=(conn,)).start()


if __name__ == "__main__":
    start_server()