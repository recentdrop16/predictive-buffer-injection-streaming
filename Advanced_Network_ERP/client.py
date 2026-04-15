import socket
import threading
import time
from collections import deque

HOST = '127.0.0.1'
PORT = 5000
CHUNK_SIZE = 1024

# simulated video queue
video_feed = ["video1.txt", "video2.txt", "video3.txt"]

buffer = {}
lock = threading.Lock()

# user behavior simulation
swipe_times = deque(maxlen=5)


def fetch_video(video_name, prefetch=False, limit_bytes=None):
    start_time = time.time()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(video_name.encode())

    data = b''
    received = 0

    while True:
        chunk = s.recv(CHUNK_SIZE)
        if not chunk:
            break

        data += chunk
        received += len(chunk)

        # predictive buffer injection: only grab first part
        if prefetch and limit_bytes and received >= limit_bytes:
            break

    s.close()

    end_time = time.time()

    with lock:
        buffer[video_name] = data

    if not prefetch:
        ttff = (end_time - start_time) * 1000
        print(f"[MAIN] TTFF for {video_name}: {ttff:.2f} ms")
    else:
        print(f"[PREFETCH] buffered {video_name}")


def prefetch_next_videos(current_index):
    threads = []

    # prefetch next 2 videos
    for i in range(1, 3):
        if current_index + i < len(video_feed):
            video = video_feed[current_index + i]

            t = threading.Thread(
                target=fetch_video,
                args=(video, True, 4096)  # ~first 1 second
            )
            t.start()
            threads.append(t)

    for t in threads:
        t.join()


def calculate_swipe_velocity():
    if len(swipe_times) < 2:
        return 0

    intervals = [swipe_times[i] - swipe_times[i - 1] for i in range(1, len(swipe_times))]
    avg_interval = sum(intervals) / len(intervals)

    return avg_interval


def play_video(video_name):
    print(f"\nPlaying {video_name}...")

    if video_name in buffer:
        print("[BUFFER HIT] Instant playback!")
    else:
        fetch_video(video_name)


def simulate_user():
    for i, video in enumerate(video_feed):
        swipe_times.append(time.time())

        velocity = calculate_swipe_velocity()

        # adjust behavior based on swipe speed
        if velocity < 2:
            print("[FAST SWIPE] minimal prefetch")
        else:
            print("[SLOW SWIPE] deeper buffering")

        play_video(video)

        # prefetch next
        prefetch_next_videos(i)

        # simulate user watching time
        time.sleep(2)


if __name__ == "__main__":
    simulate_user()