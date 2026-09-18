#!/usr/bin/env python3
"""检查官方 scenario generator 的输出结构。"""

from __future__ import annotations
import argparse
from pathlib import Path
import torch

NOISE_MAG = 4.0
OFFSET = 180
RADIUS = 0.2

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    root = args.upstream.resolve()
    data = root / "data" / "scenario_generation"

    forecast_path = data / f"forecast_trajs_rad{RADIUS}.pt"
    nom_path = data / f"test_trajs_no_mismatch_rad{RADIUS}.pt"
    mismatch_dir = data / f"test_trajs_with_mismatch_rad{RADIUS}"

    required = [
        forecast_path,
        nom_path,
        mismatch_dir / f"test_trajs_with_mismatch_noise_mag{NOISE_MAG}_offset{OFFSET}_tsm10.pt",
        mismatch_dir / f"test_trajs_with_mismatch_noise_mag{NOISE_MAG}_offset{OFFSET}_tsm20.pt",
        mismatch_dir / f"test_trajs_with_mismatch_noise_mag{NOISE_MAG}_offset{OFFSET}_tsm30.pt",
        mismatch_dir / f"test_trajs_with_mismatch_noise_mag{NOISE_MAG}_offset{OFFSET}_tsm40.pt",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing generated files:\n" + "\n".join(missing))

    forecast = torch.load(forecast_path, weights_only=False)
    nominal = torch.load(nom_path, weights_only=False)

    assert forecast["num_forecast_traj"] == 10
    assert forecast["num_forecast_seeds"] == 5
    assert abs(float(forecast["forecast_radius"]) - RADIUS) < 1e-12
    assert forecast[(NOISE_MAG, OFFSET, 0)].shape[0] == 10
    assert nominal["num_test_traj"] == 10
    assert nominal[(NOISE_MAG, OFFSET)].shape[0] == 10

    for tsm in (10, 20, 30, 40):
        p = mismatch_dir / f"test_trajs_with_mismatch_noise_mag{NOISE_MAG}_offset{OFFSET}_tsm{tsm}.pt"
        obj = torch.load(p, weights_only=False)
        assert obj["num_test_traj"] == 10
        assert obj["num_test_seeds"] == 3
        for seed in (0, 1, 2):
            assert obj[(NOISE_MAG, OFFSET, tsm, seed)].shape[0] == 10

    print("Scenario-data structure check PASSED.")
    print(f"Canonical key: noise_mag={NOISE_MAG}, offset={OFFSET}, radius={RADIUS}")

if __name__ == "__main__":
    main()
