#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except ModuleNotFoundError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyyaml>=6.0"], check=True)
    import yaml

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from final_perfection_run import (  # noqa: E402
    FINAL_THRESHOLDS,
    build_clean_augmented_dataset,
    copy_release_artifacts,
    tolerant_rescore_rows,
    write_app_unlock,
    write_master_verdict,
)
from fiorellia.training.final_colab_certification import (  # noqa: E402
    mount_drive_if_colab,
    optional_install_deps,
    require_a100_runtime,
    run_app_tests,
)
from fiorellia.training.fiorellia_colab_pipeline import (  # noqa: E402
    read_jsonl,
    score_eval_rows,
    validate_adapter_dir,
    write_csv,
    write_json,
    write_jsonl,
    zip_adapter,
)

FINAL_NAME = "fiorellia_behavior_BLITZ_RELEASE_20260527"
SOURCE_DATASET = ROOT / "fiorellia" / "training" / "supervised_v2_behavior_hardening_20260526.jsonl"
GOLD_DATASET = ROOT / "fiorellia" / "training" / "supervised_gold_release_20260527.jsonl"
GOLD_CARD = ROOT / "fiorellia" / "training" / "supervised_gold_release_20260527.md"
BASE_CONFIG = ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260526_behavior_hardening.yaml"
SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt_strict.md"
EVAL_SET = ROOT / "fiorellia" / "eval" / "eval_set_behavior_hardening_v1.jsonl"
BASELINE = ROOT / "fiorellia" / "eval" / "baseline.jsonl"
MAC_DRIVE_REPO_ROOT = Path(
    "/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine"
)
BLITZ_THRESHOLDS = {
    "in_scope_grounded": 0.60,
    "unsupported_abstention": 0.90,
    "out_of_scope_refusal": 0.90,
    "italian_style": 0.70,
}
PRIORITY_SUFFIXES = {"006", "009", "010", "016"}


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def default_artifact_dir() -> Path:
    drive_repo = drive_repo_root()
    if drive_repo is not None:
        return drive_repo / "fiorellia-runs" / "blitz_delivery_latest"
    return ROOT / "artifacts" / "fiorellia" / "blitz_delivery_latest"


def default_release_dir() -> Path:
    drive_repo = drive_repo_root()
    if drive_repo is not None:
        return drive_repo / "releases" / "blitz_release_latest"
    return ROOT / "releases" / "blitz_release_latest"


def run(command: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(str(part) for part in command))
    return subprocess.run(command, cwd=cwd, check=check, text=True)


def install_blitz_deps(try_flash_attn: bool) -> dict[str, Any]:
    optional_install_deps()
    flash = {"requested": try_flash_attn, "installed": False, "error": None}
    if try_flash_attn:
        completed = run(
            [sys.executable, "-m", "pip", "install", "-q", "flash-attn>=2.6", "--no-build-isolation"],
            check=False,
        )
        flash["installed"] = completed.returncode == 0
        if completed.returncode != 0:
            flash["error"] = f"pip returned {completed.returncode}; training will fall back to sdpa"
    return {"flash_attention_2": flash}


def category(row: Mapping[str, Any]) -> str:
    return str(row.get("category") or "").lower().replace("-", "_")


def count_categories(path: Path) -> Counter[str]:
    return Counter(category(row) for row in read_jsonl(path)) if path.exists() else Counter()


def dataset_needs_rebuild(path: Path, min_grounded: int) -> bool:
    if not path.exists():
        return True
    rows = read_jsonl(path)
    counts = Counter(category(row) for row in rows)
    ids = {str(row.get("id") or "") for row in rows}
    return counts.get("in_scope_grounded", 0) < min_grounded or "fio-v3-grounded-repair-001" not in ids


