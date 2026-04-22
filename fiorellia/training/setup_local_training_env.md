# Local Training Environment Setup

This guide prepares a local environment for Fiorell.IA LoRA behavior tuning.

Do not install packages into the shared runtime environment unless that is your intentional local setup. The training environment is experimental and separate from backend serving.

## Option A — Python venv

```bash
python3.11 -m venv .venv-fiorellia-lora
source .venv-fiorellia-lora/bin/activate
python -m pip install --upgrade pip
```

If `python3.11` is not available, install or activate any Python 3.10+ interpreter first. The current system Python 3.9.6 is not sufficient for the conservative training workflow.

Install PyTorch first using the official selector for your machine:

```text
https://pytorch.org/get-started/locally/
```

Then install the Fiorell.IA LoRA requirements:

```bash
pip install -r fiorellia/training/requirements-lora.txt
```

## Option B — Conda

```bash
conda create -n fiorellia-lora python=3.11
conda activate fiorellia-lora
```

Install PyTorch first using the official selector for your CPU/GPU platform:

```text
https://pytorch.org/get-started/locally/
```

Then install:

```bash
pip install -r fiorellia/training/requirements-lora.txt
```

## Validate Imports

```bash
python - <<'PY'
import torch
import transformers
import peft
import datasets
import yaml

print("torch", torch.__version__)
print("cuda", torch.cuda.is_available())
print("transformers", transformers.__version__)
print("peft", peft.__version__)
print("datasets", datasets.__version__)
print("yaml", yaml.__version__)
PY
```

Then run the project preflight:

```bash
python fiorellia/training/preflight_check_training.py
```

The preflight must print `SUMMARY: PASS` before training starts.

## Current Local Environment Note

On 2026-04-21, `.venv-fiorellia-lora` was created with Homebrew Python 3.11 and passed preflight. The remaining blocker is not Python imports; it is completing the Qwen2.5-3B model download and running training on suitable hardware.

## CPU-Only Notes

CPU training can be slow for Qwen2.5-3B. Use it only for smoke checks or very small experiments. If memory is limited, reduce sequence length, epochs, or batch-related settings in the local training config.

Do not use the backend runtime virtual environment as the training environment unless you intentionally want to mix serving and training dependencies. A dedicated training environment is safer and easier to remove.

## GPU Notes

Use the PyTorch install command that matches your GPU and driver stack. Verify:

```bash
python - <<'PY'
import torch
print(torch.cuda.is_available())
PY
```

## Optional QLoRA / 4-bit Notes

The current config has `use_4bit: true`. For CUDA QLoRA, install `bitsandbytes` only if your platform supports it:

```bash
pip install bitsandbytes
```

If 4-bit loading is unavailable, the training script attempts to continue without quantization. That may require more memory.
