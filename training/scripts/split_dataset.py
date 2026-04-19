#!/usr/bin/env python3
"""Split a supervised JSONL dataset into train/validation sets.

Simple, dependency-free script intended to be run from the repository root.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import List


def load_jsonl(path: Path) -> List[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path: Path, items: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for rec in items:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Split supervised JSONL into train/val")
    parser.add_argument("--config", default="training/config/config.json", help="Path to config JSON")
    parser.add_argument("--input", help="Override input dataset path")
    parser.add_argument("--train-out", default="training/data/train.jsonl")
    parser.add_argument("--val-out", default="training/data/val.jsonl")
    parser.add_argument("--ratio", type=float, help="Train ratio override (0-1)")
    parser.add_argument("--seed", type=int, help="Random seed override")
    parser.add_argument("--max-samples", type=int, help="Limit total samples (optional)")
    args = parser.parse_args(argv)

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"Config not found: {cfg_path}")
        return 2

    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    input_path = Path(args.input or cfg.get("dataset_path"))
    if not input_path.exists():
        print(f"Input dataset not found: {input_path}")
        return 2

    ratio = args.ratio if args.ratio is not None else cfg.get("train_val_split", 0.9)
    seed = args.seed if args.seed is not None else cfg.get("seed", 42)
    max_samples = args.max_samples if args.max_samples is not None else cfg.get("max_samples")

    records = load_jsonl(input_path)
    if max_samples:
        records = records[:max_samples]

    random.Random(seed).shuffle(records)

    split_idx = int(len(records) * ratio)
    train = records[:split_idx]
    val = records[split_idx:]

    write_jsonl(Path(args.train_out), train)
    write_jsonl(Path(args.val_out), val)

    print(f"Wrote {len(train)} train and {len(val)} val records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
