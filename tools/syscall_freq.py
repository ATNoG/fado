from matplotlib.ticker import PercentFormatter
from utils import DB
import os
from probe.bcc.syscall import syscalls
from collections import Counter
import pandas as pd
import sys
import matplotlib.pyplot as plt

# --- Read and preprocess data ---

windows = [2, 3, 4, 6, 8, 10]
scenarios = ["baseline_Log4Shell_", "baseline_SentimentAnalyzer_", "baseline_YamlLoad_"]
entropies = {s.split("_")[1]: [] for s in scenarios} 


for scenario in scenarios:
    avg_remaining = 0
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
        # --- Compute relative frequencies ---
        relative_freqs = {seq: count / total for seq, count in counter.items()}

        # --- Calculate how much data remains after removing frequent sequences ---
        # Thresholds
        thr_10 = 0.10
        remaining_10 = sum(count for seq, count in counter.items() if relative_freqs[seq] <= thr_10)

        # Convert to percentages of total data
        percent_remaining_10 = (remaining_10 / total) * 100
        avg_remaining += percent_remaining_10

        print(f"Data remaining after removing sequences >10% frequency: {remaining_10} rows ({percent_remaining_10:.2f}%)")
    
    entropies[scenario.split("_")[1]].append(avg_remaining/len(windows))
        
for k, v in entropies.items():
    print(k)
    print(v)
# thresholds = [0.001, 0.005, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5]
# remaining = {}
# sizes = [2, 3, 4, 6, 8, 10]

# for s in sizes:
#     datapath = f"{name}_{s}.csv"
#     datapath = os.path.join(DB, datapath)
#     data = pd.read_csv(datapath, header=None)

#     # Drop last column if not needed
#     data.drop(data.columns[-1], axis=1, inplace=True)

#     # Convert to tuples (hashable for Counter)
#     rows = [tuple(row) for row in data.to_numpy()]

#     # --- Count frequency of each unique row ---
#     counter = Counter(rows)
#     total = len(rows)

#     # --- Compute relative frequencies ---
#     remaining[s] = []
#     relative_freqs = {seq: count / total for seq, count in counter.items()}
#     for i in thresholds:
#         k = sum(count for seq, count in counter.items() if relative_freqs[seq] <= i)
#         percent_remaining = (k / total) * 100
#         remaining[s].append(percent_remaining)

# # --- Plot ---
# plt.figure(figsize=(10, 6))
# for s, values in remaining.items():
#     plt.plot([t * 100 for t in thresholds], values, marker='o', label=f'Window {s}')

# plt.xscale('log')
# plt.xlabel("Threshold Frequency (%)")
# plt.ylabel("Data Remaining (%)")
# plt.title("Data Retention vs Frequency Thresholds")
# plt.legend(title="Window Size")
# plt.grid(True, linestyle='--', alpha=0.6)
# plt.tight_layout()
# plt.savefig(f"{name}_variation.png")
# Count how many rows remain if we exclude sequences > threshold



# # Get 10 most common
# top10 = counter.most_common(10)
# # Compute relative frequencies
# total = len(rows)   
# labels = []
# values = []
# for seq_tuple, count in top10:
#     decoded_seq = []
#     for sc in seq_tuple:
#         try:
#             name = syscalls.get(int(sc), b"unkown")
#             if isinstance(name, bytes):
#                 name = name.decode()
#             decoded_seq.append(name)
#         except Exception:
#             decoded_seq.append(f"unknown({sc})")
#     # Join syscalls in sequence for readable label
#     labels.append(" → ".join(decoded_seq))
#     values.append((count / total) * 100)

# plt.figure(figsize=(14, 8))
# plt.rcParams.update({'font.size': 23})

# ax = plt.gca()
# plt.barh(labels, values, color='steelblue')

# # Format x-axis
# ax.xaxis.set_major_formatter(PercentFormatter(xmax=100))

# # Add vertical line BEFORE saving
# ax.axvline(x=10, color='red', linestyle='--', linewidth=2)

# # Labels and layout
# plt.xlabel("Relative Frequency")
# plt.ylabel("Sequence")
# ax.invert_yaxis()
# plt.grid(axis='x', linestyle='--', alpha=0.5)
# plt.tight_layout()
# plt.margins(0)
# plt.savefig("freqs.pdf", bbox_inches='tight', pad_inches=0)