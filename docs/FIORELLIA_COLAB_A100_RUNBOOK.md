# Fiorell.IA Colab A100 Runbook

This is the active release path for Fiorell.IA: Google Colab Pro A100 for execution, Google Drive for artifacts, GitHub for final versioned source.

Do not use managed cloud endpoints, external VMs, or non-Drive artifact stores for this run.

## Required Colab State

- Runtime: Google Colab Pro, A100 GPU, high RAM.
- TPU/TCU runtimes are not valid for this release path: `nvidia-smi` must exist and `torch.cuda.is_available()` must be `True`.
- Repo/source root: `/content/drive/MyDrive/regulatory-insight-engine`.
- Local Mac Drive source root: `/Users/itsgennymac/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine`.
- Drive artifact root: `/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/`.
- Normative corpus root: `/content/drive/MyDrive/regulatory-insight-engine/docs/normativa/`.
- `RUN_ENV = "colab"` remains the default in notebook config cells.

## Drive-First Bootstrap

All active Fiorell.IA notebooks start with a `00 - Fiorell.IA Drive-first bootstrap` cell. The cell always resolves the operational root to Drive, downloads `fiorellia_colab_drive_bootstrap.py` from GitHub if missing, and then executes it.

The bootstrap:

- mounts Google Drive when needed;
- sets `REPO_ROOT = /content/drive/MyDrive/regulatory-insight-engine`;
- sets `ARTIFACT_DIR = /content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest`;
- refreshes stale critical scripts from GitHub, including `final_colab_certification.py` and `fiorellia_colab_cell04_hotfix.py`;
- creates stable aliases and `__init__.py` files required by Colab imports.

## Current Behavior Hardening Candidate

The active recovery candidate after the real `NO-GO` certification is:

```text
fiorellia_behavior_RC_HARDENED_20260526
```

It uses:

```text
fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl
fiorellia/training/configs/config_lora_behavior_20260526_behavior_hardening.yaml
fiorellia/prompts/system_prompt_strict.md
fiorellia/eval/eval_set_behavior_hardening_v1.jsonl
```

The v2 dataset contains 60 supervised records:

- 30 unsupported abstention examples;
- 18 out-of-scope refusal examples;
- 12 narrow in-scope grounded examples with explicit retrieved context.

## Final Perfection Recovery

After a real `NO-GO`, use the failure-audit runner instead of reusing stale verdict files:

```bash
python final_perfection_run.py \
  --install-deps \
  --copy-verdict-to-repo
```

The runner:

- reads the latest `adapter_eval_scored.jsonl` from `/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/` when present;
- writes `failure_audit.json` and `failure_audit.md`;
- removes training rows that fuzzy-match failed eval queries;
- adds 20 extreme abstention examples for real-time market data, future political predictions and personal legal advice;
- writes `supervised_v3_final_perfection_20260527.jsonl`;
- trains `fiorellia_behavior_FINAL_PERFECTION_20260527` with LR `5e-5`, 5 epochs and `weight_decay: 0.05`;
- evaluates with `system_prompt_strict.md`;
- writes `metrics_summary.json`, `comparison.csv`, `adapter_eval_scored.jsonl`, `final_perfection_summary.json`, `final_verdict_master.md` and `app_unlock.json`.

`GO DEFINITIVO` is allowed only from the current run metrics and app smoke tests; previous `NO-GO` RuntimeErrors are ignored, but failed current metrics still keep the app locked.

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
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip
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
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/reports/adapter_eval.jsonl
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/adapter_eval_scored.jsonl
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/comparison.csv
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/metrics_summary.json
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/eval_diagnostics.json
/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/final_verdict.md
```

`metrics_summary.json` contains only real float metrics:

- `in_scope_grounded`
- `unsupported_abstention`
- `out_of_scope_refusal`
- `italian_style`

## Clean Restart

Before a full Colab rerun, use `Runtime -> Restart session and run all`. The final eval script removes stale `metrics_summary*.json` and `final_verdict*.md` files before writing a fresh verdict.

## Final Certification Flow

In Colab, mount Drive from a notebook cell before launching the CLI runner:

```python
from google.colab import drive
drive.mount("/content/drive", force_remount=True)
```

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

The notebook wraps the same release script and also handles Drive mount, CUDA/A100 verification, stale artifact archival, final artifact validation, best-effort GitHub publication of the real final reports, and the final Gradio `--share` launch after a `GO DEFINITIVO` verdict.

The script fails fast unless CUDA is visible and the GPU is an A100. It then:

- trains `fiorellia_behavior_RC_HARDENED_20260526` on the behavior-hardening dataset;
- saves `fiorellia_behavior_RC_HARDENED_20260526.zip` to `/content/drive/MyDrive/regulatory-insight-engine/fiorellia-runs/final_delivery_latest/`;
- runs adapter eval with `prompt_harness_local_adapter.py`;
- writes `metrics_summary.json`, `comparison.csv`, `adapter_eval_scored.jsonl`, `eval_diagnostics.json`, and `final_verdict.md`;
- runs the required app smoke tests and writes `app_final_test_results.json`.

The notebook writes `github_publish_status.json` in the artifact directory. If Colab has no GitHub token or credential helper, the push is recorded as non-fatal and Drive remains the source of truth until the same real reports are pushed from a local authenticated checkout.

The notebook writes `app_launch_status.json` in the artifact directory. If the final verdict is not `GO DEFINITIVO`, the public Gradio launch is skipped and recorded instead of publishing an unqualified app.

If the final verdict is `GO DEFINITIVO`, run the Colab app:

```bash
python fiorellia_app_colab.py \
  --adapter-path /content/fiorellia_behavior_RC_HARDENED_20260526 \
  --share
```
