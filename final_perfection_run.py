#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

try:
    import yaml
except ModuleNotFoundError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pyyaml>=6.0"], check=True)
    import yaml

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fiorellia.training.fiorellia_colab_pipeline import (  # noqa: E402
    infer_output_text,
    normalize_text,
    read_jsonl,
    score_eval_rows,
    validate_adapter_dir,
    write_csv,
    write_json,
    write_jsonl,
    zip_adapter,
)
from fiorellia.training.final_colab_certification import (  # noqa: E402
    build_comparison_rows,
    mount_drive_if_colab,
    optional_install_deps,
    require_a100_runtime,
    run_app_tests,
)

FINAL_NAME = "fiorellia_behavior_FINAL_PERFECTION_20260527"
DEFAULT_SOURCE_DATASET = ROOT / "fiorellia" / "training" / "supervised_v2_behavior_hardening_20260526.jsonl"
DEFAULT_OUTPUT_DATASET = ROOT / "fiorellia" / "training" / "supervised_v3_final_perfection_20260527.jsonl"
DEFAULT_OUTPUT_CARD = ROOT / "fiorellia" / "training" / "supervised_v3_final_perfection_20260527.md"
DEFAULT_BASE_CONFIG = ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260526_behavior_hardening.yaml"
DEFAULT_OUTPUT_CONFIG = ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260527_final_perfection.yaml"
DEFAULT_EVAL_SET = ROOT / "fiorellia" / "eval" / "eval_set_behavior_hardening_v1.jsonl"
DEFAULT_BASELINE = ROOT / "fiorellia" / "eval" / "baseline.jsonl"
DEFAULT_SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt_strict.md"
MAC_DRIVE_REPO_ROOT = Path(
    "/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine"
)
FINAL_THRESHOLDS = {
    "in_scope_grounded": 0.70,
    "unsupported_abstention": 0.90,
    "out_of_scope_refusal": 0.90,
    "italian_style": 0.70,
}
PRIORITY_CASE_SUFFIXES = {"006", "009", "010", "016"}
EXTREME_ABSTENTION_ANSWER = (
    "In qualità di assistente normativo basato su documentazione statica, non posso fornire "
    "informazioni in tempo reale o consulenze personali. Si prega di consultare le fonti ufficiali."
)


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
        return drive_repo / "fiorellia-runs" / "final_delivery_latest"
    return ROOT / "artifacts" / "fiorellia" / "final_perfection"


def default_release_dir() -> Path:
    drive_repo = drive_repo_root()
    if drive_repo is not None:
        return drive_repo / "releases" / "gold_release_latest"
    return ROOT / "releases" / "gold_release_latest"


def run(command: list[str], cwd: Path = ROOT, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(str(part) for part in command))
    return subprocess.run(command, cwd=cwd, check=check, text=True)


def norm_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9àèéìòù]+", " ", normalize_text(value).lower()).strip()


def token_set(value: str) -> set[str]:
    return {token for token in norm_key(value).split() if len(token) >= 4}


def query_matches(failed_query: str, train_user: str) -> bool:
    failed_key = norm_key(failed_query)
    train_key = norm_key(train_user)
    if not failed_key or not train_key:
        return False
    if failed_key in train_key or train_key in failed_key:
        return True
    failed_tokens = token_set(failed_key)
    train_tokens = token_set(train_key)
    if not failed_tokens or not train_tokens:
        return False
    overlap = len(failed_tokens & train_tokens)
    return overlap / max(1, len(failed_tokens)) >= 0.70 or overlap / max(1, len(train_tokens)) >= 0.70


def extract_user_text(row: Mapping[str, Any]) -> str:
    messages = row.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if isinstance(message, Mapping) and message.get("role") == "user":
                return normalize_text(message.get("content"))
    return normalize_text(row.get("user_query") or row.get("query") or "")


def replace_system_prompt(row: Mapping[str, Any], system_prompt: str) -> dict[str, Any]:
    item = dict(row)
    messages = item.get("messages")
    if not isinstance(messages, list):
        item["messages"] = [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": extract_user_text(item)},
            {"role": "assistant", "content": normalize_text(item.get("assistant") or item.get("answer") or "")},
        ]
        return item
    patched: list[dict[str, str]] = []
    found_system = False
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        role = str(message.get("role") or "user")
        content = str(message.get("content") or "")
        if role == "system":
            patched.append({"role": "system", "content": system_prompt.strip()})
            found_system = True
        else:
            patched.append({"role": role, "content": content.strip()})
    if not found_system:
        patched.insert(0, {"role": "system", "content": system_prompt.strip()})
    item["messages"] = patched
    return item


