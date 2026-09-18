# P0 staged execution plan

## P0-A — Smoke

Purpose: prove the pinned code/data/solver/checkpoint path is operational.

Canonical point:
- noise_mag = 4.0
- offset = 180
- radius = 0.2
- forecast_seed = 0
- test_skew_mag = 20

Methods:
- OPT
- DEC
- PROXY
- OURS

Exit:
- hard Gate-A status is not FAIL.

## P0-B — Main-Figure subset

Purpose: reproduce the parameter region actually used by the official main plotting cells.

Noise:
- 2.0
- 2.5
- 3.0
- 3.5
- 4.0

Offsets:
- 0
- 60
- 120
- 180

Forecast seeds:
- 0..4

Test skew:
- 0, 10, 20, 30, 40

Total process-level runs: 400.

Recommended execution:

1. Generate:
   `python p0/scripts/generate_manifest.py --stage main --out p0/results/p0_main_manifest.csv`
2. Generate SLURM wrapper if needed.
3. Run all tasks.
4. Normalize filenames.
5. Build a rerun manifest for missing outputs.
6. Rerun until complete.
7. Validate with `validate_results.py --stage main`.
8. Regenerate official figures.

## P0-C — Full notebook dataset

Adds noise_mag = 2.4 and 2.45.

Total process-level runs: 560.

P0-C exists to make the official notebook data grid complete. It is not required before we can begin mathematical analysis of P1, but it should be finished before claiming a full reproduction package.

## Freeze rule

The branch `p0/mit-rte-reproduction` is frozen after P0-C.

All new research code starts from a new branch. Never introduce MARL, collision, or a new QP shield into P0.
