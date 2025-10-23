import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import seaborn as sns
from matplotlib.colors import LogNorm

# --- Load CSV ---
df = pd.read_csv("tools/s4s_ait.csv")
df = df.set_index("GramSize")


plt.figure(figsize=(10, 8))
plt.rcParams.update({'font.size': 23})

vmin, vmax = 0.3, 0.85
sns.heatmap(df, vmin=vmin, vmax=vmax,  annot=True, cmap="RdYlBu_r", cbar_kws={"label": "AIT"})
plt.xlabel("Number of States")
plt.ylabel("Sequence Size")
plt.tight_layout()
plt.margins(0)  # remove margins around data


plt.savefig("s4s_ait_heatmap.pdf", dpi=200,bbox_inches='tight', 
            pad_inches=0)


# sns.heatmap(
#     df,
#     norm=LogNorm(vmin=1, vmax=175),  # logarithmic scaling
#     annot=True,
#     cmap="RdYlBu_r",
#     fmt=".0f",
#     cbar_kws={"label": "FAR"}
# )

# plt.xlabel("Number of States")
# plt.ylabel("Sequence Size")
# plt.tight_layout()
# plt.savefig("l4s_far_heatmap.pdf", dpi=200, bbox_inches='tight', pad_inches=0)