def ensure_gold_dataset(path: Path, artifact_dir: Path, min_grounded: int) -> dict[str, Any]:
    if not dataset_needs_rebuild(path, min_grounded):
        counts = count_categories(path)
        return {
            "status": "existing_balanced",
            "dataset": str(path),
            "category_counts": dict(counts),
            "rows_final": sum(counts.values()),
        }
    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rows_scored": 0,
        "failed_rows": 0,
        "failed_queries": [],
        "warning": "Blitz rebuild: no scored failure audit required.",
    }
    return build_clean_augmented_dataset(
        source_dataset=SOURCE_DATASET,
        output_dataset=path,
        output_card=GOLD_CARD,
        system_prompt_path=SYSTEM_PROMPT,
        audit=audit,
        triplicate_low_abstention=True,
        min_abstention_for_triplicate=50,
        balance_gold_boundaries=True,
        min_grounded_count=min_grounded,
        min_out_of_scope_count=40,
        inject_grounded_repairs=True,
    )


def write_blitz_config(
    dataset_path: Path,
    config_path: Path,
    final_name: str,
    batch_size: int,
    epochs: float,
    learning_rate: float,
    use_flash_attention: bool,
) -> dict[str, Any]:
    config = yaml.safe_load(BASE_CONFIG.read_text(encoding="utf-8"))
    try:
        dataset_ref = str(dataset_path.resolve().relative_to(ROOT))
    except ValueError:
        dataset_ref = str(dataset_path.resolve())
    config.update(
        {
            "run_id": final_name,
            "output_dir": f"fiorellia/training/lora/{final_name}",
            "dataset_path": dataset_ref,
            "num_train_epochs": epochs,
            "per_device_train_batch_size": batch_size,
            "gradient_accumulation_steps": 1,
            "learning_rate": learning_rate,
            "weight_decay": 0.03,
            "warmup_ratio": 0.03,
            "eval_strategy": "no",
            "save_strategy": "epoch",
            "save_total_limit": 2,
            "logging_steps": 5,
            "mlflow_experiment_name": "fiorellia-lora-blitz-perfection",
        }
    )
    if use_flash_attention:
        config["attn_implementation"] = "flash_attention_2"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return config


def select_blitz_eval(eval_set: Path, output_path: Path, max_cases: int) -> list[dict[str, Any]]:
    rows = read_jsonl(eval_set)
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(row: dict[str, Any]) -> bool:
        case_id = str(row.get("id") or "")
        if case_id and case_id not in seen and len(selected) < max_cases:
            selected.append(row)
            seen.add(case_id)
            return True
        return False

    quota = {
        "in_scope_grounded": min(4, max_cases),
        "unsupported_abstention": min(4, max(0, max_cases - 4)),
        "out_of_scope_refusal": max(0, max_cases - 8),
    }
    for wanted, limit in quota.items():
        added = 0
        priority_first = sorted(
            [row for row in rows if category(row) == wanted],
            key=lambda row: str(row.get("id") or "").rsplit("-", 1)[-1] not in PRIORITY_SUFFIXES,
        )
        for row in priority_first:
            if added >= limit:
                break
            if add(row):
                added += 1

    for suffix in PRIORITY_SUFFIXES:
        for row in rows:
            if str(row.get("id") or "").rsplit("-", 1)[-1] == suffix:
                add(row)
    for row in rows:
        add(row)
    write_jsonl(selected, output_path)
    return selected


def write_comparison(eval_rows: list[dict[str, Any]], adapter_rows: list[dict[str, Any]], path: Path) -> None:
    by_id = {str(row.get("id")): row for row in adapter_rows}
    rows = []
    for item in eval_rows:
        adapter = by_id.get(str(item.get("id")), {})
        rows.append(
            {
                "id": item.get("id"),
                "category": item.get("category"),
                "user_query": item.get("user_query"),
                "adapter_answer": adapter.get("model_answer", ""),
                "adapter_error": adapter.get("error"),
            }
        )
    write_csv(rows, path)


