#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import yaml  # noqa: F401
except ModuleNotFoundError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyyaml>=6.0"], check=True)

from fiorellia.training.fiorellia_colab_pipeline import (  # noqa: E402
    infer_output_text,
    read_jsonl,
    score_eval_rows,
    validate_adapter_dir,
    write_csv,
    write_json,
    write_jsonl,
    zip_adapter,
)


FINAL_NAME = "fiorellia_behavior_FINAL_RELEASE"
DEFAULT_CONFIG = ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260421_style_abstention_patch.yaml"
DEFAULT_DATASET = ROOT / "fiorellia" / "training" / "supervised_v1_curated_20260421_style_abstention_patch.jsonl"
DEFAULT_EVAL_SET = ROOT / "fiorellia" / "eval" / "eval_set.jsonl"
DEFAULT_BASELINE = ROOT / "fiorellia" / "eval" / "baseline.jsonl"
DEFAULT_SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt.md"
FINAL_THRESHOLDS = {
    "in_scope_grounded": 0.70,
    "unsupported_abstention": 0.95,
    "out_of_scope_refusal": 0.90,
    "italian_style": 0.95,
}
PRIORITY_CASES = {"fio-v0-006", "fio-v0-009", "fio-v0-010", "fio-v0-016"}
MAC_DRIVE_REPO_ROOT = Path(
    "/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine"
)


def drive_root() -> Path | None:
    root = Path("/content/drive/MyDrive")
    return root if root.exists() else None


