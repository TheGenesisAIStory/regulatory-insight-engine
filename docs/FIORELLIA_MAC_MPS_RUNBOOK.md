# Fiorell.IA Mac MPS Runbook

This is the local fallback path when Colab runtimes keep disconnecting.

It does not use Azure. It trains a local PEFT/LoRA adapter with PyTorch MPS on
Apple Silicon and writes all heavy outputs under `local_runs/`, which is ignored
by Git.

## Environment

Use a clean Python environment:

```bash
cd /Users/itsgennymac/GitHub/regulatory-insight-engine
python3.10 -m venv .venv-fiorellia-mac
source .venv-fiorellia-mac/bin/activate
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio
python -m pip install -r fiorellia/training/requirements-lora.txt
```

If you use conda:

```bash
conda create -n fiorellia-mac python=3.10 -y
conda activate fiorellia-mac
python -m pip install --upgrade pip
python -m pip install torch torchvision torchaudio
python -m pip install -r fiorellia/training/requirements-lora.txt
```

Verify MPS:

```bash
python - <<'PY'
import torch
print(torch.__version__)
print(torch.backends.mps.is_available())
PY
```

The second line must be `True`.

## Dry Run

```bash
python mac_master_train.py --dry-run
```

By default the script prefers the local Google Drive mirror when it exists:

```text
/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine
```

Override it with:

```bash
python mac_master_train.py --repo-root /path/to/regulatory-insight-engine --dry-run
```

## Recommended Training

Conservative profile for a 16-24 GB Apple Silicon Mac:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 TOKENIZERS_PARALLELISM=false \
python mac_master_train.py \
  --engine transformers-mps \
  --epochs 2 \
  --batch-size 1 \
  --gradient-accumulation-steps 16 \
  --max-seq-length 768 \
  --lora-r 8 \
  --lora-alpha 16
```

Stronger profile for larger unified memory:

```bash
PYTORCH_ENABLE_MPS_FALLBACK=1 TOKENIZERS_PARALLELISM=false \
python mac_master_train.py \
  --engine transformers-mps \
  --epochs 3 \
  --batch-size 1 \
  --gradient-accumulation-steps 8 \
  --max-seq-length 1024 \
  --lora-r 16 \
  --lora-alpha 32
```

Outputs:

```text
local_runs/<run_name>/adapter/
local_runs/<run_name>/<run_name>.zip
local_runs/<run_name>/manifest.json
```

## Optional Eval

Mac eval is slow, so keep it short:

```bash
python mac_master_train.py --run-eval --eval-limit 10 --eval-max-new-tokens 96
```

## MLX Experimental Path

MLX is not the default path because the repo training/eval stack is built around
Transformers + PEFT + the existing prompt harness. The runner can prepare an
MLX-style text dataset and call `mlx_lm.lora` if `mlx-lm` is installed:

```bash
python -m pip install mlx-lm
python mac_master_train.py --engine mlx-lm --mlx-iters 300 --batch-size 1
```

Treat MLX output as experimental until it passes the same prompt harness eval.

## Cost And Stability Notes

- 4-bit bitsandbytes is disabled on MPS because it is CUDA-only in this repo path.
- The Mac profile uses float16 model loading on MPS and smaller sequence lengths
  to reduce swap risk.
- `local_runs/` is ignored by Git. Commit only source, configs, docs, and real
  summary reports.
