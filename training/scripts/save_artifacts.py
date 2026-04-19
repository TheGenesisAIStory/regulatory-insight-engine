#!/usr/bin/env python3
"""Save artifacts and basic metrics from training data preparation.

Copies datasets and writes a small `metrics.json` describing counts per example_type and category.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if s:
                yield json.loads(s)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Save dataset artifacts and metrics")
    parser.add_argument("--input", required=True, help="Input data folder or JSONL file")
    parser.add_argument("--output", required=True, help="Output folder for artifacts")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

    jsonl_files = []
    if input_path.is_dir():
        jsonl_files = list(input_path.glob("*.jsonl"))
    elif input_path.is_file():
        jsonl_files = [input_path]
    else:
        print(f"Input not found: {input_path}")
        return 2

    stats: Dict[str, int] = {}
    type_counter = Counter()
    cat_counter = Counter()

    total = 0
    for f in jsonl_files:
        for rec in load_jsonl(f):
            total += 1
            type_counter[rec.get("example_type", "unknown")] += 1
            cat_counter[rec.get("category", "unknown")] += 1

    stats["total_records"] = total
    stats["per_example_type"] = dict(type_counter)
    stats["per_category"] = dict(cat_counter)

    # copy source files for traceability
    copied = []
    for f in jsonl_files:
        dst = out_dir / f.name
        shutil.copy2(f, dst)
        copied.append(str(dst))

    metrics_path = out_dir / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as fh:
        json.dump({"stats": stats, "copied": copied}, fh, ensure_ascii=False, indent=2)

    print(f"Saved artifacts to {out_dir} (metrics: {metrics_path})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
