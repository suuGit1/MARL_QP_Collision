#!/usr/bin/env python3
"""Capture exact P0 software/upstream provenance without modifying experiments."""

from __future__ import annotations

import argparse
import importlib
import json
import platform
import subprocess
import sys
from pathlib import Path

MODULES = [
    "numpy", "scipy", "pandas", "torch", "cvxpy",
    "qpsolvers", "gurobipy", "mosek", "qdldl", "qpth", "tqdm",
]

def run(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception as exc:
        return f"<failed: {exc}>"

def module_version(name):
    try:
        mod = importlib.import_module(name)
        return {
            "ok": True,
            "version": getattr(mod, "__version__", None),
        }
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    upstream = args.upstream.resolve()
    report = {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "modules": {m: module_version(m) for m in MODULES},
        "upstream": {
            "path": str(upstream),
            "head": run(["git", "-C", str(upstream), "rev-parse", "HEAD"]),
            "status_porcelain": run(["git", "-C", str(upstream), "status", "--porcelain"]),
            "diff": run(["git", "-C", str(upstream), "diff", "--",
                         "experiments/run_opt.py",
                         "experiments/run_dec.py",
                         "experiments/run_proxy.py",
                         "experiments/run_ours.py"]),
        },
        "pip_freeze": run([sys.executable, "-m", "pip", "freeze"]),
    }

    try:
        import gurobipy as gp
        report["gurobi"] = {
            "version": ".".join(map(str, gp.gurobi.version())),
        }
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.start()
        report["gurobi"]["license_ok"] = True
        env.dispose()
    except Exception as exc:
        report["gurobi"] = {
            "license_ok": False,
            "error": repr(exc),
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
