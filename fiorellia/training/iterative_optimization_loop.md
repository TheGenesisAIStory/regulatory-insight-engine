# Iterative Optimization Loop

This loop is intentionally small. It is designed to improve Fiorell.IA behavior without modifying backend, retrieval, serving, indexing, domain gate logic, or shared eval runners.

## Stop Rules

Stop immediately with a documented NO-GO if:

- preflight fails;
- training cannot start safely;
- two consecutive iterations show no meaningful improvement;
- validation degrades while training behavior appears better;
- any severe false answer remains on priority cases after targeted iteration;
- adapted answers invent citations or exceed retrieved evidence.

## Target Thresholds

| Metric | Threshold |
|---|---:|
| in_scope_grounded | 0.80 |
| unsupported_abstention | 0.90 |
| out_of_scope_refusal | 0.95 |
| citation_fidelity | 0.85 |
| italian_regulatory_style | 0.85 |

Critical condition: zero severe false answers on the four priority cases.

## Priority Cases

| id | Risk |
|---|---|
| fio-v0-006 | unsupported IFRS 9 broad overview |
| fio-v0-009 | unsupported EBA/Basel broad overview |
| fio-v0-010 | unsupported CRR article-by-article comparison |
| fio-v0-016 | out-of-scope current ranking/current-data query |

## Iteration A — Prompt-Only Baseline

Already completed:

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model qwen2.5:3b \
  --mode api \
  --timeout 180 \
  --out fiorellia/eval/prompt_harness_baseline_20260421.jsonl
```

Result: baseline log exists. This is the comparison anchor.

## Iteration B — Conservative LoRA v1

Run only after preflight passes:

```bash
python3 fiorellia/training/preflight_check_training.py
```

Then:

```bash
python3 fiorellia/training/train_lora_behavior_v1.py \
  --config fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

Expected output:

```text
fiorellia/training/lora/fiorellia_behavior_20260421/
```

## Iteration C — One Targeted Adjustment Only If Justified

Allowed only if Iteration B produces partial improvement without regressions.

Permitted small adjustments:

- add 20-50 curated refusal/abstention examples;
- reduce epochs if overfitting appears;
- keep LoRA rank conservative;
- keep validation split enabled.

Do not expand scope or train the model to answer from memory.

## Iteration D — Final Candidate Evaluation

Run adapted output through the same eval set:

```bash
python3 fiorellia/eval/prompt_harness.py \
  --dataset fiorellia/eval/eval_set_v0.jsonl \
  --model fiorellia-behavior-20260421 \
  --mode api \
  --out fiorellia/eval/prompt_harness_behavior_lora_20260421.jsonl
```

Then complete:

- `fiorellia/eval/compare_baseline_vs_adapter_20260421.md`
- `fiorellia/eval/final_beta_candidate_report.md`
- `fiorellia/training/experiments/fiorellia_runs.jsonl`

## Checkpoint Selection

If multiple checkpoints are scored manually, create a local JSON score file with:

```json
{
  "candidates": [
    {
      "checkpoint": "fiorellia/training/lora/fiorellia_behavior_20260421/checkpoint-1",
      "metrics": {
        "in_scope_grounded": 0.0,
        "unsupported_abstention": 0.0,
        "out_of_scope_refusal": 0.0,
        "citation_fidelity": 0.0,
        "italian_regulatory_style": 0.0
      },
      "priority_cases": {
        "fio-v0-006": "correct_abstention",
        "fio-v0-009": "correct_abstention",
        "fio-v0-010": "correct_abstention",
        "fio-v0-016": "correct_refusal"
      },
      "regressions": []
    }
  ]
}
```

Then run:

```bash
python3 fiorellia/training/select_best_checkpoint.py --scores fiorellia/eval/checkpoint_scores_20260421.json
```
