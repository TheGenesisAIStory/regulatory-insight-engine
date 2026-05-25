from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


SYSTEM_PROMPT = """Sei Fiorell.IA, un assistente regolamentare bancario italian-first.
Rispondi solo se il contesto o la richiesta forniscono fonti locali sufficienti.
Non inventare articoli, pagine, date, banche, classifiche o citazioni.
Se le fonti sono insufficienti, astieniti chiaramente.
Rispondi in italiano con tono tecnico, prudente e conciso.
Formato:
Risposta:
<risposta o astensione>

Fonti:
- <fonte locale, se disponibile>

Nota:
Risposta limitata ai documenti indicizzati nel corpus locale."""

ABSTENTION_RE = re.compile(
    r"\b(non posso|non ho trovato|fonti insufficienti|senza fonti|mi astengo|fuori dal perimetro)\b",
    re.IGNORECASE,
)

tokenizer: AutoTokenizer | None = None
model: PeftModel | None = None
device = "cpu"


def _find_adapter_dir() -> Path:
    model_root = Path(os.environ.get("AZUREML_MODEL_DIR", "/var/azureml-app/azureml-models"))
    candidates = [path for path in model_root.rglob("adapter_config.json")]
    if not candidates:
        raise FileNotFoundError(f"adapter_config.json not found under {model_root}")
    return candidates[0].parent


def _detect_device() -> tuple[str, torch.dtype]:
    if torch.cuda.is_available():
        return "cuda", torch.float16
    return "cpu", torch.float32


def init() -> None:
    global tokenizer, model, device
    adapter_dir = _find_adapter_dir()
    adapter_config = json.loads((adapter_dir / "adapter_config.json").read_text(encoding="utf-8"))
    base_model = adapter_config.get("base_model_name_or_path", "Qwen/Qwen2.5-3B-Instruct")
    device, dtype = _detect_device()

    tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=dtype,
        low_cpu_mem_usage=True,
    )
    model = PeftModel.from_pretrained(base, adapter_dir)
    model.to(device)
    model.eval()


def _payload_query(payload: Any) -> str:
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            return payload
    if isinstance(payload, dict):
        if "query" in payload:
            return str(payload["query"])
        if "question" in payload:
            return str(payload["question"])
        data = payload.get("data")
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return str(first.get("query") or first.get("question") or "")
            return str(first)
    return ""


def _build_prompt(query: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Domanda utente:\n"
                f"{query.strip()}\n\n"
                "Rispondi secondo le regole Fiorell.IA. Se mancano fonti locali recuperate, astieniti."
            ),
        },
    ]
    assert tokenizer is not None
    if hasattr(tokenizer, "apply_chat_template"):
        return tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    return "\n\n".join(message["content"] for message in messages)


def _score_confidence(answer: str, no_answer: bool) -> tuple[str, float]:
    if no_answer:
        return "low", 0.18
    has_sources = "Fonti:" in answer and "-" in answer.split("Fonti:", 1)[-1]
    if has_sources:
        return "medium", 0.72
    return "low", 0.42


def run(raw_data: Any) -> dict[str, Any]:
    if model is None or tokenizer is None:
        raise RuntimeError("Model is not initialized.")
    query = _payload_query(raw_data).strip()
    if not query:
        return {
            "answer": "Non posso rispondere: la domanda e' vuota.",
            "confidence": "low",
            "confidenceScore": 0.0,
            "noAnswer": True,
            "reason": "empty_query",
        }

    prompt = _build_prompt(query)
    inputs = tokenizer(prompt, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}
    prompt_len = inputs["input_ids"].shape[-1]

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=220,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )

    answer = tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True).strip()
    no_answer = bool(ABSTENTION_RE.search(answer))
    confidence, confidence_score = _score_confidence(answer, no_answer)
    return {
        "answer": answer,
        "confidence": confidence,
        "confidenceScore": confidence_score,
        "noAnswer": no_answer,
        "reason": "abstention_detected" if no_answer else None,
        "model": "Qwen/Qwen2.5-3B-Instruct+Fiorell.IA-LoRA",
    }
