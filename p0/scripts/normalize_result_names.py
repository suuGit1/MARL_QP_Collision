#!/usr/bin/env python3
"""Create notebook-compatible result filenames without modifying raw checkpoints.

The pinned upstream experiment scripts save checkpoint_<tag>.pt files, while the
official results/generate_figures.ipynb expects method_<tag>.pt filenames.
This adapter creates symlinks by default (or copies with --copy).
"""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
import torch


def fmt_float(v):
    s = f"{float(v):g}"
    return s if "." in s else s + ".0"


def expected_name(method: str, ckpt: dict) -> str:
    if method in {"ours", "proxy"}:
        max_grad = int(float(ckpt["max_grad_norm"]))
        return (
            f"{method}_noise_mag{fmt_float(ckpt['noise_mag'])}"
            f"_offset{int(ckpt['offset'])}"
            f"_epochs{int(ckpt['epochs'])}"
            f"_lr{float(ckpt['lr']):g}"
            f"_forecast_seed{int(ckpt['forecast_seed'])}"
            f"_radius{fmt_float(ckpt['radius'])}"
            f"_optimizer_type{ckpt['optimizer_type']}"
            f"_lr_schedule{ckpt['lr_schedule']}"
            f"_lr_decay_step{int(ckpt['lr_decay_step'])}"
            f"_patience{int(ckpt['patience'])}"
            f"_batch_size{int(ckpt['batch_size'])}"
            f"_max_grad_norm{max_grad}.pt"
        )

    if method in {"opt", "dec"}:
        nm = fmt_float(ckpt["noise_mag"])
        off = int(ckpt["offset"])
        rad = fmt_float(ckpt["radius"])
        tsm = int(ckpt["test_skew_mag"])
        if tsm == 0:
            return f"{method}_noise_mag{nm}_offset{off}_radius{rad}.pt"
        return (
            f"{method}_noise_mag{nm}_offset{off}"
            f"_test_skew_mag{tsm}_radius{rad}.pt"
        )

    raise ValueError(method)


def normalize_dir(method: str, folder: Path, copy: bool) -> tuple[int, int]:
    made = 0
    skipped = 0

    for src in sorted(folder.glob("checkpoint_*.pt")):
        ckpt = torch.load(src, map_location="cpu", weights_only=False)
        dst = folder / expected_name(method, ckpt)

        if dst.exists():
            skipped += 1
            continue

        if copy:
            shutil.copy2(src, dst)
        else:
            rel = os.path.relpath(src, start=dst.parent)
            dst.symlink_to(rel)
        made += 1

    return made, skipped


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--copy", action="store_true", help="copy instead of symlink")
    args = parser.parse_args()

    root = args.upstream.resolve()
    total_made = total_skipped = 0

    for method in ("opt", "dec", "proxy", "ours"):
        folder = root / "results" / method
        if not folder.exists():
            print(f"[skip] {folder} does not exist")
            continue
        made, skipped = normalize_dir(method, folder, args.copy)
        total_made += made
        total_skipped += skipped
        print(f"{method}: created={made}, already_present={skipped}")

    print(f"done: created={total_made}, already_present={total_skipped}")


if __name__ == "__main__":
    main()
