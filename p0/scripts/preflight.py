#!/usr/bin/env python3
"""P0 静态/环境预检：不修改官方代码。"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

REQUIRED_FILES = [
    "grid_pkg.py",
    "controller_pkg.py",
    "controller_utils.py",
    "dQPTH.py",
    "evals.py",
    "requirements.txt",
    "data/case118_bus_data.pt",
    "data/case118_gen_data.pt",
    "data/case118_line_data.pt",
    "data/case118_ptdf_data.pt",
    "data/tauxDeChargeMTJLMA2juillet2018.txt",
    "data/scenario_generation/generate_data.ipynb",
    "experiments/run_opt.py",
    "experiments/run_dec.py",
    "experiments/run_proxy.py",
    "experiments/run_ours.py",
    "results/generate_figures.ipynb",
]

MODULES = [
    "numpy",
    "scipy",
    "pandas",
    "torch",
    "cvxpy",
    "qpsolvers",
    "gurobipy",
    "mosek",
    "qdldl",
    "qpth",
    "tqdm",
]

def check_import(name: str):
    try:
        mod = importlib.import_module(name)
        return {"ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    args = parser.parse_args()
    upstream = args.upstream.resolve()

    report = {
        "python": sys.version,
        "platform": sys.platform,
        "upstream": str(upstream),
        "files": {},
        "imports": {},
        "solver_notes": [],
    }

    for rel in REQUIRED_FILES:
        p = upstream / rel
        report["files"][rel] = {"exists": p.exists(), "size": p.stat().st_size if p.exists() else None}

    for mod in MODULES:
        report["imports"][mod] = check_import(mod)

    try:
        import gurobipy as gp
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        report["gurobi_license"] = {"ok": True}
        env.dispose()
    except Exception as exc:
        report["gurobi_license"] = {"ok": False, "error": repr(exc)}
        report["solver_notes"].append(
            "官方 dQPTH 设置使用 Gurobi。若许可证不可用，不能宣称已完成严格 P0 数值复现。"
        )

    missing_files = [k for k, v in report["files"].items() if not v["exists"]]
    failed_imports = [k for k, v in report["imports"].items() if not v["ok"]]

    print(json.dumps(report, indent=2, ensure_ascii=False))
    if missing_files or failed_imports:
        print("\nPRECHECK FAILED")
        if missing_files:
            print("Missing files:", missing_files)
        if failed_imports:
            print("Failed imports:", failed_imports)
        return 2

    print("\nPRECHECK PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
