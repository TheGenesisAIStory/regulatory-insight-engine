#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent
MAC_DRIVE_REPO_ROOT = Path(
    "/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine"
)
def default_datasets(repo_root: Path) -> list[Path]:
    return [
        repo_root / "fiorellia" / "training" / "supervised_gold_release_20260527.jsonl",
        repo_root / "fiorellia" / "training" / "supervised_v3_final_perfection_20260527.jsonl",
        repo_root / "fiorellia" / "training" / "supervised_v2_behavior_hardening_20260526.jsonl",
    ]


def default_configs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260527_final_perfection.yaml",
        repo_root / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260526_behavior_hardening.yaml",
    ]


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def run(command: list[str], cwd: Path = ROOT, check: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(str(part) for part in command))
    return subprocess.run(command, cwd=cwd, check=check, text=True, env=env)


def choose_existing(candidates: list[Path], label: str) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    raise FileNotFoundError(f"{label} not found. Checked: {[str(path) for path in candidates]}")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{line_no}")
            rows.append(row)
    if not rows:
        raise ValueError(f"JSONL file is empty: {path}")
    return rows


def write_json(data: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def render_chat(messages: list[dict[str, str]]) -> str:
    chunks = []
    for message in messages:
        role = message.get("role", "user")
        content = str(message.get("content", "")).strip()
        chunks.append(f"<|im_start|>{role}\n{content}<|im_end|>")
    return "\n".join(chunks)


def detect_runtime() -> dict[str, Any]:
    info: dict[str, Any] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "is_apple_silicon": platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"},
    }
    try:
        import torch

        info.update(
            {
                "torch": torch.__version__,
                "mps_available": bool(hasattr(torch.backends, "mps") and torch.backends.mps.is_available()),
                "cuda_available": bool(torch.cuda.is_available()),
            }
        )
    except Exception as exc:
        info["torch_error"] = str(exc)
    return info


def build_mac_config(
    base_config_path: Path,
    dataset_path: Path,
    output_dir: Path,
    run_id: str,
    args: argparse.Namespace,
) -> dict[str, Any]:
    config = yaml.safe_load(base_config_path.read_text(encoding="utf-8"))
    config.update(
        {
            "run_id": run_id,
            "base_model_name": args.base_model,
            "dataset_path": str(dataset_path),
            "output_dir": str(output_dir),
            "allow_mps": True,
            "mps_float16": not args.no_mps_float16,
            "use_4bit": False,
            "num_train_epochs": float(args.epochs),
            "per_device_train_batch_size": int(args.batch_size),
            "gradient_accumulation_steps": int(args.gradient_accumulation_steps),
            "learning_rate": float(args.learning_rate),
            "weight_decay": float(args.weight_decay),
            "max_seq_length": int(args.max_seq_length),
            "save_strategy": "epoch",
            "eval_strategy": args.eval_strategy,
            "save_total_limit": int(args.save_total_limit),
            "logging_steps": int(args.logging_steps),
            "mlflow_experiment_name": "fiorellia-lora-mac-mps",
            "lora_r": int(args.lora_r),
            "lora_alpha": int(args.lora_alpha),
            "lora_dropout": float(args.lora_dropout),
        }
    )
    return config


def validate_adapter_dir(adapter_dir: Path) -> None:
    missing = [name for name in ["adapter_config.json", "adapter_model.safetensors"] if not (adapter_dir / name).exists()]
    if missing:
        raise RuntimeError(f"Adapter incomplete at {adapter_dir}. Missing: {missing}")


def zip_adapter(adapter_dir: Path, zip_path: Path) -> Path:
    validate_adapter_dir(adapter_dir)
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for item in sorted(adapter_dir.rglob("*")):
            rel = item.relative_to(adapter_dir)
            if any(part.startswith("checkpoint-") for part in rel.parts):
                continue
            if any(part in {"runs", "logs"} for part in rel.parts):
                continue
            if item.is_file():
                zf.write(item, arcname=str(rel))
    with zipfile.ZipFile(zip_path) as zf:
        corrupt = zf.testzip()
        if corrupt:
            raise RuntimeError(f"Corrupt adapter zip member: {corrupt}")
    print(f"adapter_zip={zip_path} size={zip_path.stat().st_size}")
    return zip_path


