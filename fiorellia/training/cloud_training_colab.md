# Fiorell.IA Cloud Training (Colab / Kaggle)

This guide keeps Fiorell.IA training separate from the shared backend runtime.

Use the notebook:

```text
fiorellia/training/notebooks/fiorellia_lora_colab.ipynb
```

## What To Upload Or Access

Preferred path:

1. Open the notebook in Google Colab.
2. Clone the repository from GitHub inside the notebook.

If cloning is not possible, upload a zip of the repo root or at minimum these files:

```text
fiorellia/training/train_lora_behavior_v1.py
fiorellia/training/requirements-lora.txt
fiorellia/training/configs/config_lora_behavior_20260421.yaml
fiorellia/training/supervised_v1_curated_20260421.jsonl
```

## Recommended Colab Paths

If you clone the repo in Colab:

```text
/content/regulatory-insight-engine
```

If you mount Google Drive and want artifacts to persist:

```text
/content/drive/MyDrive/fiorellia-runs/
```

## What The Notebook Does

The notebook:

1. mounts Google Drive optionally;
2. clones the repo or uses an existing uploaded copy;
3. installs the minimum training dependencies;
4. reads the existing Fiorell.IA config and dataset;
5. runs:

```bash
python fiorellia/training/train_lora_behavior_v1.py \
  --config fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

6. copies the final adapter to a predictable export folder;
7. zips the adapter for easy download.

## Cloud Output Paths

Default training output inside the repo:

```text
fiorellia/training/lora/fiorellia_behavior_20260421/
```

Notebook export folder:

```text
<repo-root>/artifacts/fiorellia_behavior_20260421/
```

Notebook zip file:

```text
<repo-root>/artifacts/fiorellia_behavior_20260421.zip
```

If Drive export is enabled, the same adapter is copied under:

```text
/content/drive/MyDrive/fiorellia-runs/fiorellia_behavior_20260421/
```

## Colab Workflow

1. Open `fiorellia/training/notebooks/fiorellia_lora_colab.ipynb`.
2. Set `REPO_MODE` in the first config cell:
   - `github_public`
   - `github_private`
   - `drive_existing`
3. If the repo is private, paste a temporary GitHub token only when prompted.
4. Run the dependency install cell.
5. Run the config inspection cell and confirm:
   - dataset path exists;
   - base model is `Qwen/Qwen2.5-3B-Instruct`;
   - output dir is `fiorellia/training/lora/fiorellia_behavior_20260421`.
6. Run the training cell.
7. Run the export cell.
8. Download the zip or keep it in Drive.

## Kaggle Notes

The same script can run in Kaggle if you:

1. upload the repo as a dataset or notebook input;
2. install the requirements from `fiorellia/training/requirements-lora.txt`;
3. run the same training command from the repo root;
4. save the adapter under `/kaggle/working/artifacts/`.

The included notebook is Colab-oriented, but the script and config remain cloud-portable.

## Bring The Adapter Back Into The Repo

After download, place the adapter locally at:

```text
fiorellia/training/lora/fiorellia_behavior_20260421/
```

Keep the adapter local by default. Do not commit large binary weights into normal Git history.

## Run Baseline Vs Adapter Comparison

1. Run the baseline harness if needed:

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model qwen2.5:3b \
  --mode api \
  --out fiorellia/eval/prompt_harness_logs.jsonl
```

2. Follow:

```text
fiorellia/eval/prompt_harness_with_adapter.md
fiorellia/eval/compare_baseline_vs_adapter_20260421.md
```

3. Record the result in:

```text
fiorellia/training/experiments/fiorellia_runs.jsonl
```

## Minimal Rule

Training artifacts stay in `fiorellia/training/` and evaluation artifacts stay in `fiorellia/eval/` or `backend/eval/`.

No backend runtime, API, retrieval, or ingestion changes are required for this workflow.
