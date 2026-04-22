#!/usr/bin/env python3
from __future__ import annotations

import importlib
import platform
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MODULES = ["torch", "transformers", "peft", "datasets", "yaml"]
REQUIRED_FILES = [
    ROOT / "fiorellia" / "training" / "supervised_v1_curated_20260421.jsonl",
    ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260421.yaml",
    ROOT / "fiorellia" / "eval" / "prompt_harness_baseline_20260421.jsonl",
]


def check_module(name: str) -> tuple[bool, str]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return False, str(exc)
    version = getattr(module, "__version__", "version unknown")
    return True, str(version)


def main() -> int:
    failures: list[str] = []

    print("Fiorell.IA LoRA training preflight")
    print(f"python={platform.python_version()}")
    print(f"executable={sys.executable}")
    print(f"virtual_env={os.environ.get('VIRTUAL_ENV', '') or 'not active'}")
    print()

    if sys.version_info < (3, 10):
        failures.append("Python 3.10+ is required for this conservative training workflow.")
        print("FAIL python_version: Python 3.10+ required")
    else:
        print("PASS python_version")

    torch_module = None
    for module_name in REQUIRED_MODULES:
        ok, detail = check_module(module_name)
        if ok:
            print(f"PASS import {module_name}: {detail}")
            if module_name == "torch":
                torch_module = importlib.import_module("torch")
        else:
            failures.append(f"Missing import {module_name}: {detail}")
            print(f"FAIL import {module_name}: {detail}")

    if torch_module is not None:
        print(f"torch_version={torch_module.__version__}")
        print(f"torch_cuda_available={torch_module.cuda.is_available()}")

    print()
    for path in REQUIRED_FILES:
        if path.exists():
            print(f"PASS file exists: {path}")
        else:
            failures.append(f"Missing required file: {path}")
            print(f"FAIL file missing: {path}")

    print()
    if failures:
        print("SUMMARY: FAIL")
        for failure in failures:
            print(f"- {failure}")
        print()
        print("NEXT:")
        print("1. Create a dedicated Python 3.10+ training environment.")
        print("2. Install PyTorch with the official selector for this machine.")
        print("3. Run: pip install -r fiorellia/training/requirements-lora.txt")
        print("4. Rerun this preflight before training.")
        return 1

    print("SUMMARY: PASS")
    print("Training prerequisites are present. You can start the first LoRA run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
