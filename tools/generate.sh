#!/usr/bin/env bash
# Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]
# Example: sudo ./generate 0 YamlLoad 2 3 4 6 8 10

set -e

if [ "$#" -lt 3 ]; then
    echo "Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]"
    echo "Example: sudo ./generate 0 yaml_load 2 3 4"
    exit 1
fi

NUM=$1
NAME=$2
shift 2 # "$@" now holds all W values

for W in "$@"; do
    echo "=== Generating training and test data for W=$W ==="
    sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_${W}_baseline" -l 2000000 -d 600 # 10 min
    sudo venv/bin/python3 -m src.main -sc "$NUM" -w "$W" -fn "${NAME}_${W}_test" -l 2000000 -d 600 -e # 10 min
    sudo venv/bin/python3 -m src.cleanup_data data/logs/"${NAME}_${W}_baseline" data/logs/"${NAME}_${W}_test"
done

# wait for all background jobs to finish
wait

echo "=== All evaluations completed successfully ==="
