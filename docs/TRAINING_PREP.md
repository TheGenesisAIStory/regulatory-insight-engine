# Training Preparation Docs

Purpose
- Describe how to prepare a supervised/instruction-tuning dataset from the curated corpus, without coupling training to the runtime.

Location
- Training scripts and configs are in `training/`.

Quick commands
1. Split dataset for train/val:
```bash
python3 training/scripts/split_dataset.py --config training/config/config.json
```
2. Export instruction tuning format:
```bash
python3 training/scripts/export_instruction_tuning.py --input training/data/train.jsonl --output training/data/output/instruction_train.jsonl
```
3. Save artifacts (packaging):
```bash
python3 training/scripts/save_artifacts.py --input training/data --output training/data/output
```

Notes
- Training is intentionally decoupled from runtime RAG. The repository contains export and validation tooling but does not run model fine-tuning by default.
- If you run local training, do it on a separate machine or conda/venv and keep large artifacts in `training/data/output` (do not commit large model files).

Recommended artifacts to keep
- `instruction_train.jsonl` — final instruction-style dataset for tuning.
- `metrics.json` — dataset statistics and split proportions.

Next steps (optional)
- Implement LoRA or small-shot instruction tuning pipelines; keep those experiments separate from the main repo or under a `training/experiments/` folder with clear cleanup instructions.