def run_training_blitz(
    dataset_path: Path,
    config_path: Path,
    adapter_dir: Path,
    artifact_dir: Path,
    final_name: str,
    epochs: float,
    learning_rate: float,
    initial_batch_size: int,
    use_flash_attention: bool,
) -> dict[str, Any]:
    attempts = []
    for batch_size in [initial_batch_size, 2, 1]:
        if adapter_dir.exists():
            shutil.rmtree(adapter_dir)
        config = write_blitz_config(
            dataset_path=dataset_path,
            config_path=config_path,
            final_name=final_name,
            batch_size=batch_size,
            epochs=epochs,
            learning_rate=learning_rate,
            use_flash_attention=use_flash_attention,
        )
        completed = run(
            [
                sys.executable,
                str(ROOT / "fiorellia" / "training" / "train_lora_behavior_v1.py"),
                "--config",
                str(config_path),
                "--dataset-path",
                str(dataset_path),
                "--output-dir",
                str(adapter_dir),
            ],
            check=False,
        )
        attempts.append({"batch_size": batch_size, "returncode": completed.returncode, "config": str(config_path)})
        if completed.returncode == 0:
            write_json({"ok": True, "attempts": attempts, "training_config": config}, artifact_dir / "blitz_training_attempts.json")
            return {"ok": True, "attempts": attempts, "training_config": config}
    write_json({"ok": False, "attempts": attempts}, artifact_dir / "blitz_training_attempts.json")
    raise RuntimeError(f"BLOCCANTE: Blitz training failed after retries: {attempts}")


def restore_adapter_from_zip(adapter_dir: Path, candidates: list[Path]) -> dict[str, Any]:
    if adapter_dir.exists():
        return {"restored": False, "reason": "adapter_dir_exists", "adapter_dir": str(adapter_dir)}
    for candidate in candidates:
        if not candidate.exists():
            continue
        adapter_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(candidate) as zf:
            corrupt = zf.testzip()
            if corrupt:
                shutil.rmtree(adapter_dir, ignore_errors=True)
                raise RuntimeError(f"BLOCCANTE: adapter zip corrotto: {candidate} member={corrupt}")
            zf.extractall(adapter_dir)
        try:
            validate_adapter_dir(adapter_dir)
        except RuntimeError:
            nested = [
                path
                for path in adapter_dir.iterdir()
                if path.is_dir() and (path / "adapter_config.json").exists()
            ]
            if len(nested) == 1:
                tmp_dir = adapter_dir.with_name(f"{adapter_dir.name}_extract_tmp")
                if tmp_dir.exists():
                    shutil.rmtree(tmp_dir)
                nested[0].rename(tmp_dir)
                shutil.rmtree(adapter_dir)
                tmp_dir.rename(adapter_dir)
            validate_adapter_dir(adapter_dir)
        return {"restored": True, "adapter_dir": str(adapter_dir), "source_zip": str(candidate)}
    raise RuntimeError(
        "BLOCCANTE: adapter locale assente e nessuno ZIP Blitz trovato su Drive. "
        f"Cercati: {[str(path) for path in candidates]}. "
        "Rilancia il Blitz completo senza --reuse-existing-adapter."
    )


def output_diagnostics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    errors = [row for row in rows if row.get("error")]
    empty = [row for row in rows if not str(row.get("model_answer") or "").strip()]
    previews = [
        {
            "id": row.get("id"),
            "category": row.get("category"),
            "error": row.get("error"),
            "answer_preview": str(row.get("model_answer") or "")[:240],
        }
        for row in rows[:5]
    ]
    return {
        "rows": len(rows),
        "error_count": len(errors),
        "empty_answer_count": len(empty),
        "all_empty": bool(rows) and len(empty) == len(rows),
        "all_error": bool(rows) and len(errors) == len(rows),
        "previews": previews,
    }


def run_adapter_eval(
    adapter_dir: Path,
    eval_subset: Path,
    output_path: Path,
    max_new_tokens: int,
    use_flash_attention: bool,
    use_4bit: bool,
) -> list[dict[str, Any]]:
    command = [
        sys.executable,
        str(ROOT / "fiorellia" / "eval" / "prompt_harness_local_adapter.py"),
        "--dataset",
        str(eval_subset),
        "--system-prompt",
        str(SYSTEM_PROMPT),
        "--adapter-path",
        str(adapter_dir),
        "--base-model",
        "Qwen/Qwen2.5-3B-Instruct",
        "--out",
        str(output_path),
        "--max-new-tokens",
        str(max_new_tokens),
        "--attn-implementation",
        "flash_attention_2" if use_flash_attention else "sdpa",
    ]
    if use_4bit:
        command.append("--use-4bit")
    print("+", " ".join(str(part) for part in command))
    completed = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    log_path = output_path.with_suffix(output_path.suffix + ".subprocess.log")
    log_path.write_text(
        "\n".join(
            [
                "$ " + " ".join(str(part) for part in command),
                "",
                "## STDOUT",
                completed.stdout,
                "",
                "## STDERR",
                completed.stderr,
            ]
        ),
        encoding="utf-8",
    )
    if completed.stdout:
        print(completed.stdout[-4000:])
    if completed.stderr:
        print(completed.stderr[-4000:])
    if completed.returncode != 0:
        raise RuntimeError(
            "BLOCCANTE: prompt_harness_local_adapter.py failed. "
            f"returncode={completed.returncode}; log={log_path}; command={' '.join(str(part) for part in command)}"
        )
    return read_jsonl(output_path)


