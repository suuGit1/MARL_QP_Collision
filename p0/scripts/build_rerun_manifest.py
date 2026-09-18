#!/usr/bin/env python3
"""Build a manifest containing only missing/failed P0 tasks.

The script infers completion from notebook-compatible result filenames after
normalize_result_names.py has been run.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def fmt_float(v):
    s = f"{float(v):g}"
    return s if "." in s else s + ".0"


def expected_output(row, upstream: Path) -> Path:
    method = row["method"]
    noise = float(row["noise_mag"])
    offset = int(row["offset"])

    if method in {"ours", "proxy"}:
        seed = int(row["forecast_seed"])
        name = (
            f"{method}_noise_mag{fmt_float(noise)}"
            f"_offset{offset}_epochs120_lr0.001"
            f"_forecast_seed{seed}_radius0.2"
            f"_optimizer_typeclipped_gd_lr_scheduleplateau"
            f"_lr_decay_step20_patience5_batch_size2_max_grad_norm30000.pt"
        )
    else:
        skew = int(row["test_skew_mag"])
        if skew == 0:
            name = (
                f"{method}_noise_mag{fmt_float(noise)}"
                f"_offset{offset}_radius0.2.pt"
            )
        else:
            name = (
                f"{method}_noise_mag{fmt_float(noise)}"
                f"_offset{offset}_test_skew_mag{skew}_radius0.2.pt"
            )

    return upstream / "results" / method / name


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    with args.manifest.open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    missing = []
    for row in rows:
        if not expected_output(row, args.upstream.resolve()).exists():
            missing.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            for new_id, row in enumerate(missing):
                row = dict(row)
                row["task_id"] = str(new_id)
                w.writerow(row)

    print(f"original_tasks={len(rows)}")
    print(f"missing_or_failed={len(missing)}")
    print(f"rerun_manifest={args.out}")

if __name__ == "__main__":
    main()
