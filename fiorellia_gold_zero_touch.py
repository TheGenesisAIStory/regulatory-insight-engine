#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_URL = "https://github.com/TheGenesisAIStory/regulatory-insight-engine"
RAW_BASE = f"{REPO_URL}/raw/main"
DRIVE_ROOT = Path("/content/drive/MyDrive")
DRIVE_REPO_ROOT = DRIVE_ROOT / "regulatory-insight-engine"
ARTIFACT_DIR = DRIVE_REPO_ROOT / "fiorellia-runs" / "final_delivery_latest"
RELEASE_DIR = DRIVE_REPO_ROOT / "releases" / "gold_release_latest"
FINAL_NAME = "fiorellia_behavior_GOLD_RELEASE_20260527"
GOLD_DATASET = DRIVE_REPO_ROOT / "fiorellia" / "training" / "supervised_gold_release_20260527.jsonl"
GOLD_CARD = DRIVE_REPO_ROOT / "fiorellia" / "training" / "supervised_gold_release_20260527.md"
GOLD_CONFIG = DRIVE_REPO_ROOT / "fiorellia" / "training" / "configs" / "config_lora_behavior_20260527_gold_release.yaml"


def run(command: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(str(part) for part in command))
    return subprocess.run(command, cwd=cwd, check=check, text=True)


def now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def in_colab() -> bool:
    return Path("/content").exists()


def mount_drive() -> None:
    if not in_colab():
        raise RuntimeError("BLOCCANTE: questo notebook deve essere eseguito in Google Colab.")
    if DRIVE_ROOT.exists():
        print("Drive already mounted.")
        return
    try:
        from google.colab import drive  # type: ignore
    except Exception as exc:
        raise RuntimeError("BLOCCANTE: google.colab non disponibile. Apri il notebook in Colab web.") from exc
    drive.mount("/content/drive", force_remount=False)
    if not DRIVE_ROOT.exists():
        raise RuntimeError("BLOCCANTE: Google Drive non montato in /content/drive/MyDrive.")


def download_text(relative_path: str) -> str:
    with urllib.request.urlopen(f"{RAW_BASE}/{relative_path}") as response:
        return response.read().decode("utf-8")


def ensure_file_from_github(relative_path: str, marker: str | None = None) -> Path:
    target = DRIVE_REPO_ROOT / relative_path
    refresh = not target.exists()
    if target.exists() and marker is not None:
        try:
            refresh = marker not in target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            refresh = True
    if refresh:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(download_text(relative_path), encoding="utf-8")
        print(f"Updated from GitHub: {relative_path}")
    return target


def ensure_repo_root() -> None:
    DRIVE_REPO_ROOT.mkdir(parents=True, exist_ok=True)
    os.chdir(DRIVE_REPO_ROOT)
    if str(DRIVE_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(DRIVE_REPO_ROOT))
    if not (DRIVE_REPO_ROOT / ".git").exists():
        print("Drive repo has no .git; using raw GitHub refresh for critical files.")
        return
    status = run(["git", "status", "--porcelain"], cwd=DRIVE_REPO_ROOT, check=False)
    if status.returncode == 0:
        run(["git", "pull", "--ff-only", "origin", "main"], cwd=DRIVE_REPO_ROOT, check=False)


def refresh_critical_files() -> None:
    critical_files = {
        "fiorellia_colab_drive_bootstrap.py": "drive_first_bootstrap",
        "final_perfection_run.py": "gold-release",
        "fiorellia_gold_zero_touch.py": "GOLD_RELEASE",
        "fiorellia/training/train_lora_behavior_v1.py": "weight_decay",
        "fiorellia/training/fiorellia_colab_pipeline.py": "documentazione statica",
        "fiorellia/training/final_colab_certification.py": "Drive already available",
        "fiorellia/eval/prompt_harness_local_adapter.py": "Contesto locale recuperato",
        "fiorellia/prompts/system_prompt_strict.md": "Regole vincolanti",
        "fiorellia/eval/eval_set_behavior_hardening_v1.jsonl": "fio-v1-001",
        "fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl": "fio-v2-ua-001",
        "fiorellia/training/configs/config_lora_behavior_20260526_behavior_hardening.yaml": "fiorellia_behavior_hardening_20260526",
        "fiorellia_app.py": "SMOKE_CASES",
        "fiorellia_app_colab.py": "Fiorell.IA Colab Gradio launcher",
    }
    for relative_path, marker in critical_files.items():
        ensure_file_from_github(relative_path, marker)


def harmonize_drive() -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    (DRIVE_REPO_ROOT / "archive").mkdir(parents=True, exist_ok=True)
    archive_dir = DRIVE_REPO_ROOT / "archive" / f"stale_gold_release_{now_stamp()}"
    moved: list[str] = []
    for pattern in ["metrics_summary*.json", "final_verdict*.md", "final_perfection_summary*.json", "app_launch_status*.json"]:
        for source in ARTIFACT_DIR.glob(pattern):
            archive_dir.mkdir(parents=True, exist_ok=True)
            target = archive_dir / source.name
            shutil.move(str(source), str(target))
            moved.append(str(target))
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(DRIVE_REPO_ROOT),
        "artifact_dir": str(ARTIFACT_DIR),
        "release_dir": str(RELEASE_DIR),
        "archived_stale_files": moved,
    }
    (DRIVE_REPO_ROOT / "drive_harmonization_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return manifest


def install_minimal_dependencies() -> None:
    run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "pyyaml>=6.0",
            "gradio>=4.0",
        ]
    )


