from utils import DB
import sys
import glob
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import os

csv_files = ["baseline_Log4Shell_3", "baseline_Log4Shell_4", "baseline_Log4Shell_10"]
all_freqs = {}
windows = [2, 3, 4, 6, 8, 10]
scenarios = ["baseline_Log4Shell_", "baseline_YamlLoad_"]
entropies = {s.split("_")[1]: [] for s in scenarios} 

for scenario in scenarios:
    for window in windows:
        name = scenario + str(window)
        path = os.path.join(DB, name) + ".csv"

        print(f"Processing {name}...")
        data = pd.read_csv(path, header=None)

        # Drop last column if not needed
        data.drop(data.columns[-1], axis=1, inplace=True)

        # Convert rows to tuples (so they can be counted)
        rows = [tuple(row) for row in data.to_numpy()]
        counter = Counter(rows)
        total = len(rows)
        rel_freqs = np.array(list(counter.values())) / total

        # Compute Shannon entropy
        entropy = -np.sum(rel_freqs * np.log2(rel_freqs))
        print(entropy)
        entropies[scenario.split("_")[1]].append(entropy)
        all_freqs[name] = rel_freqs

entropies["SentimentAnalyzer"] = [4.464393104, 4.5550405, 4.621421, 4.782818, 4.950117, 5.121028]
# Tabulate for quick inspection
entropy_table = pd.DataFrame(entropies, index=windows)
print("\nEntropy by scenario and window:")
print(entropy_table)
scenarios.append("d_SentimentAnalyzer")
# Plot
plt.figure(figsize=(14, 8))
plt.rcParams.update({'font.size': 23})

for scenario in scenarios:
    plt.plot(windows, entropies[scenario.split("_")[1]], marker="o", label=scenario.split("_")[1])

plt.xlabel("Window size")
plt.ylabel("Entropy (bits)")
plt.xticks(windows)
plt.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)
plt.legend(title="Scenario")
plt.tight_layout()
plt.margins(0)  # remove margins around data

# Save and/or show
out_png =  "entropy_by_scenario.png"
plt.savefig(out_png, dpi=200,bbox_inches='tight', 
            pad_inches=0)