def drive_repo_root() -> Path | None:
    env_root = os.getenv("FIORELLIA_DRIVE_REPO_ROOT")
    candidates = [
        Path(env_root).expanduser() if env_root else None,
        Path("/content/drive/MyDrive/regulatory-insight-engine"),
        MAC_DRIVE_REPO_ROOT,
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    return None


def mount_drive_if_colab() -> None:
    drive_path = Path("/content/drive/MyDrive")
    if drive_path.exists():
        print("Drive already available, skipping mount.")
        return

    try:
        from google.colab import drive  # type: ignore
    except Exception:
        print("google.colab non disponibile, skip mount.")
        return

    try:
        import IPython

        if IPython.get_ipython() is None:
            raise RuntimeError("No live IPython kernel available for interactive drive.mount()")
    except Exception as exc:
        raise RuntimeError(
            "Google Drive non montato e mount interattivo impossibile da processo batch. "
            "Monta Drive in una cella notebook prima di lanciare il runner."
        ) from exc

    drive.mount("/content/drive")


def default_artifact_dir() -> Path:
    drive_repo = drive_repo_root()
    if drive_repo is not None:
        return drive_repo / "fiorellia-runs" / "final_delivery_latest"
    drive = drive_root()
    if drive is not None:
        return drive / "fiorellia-runs" / "final_delivery_latest"
    return ROOT / "artifacts" / "fiorellia" / "final_release"


def require_a100_runtime(require_a100: bool) -> dict[str, Any]:
    import torch

    info = {
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    if not info["cuda_available"]:
        raise RuntimeError("BLOCCANTE: questo terminale non vede CUDA; collega VS Code a Colab A100 e rilancia.")
    if require_a100 and "A100" not in str(info["device_name"]):
        raise RuntimeError(f"BLOCCANTE: runtime GPU non A100 rilevato: {info['device_name']}")
    return info


def run(command: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print("+", " ".join(command))
    subprocess.run(command, cwd=cwd, env=env, check=True)


def optional_install_deps() -> None:
    packages = [
        "transformers>=4.45,<4.58",
        "datasets>=2.20,<4.0",
        "accelerate>=0.33,<2.0",
        "peft>=0.12,<0.18",
        "trl>=0.9,<0.13",
        "bitsandbytes>=0.43,<0.47",
        "safetensors>=0.4",
        "pyyaml>=6.0",
        "gradio>=4.0",
        "pandas>=2.0",
    ]
    run([sys.executable, "-m", "pip", "install", "-q", *packages])


def output_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id") is not None}


def build_comparison_rows(
    eval_rows: list[dict[str, Any]],
    baseline_rows: list[dict[str, Any]],
    adapter_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    baseline = output_by_id(baseline_rows)
    adapter = output_by_id(adapter_rows)
    rows = []
    for item in eval_rows:
        case_id = str(item["id"])
        baseline_row = baseline.get(case_id, {})
        adapter_row = adapter.get(case_id, {})
        rows.append(
            {
                "id": case_id,
                "category": item.get("category"),
                "user_query": item.get("user_query"),
                "baseline_answer": infer_output_text(baseline_row),
                "adapter_answer": infer_output_text(adapter_row),
                "adapter_error": adapter_row.get("error"),
            }
        )
    return rows


def release_metrics(raw_metrics: dict[str, Any]) -> dict[str, float]:
    metrics = {}
    for name in FINAL_THRESHOLDS:
        value = raw_metrics.get(name)
        if value is None:
            raise RuntimeError(f"BLOCCANTE: metrica mancante: {name}")
        metrics[name] = float(value)
    return metrics


def priority_cases_ok(scored_rows: list[dict[str, Any]]) -> bool:
    rows = {row["id"]: row for row in scored_rows if row.get("id") in PRIORITY_CASES}
    if set(rows) != PRIORITY_CASES:
        return False
    return all(bool(row.get("pred_is_abstention")) for row in rows.values())


def write_final_verdict(path: Path, verdict: str, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# Fiorell.IA Final Certification",
        "",
        f"VERDETTO: {verdict}",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")


def run_app_tests(adapter_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    env = os.environ.copy()
    env["FIORELLIA_SMOKE_LOAD_MODEL"] = "1"
    env["FIORELLIA_ADAPTER_PATH"] = str(adapter_dir)
    output = artifact_dir / "app_final_test_results.json"
    history = artifact_dir / "app_final_history.jsonl"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "fiorellia_app.py"),
            "--smoke-test",
            "--adapter-path",
            str(adapter_dir),
            "--history",
            str(history),
        ],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        payload = {"ok": False, "returncode": completed.returncode, "stderr": completed.stderr, "stdout": completed.stdout}
    else:
        payload = json.loads(completed.stdout)
        payload["ok"] = all(item.get("ok") for item in payload.get("results", []))
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Final Fiorell.IA Colab A100 training, eval and certification.")
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--no-require-a100", action="store_true")
    parser.add_argument("--copy-verdict-to-repo", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mount_drive_if_colab()
    artifact_dir = (args.artifact_dir or default_artifact_dir()).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = artifact_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    local_adapter_dir = Path("/content") / FINAL_NAME if Path("/content").exists() else artifact_dir / FINAL_NAME
    final_zip = artifact_dir / f"{FINAL_NAME}.zip"
    adapter_eval = reports_dir / "adapter_eval.jsonl"

    preflight = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(ROOT),
        "artifact_dir": str(artifact_dir),
        "dataset": str(args.dataset),
        "config": str(args.config),
        "eval_set": str(args.eval_set),
        "baseline": str(args.baseline),
        "system_prompt": str(args.system_prompt),
        "adapter_dir": str(local_adapter_dir),
        "adapter_zip": str(final_zip),
    }
    write_json(preflight, artifact_dir / "final_certification_preflight.json")

    for required in [args.config, args.dataset, args.eval_set, args.baseline, args.system_prompt]:
        if not required.exists():
            raise FileNotFoundError(required)
    if args.dry_run:
        print(json.dumps(preflight, indent=2, ensure_ascii=False))
        return 0

    if args.install_deps:
        optional_install_deps()
    runtime = require_a100_runtime(require_a100=not args.no_require_a100)
    write_json(runtime, artifact_dir / "runtime_gpu.json")

    run(
        [
            sys.executable,
            str(ROOT / "fiorellia" / "training" / "train_lora_behavior_v1.py"),
            "--config",
            str(args.config),
            "--dataset-path",
            str(args.dataset),
            "--output-dir",
            str(local_adapter_dir),
        ]
    )
    validate_adapter_dir(local_adapter_dir)
    zip_adapter(local_adapter_dir, final_zip)

    run(
        [
            sys.executable,
            str(ROOT / "fiorellia" / "eval" / "prompt_harness_local_adapter.py"),
            "--dataset",
            str(args.eval_set),
            "--system-prompt",
            str(args.system_prompt),
            "--adapter-path",
            str(local_adapter_dir),
            "--base-model",
            args.base_model,
            "--out",
            str(adapter_eval),
            "--max-new-tokens",
            str(args.max_new_tokens),
        ]
    )

    eval_rows = read_jsonl(args.eval_set)
    baseline_rows = read_jsonl(args.baseline)
    adapter_rows = read_jsonl(adapter_eval)
    scored_rows, raw_metrics = score_eval_rows(adapter_rows)
    metrics = release_metrics(raw_metrics)
    write_jsonl(scored_rows, artifact_dir / "adapter_eval_scored.jsonl")
    write_csv(build_comparison_rows(eval_rows, baseline_rows, adapter_rows), artifact_dir / "comparison.csv")
    write_json(metrics, artifact_dir / "metrics_summary.json")
    write_json({"raw_metrics": raw_metrics, "thresholds": FINAL_THRESHOLDS}, artifact_dir / "eval_diagnostics.json")

    app_results = run_app_tests(local_adapter_dir, artifact_dir)
    metric_checks = {name: metrics[name] >= threshold for name, threshold in FINAL_THRESHOLDS.items()}
    priority_ok = priority_cases_ok(scored_rows)
    verdict = "GO DEFINITIVO" if all(metric_checks.values()) and priority_ok and app_results.get("ok") else "NO-GO"
    certification = {
        "verdict": verdict,
        "metrics": metrics,
        "thresholds": FINAL_THRESHOLDS,
        "metric_checks": metric_checks,
        "priority_cases_ok": priority_ok,
        "app_results_ok": bool(app_results.get("ok")),
        "adapter_zip": str(final_zip),
        "adapter_eval": str(adapter_eval),
    }
    write_json(certification, artifact_dir / "final_certification_summary.json")
    write_final_verdict(artifact_dir / "final_verdict.md", verdict, certification)
    if args.copy_verdict_to_repo:
        write_final_verdict(ROOT / "fiorellia" / "eval" / "final_verdict.md", verdict, certification)

    print(json.dumps(certification, indent=2, ensure_ascii=False))
    return 0 if verdict == "GO DEFINITIVO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
