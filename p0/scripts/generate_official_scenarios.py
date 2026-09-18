#!/usr/bin/env python3
"""Deterministic CLI transcription of the official generate_data.ipynb.

No modeling change is introduced. Outputs are written into the pinned upstream
repository's data/scenario_generation directory.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import torch


NUMPY_SEED = 0
TORCH_SEED = 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()

    root = args.upstream.resolve()
    sys.path.insert(0, str(root))

    import grid_pkg
    import controller_utils

    torch.set_default_dtype(torch.double)
    torch.set_printoptions(threshold=10000)
    np.random.seed(NUMPY_SEED)
    torch.manual_seed(TORCH_SEED)

    data_dir = root / "data"
    out_dir = data_dir / "scenario_generation"
    out_dir.mkdir(parents=True, exist_ok=True)

    line_data_loc = data_dir / "case118_line_data.pt"
    bus_data_loc = data_dir / "case118_bus_data.pt"
    gen_data_loc = data_dir / "case118_gen_data.pt"
    ptdf_data_loc = data_dir / "case118_ptdf_data.pt"

    bus_with_curt = torch.load(gen_data_loc, weights_only=True)[:, 0].int()
    bus_with_batt = torch.tensor([10 * i + 2 for i in range(12)], dtype=torch.int)
    delta_t = 15

    grid = grid_pkg.Grid(
        bus_with_curt,
        bus_with_batt,
        delta_t,
        str(line_data_loc),
        str(bus_data_loc),
        str(gen_data_loc),
        str(ptdf_data_loc),
    )

    T = 20
    H = 5
    bus_idx_gap = 10
    rte_file = data_dir / "tauxDeChargeMTJLMA2juillet2018.txt"

    noise_mags = [2.0, 2.4, 2.45, 2.5, 3.0, 3.5, 4.0]
    offset_vals = [30 * i for i in range(10)]

    # Cell: forecast_skews
    forecast_skews = {}
    for noise_mag in noise_mags:
        for offset in offset_vals:
            forecast_skews[(noise_mag, offset)] = controller_utils.get_RTE_noise_values(
                str(rte_file),
                grid,
                T,
                H,
                noise_mag,
                bus_idx_gap,
                offset=offset,
            )
    forecast_skews["noise_mags"] = noise_mags
    forecast_skews["offset_vals"] = offset_vals
    torch.save(forecast_skews, out_dir / "forecast_skews.pt")

    # Cell: forecast trajectories
    num_forecast_traj = 10
    num_forecast_seeds = 5
    forecast_seeds = list(range(num_forecast_seeds))
    forecast_radius = 0.2
    forecast_trajs = {}

    for noise_mag in noise_mags:
        for offset in offset_vals:
            forecast_skew = forecast_skews[(noise_mag, offset)]
            for forecast_seed in forecast_seeds:
                torch.manual_seed(forecast_seed)
                all_forecast_traj = torch.zeros(
                    num_forecast_traj, T + H, grid.num_buses
                )
                for i in range(num_forecast_traj):
                    dist_error = (
                        torch.rand_like(forecast_skew) * forecast_radius * 2
                        + (1 - forecast_radius)
                    )
                    all_forecast_traj[i] = dist_error * forecast_skew
                forecast_trajs[(noise_mag, offset, forecast_seed)] = all_forecast_traj
            forecast_trajs[(noise_mag, offset)] = forecast_skew

    forecast_trajs["num_forecast_traj"] = num_forecast_traj
    forecast_trajs["num_forecast_seeds"] = num_forecast_seeds
    forecast_trajs["forecast_radius"] = forecast_radius
    torch.save(
        forecast_trajs,
        out_dir / f"forecast_trajs_rad{forecast_radius}.pt",
    )

    # Cell: no-mismatch test trajectories.
    # IMPORTANT: we intentionally do not reset torch's RNG here because the
    # official notebook also continues from the preceding cell's RNG state.
    num_test_traj = 10
    test_radius = 0.2
    test_trajs_no_mismatch = {}

    for noise_mag in noise_mags:
        for offset in offset_vals:
            forecast_skew = forecast_skews[(noise_mag, offset)]
            all_test_traj = torch.zeros(num_test_traj, T + H, grid.num_buses)
            for i in range(num_test_traj):
                dist_error = (
                    torch.rand_like(forecast_skew) * test_radius * 2
                    + (1 - test_radius)
                )
                all_test_traj[i] = dist_error * forecast_skew
            test_trajs_no_mismatch[(noise_mag, offset)] = all_test_traj

    test_trajs_no_mismatch["num_test_traj"] = num_test_traj
    test_trajs_no_mismatch["test_radius"] = test_radius
    torch.save(
        test_trajs_no_mismatch,
        out_dir / f"test_trajs_no_mismatch_rad{test_radius}.pt",
    )

    # Cell: mismatch test trajectories
    test_skew_mags = [10, 20, 30, 40]
    num_test_seeds = 3
    test_seeds = list(range(num_test_seeds))
    mismatch_dir = out_dir / f"test_trajs_with_mismatch_rad{test_radius}"
    mismatch_dir.mkdir(parents=True, exist_ok=True)

    for noise_mag in noise_mags:
        for offset in offset_vals:
            forecast_skew = forecast_skews[(noise_mag, offset)]
            for test_skew_mag in test_skew_mags:
                test_trajs_with_mismatch = {}

                for test_seed in test_seeds:
                    torch.manual_seed(test_seed)
                    dist_error = (
                        torch.rand_like(forecast_skew)
                        * (test_skew_mag / 100)
                        * 2
                        + (1 - test_skew_mag / 100)
                    )
                    test_skew = forecast_skew * dist_error

                    all_test_traj = torch.zeros(
                        num_test_traj, T + H, grid.num_buses
                    )
                    for i in range(num_test_traj):
                        dist_error = (
                            torch.rand_like(test_skew) * test_radius * 2
                            + (1 - test_radius)
                        )
                        all_test_traj[i] = dist_error * test_skew

                    test_trajs_with_mismatch[
                        (noise_mag, offset, test_skew_mag, test_seed)
                    ] = all_test_traj

                test_trajs_with_mismatch["num_test_traj"] = num_test_traj
                test_trajs_with_mismatch["test_radius"] = test_radius
                test_trajs_with_mismatch["test_skew_mags"] = test_skew_mags
                test_trajs_with_mismatch["num_test_seeds"] = num_test_seeds

                torch.save(
                    test_trajs_with_mismatch,
                    mismatch_dir
                    / (
                        "test_trajs_with_mismatch_"
                        f"noise_mag{noise_mag}_offset{offset}_"
                        f"tsm{test_skew_mag}.pt"
                    ),
                )

    print("Official scenario generation transcription completed.")
    print(f"Output directory: {out_dir}")


if __name__ == "__main__":
    main()