def score_adapter_eval(adapter_rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, Any]]:
    strict_scored, strict_metrics = score_eval_rows(adapter_rows)
    scored_rows, raw_metrics, diagnostics = tolerant_rescore_rows(strict_scored)
    metrics = {name: float(raw_metrics.get(name) or 0.0) for name in BLITZ_THRESHOLDS}
    diagnostics = {**diagnostics, "output_diagnostics": output_diagnostics(adapter_rows)}
    return metrics, scored_rows, {"strict_metrics": strict_metrics, "diagnostics": diagnostics}


def should_retry_eval(metrics: Mapping[str, float], diagnostics: Mapping[str, Any]) -> bool:
    output = diagnostics.get("output_diagnostics") if isinstance(diagnostics, Mapping) else None
    if isinstance(output, Mapping) and (output.get("all_empty") or output.get("all_error")):
        return True
    return all(float(metrics.get(name, 0.0)) == 0.0 for name in BLITZ_THRESHOLDS)


def evaluate_blitz(
    adapter_dir: Path,
    eval_subset: Path,
    artifact_dir: Path,
    max_new_tokens: int,
    use_flash_attention: bool,
    eval_4bit: bool,
) -> tuple[dict[str, float], list[dict[str, Any]], dict[str, Any]]:
    reports_dir = artifact_dir / "reports"
    adapter_eval = reports_dir / "adapter_eval.jsonl"
    attempts = []
    adapter_rows = run_adapter_eval(
        adapter_dir=adapter_dir,
        eval_subset=eval_subset,
        output_path=adapter_eval,
        max_new_tokens=max_new_tokens,
        use_flash_attention=use_flash_attention,
        use_4bit=eval_4bit,
    )
    metrics, scored_rows, eval_info = score_adapter_eval(adapter_rows)
    attempts.append({"path": str(adapter_eval), "eval_4bit": eval_4bit, "flash_attention": use_flash_attention, **eval_info})
    if should_retry_eval(metrics, eval_info["diagnostics"]):
        retry_eval = reports_dir / "adapter_eval_bf16_sdpa_retry.jsonl"
        adapter_rows = run_adapter_eval(
            adapter_dir=adapter_dir,
            eval_subset=eval_subset,
            output_path=retry_eval,
            max_new_tokens=max_new_tokens,
            use_flash_attention=False,
            use_4bit=False,
        )
        metrics, scored_rows, eval_info = score_adapter_eval(adapter_rows)
        adapter_eval = retry_eval
        attempts.append({"path": str(retry_eval), "eval_4bit": False, "flash_attention": False, **eval_info})
    write_jsonl(scored_rows, artifact_dir / "adapter_eval_scored.jsonl")
    write_json(metrics, artifact_dir / "metrics_summary.json")
    write_json(
        {
            "attempts": attempts,
            "blitz_thresholds": BLITZ_THRESHOLDS,
            "full_release_thresholds": FINAL_THRESHOLDS,
            "selected_attempt": attempts[-1],
        },
        artifact_dir / "eval_diagnostics.json",
    )
    return metrics, scored_rows, {"adapter_eval": str(adapter_eval), "attempts": attempts, **eval_info}


