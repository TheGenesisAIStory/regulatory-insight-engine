from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

REPO_URL = "https://github.com/TheGenesisAIStory/regulatory-insight-engine"
RAW_BASE = f"{REPO_URL}/raw/main"
COLAB_DRIVE_ROOT = Path("/content/drive/MyDrive")
DRIVE_REPO_ROOT = COLAB_DRIVE_ROOT / "regulatory-insight-engine"
MAC_DRIVE_REPO_ROOT = Path(
    "/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine"
)


def in_colab() -> bool:
    return Path("/content").exists()


def ensure_drive_mount() -> None:
    if not in_colab():
        return
    if COLAB_DRIVE_ROOT.exists():
        return
    try:
        from google.colab import drive  # type: ignore
    except Exception as exc:
        raise RuntimeError("Google Drive non disponibile nel runtime Colab.") from exc
    drive.mount("/content/drive", force_remount=False)
    if not COLAB_DRIVE_ROOT.exists():
        raise RuntimeError("Google Drive non montato: /content/drive/MyDrive non esiste.")


def resolve_repo_root() -> Path:
    if in_colab():
        root = DRIVE_REPO_ROOT
    elif MAC_DRIVE_REPO_ROOT.exists():
        root = MAC_DRIVE_REPO_ROOT
    else:
        root = Path.cwd()
    root.mkdir(parents=True, exist_ok=True)
    return root


def download_text(relative_path: str) -> str:
    url = f"{RAW_BASE}/{relative_path}"
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def ensure_file(relative_path: str, required_text: str | None = None) -> Path:
    target = REPO_ROOT / relative_path
    refresh = not target.exists()
    if target.exists() and required_text is not None:
        try:
            refresh = required_text not in target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            refresh = True
    if refresh:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(download_text(relative_path), encoding="utf-8")
        print(f"Updated from GitHub: {relative_path}")
    return target


def ensure_aliases() -> None:
    alias_pairs = [
        ("fiorellia/prompts/system_prompt.md", "fiorellia/prompts/system_prompt.txt"),
        ("fiorellia/eval/eval_set.jsonl", "fiorellia/eval/eval_set_v0.jsonl"),
        ("fiorellia/eval/baseline.jsonl", "fiorellia/eval/prompt_harness_baseline_20260421.jsonl"),
    ]
    for dst_rel, src_rel in alias_pairs:
        dst = REPO_ROOT / dst_rel
        src = REPO_ROOT / src_rel
        if not dst.exists() and src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"Created alias: {dst_rel}")
    for init_rel in [
        "fiorellia/__init__.py",
        "fiorellia/training/__init__.py",
        "fiorellia/eval/__init__.py",
    ]:
        init_path = REPO_ROOT / init_rel
        init_path.parent.mkdir(parents=True, exist_ok=True)
        init_path.touch(exist_ok=True)


ensure_drive_mount()
REPO_ROOT = resolve_repo_root()
ARTIFACT_DIR = REPO_ROOT / "fiorellia-runs" / "final_delivery_latest"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
os.environ["FIORELLIA_DRIVE_REPO_ROOT"] = str(REPO_ROOT)
os.chdir(REPO_ROOT)
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ensure_file("fiorellia_colab_cell04_hotfix.py", "Runner mount guard verified")
ensure_file("fiorellia/training/final_colab_certification.py", "Drive already available, skipping mount.")
ensure_file("final_perfection_run.py", "Fiorell.IA failure audit, final dataset recovery")
ensure_file("fiorellia_gold_zero_touch.py", "GOLD_RELEASE")
ensure_file("fiorellia_gold_rescore_existing.py", "Rescore an existing Fiorell.IA Gold eval")
ensure_file("fiorellia/training/train_lora_behavior_v1.py", "weight_decay")
ensure_file("fiorellia/training/fiorellia_colab_pipeline.py", "crr\\s*,?\\s*art")
ensure_file("fiorellia/training/build_behavior_hardening_v2.py", "supervised_v2_behavior_hardening_20260526")
ensure_file("fiorellia/training/configs/config_lora_behavior_20260526_behavior_hardening.yaml", "fiorellia_behavior_hardening_20260526")
ensure_file("fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl", "fio-v2-ua-001")
ensure_file("fiorellia/prompts/system_prompt_strict.md", "Regole vincolanti")
ensure_file("fiorellia/prompts/system_prompt_short.md", "Formato:")
ensure_file("fiorellia/eval/eval_set_behavior_hardening_v1.jsonl", "fio-v1-001")
ensure_file("fiorellia_app_colab.py", "Fiorell.IA Colab Gradio launcher")
ensure_file("fiorellia_app.py", "Model loaded on:")
ensure_aliases()

print(
    json.dumps(
        {
            "drive_first_bootstrap": "OK",
            "repo_root": str(REPO_ROOT),
            "artifact_dir": str(ARTIFACT_DIR),
        },
        indent=2,
        ensure_ascii=False,
    )
)