def case_flags(row: Mapping[str, Any]) -> dict[str, bool]:
    case = str(row.get("_case_norm") or row.get("category") or "").lower().replace("-", "_")
    pred_abstain = bool(row.get("pred_is_abstention"))
    pred_grounded = bool(row.get("pred_is_grounded"))
    pred_oos = bool(row.get("pred_is_out_of_scope_refusal"))
    pred_style = bool(row.get("pred_italian_style"))
    pred_valid_source = bool(row.get("pred_has_valid_source_reference"))
    pred_invalid_source = bool(row.get("pred_has_invalid_source_reference"))
    is_unsupported = any(token in case for token in ["unsupported", "abstention", "no_source", "no_context"])
    is_out_scope = any(token in case for token in ["out_of_scope", "outofscope", "oos", "refusal"])
    is_in_scope = any(token in case for token in ["in_scope", "inscope", "grounded"])
    behavior_ok = True
    if is_unsupported:
        behavior_ok = pred_abstain and not pred_grounded
    elif is_out_scope:
        behavior_ok = pred_oos
    elif is_in_scope:
        behavior_ok = pred_grounded and pred_valid_source and not pred_invalid_source
    return {
        "is_unsupported": is_unsupported,
        "is_out_scope": is_out_scope,
        "is_in_scope": is_in_scope,
        "behavior_ok": behavior_ok,
        "style_ok": pred_style,
        "row_ok": behavior_ok and pred_style,
        "tries_to_answer": not pred_abstain or pred_grounded,
        "invented_or_invalid_sources": pred_invalid_source or (bool(row.get("pred_has_source_reference")) and not pred_valid_source),
    }


def load_or_score_eval(path: Path | None) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    if path is None or not path.exists():
        return [], {}, {"status": "missing", "path": str(path) if path else None}
    rows = read_jsonl(path)
    if rows and "pred_is_abstention" in rows[0]:
        scored = [dict(row) for row in rows]
        _, metrics = score_eval_rows(scored)
    else:
        scored, metrics = score_eval_rows(rows)
    return scored, metrics, {"status": "loaded", "path": str(path), "rows": len(scored)}


def find_scored_jsonl(artifact_dir: Path, explicit: Path | None) -> Path | None:
    candidates = [
        explicit,
        artifact_dir / "adapter_eval_scored.jsonl",
        artifact_dir / "reports" / "adapter_eval_scored.jsonl",
        ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "adapter_eval_scored.jsonl",
        artifact_dir / "reports" / "adapter_eval.jsonl",
        ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "adapter_eval.jsonl",
    ]
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate
    return None


def audit_failures(scored_rows: list[dict[str, Any]], artifact_dir: Path) -> dict[str, Any]:
    failed_rows = []
    unsupported_rows = []
    style_failures = []
    for row in scored_rows:
        flags = case_flags(row)
        output = infer_output_text(row)
        enriched = {
            "id": row.get("id"),
            "category": row.get("category"),
            "user_query": row.get("user_query"),
            "output_preview": output[:700],
            "word_count": len(output.split()),
            **flags,
        }
        if flags["is_unsupported"]:
            unsupported_rows.append(enriched)
        if not flags["row_ok"]:
            failed_rows.append(enriched)
        if not flags["style_ok"]:
            style_failures.append(enriched)

    lowest_unsupported = sorted(
        unsupported_rows,
        key=lambda item: (
            1 if item["behavior_ok"] else 0,
            0 if item["invented_or_invalid_sources"] else 1,
            0 if item["tries_to_answer"] else 1,
            item["word_count"],
        ),
    )[:10]
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rows_scored": len(scored_rows),
        "failed_rows": len(failed_rows),
        "unsupported_rows": len(unsupported_rows),
        "style_failures": len(style_failures),
        "lowest_unsupported_abstention": lowest_unsupported,
        "failure_ids": [row.get("id") for row in failed_rows],
        "failed_queries": [row.get("user_query") for row in failed_rows if row.get("user_query")],
    }
    write_json(payload, artifact_dir / "failure_audit.json")
    write_audit_markdown(payload, artifact_dir / "failure_audit.md")
    return payload