def launch_gradio(adapter_dir: Path, artifact_dir: Path, max_new_tokens: int) -> int:
    return run(
        [
            sys.executable,
            str(ROOT / "fiorellia_app_colab.py"),
            "--adapter-path",
            str(adapter_dir),
            "--history",
            str(artifact_dir / "blitz_app_history.jsonl"),
            "--max-new-tokens",
            str(max_new_tokens),
            "--share",
        ],
        check=False,
    ).returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Fiorell.IA Blitz Perfection: fast A100 recovery run.")
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--release-dir", type=Path, default=None)
    parser.add_argument("--final-name", default=FINAL_NAME)
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=0.00003)
    parser.add_argument("--min-grounded-count", type=int, default=96)
    parser.add_argument("--eval-cases", type=int, default=10)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--try-flash-attn-install", action="store_true")
    parser.add_argument("--no-flash-attn", action="store_true")
    parser.add_argument("--eval-4bit", action="store_true")
    parser.add_argument("--no-require-a100", action="store_true")
    parser.add_argument("--skip-app-tests", action="store_true")
    parser.add_argument("--launch-gradio", action="store_true")
    parser.add_argument("--copy-verdict-to-repo", action="store_true")
    parser.add_argument("--reuse-existing-adapter", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mount_drive_if_colab()
    artifact_dir = (args.artifact_dir or default_artifact_dir()).resolve()
    release_dir = (args.release_dir or default_release_dir()).resolve()
    reports_dir = artifact_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    release_dir.mkdir(parents=True, exist_ok=True)
    adapter_dir = Path("/content") / args.final_name if Path("/content").exists() else artifact_dir / args.final_name
    config_path = artifact_dir / "config_lora_behavior_20260527_blitz.yaml"
    eval_subset = artifact_dir / "eval_set_blitz_critical.jsonl"
    adapter_zip = artifact_dir / f"{args.final_name}.zip"

    if (args.install_deps or args.reuse_existing_adapter) and not args.dry_run:
        install_blitz_deps(try_flash_attn=args.try_flash_attn_install and not args.no_flash_attn)
    runtime = (
        {"dry_run": True, "cuda_check": "skipped"}
        if args.dry_run
        else require_a100_runtime(require_a100=not args.no_require_a100)
    )
    write_json(runtime, artifact_dir / "runtime_gpu.json")
    dataset_summary = ensure_gold_dataset(GOLD_DATASET, artifact_dir, min_grounded=args.min_grounded_count)
    eval_rows = select_blitz_eval(EVAL_SET, eval_subset, max_cases=args.eval_cases)
    if args.dry_run:
        config = write_blitz_config(
            dataset_path=GOLD_DATASET,
            config_path=config_path,
            final_name=args.final_name,
            batch_size=args.batch_size,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            use_flash_attention=not args.no_flash_attn,
        )
        preflight = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": True,
            "artifact_dir": str(artifact_dir),
            "release_dir": str(release_dir),
            "dataset_summary": dataset_summary,
            "eval_cases": [row.get("id") for row in eval_rows],
            "config": config,
            "blitz_thresholds": BLITZ_THRESHOLDS,
        }
        write_json(preflight, artifact_dir / "blitz_preflight.json")
        print(json.dumps(preflight, indent=2, ensure_ascii=False))
        return 0
    if args.reuse_existing_adapter:
        restore_info = restore_adapter_from_zip(
            adapter_dir,
            [
                adapter_zip,
                release_dir / f"{args.final_name}.zip",
                artifact_dir / f"{args.final_name}.zip",
            ],
        )
        validate_adapter_dir(adapter_dir)
        training = {
            "ok": True,
            "reused_existing_adapter": True,
            "adapter_dir": str(adapter_dir),
            "restore_info": restore_info,
            "note": "Training skipped by --reuse-existing-adapter; running stabilized Blitz evaluation only.",
        }
        write_json(training, artifact_dir / "blitz_training_attempts.json")
    else:
        training = run_training_blitz(
            dataset_path=GOLD_DATASET,
            config_path=config_path,
            adapter_dir=adapter_dir,
            artifact_dir=artifact_dir,
            final_name=args.final_name,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            initial_batch_size=args.batch_size,
            use_flash_attention=not args.no_flash_attn,
        )
    validate_adapter_dir(adapter_dir)
    zip_adapter(adapter_dir, adapter_zip)
    metrics, scored_rows, eval_info = evaluate_blitz(
        adapter_dir=adapter_dir,
        eval_subset=eval_subset,
        artifact_dir=artifact_dir,
        max_new_tokens=args.max_new_tokens,
        use_flash_attention=not args.no_flash_attn,
        eval_4bit=args.eval_4bit,
    )
    adapter_rows = read_jsonl(Path(eval_info["adapter_eval"]))
    write_comparison(eval_rows, adapter_rows, artifact_dir / "comparison.csv")

    relaxed_checks = {name: metrics[name] >= threshold for name, threshold in BLITZ_THRESHOLDS.items()}
    relaxed_checks["in_scope_grounded"] = metrics["in_scope_grounded"] > BLITZ_THRESHOLDS["in_scope_grounded"]
    full_checks_on_subset = {name: metrics[name] >= threshold for name, threshold in FINAL_THRESHOLDS.items()}
    blitz_metrics_ok = all(relaxed_checks.values())
    app_results: dict[str, Any] = {"skipped": True, "ok": False, "reason": "metrics_not_positive"}
    if blitz_metrics_ok and not args.skip_app_tests:
        app_results = run_app_tests(adapter_dir, artifact_dir)
    elif blitz_metrics_ok and args.skip_app_tests:
        app_results = {"skipped": True, "ok": True, "reason": "skip_app_tests"}

    app_ok = bool(app_results.get("ok"))
    verdict = "GO CON RISERVA" if blitz_metrics_ok and app_ok else "NO-GO"
    full_release_possible = all(full_checks_on_subset.values()) and app_ok
    unlock = write_app_unlock(
        artifact_dir / "app_unlock.json",
        unlocked=verdict == "GO CON RISERVA",
        adapter_dir=adapter_dir,
        artifact_dir=artifact_dir,
        reason="blitz_relaxed_gate_positive" if verdict == "GO CON RISERVA" else "blitz_gate_not_positive",
    )
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "verdict": verdict,
        "not_final_certification": True,
        "reason": "Blitz uses 10-case critical eval and relaxed in_scope threshold; run full Gold certification for GO DEFINITIVO.",
        "metrics": metrics,
        "blitz_thresholds": BLITZ_THRESHOLDS,
        "full_release_thresholds": FINAL_THRESHOLDS,
        "relaxed_checks": relaxed_checks,
        "full_checks_on_subset": full_checks_on_subset,
        "full_release_possible_on_subset": full_release_possible,
        "runtime": runtime,
        "dataset_summary": dataset_summary,
        "eval_cases": [row.get("id") for row in eval_rows],
        "training": training,
        "app_results": app_results,
        "app_unlock": unlock,
        "adapter_dir": str(adapter_dir),
        "adapter_zip": str(adapter_zip),
        "artifact_dir": str(artifact_dir),
        "release_dir": str(release_dir),
        "config": str(config_path),
        "eval_set": str(eval_subset),
        "eval_info": eval_info,
    }
    write_json(summary, artifact_dir / "blitz_summary.json")
    write_master_verdict(artifact_dir / "blitz_verdict.md", summary)
    if args.copy_verdict_to_repo:
        write_master_verdict(ROOT / "fiorellia" / "eval" / "blitz_verdict.md", summary)
        write_json(summary, ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "blitz_summary.json")
    release_manifest = copy_release_artifacts(release_dir, adapter_zip, artifact_dir, certification=summary)
    for name in ["blitz_summary.json", "blitz_verdict.md", "eval_set_blitz_critical.jsonl", "blitz_training_attempts.json"]:
        source = artifact_dir / name
        if source.exists():
            shutil.copy2(source, release_dir / name)
    summary["release_manifest"] = release_manifest
    write_json(summary, artifact_dir / "blitz_summary.json")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if args.launch_gradio and verdict == "GO CON RISERVA":
        return launch_gradio(adapter_dir, artifact_dir, max_new_tokens=args.max_new_tokens)
    return 0 if verdict == "GO CON RISERVA" else 2


if __name__ == "__main__":
    code = main()
    if os.environ.get("FIORELLIA_NOTEBOOK_NO_EXIT") == "1":
        print(f"Fiorell.IA Blitz return_code={code}")
    else:
        raise SystemExit(code)
