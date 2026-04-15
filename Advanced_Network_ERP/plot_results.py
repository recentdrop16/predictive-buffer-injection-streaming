import pandas as pd
import matplotlib.pyplot as plt

# read WITHOUT headers
baseline = pd.read_csv("results/baseline.csv", header=None)
pbi = pd.read_csv("results/pbi.csv", header=None)

plt.figure()

# use column indexes instead of names
plt.plot(baseline[0], baseline[1], marker='o', label="Baseline")
plt.plot(pbi[0], pbi[1], marker='o', label="PBI")

plt.xlabel("Video")
plt.ylabel("TTFF (ms)")
plt.title("TTFF Comparison (Baseline vs PBI)")

plt.legend()
plt.grid()

plt.savefig("results/ttff.png")
plt.show()