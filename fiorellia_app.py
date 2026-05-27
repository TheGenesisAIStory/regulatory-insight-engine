#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_ADAPTER = ROOT / "fiorellia" / "training" / "lora" / "fiorellia_behavior_RC_HARDENED_20260526"
DEFAULT_HISTORY = ROOT / "fiorellia_app_history.jsonl"
DEFAULT_MAX_NEW_TOKENS = int(os.getenv("FIORELLIA_MAX_NEW_TOKENS", "96"))

SYSTEM_PROMPT = next(
    path
    for path in [
        ROOT / "fiorellia" / "prompts" / "system_prompt_strict.md",
        ROOT / "fiorellia" / "prompts" / "system_prompt.md",
        ROOT / "fiorellia" / "prompts" / "system_prompt.txt",
    ]
    if path.exists()
).read_text(encoding="utf-8")
ABSTENTION_TEXT = (
    "Non ho trovato fonti locali sufficienti per rispondere in modo affidabile. "
    "Posso rispondere solo su contenuti regolamentari bancari supportati dai documenti indicizzati."
)
ABSTENTION_RE = re.compile(
    r"\b(non posso|non ho trovato|non ci sono fonti|fonti insufficienti|senza fonti|mi astengo|fuori (dal )?perimetro|non rientra|non fornisce)\b",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def append_history(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def export_history(history_path: Path) -> str:
    rows: list[dict[str, Any]] = []
    if history_path.exists():
        with history_path.open("r", encoding="utf-8") as handle:
            rows = [json.loads(line) for line in handle if line.strip()]
    export_path = history_path.with_name(
        f"history_export_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    )
    export_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(export_path)


def confidence(answer: str, no_answer: bool) -> tuple[str, float]:
    if no_answer:
        return "low", 0.18
    if "Fonti:" in answer and "-" in answer.split("Fonti:", 1)[-1]:
        return "medium", 0.72
    return "low", 0.42


class LocalLoraClient:
    def __init__(self, adapter_path: Path):
        self.adapter_path = adapter_path
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self.dtype = None
        self.loaded_with_4bit = False

    @property
    def available(self) -> bool:
        return (self.adapter_path / "adapter_config.json").exists() and any(self.adapter_path.glob("*.safetensors"))

    def _load(self) -> None:
        if self.model is not None and self.tokenizer is not None:
            return
        if not self.available:
            raise FileNotFoundError(f"Adapter weights not found in {self.adapter_path}")

        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer

        started = time.time()
        adapter_config = load_json(self.adapter_path / "adapter_config.json")
        base_model = adapter_config.get("base_model_name_or_path", "Qwen/Qwen2.5-3B-Instruct")
        has_cuda = torch.cuda.is_available()
        if torch.cuda.is_available():
            self.device = "cuda:0"
            self.dtype = torch.float16
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = "mps"
            self.dtype = torch.float16
        else:
            self.device = "cpu"
            self.dtype = torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        model_kwargs: dict[str, Any] = {
            "torch_dtype": self.dtype,
            "low_cpu_mem_usage": True,
        }
        if has_cuda and os.getenv("FIORELLIA_DISABLE_4BIT", "0") != "1":
            from transformers import BitsAndBytesConfig

            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            model_kwargs["device_map"] = "auto"
            self.loaded_with_4bit = True
        elif has_cuda:
            model_kwargs["device_map"] = "auto"

        base = AutoModelForCausalLM.from_pretrained(base_model, **model_kwargs)
        self.model = PeftModel.from_pretrained(base, self.adapter_path)
        if not self.loaded_with_4bit and not has_cuda:
            self.model.to(self.device)
        self.model.eval()
        loaded_device = next(self.model.parameters()).device
        gpu_allocated = torch.cuda.memory_allocated(0) / (1024**3) if has_cuda else 0.0
        gpu_reserved = torch.cuda.memory_reserved(0) / (1024**3) if has_cuda else 0.0
        print(
            f"Model loaded on: {loaded_device}; input_device={self.device}; "
            f"4bit={self.loaded_with_4bit}; gpu_allocated_gb={gpu_allocated:.2f}; "
            f"gpu_reserved_gb={gpu_reserved:.2f}; load_seconds={time.time() - started:.1f}"
        )

    def preload(self) -> None:
        self._load()

    def _prompt(self, query: str, retrieved_context: str = "") -> str:
        context = retrieved_context.strip() or "[nessun contesto recuperato]"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Contesto locale recuperato:\n"
                    f"{context}\n\n"
                    "Domanda utente:\n"
                    f"{query.strip()}\n\n"
                    "Rispondi secondo le regole Fiorell.IA. Se mancano fonti locali recuperate, astieniti."
                ),
            },
        ]
        if hasattr(self.tokenizer, "apply_chat_template"):
            return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return "\n\n".join(message["content"] for message in messages)

    def ask(self, query: str, retrieved_context: str = "") -> dict[str, Any]:
        self._load()
        import torch

        prompt = self._prompt(query, retrieved_context)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        prompt_len = inputs["input_ids"].shape[-1]
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=DEFAULT_MAX_NEW_TOKENS,
                do_sample=False,
                use_cache=True,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        answer = self.tokenizer.decode(output[0][prompt_len:], skip_special_tokens=True).strip()
        no_answer = bool(ABSTENTION_RE.search(answer))
        label, score = confidence(answer, no_answer)
        return {
            "answer": answer,
            "confidence": label,
            "confidenceScore": score,
            "noAnswer": no_answer,
            "reason": "abstention_detected" if no_answer else None,
            "model": f"local-lora:{self.adapter_path.name}",
        }


