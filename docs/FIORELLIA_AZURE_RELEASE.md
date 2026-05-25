# Fiorell.IA Azure Release Runbook

This runbook connects the local repository, Azure ML training/deployment, the Gradio release app, and the Google Drive project folder.

## Source Files

- `azure_ml_config.yaml`: Azure ML workspace, compute, endpoint, and deployment settings. Values may reference environment variables. Do not store secrets here.
- `fiorellia/training/azure_master_release.ipynb`: VS Code/Jupyter notebook for Azure ML training, model registration, endpoint deployment, and summary export.
- `fiorellia/training/azure_endpoint/score.py`: Azure ML scoring entrypoint.
- `fiorellia_app.py`: Gradio release app. It prefers an Azure ML endpoint when configured and falls back to local LoRA only when adapter weights are present.
- `deployment_one_click.sh`: frontend build, `dist` ZIP packaging, Google Drive sync, and app smoke test.

## Secrets And Artifacts

Do not commit:

- `azure_deploy_summary.json`, because it can contain the Azure ML endpoint key;
- `dist*.zip` and `.artifacts/`;
- `fiorellia_app_history.jsonl` and `history_export_*.json`;
- `*.safetensors`, `*.pt`, `*.bin`, and training checkpoints.

The project `.gitignore` covers these paths.

## Azure ML Notebook Flow

1. Export Azure workspace values in the shell that launches VS Code:

```bash
export AZURE_SUBSCRIPTION_ID="<subscription-id>"
export AZURE_RESOURCE_GROUP="<resource-group>"
export AZURE_ML_WORKSPACE="<workspace-name>"
```

2. Open `fiorellia/training/azure_master_release.ipynb`.
3. Run the cells in order:
   - install Azure ML SDK dependencies;
   - validate local dataset/config paths;
   - connect to the workspace;
   - create or reuse compute;
   - submit LoRA training;
   - register the adapter output;
   - deploy the managed online endpoint;
   - write `azure_deploy_summary.json`.
4. Copy `azure_deploy_summary.json` to the Google Drive project folder only through the approved secure channel.

## Azure ML One-Command Launcher

The repository also includes `launch_azure_train.py`, configured for the `FIorellIA` workspace in `italynorth`.

Install launcher dependencies in the VS Code Python environment:

```bash
python3 -m pip install -r requirements-azure-ml.txt
```

Dry-run the local preparation without contacting Azure:

```bash
python3 launch_azure_train.py --dry-run
```

Submit the final training job and deploy `fiorellia-endpoint` after a completed run:

```bash
python3 launch_azure_train.py
```

The launcher prepares `fiorellia/training/supervised_v1_curated_20260421_style_abstention_patch.jsonl` at about 40% abstention/refusal rows, logs MLflow metrics in Azure ML, writes `azure_deploy_summary.json`, and leaves endpoint keys out of Git.

## Gradio App

Run:

```bash
python3 -m pip install -r requirements-fiorellia-app.txt
python3 fiorellia_app.py
```

The app reads Azure endpoint settings from `azure_deploy_summary.json` or these environment variables:

```bash
export FIORELLIA_AZURE_ENDPOINT="https://..."
export FIORELLIA_AZURE_API_KEY="<do-not-commit>"
export FIORELLIA_AZURE_DEPLOYMENT="blue"
```

For a lightweight verification without loading the 3B model:

```bash
python3 fiorellia_app.py --smoke-test
```

For browser-only UI checks without loading local weights on submit:

```bash
FIORELLIA_DISABLE_LOCAL_MODEL=1 python3 fiorellia_app.py
```

To force the smoke test to load the local LoRA adapter:

```bash
FIORELLIA_SMOKE_LOAD_MODEL=1 python3 fiorellia_app.py --smoke-test
```

## Frontend Build And Drive Sync

Run:

```bash
./deployment_one_click.sh
```

By default, the script copies the generated `dist-<timestamp>.zip` into:

```text
~/Library/CloudStorage/GoogleDrive-sfn.gns@gmail.com/Il mio Drive/regulatory-insight-engine/dist/
```

Override the destination with:

```bash
FIORELLIA_DRIVE_DIR="/path/to/regulatory-insight-engine" ./deployment_one_click.sh
```
