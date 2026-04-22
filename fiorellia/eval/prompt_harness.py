#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request as urlrequest
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = ROOT / "fiorellia" / "eval" / "eval_set_v0.jsonl"
DEFAULT_SYSTEM_PROMPT = ROOT / "fiorellia" / "prompts" / "system_prompt.txt"
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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prompt-only Fiorell.IA harness. Does not import or modify backend runtime.",
    )
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--system-prompt", type=Path, default=DEFAULT_SYSTEM_PROMPT)
    parser.add_argument("--out", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-host", default=DEFAULT_OLLAMA_HOST)
    parser.add_argument("--mode", choices=["auto", "api", "cli"], default="auto")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--limit", type=int, default=None, help="Optional max number of records to run.")
    args = parser.parse_args()

    records = load_jsonl(args.dataset)
    if args.limit is not None:
        records = records[: args.limit]
    system_prompt = args.system_prompt.read_text(encoding="utf-8")

    run_id = datetime.now(timezone.utc).strftime("prompt-harness-%Y%m%dT%H%M%SZ")
    print(f"run_id={run_id}")
    print(f"records={len(records)}")
    print(f"model={args.model}")
    print(f"log={args.out}")

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
        append_log(args.out, log_item)
        status = "error" if error else "ok"
        print(f"[{index}/{len(records)}] {record['id']} {status}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
