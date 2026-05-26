#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fiorellia.training.fiorellia_colab_pipeline import (
    infer_output_text,
    read_jsonl,
    score_eval_rows,
    validate_adapter_zip,
    write_csv,
    write_final_verdict,
    write_json,
    write_jsonl,
)


RELEASE_THRESHOLDS = {
    "in_scope_grounded": 0.80,
    "unsupported_abstention": 0.90,
    "out_of_scope_refusal": 0.95,
    "italian_style": 0.95,
}


def default_artifact_dir(repo_root: Path) -> Path:
    drive_root = Path("/content/drive/MyDrive")
    if drive_root.exists():
        return drive_root / "fiorellia-runs" / "final_delivery_latest"
    return repo_root / "artifacts" / "fiorellia" / "final_release"


def env_path(name: str) -> Path | None:
    value = os.getenv(name)
    return Path(value) if value else None


def first_existing(candidates: list[Path], label: str) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    joined = "\n".join(f"- {candidate}" for candidate in candidates)
    raise FileNotFoundError(f"{label} not found. Checked:\n{joined}")


def clean_stale_outputs(artifact_dir: Path) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    for pattern in ["metrics_summary*.json", "final_verdict*.md"]:
        for item in artifact_dir.glob(pattern):
            item.unlink()


def run_adapter_harness(
    repo_root: Path,
    adapter_zip: Path,
    eval_set: Path,
    system_prompt: Path,
    reports_dir: Path,
    max_new_tokens: int,
    limit: int | None,
    force_cpu: bool,
) -> Path:
    command = [
        "python",
        str(repo_root / "fiorellia" / "eval" / "prompt_harness.py"),
        "--adapter_zip",
        str(adapter_zip),
        "--eval_set",
        str(eval_set),
        "--system_prompt",
        str(system_prompt),
        "--output",
        str(reports_dir),
        "--max-new-tokens",
        str(max_new_tokens),
    ]
    if limit is not None:
        command.extend(["--limit", str(limit)])
    if force_cpu:
        command.append("--force-cpu")
    subprocess.run(command, cwd=repo_root, check=True)
    return reports_dir / "adapter_eval.jsonl"


def output_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id") is not None}


def build_comparison_rows(
    eval_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    adapter_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline = output_by_id(baseline_rows)
    adapter = output_by_id(adapter_rows)
    comparison = []
    for item in eval_rows:
        case_id = str(item["id"])
        baseline_row = baseline.get(case_id, {})
        adapter_row = adapter.get(case_id, {})
        comparison.append(
            {
                "id": case_id,
                "category": item.get("category"),
                "user_query": item.get("user_query"),
                "baseline_answer": infer_output_text(baseline_row),
                "adapter_answer": infer_output_text(adapter_row),
                "adapter_error": adapter_row.get("error"),
            }
        )
    return comparison


def release_metrics(metrics: dict[str, Any]) -> dict[str, float]:
    summary: dict[str, float] = {}
    for name in RELEASE_THRESHOLDS:
        value = metrics.get(name)
        if value is None:
            raise RuntimeError(f"Metric {name} is missing; refusing to write a fake final summary.")
        summary[name] = float(value)
    return summary


def decide(summary: dict[str, float]) -> str:
    return "GO" if all(summary[name] >= threshold for name, threshold in RELEASE_THRESHOLDS.items()) else "NO-GO"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final Fiorell.IA Colab/Drive adapter eval.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--adapter-zip", type=Path, default=None)
    parser.add_argument("--eval-set", type=Path, default=None)
    parser.add_argument("--system-prompt", type=Path, default=None)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force-cpu", action="store_true")
    parser.add_argument("--skip-harness", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.expanduser().resolve()
    artifact_dir = args.artifact_dir or env_path("FIORELLIA_ARTIFACT_DIR") or default_artifact_dir(repo_root)
    artifact_dir = artifact_dir.expanduser().resolve()
    reports_dir = artifact_dir / "reports"
    clean_stale_outputs(artifact_dir)

    adapter_candidates = [
        Path("/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/fiorellia_behavior_RC_HARDENED_20260526.zip"),
        Path("/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip"),
        Path("/content/drive/MyDrive/fiorellia-runs/fiorellia_behavior_20260421.zip"),
        Path("/content/drive/MyDrive/fiorellia/artifacts/fiorellia_lora_adapter.zip"),
        repo_root / "artifacts" / "fiorellia" / "final_release" / "fiorellia_behavior_20260421_clean.zip",
    ]
    adapter_env = env_path("FIORELLIA_ADAPTER_ZIP")
    if adapter_env is not None:
        adapter_candidates.insert(0, adapter_env)
    adapter_zip = args.adapter_zip or first_existing(
        adapter_candidates,
        "Adapter ZIP",
    )
    eval_set = args.eval_set or first_existing(
        [
            repo_root / "fiorellia" / "eval" / "eval_set_behavior_hardening_v1.jsonl",
            repo_root / "fiorellia" / "eval" / "eval_set.jsonl",
            repo_root / "fiorellia" / "eval" / "eval_set_v0.jsonl",
        ],
        "Eval set",
    )
    system_prompt = args.system_prompt or first_existing(
        [
            repo_root / "fiorellia" / "prompts" / "system_prompt_strict.md",
            repo_root / "fiorellia" / "prompts" / "system_prompt.md",
            repo_root / "fiorellia" / "prompts" / "system_prompt.txt",
        ],
        "System prompt",
    )
    baseline = args.baseline or first_existing(
        [repo_root / "fiorellia" / "eval" / "baseline.jsonl", repo_root / "fiorellia" / "eval" / "prompt_harness_baseline_20260421.jsonl"],
        "Baseline JSONL",
    )

    validate_adapter_zip(adapter_zip)
    if args.skip_harness:
        adapter_eval = reports_dir / "adapter_eval.jsonl"
        if not adapter_eval.exists():
            raise FileNotFoundError(f"--skip-harness requires existing {adapter_eval}")
    else:
        adapter_eval = run_adapter_harness(
            repo_root=repo_root,
            adapter_zip=adapter_zip,
            eval_set=eval_set,
            system_prompt=system_prompt,
            reports_dir=reports_dir,
            max_new_tokens=args.max_new_tokens,
            limit=args.limit,
            force_cpu=args.force_cpu,
        )

    eval_rows = read_jsonl(eval_set)
    baseline_rows = read_jsonl(baseline)
    adapter_rows = read_jsonl(adapter_eval)
    scored_rows, metrics = score_eval_rows(adapter_rows)
    summary = release_metrics(metrics)
    verdict = decide(summary)

    write_jsonl(scored_rows, artifact_dir / "adapter_eval_scored.jsonl")
    write_csv(build_comparison_rows(eval_rows, baseline_rows, adapter_rows), artifact_dir / "comparison.csv")
    write_json(summary, artifact_dir / "metrics_summary.json")
    write_json(
        {
            "adapter_zip": str(adapter_zip),
            "adapter_eval": str(adapter_eval),
            "baseline": str(baseline),
            "eval_set": str(eval_set),
            "system_prompt": str(system_prompt),
            "thresholds": RELEASE_THRESHOLDS,
            "raw_metrics": metrics,
            "verdict": verdict,
        },
        artifact_dir / "eval_diagnostics.json",
    )
    write_final_verdict(artifact_dir / "final_verdict.md", verdict, summary)
    print(f"artifact_dir={artifact_dir}")
    print(f"verdict={verdict}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
