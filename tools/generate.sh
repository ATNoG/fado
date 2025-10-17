#!/bin/bash
# Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]
# Example: sudo ./generate 8 test 2 3 4

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]"
    echo "Example: sudo ./generate 8 test 2 3 4"
    exit 1
fi

NUM=$1
NAME=$2
W=$3
shift 2  # "$@" now holds all W values

# echo "=== Generating training and test data for W=$W ==="
# sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_WSIZE_validation" -d 720 -l 200000 # 12 min
# sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "baseline_${NAME}_WSIZE" -l 2000000 -d 7200 # 2 hours
# sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_WSIZE" -l 500000 -d 1800 # 30 min
sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_WSIZE_test_v2" -l 800000 -e -b "baseline_${NAME}_WSIZE" -d 2700 # 45 min

# # --- Stage 1: Data generation ---
# for W in "$@"; do
#     echo "=== Generating training and test data for W=$W ==="
#     # sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_${W}_validation" -d 600 -l 200000 # 10 min
#     # sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "baseline_${NAME}_${W}" -l 2000000 -d 7200 # 2 hours
#     # sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_${W}" -l 500000 -d 1800 # 30 min
#     # sudo venv/bin/python3 -m src.main -s -sc "$NUM" -w "$W" -fn "${NAME}_${W}_test" -l 800000 -e -b "baseline_${NAME}_${W}" -d 3600 # 1 hour
#     sudo venv/bin/python3 -m src.cleanup_data new_data/logs/baseline_${NAME}_${W}.csv new_data/logs/${NAME}_${W}_test_v2.csv
# done


# Wait for all background jobs to finish
wait

echo "=== All evaluations completed successfully ==="
