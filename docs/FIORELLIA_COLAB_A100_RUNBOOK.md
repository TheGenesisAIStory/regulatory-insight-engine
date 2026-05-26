# Fiorell.IA Colab A100 Runbook

This is the active release path for Fiorell.IA: Google Colab Pro A100 for execution, Google Drive for artifacts, GitHub for final versioned source.

Do not use managed cloud endpoints, external VMs, or non-Drive artifact stores for this run.

## Required Colab State

- Runtime: Google Colab Pro, A100 GPU, high RAM.
- Repo clone: `/content/regulatory-insight-engine`.
- Drive artifact root: `/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/`.
- `RUN_ENV = "colab"` remains the default in notebook config cells.

## Permanent Repo Fixes

The repo includes Colab-stable aliases so manual `touch`, `cp`, or symlink workarounds are no longer needed:

- `fiorellia/__init__.py`
- `fiorellia/training/__init__.py`
- `fiorellia/eval/__init__.py`
- `fiorellia/prompts/system_prompt.md`
- `fiorellia/eval/eval_set.jsonl`
- `fiorellia/eval/baseline.jsonl`

## Adapter ZIP

Preferred Drive ZIP:

```text
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip
```

Fallback Drive ZIPs are resolved by the final eval script if present:

```text
/content/drive/MyDrive/fiorellia-runs/fiorellia_behavior_20260421.zip
/content/drive/MyDrive/fiorellia/artifacts/fiorellia_lora_adapter.zip
```

The ZIP must contain:

```text
adapter_config.json
adapter_model.safetensors
```

## Final Eval Flow

From the Colab repo root:

```bash
python fiorellia/eval/colab_drive_final_eval.py
```

The script runs the adapter prompt harness, scores real outputs, compares baseline vs adapter, and writes:

```text
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/reports/adapter_eval.jsonl
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/adapter_eval_scored.jsonl
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/comparison.csv
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/metrics_summary.json
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/eval_diagnostics.json
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/final_verdict.md
```

`metrics_summary.json` contains only real float metrics:

- `in_scope_grounded`
- `unsupported_abstention`
- `out_of_scope_refusal`
- `italian_style`

## Clean Restart

Before a full Colab rerun, use `Runtime -> Restart session and run all`. The final eval script removes stale `metrics_summary*.json` and `final_verdict*.md` files before writing a fresh verdict.

## Final Certification Flow

To move from `GO CON RISERVA` to a real final verdict, run the all-in-one A100 certification script from the Colab repo root:

```bash
python fiorellia/training/final_colab_certification.py \
  --install-deps \
  --copy-verdict-to-repo
```

For VS Code connected to a Colab A100 kernel, open and run:

```text
fiorellia_final_colab_a100_release.ipynb
```

The notebook wraps the same release script and also handles Drive mount, CUDA/A100 verification, stale artifact archival, final artifact validation, GitHub publication of the real final reports, and the final Gradio `--share` launch after a `GO DEFINITIVO` verdict.

The script fails fast unless CUDA is visible and the GPU is an A100. It then:

- trains `fiorellia_behavior_FINAL_RELEASE` on the patched style/abstention dataset;
- saves `fiorellia_behavior_FINAL_RELEASE.zip` to `/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/`;
- runs adapter eval with `prompt_harness_local_adapter.py`;
- writes `metrics_summary.json`, `comparison.csv`, `adapter_eval_scored.jsonl`, `eval_diagnostics.json`, and `final_verdict.md`;
- runs the required app smoke tests and writes `app_final_test_results.json`.

If the final verdict is `GO DEFINITIVO`, run the Colab app:

```bash
python fiorellia_app_colab.py \
  --adapter-path /content/fiorellia_behavior_FINAL_RELEASE \
  --share
```
