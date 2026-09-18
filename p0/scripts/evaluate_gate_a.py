#!/usr/bin/env python3
"""Convert the smoke validation JSON into a conservative Gate-A decision."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    report = json.loads(args.report.read_text(encoding="utf-8"))
    hard_failures = []
    warnings = []

    if report.get("stage") != "smoke":
        hard_failures.append("report stage is not 'smoke'")

    if report.get("missing_count", 0) != 0:
        hard_failures.append(f"missing checkpoints/files: {report['missing_count']}")

    if report.get("error_count", 0) != 0:
        hard_failures.append(f"checkpoint/schema/numerical errors: {report['error_count']}")

    metrics = report.get("metrics", {}).get("20")
    if not metrics:
        hard_failures.append("canonical test_skew=20 metrics are missing")
    else:
        ours = metrics["ours_over_opt"]
        dec = metrics["dec_over_opt"]
        proxy = metrics["proxy_over_ours_case_mean"]

        # OPT is the perfect-information reference, so ratios below 1 by a
        # substantial amount are suspicious. We keep this as a warning because
        # Smoke contains only one forecast seed / one operating point.
        if ours["mean"] < 0.98:
            warnings.append(
                f"OURS/OPT mean={ours['mean']:.4f} is unexpectedly below 1; "
                "check objective alignment and solver tolerances."
            )

        if dec["mean"] <= ours["mean"]:
            warnings.append(
                f"DEC/OPT mean={dec['mean']:.4f} is not above OURS/OPT "
                f"mean={ours['mean']:.4f} in the smoke case. "
                "Do not reject reproduction from one case; verify Main-Figure sweep."
            )

        if proxy["mean"] <= 0:
            hard_failures.append("PROXY/OURS ratio is non-positive")

    if hard_failures:
        status = "FAIL"
    elif warnings:
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    decision = {
        "gate": "P0-A",
        "status": status,
        "hard_failures": hard_failures,
        "warnings": warnings,
        "next_step": (
            "Fix hard failures and rerun Smoke."
            if status == "FAIL"
            else "Proceed to P0-B Main-Figure sweep; warnings must be revisited there."
            if warnings
            else "Proceed to P0-B Main-Figure sweep."
        ),
    }

    text_out = json.dumps(decision, indent=2, ensure_ascii=False)
    print(text_out)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text_out, encoding="utf-8")

    if status == "FAIL":
        raise SystemExit(2)

if __name__ == "__main__":
    main()