def prepare_mlx_dataset(dataset_path: Path, out_dir: Path, validation_ratio: float) -> dict[str, Any]:
    rows = read_jsonl(dataset_path)
    texts = [{"text": render_chat(row["messages"])} for row in rows if isinstance(row.get("messages"), list)]
    if not texts:
        raise ValueError(f"No chat-format rows found in {dataset_path}")
    split = max(1, int(round(len(texts) * validation_ratio))) if len(texts) > 4 else 0
    valid = texts[:split]
    train = texts[split:] if split else texts
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, payload in [("train.jsonl", train), ("valid.jsonl", valid or train[:1]), ("test.jsonl", valid or train[:1])]:
        with (out_dir / name).open("w", encoding="utf-8") as handle:
            for item in payload:
                handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    return {"rows": len(texts), "train": len(train), "valid": len(valid or train[:1]), "data_dir": str(out_dir)}


def run_mlx_lora(args: argparse.Namespace, run_dir: Path, dataset_path: Path, manifest: dict[str, Any]) -> int:
    if importlib.util.find_spec("mlx_lm") is None:
        raise RuntimeError("mlx-lm is not installed. Run: python -m pip install mlx-lm")
    data_dir = run_dir / "mlx_data"
    data_info = prepare_mlx_dataset(dataset_path, data_dir, validation_ratio=args.validation_split_ratio)
    adapter_dir = run_dir / "adapter_mlx"
    command = [
        sys.executable,
        "-m",
        "mlx_lm.lora",
        "--model",
        args.base_model,
        "--train",
        "--data",
        str(data_dir),
        "--adapter-path",
        str(adapter_dir),
        "--iters",
        str(args.mlx_iters),
        "--batch-size",
        str(args.batch_size),
        "--lora-layers",
        str(args.mlx_lora_layers),
    ]
    manifest["mlx"] = {"data": data_info, "command": command}
    write_json(manifest, run_dir / "manifest.json")
    return run(command, cwd=args.repo_root, check=True).returncode


def run_transformers_mps(args: argparse.Namespace, run_dir: Path, dataset_path: Path, base_config_path: Path, manifest: dict[str, Any]) -> int:
    adapter_dir = run_dir / "adapter"
    config_path = run_dir / "config_mac_mps.yaml"
    config = build_mac_config(
        base_config_path=base_config_path,
        dataset_path=dataset_path,
        output_dir=adapter_dir,
        run_id=args.run_name,
        args=args,
    )
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    manifest["training_config"] = config
    manifest["config_path"] = str(config_path)
    write_json(manifest, run_dir / "manifest.json")

    env = os.environ.copy()
    env.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
    env.setdefault("FIORELLIA_REPORT_TO_MLFLOW", "0")
    env.setdefault("TOKENIZERS_PARALLELISM", "false")

    command = [
        sys.executable,
        str(args.repo_root / "fiorellia" / "training" / "train_lora_behavior_v1.py"),
        "--config",
        str(config_path),
        "--dataset-path",
        str(dataset_path),
        "--output-dir",
        str(adapter_dir),
    ]
    if args.skip_existing and (adapter_dir / "adapter_model.safetensors").exists():
        print(f"Existing adapter found, training skipped: {adapter_dir}")
    else:
        run(command, cwd=args.repo_root, env=env)
    validate_adapter_dir(adapter_dir)
    manifest["adapter_dir"] = str(adapter_dir)
    manifest["adapter_zip"] = str(zip_adapter(adapter_dir, run_dir / f"{args.run_name}.zip"))
    write_json(manifest, run_dir / "manifest.json")
    return 0


