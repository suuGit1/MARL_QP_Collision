#!/usr/bin/env python3
"""Validate P0 checkpoints and reproduce the notebook's core statistics.

This script does not modify results. Run normalize_result_names.py first.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import torch


MAIN_NOISE = [2.0, 2.5, 3.0, 3.5, 4.0]
FULL_NOISE = [2.0, 2.4, 2.45, 2.5, 3.0, 3.5, 4.0]
OFFSETS = [0, 60, 120, 180]
FORECAST_SEEDS = [0, 1, 2, 3, 4]
TEST_SEEDS = [0, 1, 2]
TEST_SKEWS = [0, 10, 20, 30, 40]


def fmt_float(v):
    s = f"{float(v):g}"
    return s if "." in s else s + ".0"


def train_name(method, noise, offset, seed):
    return (
        f"{method}_noise_mag{fmt_float(noise)}"
        f"_offset{offset}_epochs120_lr0.001"
        f"_forecast_seed{seed}_radius0.2"
        f"_optimizer_typeclipped_gd_lr_scheduleplateau"
        f"_lr_decay_step20_patience5_batch_size2_max_grad_norm30000.pt"
    )


def base_name(method, noise, offset, skew):
    if skew == 0:
        return f"{method}_noise_mag{fmt_float(noise)}_offset{offset}_radius0.2.pt"
    return (
        f"{method}_noise_mag{fmt_float(noise)}_offset{offset}"
        f"_test_skew_mag{skew}_radius0.2.pt"
    )


def finite_tensor(x):
    return torch.is_tensor(x) and bool(torch.isfinite(x).all())


def load(path):
    return torch.load(path, map_location="cpu", weights_only=False)


def eval_tensor_train(ckpt, skew, test_seed=None):
    if skew == 0:
        return ckpt[0]
    return ckpt[(skew, test_seed)]


def eval_tensor_base(ckpt, method, skew, test_seed=None):
    key = "optimal" if method == "opt" else "base"
    if skew == 0:
        return ckpt[key]
    return ckpt[(test_seed, key)]


def validate_eval_tensor(t, where, errors):
    if not torch.is_tensor(t):
        errors.append(f"{where}: expected tensor, got {type(t)}")
        return
    if t.ndim != 2 or t.shape[1] != 3:
        errors.append(f"{where}: expected shape [N,3], got {tuple(t.shape)}")
    if not torch.isfinite(t).all():
        errors.append(f"{where}: contains NaN/Inf")
    if (t[:, 0] < 0).any():
        errors.append(f"{where}: negative total loss found")


def stats(x):
    x = torch.as_tensor(x, dtype=torch.double).flatten()
    return {
        "n": int(x.numel()),
        "mean": float(x.mean()),
        "std": float(x.std()) if x.numel() > 1 else 0.0,
        "min": float(x.min()),
        "max": float(x.max()),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--stage", choices=["smoke", "main", "full"], required=True)
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    root = args.upstream.resolve()
    errors = []
    missing = []

    if args.stage == "smoke":
        noises = [4.0]
        offsets = [180]
        forecast_seeds = [0]
        skews = [20]
    else:
        noises = MAIN_NOISE if args.stage == "main" else FULL_NOISE
        offsets = OFFSETS
        forecast_seeds = FORECAST_SEEDS
        skews = TEST_SKEWS

    ours_gap = {s: [] for s in skews}
    dec_gap = {s: [] for s in skews}
    proxy_over_ours_case_means = {s: [] for s in skews}

    loaded_train = {}
    loaded_base = {}

    # Load/validate train-method checkpoints.
    for method in ("ours", "proxy"):
        for noise in noises:
            for offset in offsets:
                for fs in forecast_seeds:
                    p = root / "results" / method / train_name(method, noise, offset, fs)
                    if not p.exists():
                        missing.append(str(p))
                        continue
                    ckpt = load(p)
                    loaded_train[(method, noise, offset, fs)] = ckpt

                    if ckpt.get("run_failed", False):
                        errors.append(
                            f"{p}: run_failed=True, message={ckpt.get('fail_message', '')}"
                        )

                    expected_skews = TEST_SKEWS if args.stage != "smoke" else [20]
                    for skew in expected_skews:
                        seeds = [None] if skew == 0 else TEST_SEEDS
                        for ts in seeds:
                            try:
                                t = eval_tensor_train(ckpt, skew, ts)
                            except KeyError as exc:
                                errors.append(f"{p}: missing evaluation key {exc}")
                                continue
                            validate_eval_tensor(t, f"{p}:{skew}:{ts}", errors)

    # Load/validate base checkpoints.
    for method in ("opt", "dec"):
        for noise in noises:
            for offset in offsets:
                for skew in skews:
                    p = root / "results" / method / base_name(method, noise, offset, skew)
                    if not p.exists():
                        missing.append(str(p))
                        continue
                    ckpt = load(p)
                    loaded_base[(method, noise, offset, skew)] = ckpt
                    seeds = [None] if skew == 0 else TEST_SEEDS
                    for ts in seeds:
                        try:
                            t = eval_tensor_base(ckpt, method, skew, ts)
                        except KeyError as exc:
                            errors.append(f"{p}: missing evaluation key {exc}")
                            continue
                        validate_eval_tensor(t, f"{p}:{skew}:{ts}", errors)

    # Core notebook-compatible ratios.
    for noise in noises:
        for offset in offsets:
            for skew in skews:
                opt = loaded_base.get(("opt", noise, offset, skew))
                dec = loaded_base.get(("dec", noise, offset, skew))
                if opt is None or dec is None:
                    continue

                test_seeds = [None] if skew == 0 else TEST_SEEDS
                for fs in forecast_seeds:
                    ours = loaded_train.get(("ours", noise, offset, fs))
                    proxy = loaded_train.get(("proxy", noise, offset, fs))
                    if ours is None or proxy is None:
                        continue

                    for ts in test_seeds:
                        o = eval_tensor_train(ours, skew, ts)[:, 0].double()
                        p = eval_tensor_train(proxy, skew, ts)[:, 0].double()
                        opt_t = eval_tensor_base(opt, "opt", skew, ts)[:, 0].double()
                        dec_t = eval_tensor_base(dec, "dec", skew, ts)[:, 0].double()

                        if torch.any(opt_t <= 0) or torch.any(o <= 0):
                            errors.append(
                                f"non-positive denominator at noise={noise}, offset={offset}, "
                                f"skew={skew}, fs={fs}, ts={ts}"
                            )
                            continue

                        ours_gap[skew].extend((o / opt_t).tolist())
                        dec_gap[skew].extend((dec_t / opt_t).tolist())
                        # Exact concept used by official Figure 4: mean per experiment case.
                        proxy_over_ours_case_means[skew].append(float(torch.mean(p / o)))

    report = {
        "stage": args.stage,
        "missing_count": len(missing),
        "error_count": len(errors),
        "missing": missing,
        "errors": errors,
        "metrics": {},
    }

    for skew in skews:
        if not ours_gap[skew]:
            continue
        proxy_vals = torch.tensor(proxy_over_ours_case_means[skew], dtype=torch.double)
        report["metrics"][str(skew)] = {
            "ours_over_opt": stats(ours_gap[skew]),
            "dec_over_opt": stats(dec_gap[skew]),
            "proxy_over_ours_case_mean": stats(proxy_vals),
            "proxy_case_pct_over_1p05": float(
                100.0 * torch.mean((proxy_vals > 1.05).double())
            ) if proxy_vals.numel() else None,
        }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    if missing or errors:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
