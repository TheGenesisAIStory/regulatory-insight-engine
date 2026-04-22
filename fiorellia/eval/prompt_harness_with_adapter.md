# Prompt Harness With Adapter

This guide describes how to compare the Fiorell.IA prompt-only baseline with a locally adapted LoRA candidate.

The exact adapter-loading method depends on the local inference stack. Keep the shared backend runtime unchanged unless a separate experiment environment is explicitly created.

## 1. Run Baseline Prompt Harness

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model qwen2.5:3b \
  --mode api \
  --out fiorellia/eval/prompt_harness_baseline_qwen25_3b.jsonl
```

For the four known problematic cases, review:

- `fio-v0-006`: broad IFRS 9 overview
- `fio-v0-009`: full EBA/Basel perimeter
- `fio-v0-010`: CRR II vs CRR III article-by-article
- `fio-v0-016`: 2026 ranking of Italian banks by total assets

## 2. Load Or Reference The LoRA Adapter

Adapter path:

```text
fiorellia/training/lora/fiorellia_behavior_v1/
```

Common local options:

- Merge the adapter into a local Qwen2.5 model in a separate experiment directory.
- Serve the base model plus adapter with a local inference stack that supports PEFT adapters.
- Export a temporary local model name such as `fiorellia-behavior-v1` if your stack supports it.

Do not point the production shared backend to the adapted model until the candidate passes manual evaluation and go/no-go review.

## 3. Run Adapted Candidate

Use the model name exposed by your local adapter-serving setup:

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model fiorellia-behavior-v1 \
  --mode api \
  --out fiorellia/eval/prompt_harness_behavior_lora_v1.jsonl
```

If your adapter is only callable through CLI or a separate local endpoint, run the same eval set and store answers in JSONL with the same fields used by `prompt_harness.py`.

## 4. Compare Baseline vs Adapted

Review the four problematic cases first, then the full eval set.

| id | category | baseline_answer_quality | adapted_answer_quality | improved (yes/no) | notes |
|---|---|---:|---:|---|---|
| fio-v0-006 | unsupported_abstention |  |  |  |  |
| fio-v0-009 | unsupported_abstention |  |  |  |  |
| fio-v0-010 | unsupported_abstention |  |  |  |  |
| fio-v0-016 | unsupported_abstention |  |  |  |  |

Use `fiorellia/eval/rubric_v0.md` for scoring. The adapter should reduce unsupported false answers without weakening source-grounded answers.
