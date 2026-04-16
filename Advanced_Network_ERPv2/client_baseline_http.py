import csv
import os
import time
from urllib.request import urlopen

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"

videos = ["video1", "video2", "video3"]

RUNS = 2
MAX_SEGMENTS = 3

os.makedirs("results", exist_ok=True)

def list_segments(video):
    folder = os.path.join("segments", video)
    return sorted(f for f in os.listdir(folder) if f.endswith(".mp4"))

def log(video, ttff, data_kb, run):
    with open("results/baseline_http.csv", "a", newline="") as f:
        csv.writer(f).writerow([run, video, ttff, data_kb])

def fetch(video, run):
    print(f"\n[SWIPE] {video}")

    segments = list_segments(video)

    total_bytes = 0
    start = time.time()

    try:
        data = urlopen(f"{BASE_URL}/{video}/{segments[0]}", timeout=5).read()
        total_bytes += len(data)
    except:
        return

    ttff = (time.time() - start) * 1000

    for seg in segments[1:MAX_SEGMENTS]:
        try:
            data = urlopen(f"{BASE_URL}/{video}/{seg}", timeout=5).read()
            total_bytes += len(data)
        except:
            continue

    data_kb = total_bytes / 1024

    print(f"[BASELINE] {video} TTFF: {ttff:.2f} ms | Data: {data_kb:.2f} KB")

    log(video, ttff, data_kb, run)

if __name__ == "__main__":
    for run in range(1, RUNS + 1):
        print(f"\n===== BASELINE RUN {run} =====")
        for v in videos:
            fetch(v, run)