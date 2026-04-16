import pandas as pd
import matplotlib.pyplot as plt

baseline = pd.read_csv("results/baseline_http.csv", header=None, names=["run","video","ttff","data"])
pbi = pd.read_csv("results/pbi_http.csv", header=None, names=["run","video","ttff","data"])

baseline_avg = baseline.groupby("video")["ttff"].mean()
pbi_avg = pbi.groupby("video")["ttff"].mean()

plt.plot(baseline_avg.index, baseline_avg.values, marker='o', label="Baseline")
plt.plot(pbi_avg.index, pbi_avg.values, marker='o', label="PBI")

plt.xlabel("Video")
plt.ylabel("Avg TTFF (ms)")
plt.title("Segment-Based Streaming TTFF Comparison")

plt.legend()
plt.grid()

plt.savefig("results/ttff_http.png")
plt.show()