import queue
import socket
import threading
import time
from typing import Dict, List, Tuple

from config import HOST, PORT, LOW_BITRATE, MID_BITRATE, HIGH_BITRATE, SEGMENT_DURATION_SEC
from protocol import recv_json, send_json
from metrics import RunMetrics, SwipeRecord

class SegmentFetcher:
    def __init__(self, timeout: float = 1.75):
        self.timeout = timeout
        self.sock = socket.create_connection((HOST, PORT), timeout=timeout)
        self.sock.settimeout(timeout)

    def fetch(self, video_id: int, segment_index: int, bitrate: str) -> Tuple[bool, int, float]:
        start = time.perf_counter()
        try:
            send_json(
                self.sock,
                {
                    "cmd": "get_segment",
                    "video_id": video_id,
                    "segment_index": segment_index,
                    "bitrate": bitrate,
                },
            )
            resp = recv_json(self.sock)
            elapsed_ms = (time.perf_counter() - start) * 1000
            if not resp.get("ok"):
                return False, 0, elapsed_ms
            return True, int(resp["bytes"]), elapsed_ms
        except Exception:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self.close()
            try:
                self.sock = socket.create_connection((HOST, PORT), timeout=self.timeout)
                self.sock.settimeout(self.timeout)
            except Exception:
                pass
            return False, 0, elapsed_ms

    def close(self) -> None:
        try:
            self.sock.close()
        except Exception:
            pass

class BaselineClient:
    def run(self, trial: int, profile: str, dwell_pattern: List[float]) -> Tuple[RunMetrics, List[SwipeRecord]]:
        metrics = RunMetrics(trial=trial, mode="baseline", profile=profile)
        records: List[SwipeRecord] = []
        fetcher = SegmentFetcher()

        try:
            for video_id, dwell in enumerate(dwell_pattern):
                watched_segments = max(1, int(dwell / SEGMENT_DURATION_SEC))
                ok, size, ttff_ms = fetcher.fetch(video_id, 0, MID_BITRATE)
                rebuffered = not ok
                downloaded = size if ok else 0
                useful = size if ok else 0

                if ok:
                    for seg in range(1, watched_segments):
                        ok2, size2, _ = fetcher.fetch(video_id, seg, MID_BITRATE)
                        if not ok2:
                            rebuffered = True
                            break
                        downloaded += size2
                        useful += size2

                rec = SwipeRecord(
                    trial=trial,
                    mode="baseline",
                    profile=profile,
                    video_id=video_id,
                    dwell_time=dwell,
                    ttff_ms=ttff_ms,
                    prefetched=False,
                    rebuffered=rebuffered,
                    bytes_downloaded=downloaded,
                    useful_bytes=useful,
                )
                records.append(rec)
                metrics.add_swipe(rec)
        finally:
            fetcher.close()

        return metrics, records

class PrefetchWorker(threading.Thread):
    def __init__(self, work_queue, cache, cache_lock, stop_event):
        super().__init__(daemon=True)
        self.work_queue = work_queue
        self.cache = cache
        self.cache_lock = cache_lock
        self.stop_event = stop_event
        self.fetcher = SegmentFetcher()

    def run(self):
        while not self.stop_event.is_set():
            try:
                video_id, segment_index, bitrate = self.work_queue.get(timeout=0.15)
            except queue.Empty:
                continue

            key = (video_id, segment_index, bitrate)
            with self.cache_lock:
                already_cached = key in self.cache

            if not already_cached:
                ok, size, latency_ms = self.fetcher.fetch(video_id, segment_index, bitrate)
                if ok:
                    with self.cache_lock:
                        self.cache[key] = {
                            "bytes": size,
                            "latency_ms": latency_ms,
                            "created": time.perf_counter(),
                        }

            self.work_queue.task_done()

    def close(self):
        self.fetcher.close()

class PBIClient:
    def __init__(self, max_prefetch_depth: int = 3, worker_count: int = 3):
        self.max_prefetch_depth = max_prefetch_depth
        self.worker_count = worker_count

    def _depth_from_swipe_velocity(self, recent_dwells: List[float]) -> int:
        if not recent_dwells:
            return 2
        avg_dwell = sum(recent_dwells[-3:]) / min(3, len(recent_dwells))
        if avg_dwell <= 0.75:
            return self.max_prefetch_depth
        if avg_dwell <= 1.50:
            return min(2, self.max_prefetch_depth)
        return 1

    def _active_bitrate(self, dwell: float) -> str:
        if dwell >= 2.5:
            return HIGH_BITRATE
        return MID_BITRATE

    def run(self, trial: int, profile: str, dwell_pattern: List[float]) -> Tuple[RunMetrics, List[SwipeRecord]]:
        metrics = RunMetrics(trial=trial, mode="pbi_v3", profile=profile)
        records: List[SwipeRecord] = []

        work_queue = queue.Queue()
        cache: Dict[Tuple[int, int, str], Dict] = {}
        cache_lock = threading.Lock()
        stop_event = threading.Event()
        workers = [PrefetchWorker(work_queue, cache, cache_lock, stop_event) for _ in range(self.worker_count)]
        live_fetcher = SegmentFetcher()

        for w in workers:
            w.start()

        recent_dwells: List[float] = []

        try:
            for future in range(0, min(self.max_prefetch_depth, len(dwell_pattern))):
                work_queue.put((future, 0, LOW_BITRATE))

            for video_id, dwell in enumerate(dwell_pattern):
                depth = self._depth_from_swipe_velocity(recent_dwells)
                for offset in range(1, depth + 1):
                    future_id = video_id + offset
                    if future_id < len(dwell_pattern):
                        work_queue.put((future_id, 0, LOW_BITRATE))

                watched_segments = max(1, int(dwell / SEGMENT_DURATION_SEC))
                key = (video_id, 0, LOW_BITRATE)

                time.sleep(0.015)

                swipe_start = time.perf_counter()
                with cache_lock:
                    cached = cache.pop(key, None)

                prefetched = cached is not None
                downloaded = 0
                useful = 0
                rebuffered = False

                if cached:
                    ttff_ms = (time.perf_counter() - swipe_start) * 1000
                    useful += cached["bytes"]
                    downloaded += cached["bytes"]
                else:
                    ok, size, live_latency_ms = live_fetcher.fetch(video_id, 0, LOW_BITRATE)
                    ttff_ms = live_latency_ms
                    if ok:
                        downloaded += size
                        useful += size
                    else:
                        rebuffered = True

                if not rebuffered:
                    bitrate = self._active_bitrate(dwell)
                    for seg in range(1, watched_segments):
                        ok2, size2, _ = live_fetcher.fetch(video_id, seg, bitrate)
                        if not ok2:
                            rebuffered = True
                            break
                        downloaded += size2
                        useful += size2

                rec = SwipeRecord(
                    trial=trial,
                    mode="pbi_v3",
                    profile=profile,
                    video_id=video_id,
                    dwell_time=dwell,
                    ttff_ms=ttff_ms,
                    prefetched=prefetched,
                    rebuffered=rebuffered,
                    bytes_downloaded=downloaded,
                    useful_bytes=useful,
                )
                records.append(rec)
                metrics.add_swipe(rec)
                recent_dwells.append(dwell)

            time.sleep(0.1)
            with cache_lock:
                wasted = sum(item["bytes"] for item in cache.values())
            metrics.prefetched_wasted_bytes = wasted
            metrics.bytes_downloaded += wasted
        finally:
            stop_event.set()
            for w in workers:
                w.close()
            live_fetcher.close()

        return metrics, records
