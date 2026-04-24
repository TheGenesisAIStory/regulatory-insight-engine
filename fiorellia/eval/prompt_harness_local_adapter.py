#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "fiorellia" / "eval" / "eval_set_v0.jsonl"
DEFAULT_SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt.txt"
DEFAULT_OUTPUT = ROOT / "fiorellia" / "eval" / "prompt_harness_behavior_lora_20260421.jsonl"
DEFAULT_ADAPTER = ROOT / "fiorellia" / "training" / "lora" / "fiorellia_behavior_20260421"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "id" not in row or "category" not in row or "user_query" not in row:
                raise ValueError(f"Invalid record at {path}:{line_no}")
            rows.append(row)
    return rows


def detect_device(force_cpu: bool) -> tuple[str, torch.dtype]:
    if not force_cpu and torch.cuda.is_available():
        return "cuda", torch.float16
    if not force_cpu and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", torch.float16
    return "cpu", torch.float32


def is_mps_oom(exc: Exception) -> bool:
    message = str(exc).lower()
    return "mps" in message and "out of memory" in message


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


def build_inputs(
    tokenizer: AutoTokenizer,
    system_prompt: str,
    user_query: str,
    device: str,
) -> dict[str, torch.Tensor]:
    messages = build_messages(system_prompt, user_query)
    if hasattr(tokenizer, "apply_chat_template"):
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        prompt_text = "\n\n".join(message["content"] for message in messages)
    encoded = tokenizer(prompt_text, return_tensors="pt")
    return {key: value.to(device) for key, value in encoded.items()}


def load_model_and_tokenizer(
    adapter_path: Path,
    base_model_name: str,
    device: str,
    dtype: torch.dtype,
) -> tuple[AutoTokenizer, PeftModel]:
    tokenizer = AutoTokenizer.from_pretrained(base_model_name, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(model, adapter_path)
    model.to(device)
    model.eval()
    return tokenizer, model


def generate_answer(
    model: PeftModel,
    tokenizer: AutoTokenizer,
    system_prompt: str,
    user_query: str,
    device: str,
    max_new_tokens: int,
) -> str:
    inputs = build_inputs(tokenizer, system_prompt, user_query, device)
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


def append_log(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Fiorell.IA eval directly on base model + local LoRA adapter.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--adapter-path", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--base-model", default=None, help="Optional override for the base model name.")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--force-cpu", action="store_true")
    args = parser.parse_args()

    adapter_config = json.loads((args.adapter_path / "adapter_config.json").read_text(encoding="utf-8"))
    base_model = args.base_model or adapter_config["base_model_name_or_path"]
    device, dtype = detect_device(args.force_cpu)
    records = load_jsonl(args.dataset)
    if args.limit is not None:
        records = records[: args.limit]
    system_prompt = args.system_prompt.read_text(encoding="utf-8")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("", encoding="utf-8")

    print(f"dataset={args.dataset}")
    print(f"adapter={args.adapter_path}")
    print(f"base_model={base_model}")
    print(f"device={device}")
    print(f"out={args.out}")
    print(f"records={len(records)}")

    try:
        tokenizer, model = load_model_and_tokenizer(args.adapter_path, base_model, device, dtype)
    except RuntimeError as exc:
        if device == "mps" and not args.force_cpu and is_mps_oom(exc):
            print("mps_oom_detected=true")
            print("fallback_device=cpu")
            device, dtype = "cpu", torch.float32
            tokenizer, model = load_model_and_tokenizer(args.adapter_path, base_model, device, dtype)
        else:
            raise
    run_id = datetime.now(timezone.utc).strftime("prompt-harness-local-adapter-%Y%m%dT%H%M%SZ")

    for index, record in enumerate(records, start=1):
        timestamp = datetime.now(timezone.utc).isoformat()
        try:
            model_answer = generate_answer(
                model=model,
                tokenizer=tokenizer,
                system_prompt=system_prompt,
                user_query=record["user_query"],
                device=device,
                max_new_tokens=args.max_new_tokens,
            )
            error = None
        except Exception as exc:
            model_answer = ""
            error = str(exc)

        row = {
            "run_id": run_id,
            "timestamp": timestamp,
            "id": record["id"],
            "category": record["category"],
            "user_query": record["user_query"],
            "model": f"{base_model}+{args.adapter_path.name}",
            "mode": "local_adapter",
            "model_answer": model_answer,
            "error": error,
        }
        append_log(args.out, row)
        print(f"[{index}/{len(records)}] {record['id']} {'error' if error else 'ok'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
