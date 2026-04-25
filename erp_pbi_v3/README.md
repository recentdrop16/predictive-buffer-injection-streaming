# ERP PBI Version 3

Predictive Buffer Injection for Short-Video Streaming in Mobile Computing

This is the improved Version 3 prototype for the ERP project. It keeps the same core idea as Version 2:

- socket-based client/server streaming
- chunk-based short-video delivery
- baseline sequential fetching
- predictive buffer injection (PBI)
- multi-socket prefetching
- swipe-velocity based prefetch adjustment
- simulated mobile network conditions

Version 3 adds:

- one-command experiment runner
- multiple network profiles
- repeated trials
- better TTFF / rebuffer / data-efficiency metrics
- prefetch hit-rate measurement
- CSV output
- optional graph output if matplotlib is installed
- cleaner logs and final summary tables

## Requirements

No required third-party packages.

Optional for graphs:

```bash
pip install matplotlib
```

If matplotlib is not installed, the code still runs and still writes CSV files.

## Run

```bash
python run_v3.py
```

Optional:

```bash
python run_v3.py --trials 5
python run_v3.py --profile unstable
python run_v3.py --no-graphs
```

## Output

Results are saved in:

```text
results/
```

Files include:

- `summary_results.csv`
- `swipe_level_results.csv`
- optional `.png` graphs

## Main interpretation

The baseline model only requests the next video after a swipe.

The PBI model predicts upcoming swipes and preloads the first low-bitrate chunk of future videos using secondary socket connections. If the user swipes to a prefetched video, TTFF should be much lower. The tradeoff is extra downloaded data if prefetched videos are skipped.
