import matplotlib.pyplot as plt
import pandas as pd
import sys
import os

# Read CSV (replace with your actual path)
filename = sys.argv[1]
df = pd.read_csv(f"{filename}.csv")
filename = os.path.basename(filename)
output = os.path.join("data/figs", filename) + ".pdf"

# Extract X axis from the first column
x_values = df.iloc[:, 0]

# Plot
plt.figure(figsize=(14, 8))
plt.rcParams.update({'font.size': 23})

# Plot MCC (solid lines)
for i in range(1, 4):  # columns MCC_S1, MCC_S2, MCC_S3
    col_name = df.columns[i]
    scenario_num = col_name.split("_")[1][1]  # Extract number from MCC_S1 -> "1"
    plt.plot(x_values, df[col_name], label=f"S{scenario_num} (MCC)", linestyle='-', marker='o', linewidth=4, markersize=12)

# Plot APT (dashed lines)
for i in range(4, 7):  # columns APT_S1, APT_S2, APT_S3
    col_name = df.columns[i]
    scenario_num = col_name.split("_")[1][1]  # Extract number from APT_S1 -> "1"
    plt.plot(x_values, df[col_name], label=f"S{scenario_num} (APT)", linestyle='--', marker='o', linewidth=4, markersize=12)

plt.axvline(x=50, color='red', linestyle=':', linewidth=3)
# Labels and legend
plt.xticks([10, 30, 50, 70, 100])
plt.xlabel(df.columns[0])
plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
plt.grid(True)
plt.tight_layout()
plt.margins(0)  # remove margins around data
plt.savefig(output,
            bbox_inches='tight', 
            pad_inches=0)
