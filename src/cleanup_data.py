import pandas as pd
import sys

def cleanup(baseline, data):
    baseline = pd.read_csv(baseline, header=None)
    test = pd.read_csv(data, header=None)

    baseline_features = set(map(tuple, baseline.iloc[:, :-1].values))

    # Split test into features and labels
    test_features = test.iloc[:, :-1]
    test_labels = test.iloc[:, -1]

    # Mark 0 if in baseline, else 1
    is_in_baseline =(~test_features.apply(tuple, axis=1).isin(baseline_features)).astype(int)

    changes = (is_in_baseline.values != test_labels).sum()
    print(f"Number of labels changed: {changes}")

    # Recombine features + updated labels
    test_updated = test_features.copy()
    test_updated[test_features.shape[1]] = is_in_baseline.values

    # Save result
    test_updated.to_csv(data, header=False, index=False)

    print(f"Saved cleaned file to {data}")

if __name__ == "__main__":
    cleanup(sys.argv[1], sys.argv[2])