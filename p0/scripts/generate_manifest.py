#!/usr/bin/env python3
"""Generate clean P0 command manifests.

This replaces the stale upstream make_sweep_slurm.py interface without changing
any experiment equations or parameters.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


MAIN_NOISE = [2.0, 2.5, 3.0, 3.5, 4.0]
FULL_NOISE = [2.0, 2.4, 2.45, 2.5, 3.0, 3.5, 4.0]
OFFSETS = [0, 60, 120, 180]
FORECAST_SEEDS = [0, 1, 2, 3, 4]
TEST_SKEWS = [0, 10, 20, 30, 40]


def cmd_train(method, noise, offset, seed):
    return (
        f"python experiments/run_{method}.py "
        f"--noise_mag {noise} --offset {offset} --radius 0.2 "
        f"--forecast_seed {seed} --epochs 120 --lr 0.001 "
        f"--optimizer_type clipped_gd --lr_schedule plateau "
        f"--lr_decay_step 20 --patience 5 --batch_size 2 "
        f"--max_grad_norm 30000"
    )


def cmd_base(method, noise, offset, skew):
    return (
        f"python experiments/run_{method}.py "
        f"--noise_mag {noise} --offset {offset} "
        f"--test_skew_mag {skew} --radius 0.2"
    )


def rows_for(stage):
    rows = []

    if stage == "smoke":
        rows.extend([
            ("opt", 4.0, 180, "", 20, cmd_base("opt", 4.0, 180, 20)),
            ("dec", 4.0, 180, "", 20, cmd_base("dec", 4.0, 180, 20)),
            ("proxy", 4.0, 180, 0, "", cmd_train("proxy", 4.0, 180, 0)),
            ("ours", 4.0, 180, 0, "", cmd_train("ours", 4.0, 180, 0)),
        ])
        return rows

    noises = MAIN_NOISE if stage == "main" else FULL_NOISE

    for method in ("ours", "proxy"):
        for noise in noises:
            for offset in OFFSETS:
                for seed in FORECAST_SEEDS:
                    rows.append(
                        (method, noise, offset, seed, "", cmd_train(method, noise, offset, seed))
                    )

    for method in ("opt", "dec"):
        for noise in noises:
            for offset in OFFSETS:
                for skew in TEST_SKEWS:
                    rows.append(
                        (method, noise, offset, "", skew, cmd_base(method, noise, offset, skew))
                    )

    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["smoke", "main", "full"], required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    rows = rows_for(args.stage)
    out = args.out or Path(f"p0_{args.stage}_manifest.csv")
    out.parent.mkdir(parents=True, exist_ok=True)

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "task_id", "method", "noise_mag", "offset",
            "forecast_seed", "test_skew_mag", "command"
        ])
        for i, row in enumerate(rows):
            w.writerow([i, *row])

    counts = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1

    print(f"stage={args.stage}")
    print(f"manifest={out}")
    print(f"total_runs={len(rows)}")
    for method in ("opt", "dec", "proxy", "ours"):
        if method in counts:
            print(f"{method}={counts[method]}")


if __name__ == "__main__":
    main()
