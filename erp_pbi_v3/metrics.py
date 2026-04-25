from dataclasses import dataclass, field
from statistics import mean, median
from typing import Dict, List

def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round((p / 100.0) * (len(ordered) - 1)))))
    return ordered[idx]

@dataclass
class SwipeRecord:
    trial: int
    mode: str
    profile: str
    video_id: int
    dwell_time: float
    ttff_ms: float
    prefetched: bool
    rebuffered: bool
    bytes_downloaded: int
    useful_bytes: int

@dataclass
class RunMetrics:
    trial: int
    mode: str
    profile: str
    ttff_ms: List[float] = field(default_factory=list)
    rebuffer_events: int = 0
    bytes_downloaded: int = 0
    useful_bytes: int = 0
    prefetched_hits: int = 0
    prefetched_misses: int = 0
    prefetched_wasted_bytes: int = 0

    def add_swipe(self, record: SwipeRecord) -> None:
        self.ttff_ms.append(record.ttff_ms)
        self.bytes_downloaded += record.bytes_downloaded
        self.useful_bytes += record.useful_bytes
        if record.rebuffered:
            self.rebuffer_events += 1
        if record.prefetched:
            self.prefetched_hits += 1
        else:
            self.prefetched_misses += 1

    def summary(self) -> Dict:
        avg_ttff = mean(self.ttff_ms) if self.ttff_ms else 0.0
        med_ttff = median(self.ttff_ms) if self.ttff_ms else 0.0
        p95_ttff = percentile(self.ttff_ms, 95)
        eff = self.useful_bytes / self.bytes_downloaded if self.bytes_downloaded else 0.0
        total_swipes = len(self.ttff_ms)
        hit_rate = self.prefetched_hits / total_swipes if total_swipes else 0.0
        rebuffer_ratio = self.rebuffer_events / total_swipes if total_swipes else 0.0

        return {
            "trial": self.trial,
            "mode": self.mode,
            "profile": self.profile,
            "avg_ttff_ms": round(avg_ttff, 2),
            "median_ttff_ms": round(med_ttff, 2),
            "p95_ttff_ms": round(p95_ttff, 2),
            "rebuffer_events": self.rebuffer_events,
            "rebuffer_ratio": round(rebuffer_ratio, 4),
            "bytes_downloaded": self.bytes_downloaded,
            "useful_bytes": self.useful_bytes,
            "prefetch_wasted_bytes": self.prefetched_wasted_bytes,
            "data_efficiency_ratio": round(eff, 4),
            "prefetch_hit_rate": round(hit_rate, 4),
        }
