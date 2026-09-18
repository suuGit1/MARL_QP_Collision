#!/usr/bin/env python3
"""Execute P0 manifest tasks with auditable logs.

Supports local sequential execution and one-task execution for SLURM arrays.
"""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


PINNED_COMMIT = "e40ac9095291af4c1f6ee46915ce9e5dbd242f17"


def check_upstream(root: Path):
    try:
        actual = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except Exception as exc:
        raise RuntimeError(f"cannot read upstream git revision: {exc}")

    if actual != PINNED_COMMIT:
        raise RuntimeError(
            f"upstream commit mismatch: expected {PINNED_COMMIT}, got {actual}"
        )


def read_manifest(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_task(root: Path, row: dict, logs: Path) -> int:
    task_id = row["task_id"]
    method = row["method"]
    command = row["command"]
    log_path = logs / f"task_{int(task_id):04d}_{method}.log"

    print(f"[task {task_id}] {command}")
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"task_id={task_id}\n")
        log.write(f"method={method}\n")
        log.write(f"command={command}\n\n")
        log.flush()

        proc = subprocess.run(
            command,
            cwd=root,
            shell=True,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )

        log.write(f"\nexit_code={proc.returncode}\n")

    print(f"[task {task_id}] exit={proc.returncode}, log={log_path}")
    return proc.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--task-id", type=int)
    group.add_argument("--all", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()

    root = args.upstream.resolve()
    manifest = args.manifest.resolve()
    check_upstream(root)

    rows = read_manifest(manifest)
    logs = root / "p0_logs" / manifest.stem
    logs.mkdir(parents=True, exist_ok=True)

    if args.task_id is not None:
        selected = [r for r in rows if int(r["task_id"]) == args.task_id]
        if not selected:
            raise SystemExit(f"task id {args.task_id} not found")
    else:
        selected = rows

    failures = []
    for row in selected:
        code = run_task(root, row, logs)
        if code != 0:
            failures.append((row["task_id"], row["method"], code))
            if not args.continue_on_error:
                break

    if failures:
        print("Failures:", failures)
        raise SystemExit(2)

    print(f"Completed {len(selected)} task(s).")


if __name__ == "__main__":
    main()
