#!/usr/bin/env python3
"""Compare multiple RAG runtime modes (score-only, score+domain-gate, retrieval variants).

Produces a comparative JSON and Markdown report under `backend/eval/reports/`.

This script reuses the existing evaluation helpers in `run_benchmark.py` and
keeps all work offline and decoupled from production runtime logic.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import run_benchmark as rb  # module in same folder


DEFAULT_MODES = [
    {"name": "score_only", "use_domain_gate": False, "suffix": "score"},
    {"name": "score_plus_domain_gate", "use_domain_gate": True, "suffix": "score+dg"},
    {"name": "retrieval_opt", "use_domain_gate": False, "suffix": "retrieval"},
]


def summarize_metrics(report: dict[str, Any]) -> dict[str, Any]:
    m = report.get("metrics", {})
    return {
        "caseCount": m.get("caseCount"),
        "sourceHitRate": m.get("sourceHitRate"),
        "noAnswerAccuracy": m.get("noAnswerAccuracy"),
        "falseAnswerCount": m.get("falseAnswerCount"),
        "falseNoAnswerCount": m.get("falseNoAnswerCount"),
        "avgLatencyMs": m.get("avgLatencyMs"),
    }


def run_mode_for_cases(cases: list[rb.EvalCase], top_k: int, threshold: float, min_score_gap: float | None, use_domain_gate: bool) -> list[dict[str, Any]]:
    results = []
    for case in cases:
        res = rb.run_case(case, top_k=top_k, generate=False, threshold=threshold, min_score_gap=min_score_gap, use_domain_gate=use_domain_gate)
        results.append(res)
    return results


def build_comparison_report(dataset: Path, cases: list[rb.EvalCase], modes: list[dict[str, Any]], top_k: int, threshold: float, min_score_gap: float | None, retrieval_top_k: int | None, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    mode_reports: dict[str, dict[str, Any]] = {}

    for mode in modes:
        name = mode["name"]
        use_domain_gate = bool(mode.get("use_domain_gate", False))
        mode_topk = top_k if name != "retrieval_opt" else (retrieval_top_k or max(top_k * 2, top_k + 6))

        print(f"Running mode {name}: top_k={mode_topk}, domain_gate={use_domain_gate}, threshold={threshold}, min_score_gap={min_score_gap}")
        results = run_mode_for_cases(cases, top_k=mode_topk, threshold=threshold, min_score_gap=min_score_gap, use_domain_gate=use_domain_gate)
        # build a per-mode report using run_benchmark helpers
        report = rb.build_report(dataset, results, top_k=mode_topk, generate=False)

        # write per-mode JSON/MD for inspection
        per_json = out_dir / f"report_{name}.json"
        per_md = out_dir / f"report_{name}.md"
        rb.write_json_report(per_json, report)
        rb.write_markdown_report(per_md, report)

        mode_reports[name] = {"report": report, "summary": summarize_metrics(report)}

    # comparative summary
    comparison = {name: info["summary"] for name, info in mode_reports.items()}

    # pick best by primary: noAnswerAccuracy, tie-break: sourceHitRate, then penalize falseAnswerCount, then avgLatencyMs
    def mode_key(item: tuple[str, Any]):
        name, summary = item
        na = summary.get("noAnswerAccuracy") or 0.0
        sh = summary.get("sourceHitRate") or 0.0
        fa = summary.get("falseAnswerCount") or 0
        fna = summary.get("falseNoAnswerCount") or 0
        lat = summary.get("avgLatencyMs") or 1e9
        return (na, sh, -fa, -fna, -lat)

    ranked = sorted(comparison.items(), key=mode_key, reverse=True)
    best_mode = ranked[0][0] if ranked else None

    combined = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "dataset": str(dataset),
        "modes": {name: info["summary"] for name, info in mode_reports.items()},
        "bestMode": best_mode,
        "modeReports": {name: info["report"] for name, info in mode_reports.items()},
    }

    # write combined artifacts
    combo_json = out_dir / "compare_modes.json"
    combo_md = out_dir / "compare_modes.md"
    with combo_json.open("w", encoding="utf-8") as fh:
        json.dump(combined, fh, ensure_ascii=False, indent=2)

    # write a compact markdown summary
    lines = [
        "# Comparative RAG Modes Report",
        "",
        f"- Dataset: `{dataset}`",
        f"- Generated at: `{combined['generatedAt']}`",
        "",
        "## Summary table",
        "",
        "| Mode | Source hit rate | No-answer accuracy | False answers | False no-answers | Avg latency |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for name, summary in combined["modes"].items():
        def pct(v):
            return "n/a" if v is None else f"{v*100:.1f}%"

        lines.append(
            f"| `{name}` | {pct(summary.get('sourceHitRate'))} | {pct(summary.get('noAnswerAccuracy'))} | {summary.get('falseAnswerCount',0)} | {summary.get('falseNoAnswerCount',0)} | {summary.get('avgLatencyMs') or 'n/a'} ms |"
        )

    lines.extend([
        "",
        f"**Recommended mode:** `{best_mode}`",
        "",
        "## Notes & Trade-offs",
        "",
        "- The recommended mode is chosen prioritizing no-answer accuracy, then source hit rate, and penalizing false answers and latency.",
        "- Inspect per-mode reports in this folder for full failure case lists and detailed diagnostics.",
        "",
        "## Per-mode failure samples",
        "",
    ])

    for name, info in mode_reports.items():
        failed = info["report"].get("failedCases", [])
        lines.append(f"### {name} — {len(failed)} failed cases")
        lines.append("")
        if not failed:
            lines.append("No failures.")
            lines.append("")
            continue
        for item in failed[:10]:
            lines.extend([
                f"- `{item['id']}` (category: `{item['category']}`): expectedNoAnswer={item['expectedNoAnswer']}, predictedNoAnswer={item['predictedNoAnswer']}, sourceHit={item['sourceHit']}, topScore={item['topScore']:.4f}",
            ])
        lines.append("")

    combo_md_text = "\n".join(lines) + "\n"
    combo_md.write_text(combo_md_text, encoding="utf-8")

    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare RAG modes and produce a combined report")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("dataset.jsonl"))
    parser.add_argument("--outdir", type=Path, default=Path(__file__).with_name("reports"))
    parser.add_argument("--top-k", type=int, default=rb.TOP_K)
    parser.add_argument("--threshold", type=float, default=rb.MIN_SCORE_TO_ANSWER)
    parser.add_argument("--min-score-gap", type=float, default=None)
    parser.add_argument("--retrieval-top-k", type=int, default=None, help="Top-K to use for retrieval-optimized mode (defaults to 2x top-k)")
    args = parser.parse_args()

    cases = rb.load_dataset(args.dataset)
    modes = DEFAULT_MODES
    combined = build_comparison_report(args.dataset, cases, modes, top_k=args.top_k, threshold=args.threshold, min_score_gap=args.min_score_gap, retrieval_top_k=args.retrieval_top_k, out_dir=args.outdir)

    print(f"Comparison written to {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