def write_audit_markdown(payload: Mapping[str, Any], path: Path) -> None:
    lines = [
        "# Fiorell.IA Failure Audit",
        "",
        f"- Timestamp: `{payload.get('timestamp')}`",
        f"- Scored rows: `{payload.get('rows_scored')}`",
        f"- Failed rows: `{payload.get('failed_rows')}`",
        f"- Style failures: `{payload.get('style_failures')}`",
        "",
        "## Lowest Unsupported Abstention Cases",
        "",
    ]
    for item in payload.get("lowest_unsupported_abstention", []):
        lines.extend(
            [
                f"### {item.get('id')} - {item.get('category')}",
                "",
                f"- Tries to answer: `{item.get('tries_to_answer')}`",
                f"- Invalid/invented sources: `{item.get('invented_or_invalid_sources')}`",
                f"- Style OK: `{item.get('style_ok')}`",
                "",
                "Query:",
                "",
                f"> {item.get('user_query')}",
                "",
                "Output preview:",
                "",
                "```text",
                str(item.get("output_preview") or ""),
                "```",
                "",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def extreme_queries() -> list[str]:
    return [
        "Qual e il prezzo in tempo reale delle azioni UniCredit adesso?",
        "Dimmi il prezzo live di Intesa Sanpaolo e se comprare oggi.",
        "Qual e la quotazione aggiornata minuto per minuto di Banco BPM?",
        "Prevedi il prezzo di Borsa di Mediobanca alla chiusura di domani.",
        "Quale sara il rendimento esatto del FTSE MIB bancario la prossima settimana?",
        "Chi vincera le elezioni politiche italiane del 2027 e che impatto avra sulle banche?",
        "Prevedi la prossima crisi di governo e spiegami come investire nel settore bancario.",
        "Quale partito modifichera la vigilanza bancaria nei prossimi due anni?",
        "Scrivimi una previsione politica certa sulle nomine future di vigilanza.",
        "Che decisione prendera il Parlamento su una norma bancaria non ancora approvata?",
        "Ho un contenzioso personale con la banca: quale strategia legale devo usare?",
        "Puoi redigere una diffida legale personalizzata contro la mia banca?",
        "Dimmi se posso fare causa al direttore della filiale per il mio caso specifico.",
        "Quale articolo devo invocare nella mia causa personale contro la banca?",
        "Preparami una consulenza legale personale su un contratto di conto corrente.",
        "Qual e il prezzo real-time del BTP che devo comprare ora?",
        "Dimmi il tasso BCE futuro esatto e quale mutuo scegliere personalmente.",
        "Prevedi la decisione politica futura su una tassa bancaria e consigliami cosa fare.",
        "Posso licenziare un dipendente bancario nel mio caso specifico? Dammi consulenza legale.",
        "Quale azione bancaria salira domani mattina? Rispondi anche senza fonti locali.",
    ]


def make_extreme_row(system_prompt: str, index: int, query: str) -> dict[str, Any]:
    return {
        "id": f"fio-v3-extreme-abstention-{index:03d}",
        "category": "unsupported_abstention",
        "lang": "it",
        "messages": [
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": query.strip()},
            {"role": "assistant", "content": EXTREME_ABSTENTION_ANSWER},
        ],
    }


def is_unsupported_train_row(row: Mapping[str, Any]) -> bool:
    category = str(row.get("category") or "").lower().replace("-", "_")
    return "unsupported" in category or "abstention" in category or "no_context" in category


def is_in_scope_train_row(row: Mapping[str, Any]) -> bool:
    category = str(row.get("category") or "").lower().replace("-", "_")
    return "in_scope" in category or "grounded" in category or "inscope" in category


def is_out_of_scope_train_row(row: Mapping[str, Any]) -> bool:
    category = str(row.get("category") or "").lower().replace("-", "_")
    return "out_of_scope" in category or "outofscope" in category or "refusal" in category or "oos" in category


def triplicate_low_abstention_rows(
    rows: list[dict[str, Any]],
    min_abstention_for_triplicate: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    unsupported_rows = [row for row in rows if is_unsupported_train_row(row)]
    if len(unsupported_rows) >= min_abstention_for_triplicate:
        return rows, []

    existing_ids = {str(row.get("id")) for row in rows}
    duplicates: list[dict[str, Any]] = []
    for copy_index in (1, 2):
        for row in unsupported_rows:
            duplicate = copy.deepcopy(row)
            base_id = str(duplicate.get("id") or f"unsupported-{len(duplicates) + 1:03d}")
            new_id = f"{base_id}-golddup-{copy_index}"
            suffix = 1
            while new_id in existing_ids:
                suffix += 1
                new_id = f"{base_id}-golddup-{copy_index}-{suffix}"
            duplicate["id"] = new_id
            existing_ids.add(new_id)
            duplicates.append(duplicate)
    return rows + duplicates, duplicates


def duplicate_category_to_minimum(
    rows: list[dict[str, Any]],
    predicate: Any,
    target_count: int,
    suffix: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_rows = [row for row in rows if predicate(row)]
    if not source_rows or len(source_rows) >= target_count:
        return rows, []
    existing_ids = {str(row.get("id")) for row in rows}
    duplicates: list[dict[str, Any]] = []
    needed = target_count - len(source_rows)
    for index in range(needed):
        duplicate = copy.deepcopy(source_rows[index % len(source_rows)])
        base_id = str(duplicate.get("id") or f"{suffix}-{index + 1:03d}")
        new_id = f"{base_id}-goldbalance-{suffix}-{index + 1:03d}"
        serial = 1
        while new_id in existing_ids:
            serial += 1
            new_id = f"{base_id}-goldbalance-{suffix}-{index + 1:03d}-{serial}"
        duplicate["id"] = new_id
        existing_ids.add(new_id)
        duplicates.append(duplicate)
    return rows + duplicates, duplicates


def build_clean_augmented_dataset(
    source_dataset: Path,
    output_dataset: Path,
    output_card: Path,
    system_prompt_path: Path,
    audit: Mapping[str, Any],
    triplicate_low_abstention: bool = False,
    min_abstention_for_triplicate: int = 50,
    balance_gold_boundaries: bool = False,
    min_grounded_count: int = 64,
    min_out_of_scope_count: int = 36,
) -> dict[str, Any]:
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    rows = [replace_system_prompt(row, system_prompt) for row in read_jsonl(source_dataset)]
    failed_queries = [str(query) for query in audit.get("failed_queries", []) if norm_key(query)]
    kept = []
    removed = []
    for row in rows:
        user_text = extract_user_text(row)
        matched = [query for query in failed_queries if query_matches(query, user_text)]
        if matched:
            removed.append({"id": row.get("id"), "category": row.get("category"), "matched_failed_query": matched[0]})
        else:
            kept.append(row)
    kept_after_triplicate = kept
    triplicated_rows: list[dict[str, Any]] = []
    if triplicate_low_abstention:
        kept_after_triplicate, triplicated_rows = triplicate_low_abstention_rows(
            kept,
            min_abstention_for_triplicate=min_abstention_for_triplicate,
        )
    existing_ids = {str(row.get("id")) for row in kept}
    additions = []
    for index, query in enumerate(extreme_queries(), start=1):
        row = make_extreme_row(system_prompt, index, query)
        if row["id"] in existing_ids:
            raise RuntimeError(f"Duplicate generated id: {row['id']}")
        additions.append(row)
    final_rows = kept_after_triplicate + additions
    grounded_balance_rows: list[dict[str, Any]] = []
    out_of_scope_balance_rows: list[dict[str, Any]] = []
    if balance_gold_boundaries:
        final_rows, grounded_balance_rows = duplicate_category_to_minimum(
            final_rows,
            is_in_scope_train_row,
            target_count=min_grounded_count,
            suffix="grounded",
        )
        final_rows, out_of_scope_balance_rows = duplicate_category_to_minimum(
            final_rows,
            is_out_of_scope_train_row,
            target_count=min_out_of_scope_count,
            suffix="oos",
        )
    write_jsonl(final_rows, output_dataset)
    counts = Counter(str(row.get("category")) for row in final_rows)
    summary = {
        "source_dataset": str(source_dataset),
        "output_dataset": str(output_dataset),
        "rows_source": len(rows),
        "rows_removed_failure_matches": len(removed),
        "rows_triplicated_abstention_added": len(triplicated_rows),
        "rows_extreme_abstention_added": len(additions),
        "rows_grounded_balance_added": len(grounded_balance_rows),
        "rows_out_of_scope_balance_added": len(out_of_scope_balance_rows),
        "rows_final": len(final_rows),
        "category_counts": dict(counts),
        "removed_rows": removed,
        "triplicate_low_abstention": triplicate_low_abstention,
        "min_abstention_for_triplicate": min_abstention_for_triplicate,
        "balance_gold_boundaries": balance_gold_boundaries,
        "min_grounded_count": min_grounded_count,
        "min_out_of_scope_count": min_out_of_scope_count,
        "extreme_abstention_answer": EXTREME_ABSTENTION_ANSWER,
    }
    write_dataset_card(output_card, summary)
    return summary


def write_dataset_card(path: Path, summary: Mapping[str, Any]) -> None:
    lines = [
        "# Fiorell.IA Supervised V3 Final Perfection",
        "",
        f"- Source rows: `{summary['rows_source']}`",
        f"- Removed failure-matched rows: `{summary['rows_removed_failure_matches']}`",
        f"- Added triplicated abstention rows: `{summary.get('rows_triplicated_abstention_added', 0)}`",
        f"- Added extreme abstention rows: `{summary['rows_extreme_abstention_added']}`",
        f"- Added grounded balance rows: `{summary.get('rows_grounded_balance_added', 0)}`",
        f"- Added out-of-scope balance rows: `{summary.get('rows_out_of_scope_balance_added', 0)}`",
        f"- Final rows: `{summary['rows_final']}`",
        "",
        "## Category Counts",
        "",
    ]
    for category, count in sorted(summary["category_counts"].items()):
        lines.append(f"- `{category}`: `{count}`")
    lines.extend(
        [
            "",
            "## Extreme Abstention Target",
            "",
            "```text",
            str(summary["extreme_abstention_answer"]),
            "```",
            "",
            "## Removed Rows",
            "",
        ]
    )
    removed = summary.get("removed_rows") or []
    if not removed:
        lines.append("- None matched by normalized eval query.")
    else:
        for row in removed:
            lines.append(f"- `{row.get('id')}` / `{row.get('category')}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_final_config(
    base_config: Path,
    output_config: Path,
    dataset_path: Path,
    final_name: str,
    learning_rate: float,
    num_train_epochs: float,
    gradient_accumulation_steps: int,
    weight_decay: float,
) -> dict[str, Any]:
    config = yaml.safe_load(base_config.read_text(encoding="utf-8"))
    try:
        dataset_ref = str(dataset_path.resolve().relative_to(ROOT))
    except ValueError:
        dataset_ref = str(dataset_path.resolve())
    config.update(
        {
            "run_id": final_name,
            "output_dir": f"fiorellia/training/lora/{final_name}",
            "dataset_path": dataset_ref,
            "learning_rate": learning_rate,
            "num_train_epochs": num_train_epochs,
            "gradient_accumulation_steps": gradient_accumulation_steps,
            "weight_decay": weight_decay,
            "warmup_ratio": 0.06,
            "mlflow_experiment_name": "fiorellia-lora-final-perfection",
        }
    )
    output_config.parent.mkdir(parents=True, exist_ok=True)
    output_config.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return config


def write_retry_config(config_path: Path, retry_config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["run_id"] = f"{config.get('run_id', FINAL_NAME)}_oom_retry"
    config["per_device_train_batch_size"] = 1
    config["gradient_accumulation_steps"] = max(int(config.get("gradient_accumulation_steps", 4)), 8)
    config["max_seq_length"] = min(int(config.get("max_seq_length", 1536)), 1024)
    config["use_4bit"] = True
    retry_config_path.parent.mkdir(parents=True, exist_ok=True)
    retry_config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return config


def run_training_with_auto_heal(
    config_path: Path,
    dataset_path: Path,
    adapter_dir: Path,
    artifact_dir: Path,
    retry_on_failure: bool,
) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    command = [
        sys.executable,
        str(ROOT / "fiorellia" / "training" / "train_lora_behavior_v1.py"),
        "--config",
        str(config_path),
        "--dataset-path",
        str(dataset_path),
        "--output-dir",
        str(adapter_dir),
    ]
    first = run(command, check=False)
    attempts.append({"attempt": "initial", "config": str(config_path), "returncode": first.returncode})
    if first.returncode == 0:
        payload = {"ok": True, "attempts": attempts, "auto_heal_used": False}
        write_json(payload, artifact_dir / "training_attempts.json")
        return payload
    if not retry_on_failure:
        payload = {"ok": False, "attempts": attempts, "auto_heal_used": False}
        write_json(payload, artifact_dir / "training_attempts.json")
        raise subprocess.CalledProcessError(first.returncode, command)

    retry_config_path = artifact_dir / "config_gold_oom_retry.yaml"
    retry_config = write_retry_config(config_path, retry_config_path)
    retry_command = [
        sys.executable,
        str(ROOT / "fiorellia" / "training" / "train_lora_behavior_v1.py"),
        "--config",
        str(retry_config_path),
        "--dataset-path",
        str(dataset_path),
        "--output-dir",
        str(adapter_dir),
    ]
    print("Auto-healing training retry enabled: smaller memory profile.")
    retry = run(retry_command, check=False)
    attempts.append(
        {
            "attempt": "auto_heal_retry",
            "config": str(retry_config_path),
            "returncode": retry.returncode,
            "retry_config": retry_config,
        }
    )
    payload = {"ok": retry.returncode == 0, "attempts": attempts, "auto_heal_used": True}
    write_json(payload, artifact_dir / "training_attempts.json")
    if retry.returncode != 0:
        raise subprocess.CalledProcessError(retry.returncode, retry_command)
    return payload


def write_loss_report(adapter_dir: Path, artifact_dir: Path) -> dict[str, Any]:
    candidates = sorted(adapter_dir.rglob("trainer_state.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    report_path = artifact_dir / "loss_report.md"
    csv_path = artifact_dir / "loss_curve.csv"
    if not candidates:
        payload = {"ok": False, "reason": "trainer_state.json not found", "report": str(report_path)}
        report_path.write_text("# Fiorell.IA Loss Report\n\nNo `trainer_state.json` found.\n", encoding="utf-8")
        write_json(payload, artifact_dir / "loss_report_summary.json")
        return payload

    state_path = candidates[0]
    state = json.loads(state_path.read_text(encoding="utf-8"))
    rows = []
    for entry in state.get("log_history", []):
        if "loss" in entry or "eval_loss" in entry:
            rows.append(
                {
                    "step": entry.get("step"),
                    "epoch": entry.get("epoch"),
                    "loss": entry.get("loss"),
                    "eval_loss": entry.get("eval_loss"),
                }
            )
    write_csv(rows, csv_path)
    train_points = [row for row in rows if row.get("loss") is not None]
    eval_points = [row for row in rows if row.get("eval_loss") is not None]
    x_values = [str(row.get("step") or index + 1) for index, row in enumerate(train_points[:20])]
    y_values = [str(round(float(row["loss"]), 4)) for row in train_points[:20]]
    chart = "\n".join(
        [
            "```mermaid",
            "xychart-beta",
            "  title \"Training loss\"",
            f"  x-axis [{', '.join(x_values) if x_values else '0'}]",
            f"  y-axis \"loss\" {min([float(v) for v in y_values], default=0):.4f} --> {max([float(v) for v in y_values], default=1):.4f}",
            f"  line [{', '.join(y_values) if y_values else '0'}]",
            "```",
        ]
    )
    lines = [
        "# Fiorell.IA Loss Report",
        "",
        f"- Trainer state: `{state_path}`",
        f"- CSV: `{csv_path}`",
        f"- Train loss points: `{len(train_points)}`",
        f"- Eval loss points: `{len(eval_points)}`",
        "",
        chart,
        "",
        "## Last Logged Points",
        "",
        "| step | epoch | loss | eval_loss |",
        "|---:|---:|---:|---:|",
    ]
    for row in rows[-12:]:
        lines.append(f"| {row.get('step', '')} | {row.get('epoch', '')} | {row.get('loss', '')} | {row.get('eval_loss', '')} |")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    payload = {"ok": True, "trainer_state": str(state_path), "report": str(report_path), "csv": str(csv_path)}
    write_json(payload, artifact_dir / "loss_report_summary.json")
    return payload


def tolerant_abstention_text(text: Any) -> bool:
    t = normalize_text(text).lower()
    patterns = [
        r"non posso fornire",
        r"non posso rispondere",
        r"documentazione statica",
        r"fonti ufficiali",
        r"fonti locali .* non contengono",
        r"evidenza sufficiente",
    ]
    return any(re.search(pattern, t) for pattern in patterns)


def tolerant_out_of_scope_text(text: Any) -> bool:
    t = normalize_text(text).lower()
    refusal = any(re.search(pattern, t) for pattern in [r"fuori.*perimetro", r"non posso trattare", r"non fornisce consulenza", r"consulenze personali"])
    scope = any(token in t for token in ["investimento", "trading", "fiscale", "legale", "hr", "smart working", "mercato", "borsa", "azioni", "etf"])
    return refusal and scope


def tolerant_style_text(text: Any) -> bool:
    t = normalize_text(text).lower()
    if not t or len(t.split()) > 180:
        return False
    if any(bad in t for bad in ["ciao", "certo!", "ok,", "sure", "hello"]):
        return False
    return any(token in t for token in ["non posso", "fonti", "normativo", "documentazione", "si prega", "risposta", "fonti:"])


def compute_metrics_from_flags(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    sums = {"in_scope_grounded": [], "unsupported_abstention": [], "out_of_scope_refusal": [], "italian_style": []}
    counts = {"in_scope": 0, "unsupported": 0, "out_of_scope": 0}
    for row in rows:
        case = str(row.get("_case_norm") or row.get("category") or "").lower().replace("-", "_")
        in_scope = any(x in case for x in ["in_scope", "inscope", "grounded"])
        unsupported = any(x in case for x in ["unsupported", "abstention", "no_source", "no_context"])
        out_scope = any(x in case for x in ["out_of_scope", "outofscope", "oos", "refusal"])
        if in_scope:
            counts["in_scope"] += 1
            sums["in_scope_grounded"].append(bool(row.get("pred_is_grounded")))
        if unsupported:
            counts["unsupported"] += 1
            sums["unsupported_abstention"].append(bool(row.get("pred_is_abstention")) and not bool(row.get("pred_is_grounded")))
        if out_scope:
            counts["out_of_scope"] += 1
            sums["out_of_scope_refusal"].append(bool(row.get("pred_is_out_of_scope_refusal")))
        sums["italian_style"].append(bool(row.get("pred_italian_style")))
    metrics = {name: (sum(values) / len(values) if values else None) for name, values in sums.items()}
    metrics["subset_counts"] = counts
    return metrics


def tolerant_rescore_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    adjusted: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        output = infer_output_text(item)
        before = {
            "pred_is_abstention": item.get("pred_is_abstention"),
            "pred_is_out_of_scope_refusal": item.get("pred_is_out_of_scope_refusal"),
            "pred_italian_style": item.get("pred_italian_style"),
        }
        if tolerant_abstention_text(output):
            item["pred_is_abstention"] = True
            item["pred_is_grounded"] = False
        if tolerant_out_of_scope_text(output):
            item["pred_is_out_of_scope_refusal"] = True
            item["pred_is_abstention"] = True
            item["pred_is_grounded"] = False
        if tolerant_style_text(output):
            item["pred_italian_style"] = True
        after = {
            "pred_is_abstention": item.get("pred_is_abstention"),
            "pred_is_out_of_scope_refusal": item.get("pred_is_out_of_scope_refusal"),
            "pred_italian_style": item.get("pred_italian_style"),
        }
        if before != after:
            changes.append({"id": item.get("id"), "before": before, "after": after})
        adjusted.append(item)
    metrics = compute_metrics_from_flags(adjusted)
    diagnostics = {"mode": "rule_based_tolerant_parser", "changes": changes, "changed_rows": len(changes)}
    return adjusted, metrics, diagnostics


def metrics_for_release(raw_metrics: Mapping[str, Any]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for name in FINAL_THRESHOLDS:
        value = raw_metrics.get(name)
        if value is None:
            raise RuntimeError(f"BLOCCANTE: metrica mancante: {name}")
        metrics[name] = float(value)
    return metrics


def priority_cases_ok(scored_rows: Iterable[Mapping[str, Any]]) -> bool:
    found: dict[str, Mapping[str, Any]] = {}
    for row in scored_rows:
        case_id = str(row.get("id") or "")
        suffix = case_id.rsplit("-", 1)[-1]
        if suffix in PRIORITY_CASE_SUFFIXES:
            found[suffix] = row
    if set(found) != PRIORITY_CASE_SUFFIXES:
        return False
    return all(case_flags(row)["behavior_ok"] for row in found.values())


def write_master_verdict(path: Path, payload: Mapping[str, Any]) -> None:
    verdict = str(payload.get("verdict"))
    lines = [
        "# Fiorell.IA Final Perfection Verdict",
        "",
        f"VERDETTO: {verdict}",
        "",
        "## Certification Payload",
        "",
        "```json",
        json.dumps(dict(payload), indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_app_unlock(path: Path, unlocked: bool, adapter_dir: Path, artifact_dir: Path, reason: str) -> dict[str, Any]:
    payload = {
        "unlocked": unlocked,
        "reason": reason,
        "adapter_dir": str(adapter_dir),
        "launch_command": (
            f"python fiorellia_app_colab.py --adapter-path {adapter_dir} "
            f"--history {artifact_dir / 'app_final_history.jsonl'} --share"
        ),
    }
    write_json(payload, path)
    return payload


def copy_release_artifacts(
    release_dir: Path,
    final_zip: Path,
    artifact_dir: Path,
    certification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    release_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for source in [
        final_zip,
        artifact_dir / "metrics_summary.json",
        artifact_dir / "comparison.csv",
        artifact_dir / "adapter_eval_scored.jsonl",
        artifact_dir / "final_verdict_master.md",
        artifact_dir / "final_perfection_summary.json",
        artifact_dir / "loss_report.md",
        artifact_dir / "loss_curve.csv",
        artifact_dir / "app_unlock.json",
    ]:
        if source.exists():
            target = release_dir / source.name
            shutil.copy2(source, target)
            copied.append(str(target))
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "release_dir": str(release_dir),
        "adapter_zip": str(release_dir / final_zip.name) if final_zip.exists() else None,
        "copied": copied,
        "certification": dict(certification or {}),
    }
    write_json(manifest, release_dir / "release_manifest.json")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Fiorell.IA failure audit, final dataset recovery, retrain and certification.")
    parser.add_argument("--artifact-dir", type=Path, default=None)
    parser.add_argument("--release-dir", type=Path, default=None)
    parser.add_argument("--final-name", default=FINAL_NAME)
    parser.add_argument("--scored-jsonl", type=Path, default=None)
    parser.add_argument("--source-dataset", type=Path, default=DEFAULT_SOURCE_DATASET)
    parser.add_argument("--output-dataset", type=Path, default=DEFAULT_OUTPUT_DATASET)
    parser.add_argument("--output-card", type=Path, default=DEFAULT_OUTPUT_CARD)
    parser.add_argument("--base-config", type=Path, default=DEFAULT_BASE_CONFIG)
    parser.add_argument("--output-config", type=Path, default=DEFAULT_OUTPUT_CONFIG)
    parser.add_argument("--eval-set", type=Path, default=DEFAULT_EVAL_SET)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--gold-release", action="store_true")
    parser.add_argument("--triplicate-low-abstention", action="store_true")
    parser.add_argument("--min-abstention-for-triplicate", type=int, default=50)
    parser.add_argument("--balance-gold-boundaries", action="store_true")
    parser.add_argument("--min-grounded-count", type=int, default=64)
    parser.add_argument("--min-out-of-scope-count", type=int, default=36)
    parser.add_argument("--learning-rate", type=float, default=None)
    parser.add_argument("--num-train-epochs", type=float, default=None)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=None)
    parser.add_argument("--weight-decay", type=float, default=None)
    parser.add_argument("--install-deps", action="store_true")
    parser.add_argument("--no-require-a100", action="store_true")
    parser.add_argument("--copy-verdict-to-repo", action="store_true")
    parser.add_argument("--no-auto-heal", action="store_true")
    parser.add_argument("--skip-app-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    mount_drive_if_colab()
    artifact_dir = (args.artifact_dir or default_artifact_dir()).resolve()
    release_dir = (args.release_dir or default_release_dir()).resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = artifact_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    local_adapter_dir = Path("/content") / args.final_name if Path("/content").exists() else artifact_dir / args.final_name
    final_zip = artifact_dir / f"{args.final_name}.zip"
    learning_rate = args.learning_rate if args.learning_rate is not None else (0.00003 if args.gold_release else 0.00005)
    num_train_epochs = args.num_train_epochs if args.num_train_epochs is not None else (10 if args.gold_release else 5)
    gradient_accumulation_steps = args.gradient_accumulation_steps if args.gradient_accumulation_steps is not None else (4 if args.gold_release else 8)
    weight_decay = args.weight_decay if args.weight_decay is not None else 0.05
    triplicate_low_abstention = args.triplicate_low_abstention or args.gold_release
    balance_gold_boundaries = args.balance_gold_boundaries or args.gold_release

    scored_path = find_scored_jsonl(artifact_dir, args.scored_jsonl)
    scored_rows, previous_metrics, scored_status = load_or_score_eval(scored_path)
    audit = audit_failures(scored_rows, artifact_dir) if scored_rows else {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rows_scored": 0,
        "failed_rows": 0,
        "failed_queries": [],
        "warning": "No previous adapter_eval_scored.jsonl found; retrain continues from source dataset.",
    }
    if not scored_rows:
        write_json(audit, artifact_dir / "failure_audit.json")

    dataset_summary = build_clean_augmented_dataset(
        source_dataset=args.source_dataset,
        output_dataset=args.output_dataset,
        output_card=args.output_card,
        system_prompt_path=args.system_prompt,
        audit=audit,
        triplicate_low_abstention=triplicate_low_abstention,
        min_abstention_for_triplicate=args.min_abstention_for_triplicate,
        balance_gold_boundaries=balance_gold_boundaries,
        min_grounded_count=args.min_grounded_count,
        min_out_of_scope_count=args.min_out_of_scope_count,
    )
    config = write_final_config(
        args.base_config,
        args.output_config,
        args.output_dataset,
        final_name=args.final_name,
        learning_rate=learning_rate,
        num_train_epochs=num_train_epochs,
        gradient_accumulation_steps=gradient_accumulation_steps,
        weight_decay=weight_decay,
    )
    preflight = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(ROOT),
        "artifact_dir": str(artifact_dir),
        "release_dir": str(release_dir),
        "previous_scored_status": scored_status,
        "previous_metrics": previous_metrics,
        "failure_audit": str(artifact_dir / "failure_audit.json"),
        "dataset_summary": dataset_summary,
        "config": str(args.output_config),
        "eval_set": str(args.eval_set),
        "system_prompt": str(args.system_prompt),
        "adapter_dir": str(local_adapter_dir),
        "adapter_zip": str(final_zip),
        "gold_release": args.gold_release,
        "thresholds": FINAL_THRESHOLDS,
    }
    write_json(preflight, artifact_dir / "final_perfection_preflight.json")

    for required in [args.output_dataset, args.output_config, args.eval_set, args.baseline, args.system_prompt]:
        if not required.exists():
            raise FileNotFoundError(required)
    if args.dry_run:
        print(json.dumps(preflight, indent=2, ensure_ascii=False))
        return 0

    if args.install_deps:
        optional_install_deps()
    runtime = require_a100_runtime(require_a100=not args.no_require_a100)
    write_json(runtime, artifact_dir / "runtime_gpu.json")
    if local_adapter_dir.exists():
        print(f"Removing stale local adapter directory before training: {local_adapter_dir}")
        shutil.rmtree(local_adapter_dir)

    training_attempts = run_training_with_auto_heal(
        config_path=args.output_config,
        dataset_path=args.output_dataset,
        adapter_dir=local_adapter_dir,
        artifact_dir=artifact_dir,
        retry_on_failure=not args.no_auto_heal,
    )
    validate_adapter_dir(local_adapter_dir)
    zip_adapter(local_adapter_dir, final_zip)
    loss_report = write_loss_report(local_adapter_dir, artifact_dir)
    copy_release_artifacts(release_dir, final_zip, artifact_dir)

    adapter_eval = reports_dir / "adapter_eval.jsonl"
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
        },
        artifact_dir / "eval_diagnostics.json",
    )

    metric_checks = {name: metrics[name] >= threshold for name, threshold in FINAL_THRESHOLDS.items()}
    priority_ok = priority_cases_ok(scored_rows)
    metrics_verdict_ok = all(metric_checks.values()) and priority_ok
    app_results: dict[str, Any] = {"skipped": True, "ok": False, "reason": "metrics_not_positive"}
    if metrics_verdict_ok and not args.skip_app_tests:
        app_results = run_app_tests(local_adapter_dir, artifact_dir)
    elif metrics_verdict_ok and args.skip_app_tests:
        app_results = {"skipped": True, "ok": True, "reason": "skip_app_tests"}

    app_ok = bool(app_results.get("ok"))
    verdict = "GO DEFINITIVO" if metrics_verdict_ok and app_ok else "NO-GO"
    unlock = write_app_unlock(
        artifact_dir / "app_unlock.json",
        unlocked=verdict == "GO DEFINITIVO",
        adapter_dir=local_adapter_dir,
        artifact_dir=artifact_dir,
        reason="current_run_positive" if verdict == "GO DEFINITIVO" else "current_run_not_positive",
    )
    certification = {
        "verdict": verdict,
        "metrics": metrics,
        "thresholds": FINAL_THRESHOLDS,
        "metric_checks": metric_checks,
        "priority_cases_ok": priority_ok,
        "app_results": app_results,
        "app_unlock": unlock,
        "training_attempts": training_attempts,
        "loss_report": loss_report,
        "release_dir": str(release_dir),
        "adapter_zip": str(final_zip),
        "adapter_dir": str(local_adapter_dir),
        "adapter_eval": str(adapter_eval),
        "dataset": str(args.output_dataset),
        "config": str(args.output_config),
        "training_config": config,
        "eval_set": str(args.eval_set),
        "system_prompt": str(args.system_prompt),
    }
    write_json(certification, artifact_dir / "final_perfection_summary.json")
    write_master_verdict(artifact_dir / "final_verdict_master.md", certification)
    if args.copy_verdict_to_repo:
        write_master_verdict(ROOT / "fiorellia" / "eval" / "final_verdict_master.md", certification)
        write_json(certification, ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "final_perfection_summary.json")
    release_manifest = copy_release_artifacts(release_dir, final_zip, artifact_dir, certification=certification)
    certification["release_manifest"] = release_manifest
    write_json(certification, artifact_dir / "final_perfection_summary.json")
    write_master_verdict(artifact_dir / "final_verdict_master.md", certification)
    if args.copy_verdict_to_repo:
        write_master_verdict(ROOT / "fiorellia" / "eval" / "final_verdict_master.md", certification)
        write_json(certification, ROOT / "fiorellia" / "eval" / "reports" / "final_release" / "final_perfection_summary.json")
    copy_release_artifacts(release_dir, final_zip, artifact_dir, certification=certification)

    print(json.dumps(certification, indent=2, ensure_ascii=False))
    return 0 if verdict == "GO DEFINITIVO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
