#!/usr/bin/env python3
"""Verify `expected_sources` entries in an eval dataset map to files under the local `docs/` corpus.

Usage:
  python backend/eval/check_expected_sources.py --dataset backend/eval/supervised_seed.cleaned.jsonl --docs-path ../docs

The script reports missing expected sources and offers filename suggestions.
"""

from __future__ import annotations

import argparse
import json
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Dict, List, Set


def load_dataset(path: Path) -> List[Dict]:
    items: List[Dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            try:
                items.append(json.loads(s))
            except Exception:
                continue
    return items


def gather_docs(docs_root: Path) -> List[Path]:
    exts = {".pdf", ".html", ".htm", ".md", ".txt", ".json"}
    files: List[Path] = []
    if not docs_root.exists():
        return files
    for p in docs_root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            files.append(p)
    return files


def normalize_name(name: str) -> str:
    return Path(name).name.lower()


def find_matches(expected: str, docs: List[Path]) -> List[str]:
    expected_norm = normalize_name(expected)
    expected_core = expected_norm.split(".")[0]
    matches: List[str] = []
    for d in docs:
        basename = d.name.lower()
        stem = d.stem.lower()
        if basename == expected_norm or stem == expected_core or expected_core in basename:
            matches.append(str(d))

    if matches:
        return matches

    # fuzzy suggestions
    names = [p.name.lower() for p in docs]
    close = get_close_matches(expected_core, names, n=5, cutoff=0.5)
    return close


def main() -> int:
    parser = argparse.ArgumentParser(description="Check expected_sources against local docs folder")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.jsonl"))
    parser.add_argument("--docs-path", type=Path, default=None, help="Path to docs/ folder (overrides config)")
    parser.add_argument("--out", type=Path, help="Optional JSON output path for the mapping")
    args = parser.parse_args()

    # allow importing backend config if running in repo
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    try:
        from config import settings  # type: ignore

        default_docs = Path(settings.docs_path)
    except Exception:
        default_docs = Path.cwd() / "docs"

    docs_root = args.docs_path or default_docs
    docs_root = docs_root.expanduser().resolve()

    if not args.dataset.exists():
        print(f"Dataset not found: {args.dataset}")
        return 2

    items = load_dataset(args.dataset)
    expected: Set[str] = set()
    external: Set[str] = set()
    for rec in items:
        for s in rec.get("expected_sources", []) or []:
            s_str = str(s)
            if s_str.startswith("external:") or s_str.startswith("external/"):
                external.add(s_str)
                continue
            expected.add(s_str)

    docs = gather_docs(docs_root)
    found: Dict[str, List[str]] = {}
    missing: List[str] = []

    for e in sorted(expected):
        matches = find_matches(e, docs)
        if matches:
            found[e] = matches
        else:
            missing.append(e)

    print(f"Docs root: {docs_root}")
    print(f"Examined {len(docs)} files under docs/")
    print(f"Unique expected_sources: {len(expected)}")
    print(f"Marked external: {len(external)}")
    print(f"Matched: {len(found)}  Missing: {len(missing)}\n")

    if found:
        print("Sample matches:")
        for k, v in list(found.items())[:20]:
            print(f" - {k} -> {v[0]}")
        print()

    if missing:
        print("Missing expected sources (with suggestions):")
        for e in missing:
            suggestions = find_matches(e, docs)
            suggestion_text = ", ".join(suggestions) if suggestions else "(no suggestions)"
            print(f" - {e} -> {suggestion_text}")
    else:
        print("All expected sources were found in docs/.")

    if args.out:
        out_payload = {"docs_root": str(docs_root), "matched": found, "missing": missing, "external": sorted(list(external))}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote report to {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
