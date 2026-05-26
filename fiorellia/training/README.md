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

### 6. Colab Workflow Split

- `fiorellia_lora_colab_ok.ipynb`: setup/serving/testing dell'adapter LoRA, utile per prompt manuali e debug del comportamento.
- `fiorellia_eval_adapter2.ipynb`: eval completa su `fiorellia/eval/eval_set_v0.jsonl`, confronto baseline vs adapter e decisione GO / NO-GO.
- `fiorellia/eval/prompt_harness_local_adapter.py`: script di riferimento per un eval locale diretto con base model + LoRA, da usare solo su host con GPU adeguata.
- I file `prompt_harness_*.jsonl` e i CSV di confronto sono artefatti locali di eval.

## Recovery behavior hardening 2026-05-26

Dopo il verdict reale `NO-GO`, il candidato attivo e:

- dataset: `fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl`;
- builder: `fiorellia/training/build_behavior_hardening_v2.py`;
- config: `fiorellia/training/configs/config_lora_behavior_20260526_behavior_hardening.yaml`;
- prompt strict: `fiorellia/prompts/system_prompt_strict.md`;
- eval set con contesto recuperato: `fiorellia/eval/eval_set_behavior_hardening_v1.jsonl`.

Il dataset v2 contiene 60 esempi supervisionati: 50% unsupported abstention, 30% out-of-scope refusal e 20% in-scope grounded con contesto esplicito.
- Per default questi artefatti non vanno committati su GitHub.

## Final perfection recovery 2026-05-27

Il runner operativo per il retraining dopo un `NO-GO` e:

```bash
python final_perfection_run.py --install-deps --copy-verdict-to-repo
```

Produce:

- audit dei fallimenti da `adapter_eval_scored.jsonl`;
- dataset `fiorellia/training/supervised_v3_final_perfection_20260527.jsonl`;
- config `fiorellia/training/configs/config_lora_behavior_20260527_final_perfection.yaml`;
- adapter `fiorellia_behavior_FINAL_PERFECTION_20260527`;
- `final_verdict_master.md` e `app_unlock.json` nella delivery Drive.

La config finale usa `learning_rate: 5e-5`, `num_train_epochs: 5`, `weight_decay: 0.05` e `system_prompt_strict.md` per training/eval.

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
