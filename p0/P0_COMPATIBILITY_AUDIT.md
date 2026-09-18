# P0 Compatibility and Reproduction Audit

This document freezes the exact reproduction target for the MIT/RTE e-Energy 2026 baseline before any new research modification.

## 1. Official experiment grid recovered from `results/generate_figures.ipynb`

### OURS / PROXY

- forecast seeds: 0, 1, 2, 3, 4
- noise magnitudes: 2.0, 2.4, 2.45, 2.5, 3.0, 3.5, 4.0
- offsets: 0, 60, 120, 180
- epochs: 120
- radius: 0.2
- lr: 1e-3
- optimizer: clipped_gd
- lr schedule: plateau
- lr decay step: 20
- patience: 5
- batch size: 2
- max grad norm: 3e4

Number of process-level runs per method:

```
5 forecast seeds x 7 noise magnitudes x 4 offsets = 140
```

Each trained checkpoint is evaluated internally on:
- test skew 0;
- test skew 10, 20, 30, 40;
- test seeds 0, 1, 2 for non-zero skew;
- 10 test trajectories per case.

### OPT / DEC

- noise magnitudes: 2.0, 2.4, 2.45, 2.5, 3.0, 3.5, 4.0
- offsets: 0, 60, 120, 180
- test skew: 0, 10, 20, 30, 40
- radius: 0.2

Number of process-level runs per method:

```
7 noise magnitudes x 4 offsets x 5 test skews = 140
```

Therefore the complete notebook dataset corresponds to **560 process-level experiment runs** across OPT / DEC / PROXY / OURS.

## 2. Main-figure subset

The plotting cells for the main loss-vs-OPT figures use:

```
noise_mag in {2.0, 2.5, 3.0, 3.5, 4.0}
offset in {0, 60, 120, 180}
test_skew in {0, 10, 20, 30, 40}
```

The 2.4 and 2.45 noise cases are loaded by the notebook but are not required for the main plots.

This motivates three P0 gates:

### Gate A — Smoke
One canonical configuration:
- noise_mag=4.0
- offset=180
- radius=0.2
- forecast_seed=0
- test_skew_mag=20

Goal: verify solver, data, code path, checkpoint schema, and all four methods.

### Gate B — Main-Figure Reproduction
Run the five noise magnitudes used by the main plotting cells and all four offsets.

Goal: reproduce the qualitative and quantitative trends of the four official result figures without first paying for the two extra noise slices.

### Gate C — Full Notebook Reproduction
Run the entire 560-run grid.

Goal: make the official `generate_figures.ipynb` data layer complete.

## 3. Official checkpoint metric semantics

The plotting notebook reads `total_losses[..., 0]`.

For the closed-loop evaluation functions:

```
total_losses = [total_loss, economic_loss, violation_loss]
```

where total loss contains:
- battery charge-deviation cost;
- curtailment action / net-curtailment cost;
- line-limit violation penalty.

The notebook therefore treats **total loss** as the primary comparison quantity.

Primary P0 ratios:

```
OURS / OPT
PROXY / OURS
DEC / OPT   (derived for diagnostic comparison)
```

## 4. Compatibility defects in the pinned upstream repository

These are reproduction-engineering defects, not algorithmic modifications.

### A. Sweep CLI mismatch

`make_sweep_slurm.py` currently generates `--torch_seed` and `--job_id`, while the current experiment parsers do not accept those arguments.

For OURS / PROXY, the current run scripts instead expose `--forecast_seed`.

**P0 policy:** do not use the upstream sweep generator directly. Generate a clean manifest from this repository.

### B. Result filename mismatch

The experiment scripts save:

```
results/<method>/checkpoint_<tag>.pt
```

but `generate_figures.ipynb` searches for:

```
ours_<tag>.pt
proxy_<tag>.pt
opt_<tag>.pt
dec_<tag>.pt
```

For OPT/DEC at zero skew, the notebook additionally omits the `test_skew_mag0` field from the expected name.

**P0 policy:** keep raw checkpoints untouched and generate notebook-compatible copies/symlinks using `normalize_result_names.py`.

### C. Zero-skew execution defects

`run_opt.py` and `run_dec.py` reference `all_test_trajs` before assignment for `test_skew_mag == 0`.

Their final checkpoint save is also commented out.

**P0 policy:** use the explicitly documented minimal patch.

### D. Exception-recording defects

`run_ours.py` and `run_proxy.py` use an undefined variable `i` in an exception-recording path.

**P0 policy:** use the explicitly documented minimal patch.

## 5. Important modeling note for later P1 work

The top-level experiment scripts and the training functions in `evals.py` do not express the 3-area partition identically. This may be intentional because the training controller construction includes boundary buses needed for coupled constraints.

P0 must reproduce this behavior exactly.

Do **not** "clean up" or unify these partitions in P0.

Before P1, we will separately derive the semantic meaning of:
- owned buses;
- boundary buses;
- shared / neighboring line constraints;
- local information exposed to each controller.

## 6. P0 acceptance hierarchy

### Gate A passes if

- all required dependencies import;
- Gurobi is licensed and callable;
- official scenario files are generated and validated;
- all four methods complete one canonical configuration;
- checkpoints contain finite values;
- `total_losses` has expected dimensions;
- no unexplained solver failure remains.

### Gate B passes if

- main-figure parameter subset is complete;
- OURS is substantially below DEC in the difficult cases, matching the official qualitative claim;
- OURS remains close to OPT in the same qualitative regimes shown by the official figures;
- increasing distribution shift produces the same direction of robustness degradation as the official plots;
- PROXY/OURS loss-ratio distribution has the same qualitative shape as the official result figure;
- no systematic anomaly is hidden by failed trajectories.

### Gate C passes if

- all notebook-required combinations exist;
- the official figure notebook can be executed end-to-end after result-name normalization;
- no missing combination is reported;
- the four regenerated figures are qualitatively consistent with the committed official figures;
- numerical differences are documented together with solver/hardware versions.

## 7. What P0 does not prove

P0 only establishes a trustworthy baseline.

It does not yet validate:
- MARL;
- collision definitions;
- safety contracts for learned policies;
- graph communication;
- QP projection;
- hierarchical-safety theorems.

Those are P1+ research modifications.
