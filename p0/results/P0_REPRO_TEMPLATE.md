# P0 Reproduction Record

## 1. Provenance

- Upstream repository:
- Upstream commit:
- Reproduction label: `official-unmodified` / `patched-reproduction`
- Local commit:
- Date:
- Host OS:
- CPU:
- GPU:
- Python:
- PyTorch:
- Gurobi:
- Gurobi license type:
- MOSEK:
- qpth:
- qdldl:

## 2. Frozen configuration

- Grid: IEEE118
- Areas: 3
- T: 20
- H: 5
- delta_t: 15
- noise_mag: 4.0
- offset: 180
- radius: 0.2
- forecast_seed:
- test_skew_mag:
- test_seed:
- NUMPY_SEED: 0
- TORCH_SEED: 0

## 3. Data verification

- [ ] case118_bus_data.pt
- [ ] case118_gen_data.pt
- [ ] case118_line_data.pt
- [ ] case118_ptdf_data.pt
- [ ] RTE source trajectory text file
- [ ] forecast_trajs_rad0.2.pt
- [ ] test_trajs_no_mismatch_rad0.2.pt
- [ ] mismatch tsm10
- [ ] mismatch tsm20
- [ ] mismatch tsm30
- [ ] mismatch tsm40
- [ ] `check_generated_data.py` passed

## 4. Method status

| Method | Completed | Runtime | Checkpoint | NaN/Inf | Notes |
|---|---:|---:|---|---:|---|
| OPT |  |  |  |  |  |
| DEC |  |  |  |  |  |
| PROXY |  |  |  |  |  |
| OURS |  |  |  |  |  |

## 5. Raw metrics

### OPT
- total:
- operational:
- violation/slack:

### DEC
- total:
- operational:
- violation/slack:

### PROXY
- total:
- operational:
- violation/slack:

### OURS
- total:
- operational:
- violation/slack:

## 6. Distribution-shift sweep

| test skew | OPT | DEC | PROXY | OURS |
|---:|---:|---:|---:|---:|
| 0 |  |  |  |  |
| 10 |  |  |  |  |
| 20 |  |  |  |  |
| 30 |  |  |  |  |
| 40 |  |  |  |  |

## 7. Reproduction conclusion

- [ ] Method ranking is consistent with the official paper/figure notebook.
- [ ] Metric scale is consistent.
- [ ] No unexplained failed trajectory remains.
- [ ] Any patch is listed below.
- [ ] P0 is ready to freeze before P1.

## 8. Deviations / patches

Record every deviation from the pinned upstream commit, including solver-version differences.

## 9. P0 freeze decision

Status: `NOT READY` / `REPRODUCED`

Reason:
