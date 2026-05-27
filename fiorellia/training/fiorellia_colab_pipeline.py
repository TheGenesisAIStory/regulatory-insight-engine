"""Small operational helpers for Fiorell.IA LoRA runbooks.

Conservative scope: validate config/artifacts, debug eval metrics, patch SFT
style/abstention data, and prepare ablation datasets. No model, LoRA, prompt
harness or serving architecture is changed here.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import time
import unicodedata
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping

import yaml

DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
REQUIRED_CONFIG_KEYS = ["base_model_name", "output_dir", "dataset_path", "target_modules", "use_4bit"]
REQUIRED_ADAPTER_FILES = ["adapter_config.json", "adapter_model.safetensors"]

SYSTEM_STYLE_PATCH = """Sei Fiorell.IA, assistente tecnico per normativa bancaria italiana.

Regole obbligatorie:
1. Rispondi esclusivamente in lingua italiana.
2. Mantieni un tono formale, tecnico e conciso, conforme agli standard della Banca d'Italia.
3. Rispondi solo se la risposta è supportata dalle fonti locali recuperate.
4. Cita sempre le fonti disponibili con riferimento a documento e pagina/sezione quando presenti.
5. Se le fonti non sono sufficienti, non inventare: dichiara che non puoi rispondere perché l'informazione non è supportata dalle fonti disponibili.
6. Non usare tono colloquiale, formule promozionali o frasi in inglese.
7. Non fornire opinioni personali o raccomandazioni non supportate."""

ABSTENTION_TEMPLATE = "Non posso rispondere in modo affidabile perché le fonti locali disponibili non contengono elementi sufficienti per supportare la risposta."


def fail(message: str) -> None:
    raise RuntimeError(f"[Fiorell.IA preflight] {message}")


def is_drive_path(path: str | Path) -> bool:
    text = str(Path(path).expanduser())
    return "/content/drive/" in text or "GoogleDrive-" in text or "/Il mio Drive/" in text


def wait_for_path(
    path: str | Path,
    label: str,
    *,
    kind: str = "any",
    attempts: int | None = None,
    base_sleep: float | None = None,
) -> Path:
    p = Path(path).expanduser().resolve()
    default_attempts = 8 if is_drive_path(p) else 1
    total_attempts = int(os.getenv("FIORELLIA_DRIVE_WAIT_ATTEMPTS", attempts or default_attempts))
    sleep_seconds = float(os.getenv("FIORELLIA_DRIVE_WAIT_BASE_SECONDS", base_sleep or 1.5))

    def ok() -> bool:
        if kind == "file":
            return p.is_file()
        if kind == "dir":
            return p.is_dir()
        return p.exists()

    for attempt in range(1, total_attempts + 1):
        if ok():
            size = p.stat().st_size if p.is_file() else None
            suffix = f" size={size}" if size is not None else ""
            print(f"[Fiorell.IA preflight] OK {label}: {p}{suffix}")
            return p
        if attempt < total_attempts:
            wait = sleep_seconds * attempt
            print(
                f"[Fiorell.IA preflight] {label} non ancora visibile: {p} "
                f"(tentativo {attempt}/{total_attempts}); retry tra {wait:.1f}s"
            )
            time.sleep(wait)
    fail(f"Missing {label} after {total_attempts} attempts: {p}")


def require_file(path: str | Path, label: str) -> Path:
    return wait_for_path(path, label, kind="file")


def require_dir(path: str | Path, label: str, create: bool = False) -> Path:
    p = Path(path).expanduser().resolve()
    if create:
        p.mkdir(parents=True, exist_ok=True)
    return wait_for_path(p, label, kind="dir")


def load_config(config_path: str | Path) -> dict[str, Any]:
    p = require_file(config_path, "YAML config")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"Config must be a YAML object: {p}")
    return data


def save_config(config: Mapping[str, Any], config_path: str | Path) -> Path:
    p = Path(config_path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(dict(config), sort_keys=False, allow_unicode=True), encoding="utf-8")
    return wait_for_path(p, "YAML config", kind="file")


def validate_config(config: Mapping[str, Any], repo_root: str | Path) -> dict[str, Path]:
    missing = [k for k in REQUIRED_CONFIG_KEYS if k not in config]
    if missing:
        fail(f"Missing config keys: {missing}")
    if config["base_model_name"] != DEFAULT_BASE_MODEL:
        fail(f"Unexpected base model: {config['base_model_name']}")
    if not isinstance(config.get("target_modules"), list) or not config["target_modules"]:
        fail("target_modules must be a non-empty list")
    root = require_dir(repo_root, "repository root")
    dataset = root / str(config["dataset_path"])
    wait_for_path(dataset, "dataset from config", kind="file")
    output_dir = root / str(config["output_dir"])
    return {"dataset_path": dataset, "output_dir": output_dir}


def check_cuda(require_gpu: bool = True) -> dict[str, Any]:
    import torch

    info = {
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
    }
    if require_gpu and not info["cuda_available"]:
        fail("CUDA GPU not available. In Colab select an A100 GPU runtime for the final Fiorell.IA run.")
    return info


def validate_adapter_dir(adapter_dir: str | Path) -> Path:
    p = require_dir(adapter_dir, "adapter directory")
    missing = [name for name in REQUIRED_ADAPTER_FILES if not (p / name).exists()]
    if missing:
        fail(f"Adapter directory incomplete. Missing: {missing}")
    return p


def validate_adapter_zip(zip_path: str | Path) -> Path:
    p = require_file(zip_path, "adapter zip")
    with zipfile.ZipFile(p) as zf:
        corrupt = zf.testzip()
        if corrupt:
            fail(f"Corrupt zip member: {corrupt}")
        names = set(zf.namelist())
    missing = [name for name in REQUIRED_ADAPTER_FILES if not any(n.endswith(name) for n in names)]
    if missing:
        fail(f"Adapter zip incomplete. Missing: {missing}")
    return p


def zip_adapter(adapter_dir: str | Path, zip_path: str | Path) -> Path:
    adapter = validate_adapter_dir(adapter_dir)
    target = Path(zip_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(adapter.rglob("*")):
            rel = item.relative_to(adapter)
            if any(part.startswith("checkpoint-") for part in rel.parts):
                continue
            if any(part in {"runs", "logs"} for part in rel.parts):
                continue
            if item.name == ".DS_Store" or item.suffix == ".bin":
                continue
            if item.is_file():
                zf.write(item, arcname=str(rel))
    wait_for_path(target, "adapter zip", kind="file")
    return validate_adapter_zip(target)


def copy_artifact(src: str | Path, dst: str | Path) -> Path:
    source = require_file(src, "source artifact")
    target = Path(dst).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return wait_for_path(target, "copied artifact", kind="file")


def write_json(data: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(data), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return wait_for_path(target, "JSON artifact", kind="file")


def write_final_verdict(path: str | Path, verdict: str, metrics: Mapping[str, Any]) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join([
        "# CONCLUSIONE DEFINITIVA — Fiorell.IA LoRA", "", f"Esito run: **{verdict}**", "",
        "## Metriche", "", "```json", json.dumps(dict(metrics), indent=2, ensure_ascii=False, sort_keys=True), "```", "",
        "GO solo se tutte le soglie sono rispettate, nessun priority case regredisce e nessun artifact critico manca.",
    ])
    target.write_text(body, encoding="utf-8")
    return wait_for_path(target, "final verdict", kind="file")


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = require_file(path, "JSONL file")
    rows = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"Invalid JSONL at {p}:{i}: {exc}")
        if not isinstance(item, dict):
            fail(f"JSONL row must be an object at {p}:{i}")
        rows.append(item)
    if not rows:
        fail(f"JSONL file is empty: {p}")
    return rows


def write_jsonl(rows: Iterable[Mapping[str, Any]], path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    return wait_for_path(p, "JSONL artifact", kind="file")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _regex_any(patterns: Iterable[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def is_abstention(text: Any) -> bool:
    t = normalize_text(text).lower()
    patterns = [
        r"non (posso|sono in grado di) rispondere", r"non (dispongo|ho) (di )?(informazioni|fonti|contesto|evidenze)",
        r"non posso fornire (informazioni|dati|consulenze)",
        r"non posso fornire informazioni in tempo reale",
        r"fonti .* non (sono sufficienti|supportano)", r"non risulta supportat[oa] dalle fonti",
        r"non posso inferire", r"assenza di fonti", r"fuori ambito", r"non rientra nel perimetro",
        r"assistente normativo basato su documentazione statica",
    ]
    return _regex_any(patterns, t)


def is_mostly_italian(text: Any) -> bool:
    t = normalize_text(text).lower()
    it_hits = sum(bool(re.search(p, t)) for p in [r"\bnon\b", r"\bsecondo\b", r"\bfonti\b", r"\bnormativa\b", r"\bai sensi\b"])
    en_hits = sum(bool(re.search(p, t)) for p in [r"\bthe\b", r"\band\b", r"\baccording to\b", r"\bI cannot\b"])
    return it_hits >= 1 and en_hits <= 1


def is_formal_style(text: Any) -> bool:
    t = normalize_text(text).lower()
    if not t or len(t.split()) > 180:
        return False
    if any(bad in t for bad in ["ciao", "certo!", "ok,", "sure", "hello"]):
        return False
    return _regex_any(
        [
            r"ai sensi",
            r"in base",
            r"secondo",
            r"la normativa",
            r"si evidenzia",
            r"non risulta",
            r"in qualit[aà] di assistente",
            r"si prega di consultare",
        ],
        t,
    )


def has_source_reference(text: Any) -> bool:
    t = normalize_text(text).lower()
    return _regex_any([r"\[.*?p\.\s*\d+.*?\]", r"pag(ina)?\.?\s*\d+", r"fonte", r"circ\.?\s*285", r"\bcrr\b", r"ifrs\s*9"], t)


def has_invalid_source_reference(text: Any) -> bool:
    t = normalize_text(text).lower()
    patterns = [
        r"pagina non specificata",
        r"documento locale",
        r"pagina/sezione",
        r"fonte non disponibile",
        r"fonti:\s*-\s*(?:nota|nessuna)\b",
        r"fonti:\s*$",
        r"fonti:\s*-\s*$",
        r"\[pagina",
        r"\[documento",
        r"nessun documento locale",
    ]
    return _regex_any(patterns, t)


def has_valid_source_reference(text: Any) -> bool:
    if has_invalid_source_reference(text):
        return False
    t = normalize_text(text).lower()
    patterns = [
        r"fonti:\s*-\s*\[?\s*(crr|circ\.?\s*285|circolare\s*285|ifrs\s*9|basel|banca d'italia)",
        r"fonti:\s*-\s*(crr|circ\.?\s*285|circolare\s*285|ifrs\s*9|basel|banca d'italia).{0,100}\b(art|par|parte|titolo|capitolo|sezione|aggiornamento|\d)",
        r"\[?\s*crr\s*,?\s*art\.?\s*\d+",
        r"\bcrr\s*-\s*art\.?\s*\d+",
        r"\[?\s*ifrs\s*9\s*,?\s*par\.?\s*[\d.]+",
        r"\bifrs\s*9\s*-\s*par\.?\s*[\d.]+",
        r"\[?\s*circolare\s*285\s*,?\s*(parte|titolo|capitolo|aggiornamento|controlli|governo)",
        r"\bcircolare\s*285\s*-",
        r"\bcirc\.?\s*285\s*-",
        r"\[?\s*basel\s*iii\s*,?\s*(sezione|capital|framework)",
        r"\bbasel\s*iii\s*-",
        r"\[.*?p\.\s*\d+.*?\]",
    ]
    return _regex_any(patterns, t)


def is_too_generic_grounded_answer(text: Any) -> bool:
    t = normalize_text(text).lower()
    if not t:
        return True
    generic_patterns = [
        r"non sono state trovate .* specifiche",
        r"il contesto recuperato non include",
        r"risposta limitata ai documenti indicizzati",
        r"documenti locali disponibili",
    ]
    return _regex_any(generic_patterns, t) and not has_valid_source_reference(t)


def is_out_of_scope_refusal(text: Any) -> bool:
    t = normalize_text(text).lower()
    refusal = is_abstention(t) or _regex_any([r"fuori (dal )?perimetro", r"non rientra", r"non posso trattare"], t)
    scope_markers = _regex_any(
        [
            r"investimento",
            r"trading",
            r"fiscal",
            r"hr",
            r"smart working",
            r"mercato",
            r"consulenza",
            r"etf",
            r"azioni",
            r"covered call",
        ],
        t,
    )
    return refusal and scope_markers


def infer_output_text(row: Mapping[str, Any]) -> str:
    for col in ["adapter_output", "model_answer", "model_output", "prediction", "response", "generated_text", "answer", "output"]:
        if col in row and row[col] is not None:
            return normalize_text(row[col])
    return ""


def infer_case_type(row: Mapping[str, Any]) -> str:
    for col in ["case_type", "category", "expected_category", "task_type", "eval_type", "label", "expected_label", "type"]:
        value = normalize_text(row.get(col))
        if value:
            return value.lower().replace("-", "_")
    return "unknown"


def score_eval_rows(rows: list[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    scored = []
    counts = {"in_scope": 0, "unsupported": 0, "out_of_scope": 0}
    sums = {"in_scope_grounded": [], "unsupported_abstention": [], "out_of_scope_refusal": [], "italian_style": []}
    for row in rows:
        output = infer_output_text(row)
        case = infer_case_type(row)
        pred_abstain = is_abstention(output)
        pred_has_source = has_source_reference(output)
        pred_invalid_source = has_invalid_source_reference(output)
        pred_valid_source = has_valid_source_reference(output)
        pred_out_refusal = is_out_of_scope_refusal(output)
        pred_generic = is_too_generic_grounded_answer(output)
        pred_grounded = bool(output) and not pred_abstain and pred_valid_source and not pred_generic
        pred_style = is_mostly_italian(output) and (is_formal_style(output) or pred_abstain or pred_out_refusal)
        in_scope = any(x in case for x in ["in_scope", "inscope", "grounded"])
        unsupported = any(x in case for x in ["unsupported", "abstention", "no_source", "no_context"])
        out_scope = any(x in case for x in ["out_of_scope", "outofscope", "oos", "refusal"])
        if in_scope:
            counts["in_scope"] += 1
            sums["in_scope_grounded"].append(pred_grounded)
        if unsupported:
            counts["unsupported"] += 1
            sums["unsupported_abstention"].append(pred_abstain and not pred_grounded)
        if out_scope:
            counts["out_of_scope"] += 1
            sums["out_of_scope_refusal"].append(pred_out_refusal)
        sums["italian_style"].append(pred_style)
        scored.append(
            {
                **dict(row),
                "_case_norm": case,
                "_output_norm": output,
                "pred_is_abstention": pred_abstain,
                "pred_is_grounded": pred_grounded,
                "pred_is_out_of_scope_refusal": pred_out_refusal,
                "pred_has_source_reference": pred_has_source,
                "pred_has_valid_source_reference": pred_valid_source,
                "pred_has_invalid_source_reference": pred_invalid_source,
                "pred_is_too_generic_grounded_answer": pred_generic,
                "pred_italian_style": pred_style,
            }
        )
    metrics = {name: (sum(values) / len(values) if values else None) for name, values in sums.items()}
    metrics["subset_counts"] = counts
    return scored, metrics


def patch_record_system(row: Mapping[str, Any], system_patch: str = SYSTEM_STYLE_PATCH) -> dict[str, Any]:
    item = dict(row)
    if isinstance(item.get("messages"), list):
        messages = [dict(msg) for msg in item["messages"]]
        for msg in messages:
            if msg.get("role") == "system":
                old = normalize_text(msg.get("content"))
                msg["content"] = old if "Rispondi esclusivamente in lingua italiana" in old else system_patch + "\n\n" + old
                item["messages"] = messages
                return item
        item["messages"] = [{"role": "system", "content": system_patch}] + messages
        return item
    old = normalize_text(item.get("system"))
    item["system"] = old if "Rispondi esclusivamente in lingua italiana" in old else system_patch + ("\n\n" + old if old else "")
    return item


def training_text(row: Mapping[str, Any]) -> str:
    if isinstance(row.get("messages"), list):
        return "\n".join(normalize_text(m.get("content")) for m in row["messages"]).lower()
    return "\n".join(normalize_text(v) for v in row.values() if isinstance(v, (str, int, float))).lower()


def is_abstention_training_case(row: Mapping[str, Any]) -> bool:
    t = training_text(row)
    cat = normalize_text(row.get("category")).lower()
    markers = ["non posso rispondere", "non posso fornire", "fonti locali disponibili non contengono", "non supportata dalle fonti", "fuori ambito", "non rientra nel perimetro"]
    return any(m in t for m in markers) or any(x in cat for x in ["unsupported", "abstention", "out_of_scope", "refusal"])


def build_style_abstention_dataset(input_jsonl: str | Path, output_jsonl: str | Path, target_abstention_ratio: float = 0.40) -> dict[str, Any]:
    rows = [patch_record_system(row) for row in read_jsonl(input_jsonl)]
    abst = [row for row in rows if is_abstention_training_case(row)]
    if not abst:
        fail("No abstention/refusal cases detected in training dataset")
    balanced = list(rows)
    while sum(is_abstention_training_case(r) for r in balanced) / len(balanced) < target_abstention_ratio:
        balanced.extend(abst)
    out = write_jsonl(balanced, output_jsonl)
    return {"output_jsonl": str(out), "rows": len(balanced), "abstention_rows": sum(is_abstention_training_case(r) for r in balanced), "target_abstention_ratio": target_abstention_ratio}


def infer_train_category(row: Mapping[str, Any]) -> str:
    category = normalize_text(row.get("category"))
    if category:
        return category
    text = training_text(row)
    if is_abstention_training_case(row):
        return "unsupported_abstention"
    if "circ. 285" in text or "circolare 285" in text:
        return "circ_285"
    if "crr" in text:
        return "crr"
    if "ifrs" in text:
        return "ifrs9"
    return "other"


def write_ablation_datasets(input_jsonl: str | Path, output_dir: str | Path) -> list[dict[str, Any]]:
    rows = read_jsonl(input_jsonl)
    categories = sorted({infer_train_category(row) for row in rows})
    root = require_dir(output_dir, "ablation output directory", create=True)
    results = []
    for category in categories:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", category)
        kept = [row for row in rows if infer_train_category(row) != category]
        path = write_jsonl(kept, root / f"train_without__{safe}.jsonl")
        abst_ratio = sum(is_abstention_training_case(r) for r in kept) / len(kept) if kept else 0.0
        results.append({"removed_category": category, "dataset_path": str(path), "rows": len(kept), "train_abstention_ratio": abst_ratio})
    return results


def write_csv(rows: list[Mapping[str, Any]], path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()}) if rows else []
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return wait_for_path(p, "CSV artifact", kind="file")
