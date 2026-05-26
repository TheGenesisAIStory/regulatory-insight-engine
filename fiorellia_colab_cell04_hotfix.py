from pathlib import Path
import os
import subprocess
import sys

REPO_ROOT = Path("/content/drive/MyDrive/regulatory-insight-engine")
ARTIFACT_DIR = REPO_ROOT / "fiorellia-runs" / "final_delivery_latest"
runner_path = REPO_ROOT / "fiorellia" / "training" / "final_colab_certification.py"

if not (Path("/content/drive/MyDrive")).exists():
    raise RuntimeError("Drive non montato. Esegui prima: from google.colab import drive; drive.mount('/content/drive')")
if not runner_path.exists():
    raise FileNotFoundError(runner_path)

mount_guard = '''def mount_drive_if_colab() -> None:
    drive_path = Path("/content/drive/MyDrive")
    if drive_path.exists():
        print("Drive already available, skipping mount.")
        return

    try:
        from google.colab import drive  # type: ignore
    except Exception:
        print("google.colab non disponibile, skip mount.")
        return

    try:
        import IPython

        if IPython.get_ipython() is None:
            raise RuntimeError("No live IPython kernel available for interactive drive.mount()")
    except Exception as exc:
        raise RuntimeError(
            "Google Drive non montato e mount interattivo impossibile da processo batch. "
            "Monta Drive in una cella notebook prima di lanciare il runner."
        ) from exc

    drive.mount("/content/drive")
'''

runner_text = runner_path.read_text(encoding="utf-8")
start = runner_text.index("def mount_drive_if_colab() -> None:")
end = runner_text.index("\ndef default_artifact_dir()", start)
runner_text = runner_text[:start] + mount_guard + runner_text[end:]
runner_path.write_text(runner_text, encoding="utf-8")

verified = runner_path.read_text(encoding="utf-8")
if "Drive already available, skipping mount." not in verified:
    raise RuntimeError(f"Patch mount guard non applicata: {runner_path}")

print(f"Runner mount guard verified: {runner_path}")

cmd = [
    sys.executable,
    "fiorellia/training/final_colab_certification.py",
    "--artifact-dir",
    str(ARTIFACT_DIR),
    "--install-deps",
    "--copy-verdict-to-repo",
]
env = os.environ.copy()
env["FIORELLIA_DRIVE_REPO_ROOT"] = str(REPO_ROOT)
log_path = ARTIFACT_DIR / "final_certification_run.log"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

print("+", " ".join(cmd))
with log_path.open("w", encoding="utf-8") as log:
    proc = subprocess.Popen(
        cmd,
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert proc.stdout is not None
    for line in proc.stdout:
        print(line, end="")
        log.write(line)
    returncode = proc.wait()

summary_path = ARTIFACT_DIR / "final_certification_summary.json"
if returncode not in (0, 2) or not summary_path.exists():
    raise RuntimeError(f"Final certification failed before producing real summary. returncode={returncode}")
if returncode == 2:
    print("Final certification produced real outputs with NO-GO metrics. Continuing to publish real state.")
else:
    print("Final certification completed with GO DEFINITIVO.")
