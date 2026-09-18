#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UPSTREAM="$ROOT/vendor/comm-limited-congestion-mgmt"
RESULTS="$ROOT/p0/results"

mkdir -p "$RESULTS"

echo "============================================================"
echo "P0-A MIT/RTE SMOKE REPRODUCTION"
echo "Repository root: $ROOT"
echo "Upstream tree:   $UPSTREAM"
echo "============================================================"

echo "[1/9] Bootstrap pinned upstream"
bash "$ROOT/p0/scripts/bootstrap_upstream.sh"

echo "[2/9] Environment / solver preflight"
python "$ROOT/p0/scripts/preflight.py" --upstream "$UPSTREAM"

echo "[3/9] Generate official scenarios"
python "$ROOT/p0/scripts/generate_official_scenarios.py" --upstream "$UPSTREAM"

echo "[4/9] Validate generated scenarios"
python "$ROOT/p0/scripts/check_generated_data.py" --upstream "$UPSTREAM"

echo "[5/9] Apply documented minimal execution patches"
python "$ROOT/p0/scripts/apply_minimal_patches.py" --upstream "$UPSTREAM"

echo "[6/9] Capture exact provenance"
python "$ROOT/p0/scripts/capture_provenance.py" \
  --upstream "$UPSTREAM" \
  --out "$RESULTS/p0_smoke_provenance.json"

echo "[7/9] Generate and execute canonical four-method manifest"
python "$ROOT/p0/scripts/generate_manifest.py" \
  --stage smoke \
  --out "$RESULTS/p0_smoke_manifest.csv"

python "$ROOT/p0/scripts/execute_manifest.py" \
  --upstream "$UPSTREAM" \
  --manifest "$RESULTS/p0_smoke_manifest.csv" \
  --all

echo "[8/9] Normalize result names and validate checkpoints"
python "$ROOT/p0/scripts/normalize_result_names.py" --upstream "$UPSTREAM"

python "$ROOT/p0/scripts/validate_results.py" \
  --upstream "$UPSTREAM" \
  --stage smoke \
  --json-out "$RESULTS/p0_smoke_report.json"

echo "[9/9] Gate-A decision"
python "$ROOT/p0/scripts/evaluate_gate_a.py" \
  --report "$RESULTS/p0_smoke_report.json" \
  --out "$RESULTS/p0_gate_a_decision.json"

echo
echo "P0-A smoke pipeline completed."
echo "Artifacts:"
echo "  $RESULTS/p0_smoke_provenance.json"
echo "  $RESULTS/p0_smoke_manifest.csv"
echo "  $RESULTS/p0_smoke_report.json"
echo "  $RESULTS/p0_gate_a_decision.json"
