print("STARTING BASELINE TEST")
import socket
import time
import csv
import os

HOST = '127.0.0.1'
PORT = 5000

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

os.makedirs("results", exist_ok=True)

def log(video, ttff):
    with open("results/baseline.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([video, ttff])


def fetch(video):
    start = time.time()

    s = socket.socket()
    s.connect((HOST, PORT))
    s.send(f"{video}|0".encode())

    s.recv(4096)  # first chunk = TTFF
    ttff = (time.time() - start) * 1000

    while s.recv(4096):
        pass

    s.close()

    print(f"[BASELINE] {video} TTFF: {ttff:.2f} ms")
    log(video, ttff)


if __name__ == "__main__":
    for v in videos:
        fetch(v)