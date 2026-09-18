#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UPSTREAM="${1:-$ROOT/vendor/comm-limited-congestion-mgmt}"

if [ ! -d "$UPSTREAM" ]; then
  echo "Upstream tree not found: $UPSTREAM"
  echo "Run p0/scripts/bootstrap_upstream.sh first."
  exit 2
fi

cd "$UPSTREAM"

NOISE_MAG="${NOISE_MAG:-4.0}"
OFFSET="${OFFSET:-180}"
RADIUS="${RADIUS:-0.2}"
TEST_SKEW_MAG="${TEST_SKEW_MAG:-20}"
FORECAST_SEED="${FORECAST_SEED:-0}"

mkdir -p p0_logs

run_and_log () {
  name="$1"
  shift
  echo "============================================================"
  echo "RUN: $name"
  echo "CMD: $*"
  echo "============================================================"
  "$@" 2>&1 | tee "p0_logs/${name}.log"
}

run_and_log "opt_tsm${TEST_SKEW_MAG}" python experiments/run_opt.py --noise_mag "$NOISE_MAG" --offset "$OFFSET" --radius "$RADIUS" --test_skew_mag "$TEST_SKEW_MAG"
run_and_log "dec_tsm${TEST_SKEW_MAG}" python experiments/run_dec.py --noise_mag "$NOISE_MAG" --offset "$OFFSET" --radius "$RADIUS" --test_skew_mag "$TEST_SKEW_MAG"
run_and_log "proxy_fs${FORECAST_SEED}" python experiments/run_proxy.py --noise_mag "$NOISE_MAG" --offset "$OFFSET" --radius "$RADIUS" --forecast_seed "$FORECAST_SEED"
run_and_log "ours_fs${FORECAST_SEED}" python experiments/run_ours.py --noise_mag "$NOISE_MAG" --offset "$OFFSET" --radius "$RADIUS" --forecast_seed "$FORECAST_SEED"

echo
echo "Canonical P0 run finished."
echo "Inspect upstream results/{opt,dec,proxy,ours} and p0_logs/."
