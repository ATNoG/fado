#!/bin/bash
# Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]
# Example: sudo ./generate 8 test 2 3 4

set -e

if [ "$#" -lt 1 ]; then
    echo "Usage: sudo ./generate [NUM] [NAME] [ARRAY of W]"
    echo "Example: sudo ./generate 8 test 2 3 4"
    exit 1
fi

NAME=$1
MAX_JOBS=3
W_LIST=(2)
STATES_LIST=(5 10 30 50)

echo "=== Starting model evaluation in parallel ==="

for W in "${W_LIST[@]}"; do
    for STATES in "${STATES_LIST[@]}"; do
        MODEL_NAME="${NAME}_${STATES}s_w${W}_3p"
        echo "Launching evaluation for ${MODEL_NAME}"
        sudo venv/bin/python3 -m src.main \
            -m "$MODEL_NAME" \
            --test "${NAME}_${W}_test" \
            > "eval_${MODEL_NAME}_8tol.log" 2>&1 &

        # Limit concurrency: if we have $MAX_JOBS running, wait for one to finish
        while (( $(jobs -r | wc -l) >= MAX_JOBS )); do
            sleep 15
        done
    done
done

# Wait for all background jobs to finish
wait
echo "=== All evaluations completed successfully ==="
