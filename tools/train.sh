#!/usr/bin/env bash
# Usage: sudo ./train
# Example: sudo ./train

set -e

if [ "$#" -ne 0 ]; then
    echo "Usage: sudo ./train"
    echo "Example: sudo ./train"
    exit 1
fi

NAMES=("Log4Shell" "SentimentAnalyzer" "YamlLoad")
MAX_JOBS=7

# hard-coded parameter sets
W_LIST=(2 3 4 6 8 10)
STATES_LIST=(10 50 30 5)

echo "=== Starting model evaluation in parallel ${MAX_JOBS} ==="

mkdir -p eval
for NAME in "${NAMES[@]}"; do
    for W in "${W_LIST[@]}"; do
        for STATES in "${STATES_LIST[@]}"; do
            MODEL_NAME="${NAME}_${STATES}s_w${W}_10p"
            echo "Launching evaluation for ${MODEL_NAME}"
            sudo venv/bin/python3 -m src.main -fn "$MODEL_NAME" --states "$STATES" -t "${NAME}_${W}_baseline" --test "${NAME}_${W}_test"
                > "eval/eval_${MODEL_NAME}.log" 2>&1 &

            # limit concurrency: if we have $MAX_JOBS running, wait for one to finish
            while (( $(jobs -r | wc -l) >= MAX_JOBS )); do
                sleep 25
            done
        done
    done
done

# wait for all background jobs to finish
wait

echo "=== All evaluations completed successfully ==="
