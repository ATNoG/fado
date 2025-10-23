import sys
from collections import Counter
from probe.bcc.syscall import syscalls
import pandas as pd
import matplotlib.pyplot as plt

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


# Get 10 most common
top10 = counter.most_common(30)
# Compute relative frequencies
total = len(rows)   
labels = []
values = []
for seq_tuple, count in top10:
    decoded_seq = []
    for sc in seq_tuple:
        try:
            name = syscalls.get(int(sc), b"unkown")
            if isinstance(name, bytes):
                name = name.decode()
            decoded_seq.append(name)
        except Exception:
            decoded_seq.append(f"unknown({sc})")
    # Join syscalls in sequence for readable label
    labels.append(" → ".join(decoded_seq))
    values.append(count / total)

# --- Plot bar chart ---
plt.figure(figsize=(30,13))
plt.rcParams.update({'font.size': 23})
plt.barh(labels, values)
plt.axvline(x=0.03, color='red', linestyle='--', linewidth=3, label='Threshold = 3.5%')
plt.xlabel("Relative Frequency")
plt.ylabel("Sequence")
plt.gca().invert_yaxis()  # Most frequent on top
plt.tight_layout()

plt.savefig("freqs8.png")