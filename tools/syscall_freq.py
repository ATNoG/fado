from utils import DB
import os
from probe.bcc.syscall import syscalls
from collections import Counter
import pandas as pd
import sys
import matplotlib.pyplot as plt

# --- Read and preprocess data ---
if len(sys.argv) < 2:
    print("Usage: python script.py <data.csv>")
    sys.exit(1)

data_path = sys.argv[1]
data = pd.read_csv(data_path, header=None)

# Drop last column if not needed
data.drop(data.columns[-1], axis=1, inplace=True)

# Convert to tuples (hashable for Counter)
rows = [tuple(row) for row in data.to_numpy()]

# --- Count frequency of each unique row ---
counter = Counter(rows)
total = len(rows)

# --- Compute relative frequencies ---
relative_freqs = {seq: count / total for seq, count in counter.items()}

# --- Calculate how much data remains after removing frequent sequences ---
# Thresholds
thr_20 = 0.10
thr_5 = 0.03

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
remaining_20 = sum(count for seq, count in counter.items() if relative_freqs[seq] <= thr_20)
remaining_5 = sum(count for seq, count in counter.items() if relative_freqs[seq] <= thr_5)

# Convert to percentages of total data
percent_remaining_20 = (remaining_20 / total) * 100
percent_remaining_5 = (remaining_5 / total) * 100

print(f"Data remaining after removing sequences >20% frequency: {remaining_20} rows ({percent_remaining_20:.2f}%)")
print(f"Data remaining after removing sequences >5% frequency: {remaining_5} rows ({percent_remaining_5:.2f}%)")

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
#     values.append(count / total)

# # --- Plot bar chart ---
# plt.figure(figsize=(18, 8))
# plt.rcParams.update({'font.size': 23})
# plt.barh(labels, values)
# plt.xlabel("Relative Frequency")
# plt.ylabel("Sequence")
# plt.gca().invert_yaxis()  # Most frequent on top
# plt.tight_layout()
# plt.savefig("freqs.pdf")
