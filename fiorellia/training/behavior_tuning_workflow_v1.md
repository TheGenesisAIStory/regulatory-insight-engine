# Fiorell.IA Behavior Tuning Workflow v1

## 1. Why This Exists

This workflow improves actual local model behavior for Fiorell.IA without altering the shared runtime. It targets the remaining false answers in:

- `unsupported_abstention`
- `out_of_scope_refusal`

The objective is refusal discipline, unsupported-source abstention, concise Italian supervisory style, and no invented citations.

## Step 1 — Run Prompt Harness

Run the prompt-only baseline against the Fiorell.IA eval set:

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model qwen2.5:3b \
  --mode api \
  --out fiorellia/eval/prompt_harness_logs.jsonl
```

The four priority cases are:

- `fio-v0-006`: broad IFRS 9 overview
- `fio-v0-009`: full EBA/Basel perimeter
- `fio-v0-010`: CRR II vs CRR III article-by-article
- `fio-v0-016`: 2026 ranking of Italian banks by total assets

## Step 2 — Build Supervised Dataset From Logs

Convert failure-oriented logs into a draft supervised dataset:

```bash
python3 fiorellia/training/build_supervised_v1_from_logs.py \
  --in fiorellia/eval/prompt_harness_logs.jsonl \
  --out fiorellia/training/supervised_v1_from_logs_draft.jsonl
```

Only `unsupported_abstention` and `out_of_scope_refusal` records are extracted.

## Step 3 — Manually Curate Ideal Answers

Replace every `TODO_CURATED_IDEAL_ANSWER` with a short ideal answer that:

- refuses or abstains when evidence is missing;
- avoids external knowledge;
- avoids fake citations;
- uses a concise Italian regulatory tone;
- narrows the task when partial source-grounded support may exist.

For the first run, use or extend:

```text
fiorellia/training/supervised_v1_unsupported_seed.jsonl
```

Start with 100-300 high-quality examples before attempting broader training.

## Step 4 — Train LoRA Behavior v1

Run:

```bash
python3 fiorellia/training/train_lora_behavior_v1.py \
  --config fiorellia/training/configs/config_lora_behavior_v1.yaml
```

Expected adapter output:

```text
fiorellia/training/lora/fiorellia_behavior_v1/
```

This improves the model candidate only. It does not alter retrieval, serving, indexing, domain gate logic, or shared backend behavior.

## Step 5 — Evaluate Adapted Behavior

Use `fiorellia/eval/prompt_harness_with_adapter.md` to run baseline-vs-adapter comparison.

Review the four problematic cases first:

- broad IFRS 9 overview;
- full EBA/Basel perimeter;
- CRR II vs CRR III article-by-article;
- 2026 rankings/current data.

Then review the full `eval_set_v0.jsonl` for regressions.

## Step 6 — Append Experiment Manifest

Use:

```text
fiorellia/training/append_experiment_template_v1.md
```

Record:

- run id;
- date;
- base model;
- dataset version;
- config path;
- adapter path;
- eval summary;
- decision;
- notes.

## Go / No-Go Criteria

Promote the adapter only as an experimental candidate if:

- unsupported false answers decrease on the four priority cases;
- out-of-scope refusals remain correct;
- no fake citations appear;
- answers stay narrower than retrieved evidence;
- Italian supervisory style remains concise;
- no production-ready or full-coverage claim is introduced.

Reject or revise the adapter if it:

- increases false answers;
- weakens abstention;
- invents citations;
- answers current-data questions without local sources;
- expands beyond the narrow Fiorell.IA beta scope.