def run_optional_eval(args: argparse.Namespace, run_dir: Path, manifest: dict[str, Any]) -> None:
    if not args.run_eval:
        return
    adapter_dir = Path(manifest.get("adapter_dir", run_dir / "adapter"))
    out = run_dir / "eval" / "adapter_eval.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        str(args.repo_root / "fiorellia" / "eval" / "prompt_harness_local_adapter.py"),
        "--dataset",
        str(args.eval_set),
        "--system-prompt",
        str(args.system_prompt),
        "--adapter-path",
        str(adapter_dir),
        "--base-model",
        args.base_model,
        "--out",
        str(out),
        "--max-new-tokens",
        str(args.eval_max_new_tokens),
        "--limit",
        str(args.eval_limit),
    ]
    run(command, cwd=args.repo_root)
    manifest["eval"] = {"adapter_eval": str(out), "limit": args.eval_limit}
    write_json(manifest, run_dir / "manifest.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fiorell.IA Mac local training runner for Apple Silicon MPS/MLX.")
    parser.add_argument("--engine", choices=["transformers-mps", "mlx-lm"], default="transformers-mps")
    parser.add_argument("--repo-root", type=Path, default=MAC_DRIVE_REPO_ROOT if MAC_DRIVE_REPO_ROOT.exists() else ROOT)
    parser.add_argument("--dataset", type=Path, default=None)
    parser.add_argument("--base-config", type=Path, default=None)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--run-name", default=f"fiorellia_behavior_MAC_MPS_{utc_stamp()}")
    parser.add_argument("--local-runs-dir", type=Path, default=None)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=16)
    parser.add_argument("--learning-rate", type=float, default=3e-5)
    parser.add_argument("--weight-decay", type=float, default=0.03)
    parser.add_argument("--max-seq-length", type=int, default=768)
    parser.add_argument("--lora-r", type=int, default=8)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--logging-steps", type=int, default=5)
    parser.add_argument("--save-total-limit", type=int, default=2)
    parser.add_argument("--eval-strategy", choices=["no", "epoch", "steps"], default="no")
    parser.add_argument("--validation-split-ratio", type=float, default=0.10)
    parser.add_argument("--no-mps-float16", action="store_true")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--run-eval", action="store_true")
    parser.add_argument("--eval-set", type=Path, default=None)
    parser.add_argument("--system-prompt", type=Path, default=None)
    parser.add_argument("--eval-limit", type=int, default=10)
    parser.add_argument("--eval-max-new-tokens", type=int, default=96)
    parser.add_argument("--mlx-iters", type=int, default=300)
    parser.add_argument("--mlx-lora-layers", type=int, default=16)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    args.repo_root = args.repo_root.expanduser().resolve()
    if str(args.repo_root) not in sys.path:
        sys.path.insert(0, str(args.repo_root))
    dataset_path = (args.dataset or choose_existing(default_datasets(args.repo_root), "training dataset")).expanduser().resolve()
    base_config_path = (args.base_config or choose_existing(default_configs(args.repo_root), "base training config")).expanduser().resolve()
    if args.eval_set is None:
        args.eval_set = args.repo_root / "fiorellia" / "eval" / "eval_set_behavior_hardening_v1.jsonl"
    if args.system_prompt is None:
        args.system_prompt = args.repo_root / "fiorellia" / "prompts" / "system_prompt_strict.md"
    if args.local_runs_dir is None:
        args.local_runs_dir = args.repo_root / "local_runs"
    run_dir = (args.local_runs_dir / args.run_name).expanduser().resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    runtime = detect_runtime()
    manifest: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": args.engine,
        "run_name": args.run_name,
        "repo_root": str(args.repo_root),
        "run_dir": str(run_dir),
        "dataset": str(dataset_path),
        "base_config": str(base_config_path),
        "runtime": runtime,
        "notes": [
            "MPS path disables bitsandbytes 4-bit because it is CUDA-only in this repo.",
            "Outputs are local-only under local_runs/ and intentionally gitignored.",
        ],
    }
    if args.dry_run:
        write_json(manifest, run_dir / "manifest.json")
        print(json.dumps(manifest, indent=2, ensure_ascii=False))
        return 0
    if args.engine == "transformers-mps" and not runtime.get("mps_available"):
        raise RuntimeError("MPS is not available. Use an Apple Silicon Python/PyTorch environment or pass --engine mlx-lm if configured.")

    if args.engine == "mlx-lm":
        code = run_mlx_lora(args, run_dir, dataset_path, manifest)
    else:
        code = run_transformers_mps(args, run_dir, dataset_path, base_config_path, manifest)
    run_optional_eval(args, run_dir, manifest)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
