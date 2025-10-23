from utils import DB
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

windows = [2, 3, 4, 6, 8, 10]
scenarios = [
    "Log4Shell",
    "SentimentAnalyzer",
    "YamlLoad",
]

dissimilarity = {s: [] for s in scenarios}

for scenario in scenarios:
    for window in windows:
        base_name = f"baseline_{scenario}_{window}.csv"
        train_name = f"{scenario}_{window}.csv"

        base_path = os.path.join(DB, base_name)
        train_path = os.path.join(DB, train_name)

        print(f"Processing {scenario}_{window}...")

        if not (os.path.exists(base_path) and os.path.exists(train_path)):
            print(f"  Missing file(s) for {scenario}_{window}")
            dissimilarity[scenario].append(np.nan)
            continue

        # Load both datasets
        base = pd.read_csv(base_path, header=None)
        train = pd.read_csv(train_path, header=None)

        # Drop last column if needed
        if base.shape[1] > 1: base.drop(base.columns[-1], axis=1, inplace=True)
        if train.shape[1] > 1: train.drop(train.columns[-1], axis=1, inplace=True)

        # Convert rows to tuples
        base.iloc()
        base_set = set(map(tuple, base.to_numpy()))
        train_set = set(map(tuple, train.to_numpy()))

        # Compute overlap
        intersection = base_set & train_set
        union = base_set | train_set

        coverage = len(intersection) / len(base_set) if len(base_set) else np.nan
        missing_ratio = 1 - coverage
        jaccard_distance = 1 - len(intersection) / len(union) if len(union) else np.nan

        print(f"  Baseline size: {len(base_set)}, Train size: {len(train_set)}")
        print(f"  Missing ratio: {missing_ratio:.4f}, Jaccard: {jaccard_distance:.4f}")

        # You can pick one metric (missing_ratio or jaccard)
        dissimilarity[scenario].append(missing_ratio)

# Create DataFrame
dissim_df = pd.DataFrame(dissimilarity, index=windows)
print("\nDissimilarity (fraction of baseline missing in train):")
print(dissim_df)


# Plot
plt.figure(figsize=(14, 8))
plt.rcParams.update({'font.size': 23})

for scenario in scenarios:
    plt.plot(windows, dissimilarity[scenario], marker='o', label=scenario.rstrip("_"))

plt.xlabel("Window size")
plt.ylabel("Fraction of baseline missing in train")
plt.xticks(windows)
plt.grid(True, linestyle='--', linewidth=0.5, alpha=0.6)
plt.legend(title="Scenario")
plt.tight_layout()
plt.margins(0)  # remove margins around data


plt.savefig("baseline_train_dissimilarity.pdf", dpi=200,bbox_inches='tight', 
            pad_inches=0)
