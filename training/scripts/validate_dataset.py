#!/usr/bin/env python3
"""Lightweight wrapper to run the canonical validator under `backend/eval/`.

This keeps training prep decoupled while reusing the authoritative validator.
Run from repository root.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Wrapper to run backend/eval/validate_supervised_dataset.py")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL file")
    parser.add_argument("--output", "-o", help="Cleaned output JSONL (optional)")
    parser.add_argument("--strict", "-s", action="store_true", help="Drop invalid records")
    args = parser.parse_args(argv)

    script = Path("backend/eval/validate_supervised_dataset.py")
    if not script.exists():
        print(f"Validator not found at {script}. Run from repository root.")
        return 2

    cmd = [sys.executable, str(script), "--input", args.input]
    if args.output:
        cmd += ["--output", args.output]
    if args.strict:
        cmd += ["--strict"]

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
