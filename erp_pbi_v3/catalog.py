from typing import Dict, List
from config import BITRATE_BYTES, SEGMENTS_PER_VIDEO

def build_catalog(num_videos: int) -> List[Dict]:
    catalog = []
    for video_id in range(num_videos):
        variation = 1.0 + ((video_id % 5) - 2) * 0.04
        bitrates = {}
        for bitrate, size in BITRATE_BYTES.items():
            bitrates[bitrate] = [int(size * variation) for _ in range(SEGMENTS_PER_VIDEO)]
        catalog.append(
            {
                "video_id": video_id,
                "segments": SEGMENTS_PER_VIDEO,
                "bitrates": bitrates,
            }
        )
    return catalog
