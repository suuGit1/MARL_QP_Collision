#!/usr/bin/env python3
"""Generate a generic SLURM array wrapper for a P0 manifest."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def count_rows(path: Path) -> int:
    with path.open("r", encoding="utf-8", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo-root", type=str, default="$PWD")
    parser.add_argument("--partition", type=str, default="compute")
    parser.add_argument("--cpus", type=int, default=3)
    parser.add_argument("--mem", type=str, default="16G")
    parser.add_argument("--time", type=str, default="12:00:00")
    parser.add_argument(
        "--activation",
        type=str,
        default='echo "Activate your Python/Gurobi environment here"',
        help="shell command executed before each task",
    )
    args = parser.parse_args()

    n = count_rows(args.manifest)
    if n <= 0:
        raise SystemExit("manifest is empty")

    manifest_abs = args.manifest.resolve()
    text = f"""#!/usr/bin/env bash
#SBATCH --job-name=p0_repro
#SBATCH --partition={args.partition}
#SBATCH --cpus-per-task={args.cpus}
#SBATCH --mem={args.mem}
#SBATCH --time={args.time}
#SBATCH --array=0-{n-1}
#SBATCH --output=p0_slurm_%A_%a.out
#SBATCH --error=p0_slurm_%A_%a.err

set -euo pipefail

REPO_ROOT={args.repo_root}
cd "$REPO_ROOT"

{args.activation}

python p0/scripts/execute_manifest.py \
  --upstream vendor/comm-limited-congestion-mgmt \
  --manifest "{manifest_abs}" \
  --task-id "$SLURM_ARRAY_TASK_ID"
"""
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Array range: 0-{n-1}")

if __name__ == "__main__":
    main()
