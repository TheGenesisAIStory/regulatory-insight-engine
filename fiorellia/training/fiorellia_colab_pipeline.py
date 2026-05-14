"""Small operational helpers for Fiorell.IA LoRA Colab runbooks.

The helpers are intentionally conservative: they validate paths, config and
artifacts but do not change model, LoRA, prompt or eval behavior.
"""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Mapping

import yaml

DEFAULT_BASE_MODEL = "Qwen/Qwen2.5-3B-Instruct"
REQUIRED_CONFIG_KEYS = [
    "base_model_name",
    "output_dir",
    "dataset_path",
    "target_modules",
    "use_4bit",
]
REQUIRED_ADAPTER_FILES = ["adapter_config.json", "adapter_model.safetensors"]


def fail(message: str) -> None:
    raise RuntimeError(f"[Fiorell.IA preflight] {message}")


def require_file(path: str | Path, label: str) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        fail(f"Missing {label}: {p}")
    return p


def require_dir(path: str | Path, label: str, create: bool = False) -> Path:
    p = Path(path).expanduser().resolve()
    if create:
        p.mkdir(parents=True, exist_ok=True)
    if not p.exists() or not p.is_dir():
        fail(f"Missing {label}: {p}")
    return p


def load_config(config_path: str | Path) -> dict[str, Any]:
    p = require_file(config_path, "YAML config")
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"Config must be a YAML object: {p}")
    return data


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
    if not dataset.exists():
        fail(f"Dataset from config not found: {dataset}")
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
        fail("CUDA GPU not available. In Colab select a GPU runtime, e.g. T4.")
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
            if item.is_file():
                zf.write(item, arcname=str(item.relative_to(adapter)))
    return validate_adapter_zip(target)


def copy_artifact(src: str | Path, dst: str | Path) -> Path:
    source = require_file(src, "source artifact")
    target = Path(dst).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def write_json(data: Mapping[str, Any], path: str | Path) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(data), indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return target


def write_final_verdict(path: str | Path, verdict: str, metrics: Mapping[str, Any]) -> Path:
    target = Path(path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join([
        "# CONCLUSIONE DEFINITIVA — Fiorell.IA LoRA",
        "",
        f"Esito run: **{verdict}**",
        "",
        "## Metriche",
        "",
        "```json",
        json.dumps(dict(metrics), indent=2, ensure_ascii=False, sort_keys=True),
        "```",
        "",
        "GO solo se tutte le soglie sono rispettate, nessun priority case regredisce e nessun artifact critico manca.",
    ])
    target.write_text(body, encoding="utf-8")
    return target
