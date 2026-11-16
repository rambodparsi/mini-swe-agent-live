#!/usr/bin/env bash
# Evaluate the patches of one or more run folders with the SWE-bench-Live harness; results go to <run>/eval/.
#   bash minilab/scripts/evaluate.sh runs/b0/s1 runs/b0/s2
# Settings: WORKERS, DATASET (Hub name or local copy, e.g. data/SWE-bench-Live), SPLIT, EVAL_DIR (SWE-bench-Live checkout), EVAL_PYTHON.
set -euo pipefail

WORKERS=${WORKERS:-4}
DATASET=${DATASET:-SWE-bench-Live/SWE-bench-Live}
[ -e "$DATASET" ] && DATASET=$(realpath "$DATASET")  # local copy: the evaluator runs from EVAL_DIR
SPLIT=${SPLIT:-lite}
EVAL_DIR=$(realpath "${EVAL_DIR:-../SWE-bench-Live}")
EVAL_PYTHON=$(realpath -s "${EVAL_PYTHON:-$EVAL_DIR/.venv/bin/python}")

for RUN in "$@"; do
  RUN=$(realpath "$RUN")
  [ -f "$RUN/preds.json" ] || { echo "No preds.json in $RUN"; exit 1; }
  mapfile -t IDS < <(python -c 'import json, sys; print(*json.load(open(sys.argv[1])), sep="\n")' "$RUN/preds.json")
  (cd "$EVAL_DIR" && "$EVAL_PYTHON" -m evaluation.evaluation --dataset "$DATASET" --split "$SPLIT" --platform linux \
    --patch_dir "$RUN/preds.json" --output_dir "$RUN/eval" --workers "$WORKERS" --overwrite 0 \
    --instance_ids "${IDS[@]}") 2>&1 | tee "$RUN/eval.log"
  [ -f "$RUN/eval/results.json" ] || { echo "Evaluation failed for $RUN; see $RUN/eval.log"; exit 1; }
done
