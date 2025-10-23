import sys
import pandas as pd

if len(sys.argv) < 3:
    print("Usage: python diff_unique.py <baseline.csv> <test.csv>")
    sys.exit(1)



    ## AVERAGE THE PERCENTAGE FOR ALL SCENARIOS AND DO THIS FOR EVERY WINDOW SIZE

baseline_path, test_path = sys.argv[1], sys.argv[2]

# Read CSVs
baseline_df = pd.read_csv(baseline_path, header=None)
test_df     = pd.read_csv(test_path, header=None)

# Use all columns except the last to define the sequence
baseline_seqs = set(map(tuple, baseline_df.iloc[:, :-1].values)) if baseline_df.shape[1] > 1 else set(map(tuple, baseline_df.values))
test_seqs     = set(map(tuple, test_df.iloc[:, :-1].values))     if test_df.shape[1] > 1 else set(map(tuple, test_df.values))

# Unique counts
n_base = len(baseline_seqs)
n_test = len(test_seqs)

# Sequences present in one set and not the other
only_in_test = test_seqs - baseline_seqs
only_in_base = baseline_seqs - test_seqs
in_both      = baseline_seqs & test_seqs

# Percentages (guard against division by zero)
pct_only_in_test = (len(only_in_test) / n_test * 100) if n_test else 0.0
pct_only_in_base = (len(only_in_base) / n_base * 100) if n_base else 0.0

# (Optional) overlap metrics
jaccard = (len(in_both) / len(baseline_seqs | test_seqs)) * 100 if (baseline_seqs or test_seqs) else 0.0

print(f"Unique sequences (baseline): {n_base}")
print(f"Unique sequences (test):     {n_test}")
print()
print(f"Only in TEST (count): {len(only_in_test)}  -> {pct_only_in_test:.2f}% of TEST uniques")
print(f"Only in BASE (count): {len(only_in_base)}  -> {pct_only_in_base:.2f}% of BASE uniques")
print(f"In BOTH (count):      {len(in_both)}")
print(f"Jaccard similarity:   {jaccard:.2f}%")

# If you still want to compare with provided labels in test (last column):
# test_labels = test_df.iloc[:, -1]
# is_novel = ~test_df.iloc[:, :-1].apply(tuple, axis=1).isin(baseline_seqs)
# changes = (is_novel.astype(int).values != test_labels.values).sum()
# print(f"Number of labels changed (novelty vs label): {changes}")
