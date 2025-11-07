import pandas as pd
import sys

def cleanup(baseline, data):
    baseline = pd.read_csv(baseline, header=None)
    test = pd.read_csv(data, header=None)

    baseline_features = set(map(tuple, baseline.iloc[:, :-1].values))

    # Split test into features and labels
    test_features = test.iloc[:, :-1]
    test_labels = test.iloc[:, -1].copy()

    # Identify rows that are currently labeled as 1
    mask_label_1 = test_labels == 1

    # For those, check whether features exist in baseline
    is_in_baseline = test_features.apply(tuple, axis=1).isin(baseline_features)

    # Correct only labels that are 1 *and* found in baseline → set to 0
    corrected_labels = test_labels.copy()
    corrected_labels[mask_label_1 & is_in_baseline] = 0

    # Count how many labels were changed
    changes = (test_labels != corrected_labels).sum()
    print(f"Number of labels changed: {changes}")

    # Recombine features + updated labels
    test_updated = test_features.copy()
    test_updated[test_features.shape[1]] = corrected_labels.values

    # Save result
    test_updated.to_csv(data, header=False, index=False)
    print(f"Saved cleaned file to {data}")


if __name__ == "__main__":
    cleanup(sys.argv[1], sys.argv[2])