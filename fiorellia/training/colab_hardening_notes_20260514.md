# Fiorell.IA Colab LoRA hardening notes

Scope: conservative operational hardening for the existing Google Colab training/eval workflow.

No functional behavior is changed:
- base model remains `Qwen/Qwen2.5-3B-Instruct`;
- LoRA remains the training method;
- the existing abstention/refusal behavior must not be weakened;
- no HTTP endpoint or external service is introduced.

## High-priority checks to keep in Colab notebooks

Before training or eval, run small preflight cells that fail fast with explicit errors:

```python
from pathlib import Path
import torch, zipfile, yaml

REPO_ROOT = Path.cwd()
CONFIG_PATH = REPO_ROOT / "fiorellia/training/configs/config_lora_behavior_20260421.yaml"

assert CONFIG_PATH.exists(), f"Missing config: {CONFIG_PATH}"
config = yaml.safe_load(CONFIG_PATH.read_text())

required = ["base_model_name", "output_dir", "dataset_path", "target_modules", "use_4bit"]
missing = [k for k in required if k not in config]
assert not missing, f"Missing required config keys: {missing}"
assert config["base_model_name"] == "Qwen/Qwen2.5-3B-Instruct", "Unexpected base model change"
assert torch.cuda.is_available(), "CUDA GPU not available. In Colab: Runtime > Change runtime type > A100 GPU"
print("GPU:", torch.cuda.get_device_name(0))
```

Before eval, validate adapter zip contents explicitly:

```python
ADAPTER_ZIP = Path("/content/drive/MyDrive/fiorellia_lora_adapter.zip")
assert ADAPTER_ZIP.exists(), f"Missing adapter zip: {ADAPTER_ZIP}"

with zipfile.ZipFile(ADAPTER_ZIP) as zf:
    names = set(zf.namelist())
    required_suffixes = ["adapter_config.json", "adapter_model.safetensors"]
    missing = [s for s in required_suffixes if not any(n.endswith(s) for n in names)]
    assert not missing, f"Adapter zip is incomplete. Missing: {missing}"
```

## Dependency guardrail

Keep dependency installation in one cell and avoid mixing unpinned upgrades later in the notebook. If conflicts appear on Colab A100, prefer a single conservative pin-set rather than scattered `pip install -U` cells.

Suggested minimal pattern:

```bash
pip install -q \
  "transformers>=4.45,<4.52" \
  "datasets>=2.20,<3.0" \
  "accelerate>=0.33,<1.0" \
  "peft>=0.12,<0.16" \
  "trl>=0.9,<0.13" \
  "bitsandbytes>=0.43,<0.46" \
  "safetensors>=0.4" \
  "pyyaml>=6.0"
```

## Manual Colab test checklist

1. Open the training notebook on a clean Colab A100 runtime.
2. Run dependency install once, then restart runtime only if Colab asks for it.
3. Run preflight; verify config, dataset path, CUDA GPU and base model.
4. Run training with `fiorellia/training/configs/config_lora_behavior_20260421.yaml`.
5. Verify adapter directory contains `adapter_config.json` and `adapter_model.safetensors`.
6. Verify export zip is written to Google Drive.
7. Open eval notebook on a clean Colab A100 runtime.
8. Mount Drive and validate adapter zip before extraction.
9. Verify system prompt, eval set and baseline JSONL are present before generation.
10. Run eval and confirm JSONL + CSV comparative outputs are produced.
11. Review priority, unsupported abstention and out-of-scope refusal rows; these must not regress.
