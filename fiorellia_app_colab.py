#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from fiorellia_app import DEFAULT_ADAPTER, DEFAULT_HISTORY, SMOKE_CASES, answer_query, choose_client


def run_final_tests(adapter_path: Path, history_path: Path, output_path: Path) -> int:
    os.environ["FIORELLIA_SMOKE_LOAD_MODEL"] = "1"
    client = choose_client(adapter_path)
    results: list[dict[str, Any]] = []
    for case in SMOKE_CASES:
        answer, score, no_answer, meta = answer_query(case["query"], client, history_path, case.get("retrieved_context", ""))
        expected = bool(case["expected_no_answer"])
        results.append(
            {
                "id": case["id"],
                "ok": no_answer == expected,
                "expectedNoAnswer": expected,
                "noAnswer": no_answer,
                "confidenceScore": score,
                "meta": meta,
                "answerPreview": answer[:500],
            }
        )
    payload = {
        "verdict": "GO" if all(item["ok"] for item in results) else "NO-GO",
        "adapterPath": str(adapter_path),
        "historyPath": str(history_path),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["verdict"] == "GO" else 2


def launch(adapter_path: Path, history_path: Path, host: str, port: int, share: bool) -> int:
    import gradio as gr
    from fiorellia_app import answer_query, export_history

    client = choose_client(adapter_path)
    with gr.Blocks(title="Fiorell.IA Final Release") as demo:
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
            fn=lambda q: answer_query(q, client, history_path),
            inputs=query,
            outputs=[answer, score, abstention, meta],
        )
        export.click(fn=lambda: export_history(history_path), inputs=None, outputs=export_path)
    demo.launch(server_name=host, server_port=port, share=share)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Fiorell.IA Colab Gradio launcher/test runner.")
    parser.add_argument("--adapter-path", type=Path, default=Path(os.getenv("FIORELLIA_ADAPTER_PATH", DEFAULT_ADAPTER)))
    parser.add_argument("--history", type=Path, default=Path(os.getenv("FIORELLIA_HISTORY_PATH", DEFAULT_HISTORY)))
    parser.add_argument("--output", type=Path, default=Path("app_final_test_results.json"))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--share", action="store_true")
    parser.add_argument("--final-tests", action="store_true")
    args = parser.parse_args()
    if args.final_tests:
        return run_final_tests(args.adapter_path, args.history, args.output)
    return launch(args.adapter_path, args.history, args.host, args.port, args.share)


if __name__ == "__main__":
    raise SystemExit(main())
