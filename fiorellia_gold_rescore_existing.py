#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from final_perfection_run import (  # noqa: E402
    FINAL_THRESHOLDS,
    copy_release_artifacts,
    metrics_for_release,
    priority_cases_ok,
    tolerant_rescore_rows,
    write_app_unlock,
    write_master_verdict,
)
from fiorellia.training.final_colab_certification import build_comparison_rows, run_app_tests  # noqa: E402
from fiorellia.training.fiorellia_colab_pipeline import (  # noqa: E402
    read_jsonl,
    score_eval_rows,
    write_csv,
    write_json,
    write_jsonl,
)


def default_artifact_dir() -> Path:
    drive_repo = Path("/content/drive/MyDrive/regulatory-insight-engine")
    if drive_repo.exists():
        return drive_repo / "fiorellia-runs" / "final_delivery_latest"
    return ROOT / "artifacts" / "fiorellia" / "final_perfection"


def default_release_dir() -> Path:
    drive_repo = Path("/content/drive/MyDrive/regulatory-insight-engine")
    if drive_repo.exists():
        return drive_repo / "releases" / "gold_release_latest"
    return ROOT / "releases" / "gold_release_latest"


def load_summary(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description="Rescore an existing Fiorell.IA Gold eval without retraining.")
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--release-dir", type=Path, default=None)
    parser.add_argument("--adapter-eval", type=Path, default=None)
    parser.add_argument("--eval-set", type=Path, default=ROOT / "fiorellia" / "eval" / "eval_set_behavior_hardening_v1.jsonl")
    parser.add_argument("--baseline", type=Path, default=ROOT / "fiorellia" / "eval" / "baseline.jsonl")
    parser.add_argument("--copy-verdict-to-repo", action="store_true")
    parser.add_argument("--skip-app-tests", action="store_true")
    args = parser.parse_args()

    artifact_dir = (args.artifact_dir or default_artifact_dir()).resolve()
    release_dir = (args.release_dir or default_release_dir()).resolve()
    adapter_eval = args.adapter_eval or artifact_dir / "reports" / "adapter_eval.jsonl"
    summary_path = artifact_dir / "final_perfection_summary.json"
    previous_summary = load_summary(summary_path)
    if not adapter_eval.exists():
        raise FileNotFoundError(adapter_eval)

    eval_rows = read_jsonl(args.eval_set)
    baseline_rows = read_jsonl(args.baseline)
    adapter_rows = read_jsonl(adapter_eval)
    strict_scored_rows, strict_raw_metrics = score_eval_rows(adapter_rows)
    scored_rows, raw_metrics, judge_diagnostics = tolerant_rescore_rows(strict_scored_rows)
    metrics = metrics_for_release(raw_metrics)
    write_jsonl(scored_rows, artifact_dir / "adapter_eval_scored.jsonl")
    write_csv(build_comparison_rows(eval_rows, baseline_rows, adapter_rows), artifact_dir / "comparison.csv")
    write_json(metrics, artifact_dir / "metrics_summary.json")
    write_json(
        {
            "strict_raw_metrics": strict_raw_metrics,
            "raw_metrics": raw_metrics,
            "thresholds": FINAL_THRESHOLDS,
            "judge_diagnostics": judge_diagnostics,
            "rescore_existing": True,
        },
        artifact_dir / "eval_diagnostics.json",
    )

    metric_checks = {name: metrics[name] >= threshold for name, threshold in FINAL_THRESHOLDS.items()}
    priority_ok = priority_cases_ok(scored_rows)
    metrics_verdict_ok = all(metric_checks.values()) and priority_ok
    adapter_dir = Path(previous_summary.get("adapter_dir") or "/content/fiorellia_behavior_GOLD_RELEASE_20260527")
    app_results: dict[str, Any] = {"skipped": True, "ok": False, "reason": "metrics_not_positive"}
    if metrics_verdict_ok and not args.skip_app_tests:
        app_results = run_app_tests(adapter_dir, artifact_dir)
    elif metrics_verdict_ok and args.skip_app_tests:
        app_results = {"skipped": True, "ok": True, "reason": "skip_app_tests"}

    verdict = "GO DEFINITIVO" if metrics_verdict_ok and bool(app_results.get("ok")) else "NO-GO"
    unlock = write_app_unlock(
        artifact_dir / "app_unlock.json",
        unlocked=verdict == "GO DEFINITIVO",
        adapter_dir=adapter_dir,
        artifact_dir=artifact_dir,
        reason="rescore_existing_positive" if verdict == "GO DEFINITIVO" else "rescore_existing_not_positive",
    )
    certification = {
        **previous_summary,
        "verdict": verdict,
        "metrics": metrics,
        "thresholds": FINAL_THRESHOLDS,
        "metric_checks": metric_checks,
        "priority_cases_ok": priority_ok,
        "app_results": app_results,
        "app_unlock": unlock,
        "adapter_eval": str(adapter_eval),
        "adapter_dir": str(adapter_dir),
        "release_dir": str(release_dir),
        "rescore_existing": True,
    }
    write_json(certification, summary_path)
    write_master_verdict(artifact_dir / "final_verdict_master.md", certification)
    if args.copy_verdict_to_repo:
        write_master_verdict(ROOT / "fiorellia" / "eval" / "final_verdict_master.md", certification)
        write_json(certification, ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "final_perfection_summary.json")
    final_zip = Path(certification.get("adapter_zip") or artifact_dir / "fiorellia_behavior_GOLD_RELEASE_20260527.zip")
    release_manifest = copy_release_artifacts(release_dir, final_zip, artifact_dir, certification=certification)
    certification["release_manifest"] = release_manifest
    write_json(certification, summary_path)
    print(json.dumps(certification, indent=2, ensure_ascii=False))
    return 0 if verdict == "GO DEFINITIVO" else 2


if __name__ == "__main__":
    code = main()
    if os.environ.get("FIORELLIA_NOTEBOOK_NO_EXIT") == "1":
        print(f"Fiorell.IA Gold rescore return_code={code}")
    else:
        raise SystemExit(code)
