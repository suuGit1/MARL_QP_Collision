#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
LOCK_FILE="$ROOT/p0/UPSTREAM.lock"
source "$LOCK_FILE"

VENDOR_DIR="$ROOT/vendor"
TARGET="$VENDOR_DIR/comm-limited-congestion-mgmt"

mkdir -p "$VENDOR_DIR"

if [ ! -d "$TARGET/.git" ]; then
  git clone "$UPSTREAM_REPO" "$TARGET"
fi

git -C "$TARGET" fetch --all --tags
git -C "$TARGET" checkout --detach "$UPSTREAM_COMMIT"

ACTUAL="$(git -C "$TARGET" rev-parse HEAD)"
if [ "$ACTUAL" != "$UPSTREAM_COMMIT" ]; then
  echo "ERROR: upstream commit mismatch: $ACTUAL"
  exit 2
fi

echo "Pinned MIT/RTE upstream at $ACTUAL"
echo "Next:"
echo "  cd $TARGET"
echo "  python -m pip install -r requirements.txt"
echo "  python $ROOT/p0/scripts/preflight.py --upstream $TARGET"
