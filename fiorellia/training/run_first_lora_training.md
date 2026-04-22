# Run First LoRA Training

This run uses the curated 2026-04-21 dataset and dated LoRA config.

Do not publish GitHub, LinkedIn, or a public demo before the baseline-vs-adapted comparison is complete.

## 1. Activate Training Environment

```bash
source .venv-fiorellia-lora/bin/activate
```

Or, with conda:

```bash
conda activate fiorellia-lora
```

## 2. Run Preflight

```bash
python fiorellia/training/preflight_check_training.py
```

Expected result:

```text
SUMMARY: PASS
```

## 3. Start Training

```bash
python3 fiorellia/training/train_lora_behavior_v1.py --config fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

## What Success Looks Like

The script should:

- load `Qwen/Qwen2.5-3B-Instruct`;
- load `fiorellia/training/supervised_v1_curated_20260421.jsonl`;
- print trainable LoRA parameters;
- run the configured epochs;
- save the adapter.

Expected adapter output:

```text
fiorellia/training/lora/fiorellia_behavior_20260421/
```

## Common Failures

Missing PyTorch:

```text
ModuleNotFoundError: No module named 'torch'
```

Install PyTorch with the official selector, then rerun preflight.

Missing Hugging Face stack:

```text
ModuleNotFoundError: No module named 'transformers'
ModuleNotFoundError: No module named 'peft'
ModuleNotFoundError: No module named 'datasets'
ModuleNotFoundError: No module named 'yaml'
```

Run:

```bash
pip install -r fiorellia/training/requirements-lora.txt
```

4-bit unavailable:

```text
4-bit loading unavailable, continuing without quantization
```

This may still run, but memory requirements will be higher. Install `bitsandbytes` only if your local platform supports it.

Apple Silicon / MPS memory pressure:

```text
MPS out of memory
```

By default the Fiorell.IA LoRA configs set:

```yaml
allow_mps: false
```

When CUDA is unavailable and `allow_mps` is `false`, the script keeps the model on CPU instead of forcing `model.to("mps")`. This is slower but avoids common Apple Silicon MPS OOM failures.

To explicitly try MPS, set:

```yaml
allow_mps: true
```

The script wraps `model.to("mps")` in `try/except` and falls back to CPU if the move fails.

As a last resort only, advanced operators may run:

```bash
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 python3 fiorellia/training/train_lora_behavior_v1.py --config fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

Use that only after reducing sequence length and confirming the machine has enough memory. It relaxes PyTorch's MPS memory guard and can make the system unstable under pressure.

Out of memory:

- reduce `max_seq_length`;
- reduce train epochs;
- keep batch size at 1;
- keep `allow_mps: false` for CPU fallback if MPS OOMs;
- use a CUDA/QLoRA-capable environment for practical 3B training.

## Immediately After Successful Training

1. Confirm adapter files exist under `fiorellia/training/lora/fiorellia_behavior_20260421/`.
2. Run adapted evaluation using `fiorellia/eval/compare_baseline_vs_adapter_20260421.md`.
3. Review the four priority cases first.
4. Update `fiorellia/training/experiments/fiorellia_runs.jsonl`.
5. Decide go/no-go only after comparing baseline vs adapted outputs.

## Current Status

As of 2026-04-21, the dedicated `.venv-fiorellia-lora` environment passes preflight.

The first Qwen2.5-3B training attempt did not complete:

- The first downloader attempt stalled at `Fetching 2 files`.
- A second attempt used `HF_HUB_DISABLE_XET=1`.
- Hugging Face cache reached about `223 MB`, but model download remained too slow for a controlled in-session run.
- The process was stopped before model loading and before training.
- No adapter checkpoint was produced.

Do not continue to release packaging until the adapter is trained and evaluated.