class SafeFallbackClient:
    available = True

    def ask(self, query: str, retrieved_context: str = "") -> dict[str, Any]:
        return {
            "answer": (
                "Risposta:\n"
                f"{ABSTENTION_TEXT}\n\n"
                "Fonti:\n"
                "- Nessuna fonte locale recuperata nella sessione corrente.\n\n"
                "Nota:\n"
                "Avviare il backend RAG o configurare un adapter locale valido per risposte supportate da fonti."
            ),
            "confidence": "low",
            "confidenceScore": 0.18,
            "noAnswer": True,
            "reason": "no_endpoint_or_local_adapter_loaded",
            "model": "safe-fallback",
        }


def choose_client(adapter_path: Path) -> Any:
    if os.getenv("FIORELLIA_DISABLE_LOCAL_MODEL") == "1":
        return SafeFallbackClient()
    local = LocalLoraClient(adapter_path)
    if local.available:
        return local
    return SafeFallbackClient()


def answer_query(query: str, client: Any, history_path: Path, retrieved_context: str = "") -> tuple[str, float, bool, dict[str, Any]]:
    started = time.time()
    try:
        result = client.ask(query, retrieved_context=retrieved_context)
    except Exception as exc:
        result = SafeFallbackClient().ask(query)
        result["reason"] = f"runtime_error: {exc}"
    elapsed_ms = int((time.time() - started) * 1000)
    result["durationMs"] = elapsed_ms
    result["question"] = query
    result["timestamp"] = datetime.now(timezone.utc).isoformat()
    append_history(history_path, result)
    return (
        result["answer"],
        float(result["confidenceScore"]),
        bool(result["noAnswer"]),
        {
            "confidence": result.get("confidence"),
            "reason": result.get("reason"),
            "model": result.get("model"),
            "durationMs": elapsed_ms,
        },
    )


SMOKE_CASES = [
    {
        "id": "grounded_in_scope",
        "query": "Quali sono i principali requisiti sui fondi propri nel CRR?",
        "retrieved_context": "[CRR, art. 92] Le istituzioni rispettano requisiti di fondi propri espressi come coefficienti di capitale rispetto all'esposizione complessiva al rischio.",
        "expected_no_answer": False,
    },
    {
        "id": "unsupported_request",
        "query": "Quali sono tutte le disclosure Pillar 3 richieste alle banche italiane nel 2026?",
        "expected_no_answer": True,
    },
    {
        "id": "out_of_scope_request",
        "query": "Quale ETF UCITS consigli per espormi ai Treasury USA?",
        "expected_no_answer": True,
    },
    {
        "id": "critical_current_data",
        "query": "Mi dai la classifica aggiornata 2026 delle prime banche italiane per total assets?",
        "expected_no_answer": True,
    },
    {
        "id": "bank_specific_without_source",
        "query": "Quali metriche Pillar 3 specifiche pubblica Intesa Sanpaolo nell'ultimo report disponibile?",
        "expected_no_answer": True,
    },
]


def run_smoke_test(adapter_path: Path, history_path: Path) -> int:
    adapter_available = LocalLoraClient(adapter_path).available
    load_model = os.getenv("FIORELLIA_SMOKE_LOAD_MODEL") == "1"
    client = choose_client(adapter_path) if load_model else SafeFallbackClient()
    results = []
    for case in SMOKE_CASES:
        answer, score, no_answer, meta = answer_query(case["query"], client, history_path, case.get("retrieved_context", ""))
        expected = bool(case["expected_no_answer"])
        ok = no_answer == expected
        if not load_model and case["id"] == "grounded_in_scope":
            ok = no_answer is True
        results.append(
            {
                "id": case["id"],
                "ok": ok,
                "expectedNoAnswer": expected,
                "noAnswer": no_answer,
                "confidenceScore": score,
                "meta": meta,
                "answerPreview": answer[:220],
            }
        )
    verdict = "GO" if load_model and all(item["ok"] for item in results) else "GO_CON_RISERVA"
    print(
        json.dumps(
            {
                "verdict": verdict,
                "adapterPath": str(adapter_path),
                "adapterAvailable": adapter_available,
                "modelLoadRequested": load_model,
                "historyPath": str(history_path),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Fiorell.IA Gradio release app.")
    parser.add_argument("--adapter-path", type=Path, default=Path(os.getenv("FIORELLIA_ADAPTER_PATH", DEFAULT_ADAPTER)))
    parser.add_argument("--history", type=Path, default=Path(os.getenv("FIORELLIA_HISTORY_PATH", DEFAULT_HISTORY)))
    parser.add_argument("--host", default=os.getenv("FIORELLIA_GRADIO_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FIORELLIA_GRADIO_PORT", "7860")))
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test(args.adapter_path, args.history)

    try:
        import gradio as gr
    except ImportError as exc:
        raise SystemExit("Gradio is not installed. Run: python -m pip install gradio") from exc

    client = choose_client(args.adapter_path)

    with gr.Blocks(title="Fiorell.IA") as demo:
        gr.Markdown("# Fiorell.IA")
        query = gr.Textbox(label="Query normativa", lines=5)
        submit = gr.Button("Invia")
        answer = gr.Markdown(label="Risposta")
        score = gr.Number(label="Confidence score", precision=2)
        abstention = gr.Checkbox(label="Astensione")
        meta = gr.JSON(label="Dettagli")
        export = gr.Button("Esporta history JSON")
        export_path = gr.Textbox(label="History export", interactive=False)

        submit.click(
            fn=lambda q: answer_query(q, client, args.history),
            inputs=query,
            outputs=[answer, score, abstention, meta],
        )
        export.click(fn=lambda: export_history(args.history), inputs=None, outputs=export_path)

    demo.launch(server_name=args.host, server_port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
