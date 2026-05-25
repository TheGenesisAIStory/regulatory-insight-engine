# Fiorell.IA Colab A100 Runbook

This is the active release path after Azure for Students GPU quota limits.

Do not use Azure ML, managed endpoints, cloud VMs, or Azure GPU quota for this run. Training, adapter export, eval, and final verdict run in Google Colab Pro with an A100 runtime and Google Drive artifacts.

## Required Colab State

- Runtime: Google Colab Pro, A100 GPU, high RAM.
- Repo clone: `/content/regulatory-insight-engine`.
- Artifact root: `/content/drive/MyDrive/fiorellia/artifacts/`.
- Notebook: `fiorellia/training/fiorellia_lora_master_runbook.ipynb`.
- `RUN_ENV = "colab"` remains the default in `00_config`.

## Permanent Repo Fixes

The repo includes Colab-stable aliases so manual `touch`, `cp`, or symlink workarounds are no longer needed:

- `fiorellia/__init__.py`
- `fiorellia/training/__init__.py`
- `fiorellia/eval/__init__.py`
- `fiorellia/prompts/system_prompt.md`
- `fiorellia/eval/eval_set.jsonl`
- `fiorellia/eval/baseline.jsonl`

## Eval Flow

The master notebook now runs the adapter eval harness before finalization:

```bash
python fiorellia/eval/prompt_harness.py \
  --adapter_zip /content/drive/MyDrive/fiorellia/artifacts/fiorellia_lora_adapter.zip \
  --eval_set fiorellia/eval/eval_set.jsonl \
  --system_prompt fiorellia/prompts/system_prompt.md \
  --output fiorellia/eval/reports/
```

The harness writes:

- `fiorellia/eval/reports/adapter_eval.jsonl`

The final notebook cell reads that JSONL, scores it with `score_eval_rows`, and writes:

- `/content/drive/MyDrive/fiorellia/artifacts/metrics_summary.json`
- `/content/drive/MyDrive/fiorellia/artifacts/eval_diagnostics.json`
- `/content/drive/MyDrive/fiorellia/artifacts/adapter_eval_scored.jsonl`
- `/content/drive/MyDrive/fiorellia/artifacts/final_verdict.md`

`metrics_summary.json` contains only the three release metrics as floats in `[0, 1]`:

- `in_scope_grounded`
- `unsupported_abstention`
- `out_of_scope_refusal`

## Clean Restart

Before a full Colab rerun, use `Runtime -> Restart session and run all`. The notebook removes stale `metrics_summary*.json` and `final_verdict*.md` artifacts before producing new verdict files.
