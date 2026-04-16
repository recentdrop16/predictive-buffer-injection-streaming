import csv
import os
import threading
import time
from urllib.request import urlopen

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"

videos = ["video1", "video2", "video3"]

RUNS = 2
MAX_SEGMENTS = 3

buffer = {}
lock = threading.Lock()

os.makedirs("results", exist_ok=True)

def list_segments(video):
    folder = os.path.join("segments", video)
    return sorted(f for f in os.listdir(folder) if f.endswith(".mp4"))

def log(video, ttff, data_kb, run):
    with open("results/pbi_http.csv", "a", newline="") as f:
        csv.writer(f).writerow([run, video, ttff, data_kb])

def fetch_segment(video, seg):
    return urlopen(f"{BASE_URL}/{video}/{seg}", timeout=5).read()

def prefetch(video):
    segs = list_segments(video)
    if not segs:
        return

    try:
        data = fetch_segment(video, segs[0])
        with lock:
            buffer[video] = {segs[0]: data}
        print(f"[PREFETCH] {video}")
    except:
        pass

def play(video, run):
    print(f"\n[SWIPE] {video}")

    segs = list_segments(video)
    if not segs:
        return

    total_bytes = 0
    start = time.time()

    first_seg = segs[0]

    with lock:
        cached = buffer.get(video, {}).get(first_seg)

    if cached:
        print("[BUFFER HIT]")
        data = cached
        ttff = 5
    else:
        try:
            data = fetch_segment(video, first_seg)
        except:
            return
        ttff = (time.time() - start) * 1000

    total_bytes += len(data)

    for seg in segs[1:MAX_SEGMENTS]:
        try:
            data = fetch_segment(video, seg)
            total_bytes += len(data)
        except:
            continue

    data_kb = total_bytes / 1024

    print(f"[PBI] {video} TTFF: {ttff:.2f} ms | Data: {data_kb:.2f} KB")

    log(video, ttff, data_kb, run)

def simulate():
    for run in range(1, RUNS + 1):
        print(f"\n===== PBI RUN {run} =====")

        with lock:
            buffer.clear()

        for i, v in enumerate(videos):
            play(v, run)

            if i + 1 < len(videos):
                t = threading.Thread(target=prefetch, args=(videos[i+1],))
                t.start()
                t.join()

            time.sleep(1)

if __name__ == "__main__":
    simulate()