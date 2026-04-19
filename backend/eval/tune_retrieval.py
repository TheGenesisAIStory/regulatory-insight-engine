#!/usr/bin/env python3
"""Sweep retrieval-related parameters and evaluate on the domain benchmark.

This script orchestrates runs of `run_benchmark.py` for combinations of
`top_k` and `threshold` and (optionally) for different chunk sizes/overlaps.

By default it runs a small, safe grid (no re-chunking) to avoid expensive
rebuilding of embeddings. To vary chunk parameters set `--vary-chunk` and
provide `--chunk-sizes` and `--chunk-overlaps` lists; those runs will force
rebuilding of the embeddings cache per chunk configuration.

Results are saved under the provided `--outdir` as JSON and a compact
comparison JSON (`tuning_summary.json`).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from itertools import product
from pathlib import Path
from typing import List


def parse_list(s: str) -> List[str]:
    return [item.strip() for item in s.split(",") if item.strip()]


def run_benchmark_subprocess(dataset: Path, out_json: Path, out_md: Path, top_k: int, threshold: float, env: dict[str, str]) -> int:
    cmd = [sys.executable, str(Path(__file__).with_name("run_benchmark.py")), "--dataset", str(dataset), "--out", str(out_json), "--markdown", str(out_md), "--top-k", str(top_k), "--threshold", f"{threshold:.3f}"]
    proc_env = os.environ.copy()
    proc_env.update(env)
    start = time.time()
    result = subprocess.run(cmd, env=proc_env)
    dur = time.time() - start
    return result.returncode, dur


def load_metrics(report_path: Path) -> dict | None:
    if not report_path.exists():
        return None
    try:
        with report_path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune retrieval parameters using the local domain benchmark")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.jsonl"))
    parser.add_argument("--outdir", type=Path, default=Path(__file__).with_name("reports") / "tune_retrieval")
    parser.add_argument("--top-ks", default="4,6,8", help="Comma-separated top_k values to try")
    parser.add_argument("--thresholds", default="0.10,0.12,0.18", help="Comma-separated score thresholds to try")
    parser.add_argument("--min-score-gaps", default="", help="Comma-separated min score gap values to try (e.g. 0.02,0.05). Empty = no min_score_gap")
    parser.add_argument("--chunk-sizes", default="", help="Comma-separated chunk sizes (words) to try when --vary-chunk")
    parser.add_argument("--chunk-overlaps", default="", help="Comma-separated chunk overlaps to try when --vary-chunk")
    parser.add_argument("--vary-chunk", action="store_true", help="When set, vary chunk sizes/overlaps and rebuild embeddings per combination (expensive)")
    parser.add_argument("--max-runs", type=int, default=0, help="Optional limit on total runs (0 = no limit)")
    args = parser.parse_args()

    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    top_ks = [int(x) for x in parse_list(args.top_ks)]
    thresholds = [float(x) for x in parse_list(args.thresholds)]

    if args.vary_chunk:
        chunk_sizes = [int(x) for x in parse_list(args.chunk_sizes)] if args.chunk_sizes else [420]
        chunk_overlaps = [int(x) for x in parse_list(args.chunk_overlaps)] if args.chunk_overlaps else [80]
    else:
        chunk_sizes = [None]
        chunk_overlaps = [None]
    min_score_gaps = [None]
    if args.min_score_gaps:
        min_score_gaps = [float(x) for x in parse_list(args.min_score_gaps)]

    combos = list(product(chunk_sizes, chunk_overlaps, top_ks, thresholds, min_score_gaps))
    if args.max_runs > 0:
        combos = combos[: args.max_runs]

    summary = []
    for idx, (chunk_size, chunk_overlap, top_k, threshold, min_score_gap) in enumerate(combos, start=1):
        run_name_parts = [f"top{top_k}", f"thr{int(threshold*1000)}"]
        env: dict[str, str] = {}
        if chunk_size is not None:
            run_name_parts.insert(0, f"chunk{chunk_size}")
            env["CHUNK_SIZE"] = str(chunk_size)
            env["CHUNK_OVERLAP"] = str(chunk_overlap)
            # use a per-run cache file to avoid clobbering main cache
            cache_path = outdir / f"cache_chunk{chunk_size}_ov{chunk_overlap}.pkl"
            env["CACHE_PATH"] = str(cache_path)
        run_name = "_".join(run_name_parts)
        if min_score_gap is not None:
            run_name_parts.append(f"gap{int(min_score_gap*1000)}")
        out_json = outdir / f"benchmark_{run_name}.json"
        out_md = outdir / f"benchmark_{run_name}.md"

        print(f"[{idx}/{len(combos)}] Running: chunk_size={chunk_size} overlap={chunk_overlap} top_k={top_k} threshold={threshold} min_score_gap={min_score_gap}")
        # append min-score-gap to cmd via env var for this subprocess: run_benchmark accepts --min-score-gap arg
        # We call run_benchmark_subprocess which currently does not accept min_score_gap, so set it via environment variable
        # by augmenting the command we build here using subprocess directly.
        cmd = [sys.executable, str(Path(__file__).with_name("run_benchmark.py")), "--dataset", str(args.dataset), "--out", str(out_json), "--markdown", str(out_md), "--top-k", str(top_k), "--threshold", f"{threshold:.3f}"]
        if min_score_gap is not None:
            cmd += ["--min-score-gap", str(min_score_gap)]
        proc_env = os.environ.copy()
        proc_env.update(env)
        start_time = time.time()
        proc = subprocess.run(cmd, env=proc_env)
        dur = time.time() - start_time
        rc = proc.returncode
        report = load_metrics(out_json)
        if report is None:
            print(f"  -> No report found at {out_json} (rc={rc})")
            continue

        metrics = report.get("metrics", {})
        summary_item = {
            "run": run_name,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": top_k,
            "threshold": threshold,
            "min_score_gap": min_score_gap,
            "rc": rc,
            "duration_s": dur,
            "metrics": metrics,
            "report_path": str(out_json),
        }
        summary.append(summary_item)
        # write intermediate summary
        (outdir / "tuning_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    # final summary
    (outdir / "tuning_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Tuning finished. Outputs in {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
