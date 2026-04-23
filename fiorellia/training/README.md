# Fiorell.IA Training Track

Fiorell.IA training is optional and experimental. It is intended to reinforce behavior, refusal discipline, unsupported-source abstention, citation discipline and concise Italian supervisory language.

Training must not replace retrieval. Fiorell.IA must not learn to answer from memory without retrieved local sources.

## Principle

The model may be specialized to behave better, but answers must still depend on retrieved local sources from the RAG runtime.

Training should improve:

- refusal behavior;
- unsupported-source abstention;
- concise Italian regulatory style;
- citation discipline;
- recognition of insufficient evidence;
- bank-specific disclosure caution.

Training must not teach:

- unsupported regulatory facts;
- broad memorized answers without citations;
- investment or legal advice;
- claims about documents not present in the corpus.

## Staged Path

### 1. Baseline

Run the shared RAG benchmark and save the results before changing prompts or datasets. This is the reference for false answers, no-answer behavior and source fidelity.

### 2. Prompt-Only

Evaluate Fiorell.IA prompt specifications without training. Use this stage to test refusal wording, answer templates and Italian supervisory tone.

### 3. Supervised Dataset v1

Build a small, reviewed dataset focused on behavior. Start with 100-300 high-quality examples instead of a large noisy set.

### 4. First LoRA

Run a small local LoRA only after prompt-only evaluation and dataset review. Keep artifacts local by default and record the run in the manifest.

For cloud-first training on Colab, use:

```text
fiorellia/training/notebooks/fiorellia_lora_colab.ipynb
fiorellia/training/cloud_training_colab.md
```

### 5. Post-LoRA Evaluation

Compare the candidate against the baseline and prompt-only runs. Reject the candidate if false answers increase, citations become weaker or out-of-scope refusals regress.

## Dataset Categories

Use these Fiorell.IA-specific categories alongside the shared supervised schema:

- `answer_with_citations`
- `refuse_out_of_scope`
- `unsupported_abstention`
- `regulatory_comparison`
- `italian_supervisory_language`
- `bank_specific_disclosure_style`

See `dataset_guidelines_v1.md` and `dataset_schema_v1.json` before creating examples.

## Experiment Tracking

Record each run in:

```text
fiorellia/training/experiments_manifest.jsonl
```

Minimum fields:

- `run_id`
- `date`
- `base_model`
- `dataset_version`
- `config_path`
- `artifact_path`
- `eval_report_path`
- `decision`
- `notes`

Do not commit model weights, adapters or large binary training artifacts by default.

## Local Artifacts

Expected planning artifacts in this folder:

- `dataset_guidelines_v1.md`
- `dataset_schema_v1.json`
- `training_plan_v1.md`
- `experiments_manifest.jsonl`

This folder does not own runtime thresholds, retrieval settings, domain gate modes or serving behavior.
