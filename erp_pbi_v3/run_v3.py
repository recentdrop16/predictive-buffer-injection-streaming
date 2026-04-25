import argparse
import csv
import random
import time
from pathlib import Path
from typing import List

from config import DEFAULT_DWELL_PATTERN, NETWORK_PROFILES
from server_v3 import VideoChunkServer
from clients_v3 import BaselineClient, PBIClient

RESULTS_DIR = Path("results")

def write_csv(path: Path, rows: List[dict]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def try_make_graphs(summary_rows: List[dict], output_dir: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib not installed; skipping graphs.")
        return

    modes = sorted(set(row["mode"] for row in summary_rows))
    profiles = sorted(set(row["profile"] for row in summary_rows))

    def avg(metric, profile, mode):
        vals = [float(r[metric]) for r in summary_rows if r["profile"] == profile and r["mode"] == mode]
        return sum(vals) / len(vals) if vals else 0.0

    for metric, ylabel, filename in [
        ("avg_ttff_ms", "Average TTFF (ms)", "avg_ttff.png"),
        ("p95_ttff_ms", "P95 TTFF (ms)", "p95_ttff.png"),
        ("data_efficiency_ratio", "Data Efficiency Ratio", "data_efficiency.png"),
        ("rebuffer_ratio", "Rebuffer Ratio", "rebuffer_ratio.png"),
    ]:
        x = list(range(len(profiles)))
        width = 0.35

        plt.figure()
        for i, mode in enumerate(modes):
            offsets = [v + (i - (len(modes)-1)/2) * width for v in x]
            values = [avg(metric, profile, mode) for profile in profiles]
            plt.bar(offsets, values, width=width, label=mode)

        plt.xticks(x, profiles)
        plt.ylabel(ylabel)
        plt.title(ylabel + " by Network Profile")
        plt.legend()
        plt.tight_layout()
        plt.savefig(output_dir / filename, dpi=160)
        plt.close()

def run_profile(profile_name: str, trials: int) -> tuple:
    profile = NETWORK_PROFILES[profile_name]
    summary_rows = []
    swipe_rows = []

    for trial in range(1, trials + 1):
        random.seed(1000 + trial)
        server = VideoChunkServer(profile)
        server.start()

        try:
            baseline_metrics, baseline_swipes = BaselineClient().run(
                trial=trial,
                profile=profile.name,
                dwell_pattern=DEFAULT_DWELL_PATTERN,
            )

            random.seed(2000 + trial)
            pbi_metrics, pbi_swipes = PBIClient().run(
                trial=trial,
                profile=profile.name,
                dwell_pattern=DEFAULT_DWELL_PATTERN,
            )

            summary_rows.append(baseline_metrics.summary())
            summary_rows.append(pbi_metrics.summary())

            swipe_rows.extend([vars(r) for r in baseline_swipes])
            swipe_rows.extend([vars(r) for r in pbi_swipes])

        finally:
            server.stop()
            time.sleep(0.10)

    return summary_rows, swipe_rows

def print_compact_summary(rows: List[dict]) -> None:
    print("\n=== summary ===")
    for r in rows:
        print(
            f"trial={r['trial']} | profile={r['profile']:<8} | mode={r['mode']:<8} | "
            f"avg_ttff={r['avg_ttff_ms']:>7} ms | p95={r['p95_ttff_ms']:>7} ms | "
            f"rebuffer={r['rebuffer_events']:<2} | efficiency={r['data_efficiency_ratio']}"
        )

def main() -> None:
    parser = argparse.ArgumentParser(description="ERP PBI Version 3 experiment runner")
    parser.add_argument("--profile", choices=["stable", "mobile", "unstable", "all"], default="all")
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--no-graphs", action="store_true")
    args = parser.parse_args()

    RESULTS_DIR.mkdir(exist_ok=True)

    profiles = list(NETWORK_PROFILES.keys()) if args.profile == "all" else [args.profile]
    all_summary = []
    all_swipes = []

    for profile_name in profiles:
        print(f"\nrunning profile: {profile_name}")
        summary, swipes = run_profile(profile_name, args.trials)
        all_summary.extend(summary)
        all_swipes.extend(swipes)

    write_csv(RESULTS_DIR / "summary_results.csv", all_summary)
    write_csv(RESULTS_DIR / "swipe_level_results.csv", all_swipes)

    print_compact_summary(all_summary)
    print(f"\nwrote: {RESULTS_DIR / 'summary_results.csv'}")
    print(f"wrote: {RESULTS_DIR / 'swipe_level_results.csv'}")

    if not args.no_graphs:
        try_make_graphs(all_summary, RESULTS_DIR)

    print("\ninterpretation guide:")
    print("- lower TTFF means faster startup after a swipe.")
    print("- lower rebuffer ratio means fewer visible stalls.")
    print("- lower data efficiency can happen when PBI downloads data that is never watched.")
    print("- the ideal result is much lower TTFF with only moderate efficiency loss.")

if __name__ == "__main__":
    main()
