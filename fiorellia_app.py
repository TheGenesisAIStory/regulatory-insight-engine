#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_ADAPTER = ROOT / "fiorellia" / "training" / "lora" / "fiorellia_behavior_20260421"
DEFAULT_SUMMARY = ROOT / "azure_deploy_summary.json"
DEFAULT_HISTORY = ROOT / "fiorellia_app_history.jsonl"

SYSTEM_PROMPT = (ROOT / "fiorellia" / "prompts" / "system_prompt.txt").read_text(encoding="utf-8")
ABSTENTION_TEXT = (
    "Non ho trovato fonti locali sufficienti per rispondere in modo affidabile. "
    "Posso rispondere solo su contenuti regolamentari bancari supportati dai documenti indicizzati."
)
ABSTENTION_RE = re.compile(
    r"\b(non posso|non ho trovato|fonti insufficienti|senza fonti|mi astengo|fuori dal perimetro)\b",
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


def normalize_endpoint_result(payload: Any) -> dict[str, Any]:
    if isinstance(payload, list) and payload:
        payload = payload[0]
    if isinstance(payload, dict) and "predictions" in payload:
        predictions = payload["predictions"]
        payload = predictions[0] if isinstance(predictions, list) and predictions else predictions
    if not isinstance(payload, dict):
        payload = {"answer": str(payload)}

    answer = str(payload.get("answer") or payload.get("output") or payload.get("response") or payload)
    no_answer = bool(payload.get("noAnswer", payload.get("no_answer", ABSTENTION_RE.search(answer) is not None)))
    label, score = confidence(answer, no_answer)
    return {
        "answer": answer,
        "confidence": payload.get("confidence") or label,
        "confidenceScore": float(payload.get("confidenceScore", payload.get("confidence_score", score))),
        "noAnswer": no_answer,
        "reason": payload.get("reason"),
        "model": payload.get("model", "azure-ml-endpoint"),
    }


class AzureEndpointClient:
    def __init__(self, summary_path: Path):
        summary = load_json(summary_path)
        self.endpoint_url = os.getenv("FIORELLIA_AZURE_ENDPOINT") or summary.get("endpoint_url")
        self.api_key = os.getenv("FIORELLIA_AZURE_API_KEY") or summary.get("api_key")
        self.deployment_name = os.getenv("FIORELLIA_AZURE_DEPLOYMENT") or summary.get("deployment_name")

    @property
    def available(self) -> bool:
        return bool(self.endpoint_url and self.api_key)

    def ask(self, query: str) -> dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.deployment_name:
            headers["azureml-model-deployment"] = self.deployment_name
        body = json.dumps({"query": query}).encode("utf-8")
        request = urllib.request.Request(self.endpoint_url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return normalize_endpoint_result(payload)


class LocalLoraClient:
    def __init__(self, adapter_path: Path):
        self.adapter_path = adapter_path
        self.tokenizer = None
        self.model = None
        self.device = "cpu"
        self.dtype = None

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

        adapter_config = load_json(self.adapter_path / "adapter_config.json")
        base_model = adapter_config.get("base_model_name_or_path", "Qwen/Qwen2.5-3B-Instruct")
        if torch.cuda.is_available():
            self.device = "cuda"
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
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            torch_dtype=self.dtype,
            low_cpu_mem_usage=True,
        )
        self.model = PeftModel.from_pretrained(base, self.adapter_path)
        self.model.to(self.device)
        self.model.eval()

    def _prompt(self, query: str) -> str:
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
        if hasattr(self.tokenizer, "apply_chat_template"):
            return self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        return "\n\n".join(message["content"] for message in messages)

    def ask(self, query: str) -> dict[str, Any]:
        self._load()
        import torch

        prompt = self._prompt(query)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        prompt_len = inputs["input_ids"].shape[-1]
        with torch.no_grad():
            output = self.model.generate(
                **inputs,
                max_new_tokens=220,
                do_sample=False,
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

    def ask(self, query: str) -> dict[str, Any]:
        return {
            "answer": (
                "Risposta:\n"
                f"{ABSTENTION_TEXT}\n\n"
                "Fonti:\n"
                "- Nessuna fonte locale recuperata nella sessione corrente.\n\n"
                "Nota:\n"
                "Avviare il backend RAG o configurare l'endpoint Azure ML per risposte supportate da fonti."
            ),
            "confidence": "low",
            "confidenceScore": 0.18,
            "noAnswer": True,
            "reason": "no_endpoint_or_local_adapter_loaded",
            "model": "safe-fallback",
        }


def choose_client(summary_path: Path, adapter_path: Path) -> Any:
    azure = AzureEndpointClient(summary_path)
    if azure.available:
        return azure
    if os.getenv("FIORELLIA_DISABLE_LOCAL_MODEL") == "1":
        return SafeFallbackClient()
    local = LocalLoraClient(adapter_path)
    if local.available:
        return local
    return SafeFallbackClient()


def answer_query(query: str, client: Any, history_path: Path) -> tuple[str, float, bool, dict[str, Any]]:
    started = time.time()
    try:
        result = client.ask(query)
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


def run_smoke_test(summary_path: Path, adapter_path: Path, history_path: Path) -> int:
    azure = AzureEndpointClient(summary_path)
    if azure.available:
        client = azure
    elif os.getenv("FIORELLIA_SMOKE_LOAD_MODEL") == "1":
        client = choose_client(summary_path, adapter_path)
    else:
        client = SafeFallbackClient()
    answer, score, no_answer, meta = answer_query(
        "Quali disclosure Pillar 3 specifiche pubblica Intesa Sanpaolo nell'ultimo report disponibile?",
        client,
        history_path,
    )
    print(json.dumps({"answer": answer, "confidenceScore": score, "noAnswer": no_answer, "meta": meta}, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Fiorell.IA Gradio release app.")
    parser.add_argument("--summary", type=Path, default=Path(os.getenv("FIORELLIA_AZURE_SUMMARY_PATH", DEFAULT_SUMMARY)))
    parser.add_argument("--adapter-path", type=Path, default=Path(os.getenv("FIORELLIA_ADAPTER_PATH", DEFAULT_ADAPTER)))
    parser.add_argument("--history", type=Path, default=Path(os.getenv("FIORELLIA_HISTORY_PATH", DEFAULT_HISTORY)))
    parser.add_argument("--host", default=os.getenv("FIORELLIA_GRADIO_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("FIORELLIA_GRADIO_PORT", "7860")))
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()

    if args.smoke_test:
        return run_smoke_test(args.summary, args.adapter_path, args.history)

    try:
        import gradio as gr
    except ImportError as exc:
        raise SystemExit("Gradio is not installed. Run: python -m pip install gradio") from exc

    client = choose_client(args.summary, args.adapter_path)

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
