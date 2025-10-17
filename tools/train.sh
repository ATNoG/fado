#!/bin/bash
# Usage: sudo ./generate [NUM] [NAME]
# Example: sudo ./generate 8 test

set -e

if [ "$#" -ne 0 ]; then
    echo "Usage: sudo ./train [NAME]"
    echo "Example: sudo ./train test"
    exit 1
fi

# NAME=$1
NAMES=("Log4Shell" "SentimentAnalyzer") 
MAX_JOBS=7

# --- Hard-coded parameter sets ---
W_LIST=(3 2 4 6 8 10)
STATES_LIST=(10 50 30 5)

echo "=== Starting model evaluation in parallel ${MAX_JOBS} ==="


for NAME in "${NAMES[@]}"; do
    for W in "${W_LIST[@]}"; do
        for STATES in "${STATES_LIST[@]}"; do
            MODEL_NAME="${NAME}_${STATES}s_w${W}_10p"
            echo "Launching evaluation for ${MODEL_NAME}"
            sudo venv/bin/python3 -m src.main \
                -m "$MODEL_NAME" \
                --states "$STATES" \
                -t "${NAME}_${W}" \
                -v "${NAME}_${W}_validation" \
                --test "${NAME}_${W}_test_v2" \
                > "eval/eval_${MODEL_NAME}.log" 2>&1 &

            # Limit concurrency: if we have $MAX_JOBS running, wait for one to finish
            while (( $(jobs -r | wc -l) >= MAX_JOBS )); do
                sleep 25
            done
        done
    done
done

# Wait for all background jobs to finish
wait
echo "=== All evaluations completed successfully ==="
