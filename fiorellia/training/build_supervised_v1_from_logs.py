#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


TARGET_CATEGORIES = {"unsupported_abstention", "out_of_scope_refusal"}
SYSTEM_PLACEHOLDER = (
    "Fiorell.IA behavior instruction placeholder: rispondi in italiano, "
    "solo se supportato da fonti locali recuperate; altrimenti astieniti "
    "o rifiuta in modo chiaro e non speculativo."
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if not isinstance(record, dict):
                raise ValueError(f"Invalid JSONL object at {path}:{line_no}")
            records.append(record)
    return records


def infer_lang(user_query: str) -> str:
    text = user_query.lower()
    english_markers = {
        "what",
        "which",
        "how",
        "explain",
        "overview",
        "compare",
        "ranking",
        "banks",
        "capital",
        "requirements",
    }
    italian_markers = {
        "quale",
        "quali",
        "come",
        "spiega",
        "panoramica",
        "confronta",
        "classifica",
        "banche",
        "requisiti",
    }
    english_hits = sum(1 for marker in english_markers if marker in text.split())
    italian_hits = sum(1 for marker in italian_markers if marker in text.split())
    return "en" if english_hits > italian_hits and english_hits >= 2 else "it"


def to_training_record(record: dict[str, Any]) -> dict[str, Any]:
    user_query = str(record.get("user_query", "")).strip()
    return {
        "id": record.get("id", ""),
        "category": record.get("category", ""),
        "lang": infer_lang(user_query),
        "messages": [
            {"role": "system", "content": SYSTEM_PLACEHOLDER},
            {"role": "user", "content": user_query},
            {"role": "assistant", "content": "TODO_CURATED_IDEAL_ANSWER"},
        ],
        "source_log_answer": str(record.get("model_answer", "")).strip(),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Fiorell.IA supervised behavior-tuning seed records from prompt harness logs.",
    )
    parser.add_argument("--in", dest="input_path", required=True, type=Path)
    parser.add_argument("--out", dest="output_path", required=True, type=Path)
    args = parser.parse_args()

    source_records = load_jsonl(args.input_path)
    training_records = [
        to_training_record(record)
        for record in source_records
        if record.get("category") in TARGET_CATEGORIES
    ]
    write_jsonl(args.output_path, training_records)
    print(f"read={len(source_records)}")
    print(f"written={len(training_records)}")
    print(f"out={args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
