#!/usr/bin/env bash
# Smoke test on the first N SWE-bench-Live lite instances:
#   1. check dataset and images   2. evaluate gold patches   3. run the agent   4. evaluate the agent's patches
# Run from the repository root. Settings can be overridden with environment variables, e.g.
#   N=2 WORKERS=2 EVAL_DIR=../SWE-bench-Live EVAL_PYTHON=../SWE-bench-Live/.venv/bin/python bash swelive/scripts/smoke.sh
set -euo pipefail

N=${N:-2}
WORKERS=${WORKERS:-2}
DATASET=${DATASET:-SWE-bench-Live/SWE-bench-Live}
SPLIT=${SPLIT:-lite}
CONFIG=${CONFIG:-swelive/configs/swelive.yaml}
EVAL_DIR=$(realpath "${EVAL_DIR:-../SWE-bench-Live}")
EVAL_PYTHON=$(realpath "${EVAL_PYTHON:-$EVAL_DIR/.venv/bin/python}")
OUT=$(realpath -m "${OUT:-runs/smoke_$(date +%Y%m%d_%H%M%S)}")

[ -f "$EVAL_DIR/evaluation/evaluation.py" ] || { echo "SWE-bench-Live evaluator not found in $EVAL_DIR (set EVAL_DIR)"; exit 1; }
[ -x "$EVAL_PYTHON" ] || { echo "Evaluator Python not found: $EVAL_PYTHON (set EVAL_PYTHON)"; exit 1; }
mkdir -p "$OUT"
echo "Output: $OUT"

echo "== 1/4 Dataset and images"
python swelive/scripts/check_dataset.py --dataset "$DATASET" --split "$SPLIT" -n "$N" -c "$CONFIG" \
  --ids-out "$OUT/instance_ids.txt" --check-images
mapfile -t IDS < "$OUT/instance_ids.txt"

evaluate() {  # $1 = predictions file or "gold", $2 = output folder
  (cd "$EVAL_DIR" && "$EVAL_PYTHON" -m evaluation.evaluation --dataset "$DATASET" --split "$SPLIT" \
    --platform linux --patch_dir "$1" --output_dir "$2" --workers "$WORKERS" --overwrite 0 \
    --instance_ids "${IDS[@]}") 2>&1 | tee "$2.log"
}

echo "== 2/4 Gold patches (checks the evaluator and images)"
evaluate gold "$OUT/eval_gold"

echo "== 3/4 Agent"
mini-extra swebench -c swebench.yaml -c "$CONFIG" --subset "$DATASET" --split "$SPLIT" \
  --slice "0:$N" -w "$WORKERS" -o "$OUT/agent"

echo "== 4/4 Agent patches"
evaluate "$OUT/agent/preds.json" "$OUT/eval_agent"

python - "$OUT" <<'EOF'
import json, sys
from pathlib import Path
out = Path(sys.argv[1])
for name in ["eval_gold", "eval_agent"]:
    r = json.loads((out / name / "results.json").read_text())
    print(f"{name}: resolved {len(r['success_ids'])}/{r['submitted']}, failed {r['failure_ids']}, "
          f"empty {r['empty_patch_ids']}, errors {r['error_ids']}, incomplete {r['incomplete_ids']}")
EOF
echo "Done. Trajectories: $OUT/agent/<instance_id>/  Reports: $OUT/eval_*/<instance_id>/report.json"
