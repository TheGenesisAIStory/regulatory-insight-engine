#!/usr/bin/env python3
"""Build a backend/eval-compatible dataset from the Fiorell.IA supervised seed.

The supervised seed remains training-oriented and chat-style. This script creates
a lightweight benchmark view with the schema expected by run_benchmark.py:
id, category, query, expected_sources, expected_no_answer, reference_answer.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "training" / "data" / "fiorellia_supervised_seed_v1.jsonl"
DEFAULT_OUTPUT = Path(__file__).with_name("fiorellia_supervised_seed_eval.jsonl")

NO_ANSWER_TYPES = {"insufficient_context", "out_of_scope", "refusal_safe"}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc
    return rows


def message_content(row: dict[str, Any], role: str) -> str:
    for message in row.get("messages", []):
        if message.get("role") == role:
            return str(message.get("content", "")).strip()
    raise ValueError(f"{row.get('id', '<missing-id>')} has no {role!r} message")


def convert(row: dict[str, Any]) -> dict[str, Any]:
    example_type = str(row.get("type", "")).strip()
    if not example_type:
        raise ValueError(f"{row.get('id', '<missing-id>')} has no type")

    return {
        "id": row.get("id"),
        "category": f"fiorellia_{example_type}",
        "query": message_content(row, "user"),
        "expected_sources": [],
        "expected_no_answer": example_type in NO_ANSWER_TYPES,
        "reference_answer": message_content(row, "assistant"),
        "source_dataset": "training/data/fiorellia_supervised_seed_v1.jsonl",
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Fiorell.IA seed eval dataset for backend/eval.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = [convert(row) for row in load_jsonl(args.input)]
    write_jsonl(args.output, rows)

    counts: dict[str, int] = {}
    no_answer_counts: dict[bool, int] = {True: 0, False: 0}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
        no_answer_counts[bool(row["expected_no_answer"])] += 1

    print(f"input={args.input}")
    print(f"output={args.output}")
    print(f"records={len(rows)}")
    print(f"expected_no_answer_true={no_answer_counts[True]}")
    print(f"expected_no_answer_false={no_answer_counts[False]}")
    for category, count in sorted(counts.items()):
        print(f"{category}={count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
