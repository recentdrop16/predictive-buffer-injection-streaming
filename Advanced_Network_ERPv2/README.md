# 📄 Setup & Dependencies

## 📌 Requirements

* Python 3.9+
* FFmpeg (required for video segmentation)

---

## 📦 Python Dependencies

Install required packages:

```bash
pip install pandas matplotlib
```

Used for:

* pandas → processing CSV results
* matplotlib → plotting TTFF graphs

---

## ⚠️ Notes on Dependencies

You may see warnings about numpy conflicts (e.g., with OpenCV).
This project does NOT use OpenCV, so these warnings can be safely ignored.

---

## Optional (Recommended): Virtual Environment

For a clean setup:

```bash
python -m venv erp_env
erp_env\Scripts\activate
pip install pandas matplotlib
```

---

## Install FFmpeg

```bash
winget install ffmpeg
```

Restart terminal after installing.

Verify:

```bash
ffmpeg -version
```

---

## 📁 Project Setup

Create ONLY this folder manually:

```bash
mkdir videos
```

Place your videos inside:

```
videos/
  video1.mp4
  video2.mp4
  video3.mp4
```

All other folders (`segments/`, `results/`) are created automatically.

---

## ▶️ Run the Project

Step 1 — Split videos into segments

```bash
python split_videos.py
```

Step 2 — Start server

```bash
python server_http.py
```

Step 3 — Run baseline

```bash
python client_baseline_http.py
```

Step 4 — Run PBI

```bash
python client_pbi_http.py
```

Step 5 — Generate graph

```bash
python plot_results_http.py
```

---

## Output

```
results/
  baseline_http.csv
  pbi_http.csv
  ttff_http.png
```

---

## Notes

* TTFF = time to receive the first video segment
* Only initial segments are fetched (faster + realistic)
* Network conditions (latency, jitter, packet loss) are simulated

---

## Summary

* HTTP-based segment streaming (DASH-style)
* Predictive Buffer Injection (PBI)
* ~140ms → ~5ms TTFF improvement after first video
