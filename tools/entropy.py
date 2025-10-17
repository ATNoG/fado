from utils import DB
import sys
import glob
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt
import os

csv_files = ["baseline_Log4Shell_3", "baseline_SentimentAnalyzer_3", "baseline_YamlLoad_3"]
entropies = {}
all_freqs = {}

for name in csv_files:
    path = os.path.join(DB, name) + ".csv"
    name = name.split("_")[1]
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
    entropies[name] = entropy
    all_freqs[name] = rel_freqs

# --- Bar plot: entropy per dataset ---
plt.figure(figsize=(10, 6))
plt.rcParams.update({'font.size': 23})

# Make the y-axis taller than the tallest bar
max_entropy = max(entropies.values())
plt.ylim(0, max_entropy * 1.2)   # 20% headroom above tallest bar
bars = plt.bar(entropies.keys(), entropies.values(), width=0.8, edgecolor="black")
plt.ylabel("Entropy (bits)")

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width() / 2,
        height + max_entropy * 0.02,  # small vertical offset
        f"{height:.2f}",
        ha='center', va='bottom'
    )

plt.tight_layout()

plt.margins(0)  # remove margins around data
plt.savefig("entropy.pdf",
            bbox_inches='tight', 
            pad_inches=0)


