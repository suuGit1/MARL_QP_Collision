#!/usr/bin/env python3
"""只修复已确认的上游执行缺陷，不改变任何算法、模型、参数或实验设定。"""

from __future__ import annotations
import argparse
from pathlib import Path

PATCHES = {
    "experiments/run_opt.py": [
        (
            'if test_skew_mag == 0:\n        num_test_traj = test_trajs_no_mismatch["num_test_traj"]\n        optimal_losses = torch.zeros(num_test_traj, 3)',
            'if test_skew_mag == 0:\n        num_test_traj = test_trajs_no_mismatch["num_test_traj"]\n        all_test_trajs = test_trajs_no_mismatch[(noise_mag, offset)]\n        optimal_losses = torch.zeros(num_test_traj, 3)',
            "定义 zero-skew 分支的 all_test_trajs",
        ),
        (
            '    # torch.save(ckpt, f"{folder}checkpoint_{tag}.pt")',
            '    torch.save(ckpt, f"{folder}checkpoint_{tag}.pt")',
            "恢复 OPT checkpoint 保存",
        ),
    ],
    "experiments/run_dec.py": [
        (
            'if test_skew_mag == 0:\n        num_test_traj = test_trajs_no_mismatch["num_test_traj"]\n        base_losses = torch.zeros(num_test_traj, 3)',
            'if test_skew_mag == 0:\n        num_test_traj = test_trajs_no_mismatch["num_test_traj"]\n        all_test_trajs = test_trajs_no_mismatch[(noise_mag, offset)]\n        base_losses = torch.zeros(num_test_traj, 3)',
            "定义 zero-skew 分支的 all_test_trajs",
        ),
        (
            '    # torch.save(ckpt, f"{folder}checkpoint_{tag}.pt")',
            '    torch.save(ckpt, f"{folder}checkpoint_{tag}.pt")',
            "恢复 DEC checkpoint 保存",
        ),
    ],
    "experiments/run_ours.py": [
        (
            'failed_tests[(i,j)] = test_traj',
            'failed_tests[(test_seed, test_skew_mag, j)] = test_traj',
            "修复异常记录中的未定义变量 i",
        ),
    ],
    "experiments/run_proxy.py": [
        (
            'failed_tests[(i,j)] = test_traj',
            'failed_tests[(test_seed, test_skew_mag, j)] = test_traj',
            "修复异常记录中的未定义变量 i",
        ),
    ],
}

def patch_file(path: Path, replacements):
    text = path.read_text(encoding="utf-8")
    original = text
    applied = []
    for old, new, desc in replacements:
        if new in text:
            applied.append((desc, "already_applied"))
            continue
        count = text.count(old)
        if count != 1:
            raise RuntimeError(
                f"{path}: patch '{desc}' expected exactly one match, found {count}. "
                "Refusing to modify an unexpected upstream revision."
            )
        text = text.replace(old, new, 1)
        applied.append((desc, "applied"))
    if text != original:
        path.write_text(text, encoding="utf-8")
    return applied

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream.resolve()

    print("Applying P0 minimal execution patches only.")
    for rel, replacements in PATCHES.items():
        path = upstream / rel
        if not path.exists():
            raise FileNotFoundError(path)
        for desc, status in patch_file(path, replacements):
            print(f"[{status}] {rel}: {desc}")

    print("\nPatch complete.")
    print("IMPORTANT: label all outputs from this tree as 'patched-reproduction'.")

if __name__ == "__main__":
    main()
