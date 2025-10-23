from matplotlib.ticker import PercentFormatter
import pandas as pd
import matplotlib.pyplot as plt


# --- Plot ---
df = pd.read_csv("tools/train_profile.csv", header=None, names=["value"])

values = df["value"].to_numpy()
x = range(1, len(values) + 1)
plt.figure(figsize=(14, 8))
plt.rcParams.update({'font.size': 23})
plt.plot(x, values, linewidth=4, color='steelblue')

plt.xlabel("Iteration")
plt.ylabel("Log-Likelihood Gain")
plt.yscale("log")  # <- logarithmic y-axis
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.margins(0)  # remove margins around data


# Save & show
plt.savefig("train_profile.pdf", dpi=200, bbox_inches='tight', pad_inches=0)