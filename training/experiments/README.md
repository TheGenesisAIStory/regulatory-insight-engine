# Fiorell.IA Experiment Registry

This folder tracks local Fiorell.IA specialization experiments. It is intentionally lightweight and offline-first.

Use `fiorellia_runs.jsonl` as an append-only registry. Each line should describe one experiment run.

Required fields:

- `run_id`
- `date`
- `owner`
- `base_model`
- `dataset_version`
- `dataset_path`
- `config`
- `artifact_path`
- `eval_results`
- `decision`
- `notes`

Rules:

- Do not commit large model weights, adapters or binary artifacts.
- Keep artifact paths local or relative.
- Do not include confidential data or PII in notes.
- Runtime RAG remains separate from these experiments.
