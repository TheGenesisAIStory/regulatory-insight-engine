# Fiorell.IA Experiment Registry

Registry file:

```text
fiorellia/training/experiments/fiorellia_runs.jsonl
```

## Schema

Each line is JSON with:

- `run_id`
- `date`
- `stage`
- `base_model`
- `dataset`
- `config`
- `report`
- `decision`
- `notes`

## Rules

- No model weights or adapters are committed.
- No backend/runtime files are changed.
- Every run must state whether it is baseline, diagnostic, manual eval, dataset prep or LoRA candidate.
- A no-go decision is valid and should be recorded honestly.
