#!/usr/bin/env python3
"""Validate and deduplicate a supervised JSONL dataset for domain adaptation.

Lightweight validator that checks required fields, types, allowed example types
and removes duplicates (by `id` or content hash). Writes a cleaned JSONL if
`--output` is provided and prints a short summary.

Usage:
  python validate_supervised_dataset.py --input supervised_seed.jsonl --output cleaned.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

ALLOWED_TYPES = {"factual_qa", "definitional_qa", "comparison_qa", "no_answer", "classification", "source_grounded"}


def load_jsonl(path: Path) -> Iterable[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{lineno}: {exc}")
            yield lineno, obj


def validate_record(rec: Dict[str, Any]) -> List[str]:
    errs: List[str] = []
    if not isinstance(rec, dict):
        return ["record is not a JSON object"]

    required = ["id", "category", "input", "target", "example_type", "language"]
    for key in required:
        if key not in rec:
            errs.append(f"missing required field '{key}'")

    if "example_type" in rec and rec["example_type"] not in ALLOWED_TYPES:
        errs.append(f"example_type '{rec.get('example_type')}' not in allowed types {sorted(ALLOWED_TYPES)}")

    if "expected_sources" in rec and not isinstance(rec["expected_sources"], list):
        errs.append("expected_sources must be an array of strings")

    # minimal type checks
    for k in ("id", "category", "input", "target", "language", "example_type"):
        if k in rec and not isinstance(rec[k], str):
            errs.append(f"field '{k}' must be a string")

    return errs


def content_hash(rec: Dict[str, Any]) -> str:
    key = (rec.get("category", "") + "|" + rec.get("input", "") + "|" + rec.get("target", "")).encode("utf-8")
    return hashlib.sha256(key).hexdigest()


def dedupe_and_validate(input_path: Path, output_path: Path | None = None, strict: bool = False) -> Tuple[List[Dict[str, Any]], List[Tuple[int, str]], Dict[str, int]]:
    seen_ids = set()
    seen_hashes = set()
    kept: List[Dict[str, Any]] = []
    issues: List[Tuple[int, str]] = []

    for lineno, rec in load_jsonl(input_path):
        try:
            errs = validate_record(rec)
        except Exception as exc:
            issues.append((lineno, str(exc)))
            if strict:
                continue
            else:
                # fallthrough: treat as invalid but keep if not strict
                errs = [str(exc)]

        if errs:
            issues.append((lineno, "; ".join(errs)))
            if strict:
                continue

        recid = rec.get("id")
        if recid:
            if recid in seen_ids:
                issues.append((lineno, f"duplicate id {recid} - skipped"))
                continue
            seen_ids.add(recid)

        h = content_hash(rec)
        if h in seen_hashes:
            issues.append((lineno, "duplicate content - skipped"))
            continue
        seen_hashes.add(h)

        kept.append(rec)

    if output_path:
        with output_path.open("w", encoding="utf-8") as fh:
            for rec in kept:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    stats: Dict[str, int] = {}
    for rec in kept:
        t = rec.get("example_type", "unknown")
        stats[t] = stats.get(t, 0) + 1

    return kept, issues, stats


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="validate_supervised_dataset.py", description="Validate and deduplicate a JSONL supervised dataset")
    parser.add_argument("--input", "-i", required=True, help="Input JSONL file")
    parser.add_argument("--output", "-o", help="Output path for cleaned JSONL (optional)")
    parser.add_argument("--strict", "-s", action="store_true", help="Drop invalid records instead of keeping them")
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 2

    output_path = Path(args.output) if args.output else None

    kept, issues, stats = dedupe_and_validate(input_path, output_path, strict=args.strict)

    print(f"Kept records: {len(kept)}")
    if stats:
        print("By example_type:")
        for k, v in sorted(stats.items(), key=lambda x: (-x[1], x[0])):
            print(f"  {k}: {v}")

    if issues:
        print("Issues detected (sample up to 50):")
        for lineno, msg in issues[:50]:
            print(f"  Line {lineno}: {msg}")

    if output_path:
        print(f"Cleaned dataset written to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
