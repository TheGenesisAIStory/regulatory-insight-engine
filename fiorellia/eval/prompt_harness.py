#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "fiorellia" / "eval" / "eval_set.jsonl"
DEFAULT_SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt.md"
DEFAULT_LOG = ROOT / "fiorellia" / "eval" / "prompt_harness_logs.jsonl"
DEFAULT_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            if "id" not in record or "category" not in record or "user_query" not in record:
                raise ValueError(f"Invalid record at {path}:{line_no}")
            records.append(record)
    return records


def build_prompt(system_prompt: str, user_query: str) -> str:
    return "\n\n".join(
        [
            system_prompt.strip(),
            "Domanda utente:",
            user_query.strip(),
            "Rispondi secondo le regole Fiorell.IA. Se mancano fonti locali recuperate, astieniti.",
        ]
    )


def call_ollama_api(prompt: str, model: str, host: str, timeout: int) -> str:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 2048,
                "num_predict": 160,
                "temperature": 0,
            },
        }
    ).encode("utf-8")
    req = urlrequest.Request(
        f"{host.rstrip('/')}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return str(data.get("response", "")).strip()


def call_ollama_cli(prompt: str, model: str, timeout: int) -> str:
    completed = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or f"ollama exited with {completed.returncode}"
        raise RuntimeError(stderr)
    return completed.stdout.strip()


def answer(prompt: str, model: str, mode: str, host: str, timeout: int) -> str:
    if mode == "api":
        return call_ollama_api(prompt, model, host, timeout)
    if mode == "cli":
        return call_ollama_cli(prompt, model, timeout)
    try:
        return call_ollama_api(prompt, model, host, timeout)
    except (URLError, TimeoutError, OSError):
        return call_ollama_cli(prompt, model, timeout)


def append_log(path: Path, item: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")


def resolve_output_path(path: Path, adapter_mode: bool) -> Path:
    if path.suffix == ".jsonl":
        return path
    return path / ("adapter_eval.jsonl" if adapter_mode else "prompt_harness.jsonl")


def find_adapter_dir(root: Path) -> Path:
    candidates = sorted(root.rglob("adapter_config.json"))
    if not candidates:
        raise FileNotFoundError(f"adapter_config.json not found under {root}")
    return candidates[0].parent


def detect_device(force_cpu: bool) -> tuple[str, Any]:
    import torch

    if not force_cpu and torch.cuda.is_available():
        dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
        return "cuda", dtype
    return "cpu", torch.float32


def build_messages(system_prompt: str, user_query: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt.strip()},
        {
            "role": "user",
            "content": "\n\n".join(
                [
                    "Domanda utente:",
                    user_query.strip(),
                    "Rispondi secondo le regole Fiorell.IA. Se mancano fonti locali recuperate, astieniti.",
                ]
            ),
        },
    ]


def build_adapter_inputs(tokenizer: Any, system_prompt: str, user_query: str, device: str) -> dict[str, Any]:
    messages = build_messages(system_prompt, user_query)
    if hasattr(tokenizer, "apply_chat_template"):
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        prompt_text = build_prompt(system_prompt, user_query)
    encoded = tokenizer(prompt_text, return_tensors="pt")
    return {key: value.to(device) for key, value in encoded.items()}


def load_adapter_model(adapter_dir: Path, base_model_override: str | None, force_cpu: bool) -> tuple[Any, Any, str, str]:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    adapter_config = json.loads((adapter_dir / "adapter_config.json").read_text(encoding="utf-8"))
    base_model = base_model_override or adapter_config.get("base_model_name_or_path") or "Qwen/Qwen2.5-3B-Instruct"
    device, dtype = detect_device(force_cpu)

    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(model, adapter_dir)
    model.to(device)
    model.eval()
    return tokenizer, model, base_model, device


def generate_adapter_answer(
    model: Any,
    tokenizer: Any,
    system_prompt: str,
    user_query: str,
    device: str,
    max_new_tokens: int,
) -> str:
    import torch

    inputs = build_adapter_inputs(tokenizer, system_prompt, user_query, device)
    prompt_length = inputs["input_ids"].shape[-1]
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = output[0][prompt_length:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()


def run_adapter_harness(
    records: list[dict[str, Any]],
    system_prompt: str,
    adapter_zip: Path,
    base_model_override: str | None,
    out_path: Path,
    max_new_tokens: int,
    force_cpu: bool,
) -> int:
    run_id = datetime.now(timezone.utc).strftime("adapter-harness-%Y%m%dT%H%M%SZ")
    with tempfile.TemporaryDirectory(prefix="fiorellia_adapter_") as tmp:
        extract_root = Path(tmp)
        with zipfile.ZipFile(adapter_zip) as archive:
            archive.extractall(extract_root)
        adapter_dir = find_adapter_dir(extract_root)
        tokenizer, model, base_model, device = load_adapter_model(adapter_dir, base_model_override, force_cpu)

        print(f"run_id={run_id}")
        print(f"records={len(records)}")
        print(f"adapter_zip={adapter_zip}")
        print(f"adapter_dir={adapter_dir}")
        print(f"base_model={base_model}")
        print(f"device={device}")
        print(f"log={out_path}")

        for index, record in enumerate(records, start=1):
            timestamp = datetime.now(timezone.utc).isoformat()
            try:
                model_answer = generate_adapter_answer(
                    model=model,
                    tokenizer=tokenizer,
                    system_prompt=system_prompt,
                    user_query=record["user_query"],
                    device=device,
                    max_new_tokens=max_new_tokens,
                )
                error = None
            except Exception as exc:
                model_answer = ""
                error = str(exc)

            log_item = {
                "run_id": run_id,
                "timestamp": timestamp,
                "id": record["id"],
                "category": record["category"],
                "user_query": record["user_query"],
                "model": f"{base_model}+LoRA",
                "mode": "adapter_zip",
                "adapter_zip": str(adapter_zip),
                "model_answer": model_answer,
                "error": error,
            }
            append_log(out_path, log_item)
            print(f"[{index}/{len(records)}] {record['id']} {'error' if error else 'ok'}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fiorell.IA eval harness for prompt-only Ollama or a local LoRA adapter zip.",
    )
    parser.add_argument("--dataset", "--eval_set", dest="dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--system-prompt", "--system_prompt", dest="system_prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--out", "--output", dest="out", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--adapter-zip", "--adapter_zip", dest="adapter_zip", type=Path, default=None)
    parser.add_argument("--base-model", "--base_model", dest="base_model", default=None)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--mode", choices=["auto", "api", "cli"], default="auto")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-new-tokens", "--max_new_tokens", dest="max_new_tokens", type=int, default=160)
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of records to run.")
    parser.add_argument("--force-cpu", action="store_true")
    args = parser.parse_args()

    records = load_jsonl(args.dataset)
    if args.limit is not None:
        records = records[: args.limit]
    system_prompt = args.system_prompt.read_text(encoding="utf-8")
    out_path = resolve_output_path(args.out, adapter_mode=args.adapter_zip is not None)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("", encoding="utf-8")

    if args.adapter_zip is not None:
        return run_adapter_harness(
            records=records,
            system_prompt=system_prompt,
            adapter_zip=args.adapter_zip,
            base_model_override=args.base_model,
            out_path=out_path,
            max_new_tokens=args.max_new_tokens,
            force_cpu=args.force_cpu,
        )

    run_id = datetime.now(timezone.utc).strftime("prompt-harness-%Y%m%dT%H%M%SZ")
    print(f"run_id={run_id}")
    print(f"records={len(records)}")
    print(f"model={args.model}")
    print(f"log={out_path}")

    for index, record in enumerate(records, start=1):
        prompt = build_prompt(system_prompt, record["user_query"])
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            model_answer = answer(prompt, args.model, args.mode, args.ollama_host, args.timeout)
            error = None
        except Exception as exc:
            model_answer = ""
            error = str(exc)

        log_item = {
            "run_id": run_id,
            "timestamp": timestamp,
            "id": record["id"],
            "category": record["category"],
            "user_query": record["user_query"],
            "model": args.model,
            "mode": args.mode,
            "model_answer": model_answer,
            "error": error,
        }
        append_log(out_path, log_item)
        status = "error" if error else "ok"
        print(f"[{index}/{len(records)}] {record['id']} {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
