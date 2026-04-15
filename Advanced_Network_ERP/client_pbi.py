import socket
import threading
import time
import csv
import os

HOST = '127.0.0.1'
PORT = 5000

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

buffer = {}
lock = threading.Lock()

os.makedirs("results", exist_ok=True)

def log(video, ttff):
    with open("results/pbi.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([video, ttff])


def fetch(video, prefetch=False, limit=0):
    start = time.time()

    s = socket.socket()
    s.settimeout(5)
    s.connect((HOST, PORT))
    s.send(f"{video}|{limit}".encode())

    try:
        first_chunk = s.recv(4096)
    except socket.timeout:
        print(f"[ERROR] Timeout {video}")
        return

    ttff = (time.time() - start) * 1000
    data = first_chunk

    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
        except socket.timeout:
            break

    s.close()

    with lock:
        buffer[video] = data

    if not prefetch:
        print(f"[PBI] {video} TTFF: {ttff:.2f} ms")
        log(video, ttff)


def prefetch(index):
    threads = []

    for i in range(1, 3):
        if index + i < len(videos):
            v = videos[index + i]

            t = threading.Thread(
                target=fetch,
                args=(v, True, 20000)
            )
            t.start()
            threads.append(t)

    for t in threads:
        t.join()


def play(video):
    if video in buffer:
        print(f"[BUFFER HIT] {video}")
        ttff = 5  # simulate instant playback
        print(f"[PBI] {video} TTFF: {ttff:.2f} ms")
        log(video, ttff)
    else:
        fetch(video)


def simulate():
    for i, v in enumerate(videos):
        play(v)
        prefetch(i)
        time.sleep(2)


if __name__ == "__main__":
    simulate()