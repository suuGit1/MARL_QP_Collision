#!/usr/bin/env python3
"""Rebuild the four core official result plots from normalized P0 checkpoints.

This is a CLI transcription of the corresponding logic in
results/generate_figures.ipynb. It does not change any experiment result.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import torch

MAIN_NOISE = [2.0, 2.5, 3.0, 3.5, 4.0]
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


def load(path):
    return torch.load(path, map_location="cpu", weights_only=False)


def train_loss(root, method, noise, offset, fs, skew, ts=None):
    ckpt = load(root / "results" / method / train_name(method, noise, offset, fs))
    t = ckpt[0] if skew == 0 else ckpt[(skew, ts)]
    return t[:, 0].double()


def base_loss(root, method, noise, offset, skew, ts=None):
    ckpt = load(root / "results" / method / base_name(method, noise, offset, skew))
    key = "optimal" if method == "opt" else "base"
    t = ckpt[key] if skew == 0 else ckpt[(ts, key)]
    return t[:, 0].double()


def case_stats(root, noise, offset, skew):
    ours_all = []
    gaps_all = []

    if skew == 0:
        opt = base_loss(root, "opt", noise, offset, skew)
        dec = base_loss(root, "dec", noise, offset, skew)
        for fs in FORECAST_SEEDS:
            ours = train_loss(root, "ours", noise, offset, fs, skew)
            ours_all.append(ours)
            gaps_all.append(ours / opt)
    else:
        # Official notebook aggregates OURS across forecast and test seeds.
        opt_pool = []
        dec_pool = []
        for ts in TEST_SEEDS:
            opt_t = base_loss(root, "opt", noise, offset, skew, ts)
            dec_t = base_loss(root, "dec", noise, offset, skew, ts)
            opt_pool.append(opt_t)
            dec_pool.append(dec_t)
            for fs in FORECAST_SEEDS:
                ours = train_loss(root, "ours", noise, offset, fs, skew, ts)
                ours_all.append(ours)
                gaps_all.append(ours / opt_t)
        opt = torch.cat(opt_pool)
        dec = torch.cat(dec_pool)

    ours_cat = torch.cat(ours_all)
    gap_cat = torch.cat(gaps_all)

    return {
        "mean_ours": float(ours_cat.mean()),
        "std_ours": float(ours_cat.std()),
        "mean_opt": float(opt.mean()),
        "mean_dec": float(dec.mean()),
        "mean_gap": float(gap_cat.mean()),
        "std_gap": float(gap_cat.std()),
        "max_gap": float(gap_cat.max()),
    }


def build_results(root):
    results = {}
    for noise in MAIN_NOISE:
        for offset in OFFSETS:
            for skew in TEST_SKEWS:
                results[(noise, offset, skew)] = case_stats(root, noise, offset, skew)
    return results


def fig1(results, out):
    # Official Fig. 1 logic: no distribution shift.
    xs_opt, ys_dec, ys_ours, es_ours = [], [], [], []
    for noise in MAIN_NOISE:
        for offset in OFFSETS:
            d = results[(noise, offset, 0)]
            if d["mean_opt"] > 0:
                xs_opt.append(d["mean_opt"])
                ys_dec.append(d["mean_dec"])
                ys_ours.append(d["mean_ours"])
                es_ours.append(d["std_ours"])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.scatter(xs_opt, ys_dec, marker="^", label="DEC")
    ax.errorbar(xs_opt, ys_ours, es_ours, fmt="o", label="OURS")
    identity = torch.logspace(3, 6, 101)
    ax.plot(identity, identity, linestyle="--", label="OPT")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Loss incurred by OPT per test case")
    ax.set_ylabel("Loss per test case")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "Experiment results 1_reproduced.png", dpi=300)
    plt.close(fig)


def fig2(results, out):
    xs, means, stds, maxs = [], [], [], []
    for noise in MAIN_NOISE:
        for offset in OFFSETS:
            d = results[(noise, offset, 0)]
            xs.append(d["mean_opt"])
            means.append(d["mean_gap"])
            stds.append(d["std_gap"])
            maxs.append(d["max_gap"])

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.errorbar(xs, means, stds, fmt="o", label="Mean ± SD")
    ax.scatter(xs, maxs, marker="x", label="Max")
    ax.set_xscale("log")
    ax.set_xlabel("Loss incurred by OPT per test case")
    ax.set_ylabel("Loss ratio between OURS and OPT")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "Experiment results 2_reproduced.png", dpi=300)
    plt.close(fig)


def fig3(results, out):
    fig, ax = plt.subplots(figsize=(5, 4))
    markers = {0: "o", 10: "s", 20: "^", 30: "D", 40: "x"}

    for skew in TEST_SKEWS:
        xs, decs, ours, errs = [], [], [], []
        for noise in MAIN_NOISE:
            for offset in OFFSETS:
                d = results[(noise, offset, skew)]
                if 1e4 < d["mean_opt"] < 2e4:
                    xs.append(d["mean_opt"])
                    decs.append(d["mean_dec"])
                    ours.append(d["mean_ours"])
                    errs.append(d["std_ours"])
        if xs:
            ax.scatter(xs, decs, marker=markers[skew], label=f"DEC shift={skew}%")
            ax.errorbar(xs, ours, errs, fmt=markers[skew], label=f"OURS shift={skew}%")

    identity = torch.linspace(1e4, 2e4, 101)
    ax.plot(identity, identity, linestyle="--", label="OPT")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Loss incurred by OPT per test case")
    ax.set_ylabel("Loss per test case")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "Experiment results 3_reproduced.png", dpi=300)
    plt.close(fig)


def proxy_ratio_data(root, skew):
    vals = []
    if skew == 0:
        for noise in MAIN_NOISE:
            for offset in OFFSETS:
                for fs in FORECAST_SEEDS:
                    ours = train_loss(root, "ours", noise, offset, fs, 0)
                    proxy = train_loss(root, "proxy", noise, offset, fs, 0)
                    vals.append(float(torch.mean(proxy / ours)))
    else:
        for noise in MAIN_NOISE:
            for offset in OFFSETS:
                for fs in FORECAST_SEEDS:
                    for ts in TEST_SEEDS:
                        ours = train_loss(root, "ours", noise, offset, fs, skew, ts)
                        proxy = train_loss(root, "proxy", noise, offset, fs, skew, ts)
                        vals.append(float(torch.mean(proxy / ours)))
    return vals


def fig4(root, out):
    fig, axes = plt.subplots(2, 3, figsize=(8, 6))
    bins = [0.8 + 0.02 * i for i in range(26)]

    for i, skew in enumerate(TEST_SKEWS):
        ax = axes[i // 3][i % 3]
        vals = proxy_ratio_data(root, skew)
        pct = 100.0 * sum(v > 1.05 for v in vals) / len(vals)
        ax.hist(vals, bins=bins)
        ax.axvline(1.05, linestyle="--")
        ax.set_title(f"shift={skew}%")
        ax.set_yscale("log")
        ax.set_xlabel("PROXY / OURS")
        ax.text(1.06, max(1.0, ax.get_ylim()[1] / 4), f"{pct:.1f}% > 1.05")

    axes[1][2].set_visible(False)
    fig.tight_layout()
    fig.savefig(out / "Experiment results 4_reproduced.png", dpi=300)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    root = args.upstream.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    results = build_results(root)
    fig1(results, out)
    fig2(results, out)
    fig3(results, out)
    fig4(root, out)

    print(f"Wrote reproduced figures to: {out}")


if __name__ == "__main__":
    main()