def verify_cuda_a100() -> dict[str, Any]:
    nvidia = run(["nvidia-smi"], check=False)
    if nvidia.returncode != 0:
        raise RuntimeError(
            "BLOCCANTE: CUDA non visibile. In Colab usa Runtime > Cambia tipo di runtime > GPU A100."
        )
    import torch

    info = {
        "torch_version": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if not info["cuda_available"]:
        raise RuntimeError(
            "BLOCCANTE: torch.cuda.is_available() è False. In Colab seleziona una GPU A100 e riavvia la sessione."
        )
    if "A100" not in str(info["device_name"]):
        raise RuntimeError(f"BLOCCANTE: GPU rilevata non A100: {info['device_name']}. Cambia runtime Colab.")
    (ARTIFACT_DIR / "runtime_gpu.json").write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    return info


def run_gold_certification() -> dict[str, Any]:
    command = [
        sys.executable,
        "final_perfection_run.py",
        "--gold-release",
        "--install-deps",
        "--copy-verdict-to-repo",
        "--artifact-dir",
        str(ARTIFACT_DIR),
        "--release-dir",
        str(RELEASE_DIR),
        "--final-name",
        FINAL_NAME,
        "--output-dataset",
        str(GOLD_DATASET),
        "--output-card",
        str(GOLD_CARD),
        "--output-config",
        str(GOLD_CONFIG),
        "--learning-rate",
        "3e-5",
        "--num-train-epochs",
        "10",
        "--gradient-accumulation-steps",
        "4",
        "--weight-decay",
        "0.05",
    ]
    completed = run(command, cwd=DRIVE_REPO_ROOT, check=False)
    summary_path = ARTIFACT_DIR / "final_perfection_summary.json"
    if completed.returncode not in (0, 2) or not summary_path.exists():
        raise RuntimeError(f"BLOCCANTE: Gold release failed before summary. returncode={completed.returncode}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["runner_returncode"] = completed.returncode
    return summary


def write_gold_demo_status(payload: dict[str, Any]) -> None:
    (ARTIFACT_DIR / "gold_demo_status.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def launch_gold_demo(summary: dict[str, Any]) -> None:
    if summary.get("verdict") != "GO DEFINITIVO":
        write_gold_demo_status({"launched": False, "reason": "verdict_not_go", "verdict": summary.get("verdict")})
        print("Gold demo non avviata: verdict non GO.")
        return

    import gradio as gr
    from fiorellia_app import answer_query, choose_client, export_history

    adapter_dir = Path(summary.get("adapter_dir") or f"/content/{FINAL_NAME}")
    history_path = ARTIFACT_DIR / "gold_demo_history.jsonl"
    client = choose_client(adapter_dir)

    examples = {
        "Normativa": (
            "Quale indicazione generale sui fondi propri emerge dal passaggio CRR recuperato?",
            "[CRR, art. 92] Le istituzioni rispettano requisiti di fondi propri espressi come coefficienti di capitale rispetto all'esposizione complessiva al rischio.",
        ),
        "Fuori Ambito": (
            "Quale ETF UCITS consigli per espormi ai Treasury USA?",
            "",
        ),
        "Allucinazione": (
            "Quali sono tutte le disclosure Pillar 3 richieste alle banche italiane nel 2026?",
            "",
        ),
    }

    def preset(name: str) -> tuple[str, str]:
        return examples[name]

    def ask(query: str, context: str) -> tuple[str, float, bool, dict[str, Any]]:
        return answer_query(query, client, history_path, context)

    with gr.Blocks(title="Fiorell.IA Gold Release") as demo:
        gr.Markdown("# Fiorell.IA Gold Release")
        with gr.Row():
            norm_btn = gr.Button("Normativa")
            oos_btn = gr.Button("Fuori Ambito")
            hallucination_btn = gr.Button("Allucinazione")
        query = gr.Textbox(label="Query normativa", lines=4)
        context = gr.Textbox(label="Contesto recuperato", lines=4)
        submit = gr.Button("Invia")
        answer = gr.Markdown(label="Risposta")
        score = gr.Number(label="Confidence score", precision=2)
        abstention = gr.Checkbox(label="Astensione")
        meta = gr.JSON(label="Dettagli")
        export = gr.Button("Esporta history JSON")
        export_path = gr.Textbox(label="History export", interactive=False)
        norm_btn.click(lambda: preset("Normativa"), outputs=[query, context])
        oos_btn.click(lambda: preset("Fuori Ambito"), outputs=[query, context])
        hallucination_btn.click(lambda: preset("Allucinazione"), outputs=[query, context])
        submit.click(fn=ask, inputs=[query, context], outputs=[answer, score, abstention, meta])
        export.click(fn=lambda: export_history(history_path), inputs=None, outputs=export_path)
    write_gold_demo_status({"launched": True, "adapter_dir": str(adapter_dir), "history_path": str(history_path)})
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


def main() -> int:
    mount_drive()
    ensure_repo_root()
    refresh_critical_files()
    manifest = harmonize_drive()
    install_minimal_dependencies()
    runtime = verify_cuda_a100()
    print(json.dumps({"drive": manifest, "runtime": runtime}, indent=2, ensure_ascii=False))
    summary = run_gold_certification()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    launch_gold_demo(summary)
    return 0 if summary.get("verdict") == "GO DEFINITIVO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
