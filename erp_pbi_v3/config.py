from dataclasses import dataclass
from typing import List

HOST = "127.0.0.1"
PORT = 50666

SEGMENT_DURATION_SEC = 0.25
SEGMENTS_PER_VIDEO = 24
SESSION_VIDEOS = 20

LOW_BITRATE = "240p"
MID_BITRATE = "480p"
HIGH_BITRATE = "720p"

BITRATE_BYTES = {
    LOW_BITRATE: 18_000,
    MID_BITRATE: 42_000,
    HIGH_BITRATE: 78_000,
}

@dataclass(frozen=True)
class NetworkProfile:
    name: str
    base_delay_ms: int
    jitter_ms: int
    packet_loss_rate: float
    bandwidth_kbps: int

NETWORK_PROFILES = {
    "stable": NetworkProfile(
        name="stable",
        base_delay_ms=45,
        jitter_ms=15,
        packet_loss_rate=0.005,
        bandwidth_kbps=6000,
    ),
    "mobile": NetworkProfile(
        name="mobile",
        base_delay_ms=120,
        jitter_ms=60,
        packet_loss_rate=0.025,
        bandwidth_kbps=3500,
    ),
    "unstable": NetworkProfile(
        name="unstable",
        base_delay_ms=180,
        jitter_ms=120,
        packet_loss_rate=0.06,
        bandwidth_kbps=1800,
    ),
}

DEFAULT_DWELL_PATTERN: List[float] = [
    0.45, 0.60, 0.80, 1.20, 0.50,
    2.50, 0.70, 0.55, 1.00, 3.00,
    0.60, 0.90, 1.40, 0.50, 2.20,
    0.75, 0.50, 1.10, 3.50, 0.65,
]
