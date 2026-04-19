#!/usr/bin/env python3
"""Export supervised JSONL into an instruction-tuning JSONL (Alpaca-style by default).

Mapping rules:
- `instruction` <= record['input']
- `input` <= empty string (can be extended)
- `output` <= record['target']

Skips `no_answer` examples by default (configurable).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable


def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            yield json.loads(s)


def write_jsonl(path: Path, items: Iterable[dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for rec in items:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def convert_record(rec: dict, include_no_answer: bool = False) -> dict | None:
    etype = rec.get("example_type")
    if etype == "no_answer" and not include_no_answer:
        return None

    if etype == "classification":
        instruction = f"Classify the following text: {rec.get('input','') }"
    else:
        instruction = rec.get("input", "")

    return {"instruction": instruction, "input": "", "output": rec.get("target", "")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Export to instruction-tuning JSONL")
    parser.add_argument("--input", required=True, help="Input supervised JSONL")
    parser.add_argument("--output", required=True, help="Output instruction JSONL")
    parser.add_argument("--include-no-answer", action="store_true", help="Include no_answer examples")
    args = parser.parse_args(argv)

    inp = Path(args.input)
    out = Path(args.output)

    records = []
    for rec in load_jsonl(inp):
        mapped = convert_record(rec, include_no_answer=args.include_no_answer)
        if mapped is not None:
            records.append(mapped)

    write_jsonl(out, records)
    print(f"Exported {len(records)} records to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
