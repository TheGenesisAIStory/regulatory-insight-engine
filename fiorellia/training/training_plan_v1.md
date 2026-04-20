# Fiorell.IA Training Plan v1

This plan is behavior-first and optional. It does not modify the shared runtime and does not replace RAG.

## 1. Baseline Eval

Run the shared benchmark before prompt or training changes.

Capture:

- false answers;
- false no-answers;
- source hit rate;
- citation/schema validity;
- near-domain unsupported behavior.

Decision: proceed only if the baseline is documented.

## 2. Prompt-Only Eval

Evaluate Fiorell.IA prompt, refusal and answer templates without model training.

Check:

- refusal wording;
- unsupported abstention;
- Italian supervisory style;
- citation discipline.

Decision: improve templates before creating training examples if prompt-only behavior is unclear.

## 3. Dataset Build

Create supervised dataset v1 using `dataset_guidelines_v1.md` and `dataset_schema_v1.json`.

Target size:

- start with 100-300 reviewed examples;
- prioritize `unsupported_abstention`, `refuse_out_of_scope` and `answer_with_citations`;
- include bank-specific disclosure refusals when sources are missing.

Decision: no training run until examples are reviewed for unsupported facts and invented citations.

## 4. Small Supervised Run

Run a small local supervised experiment if the local tooling is ready.

Goal:

- test formatting and refusal discipline;
- avoid broad capability claims;
- keep artifacts local by default.

Decision: stop if the model starts answering from memory or weakening citations.

## 5. First LoRA Run

Run a first LoRA candidate only after the supervised dataset passes review.

Record in `experiments_manifest.jsonl`:

- run id;
- base model;
- dataset version;
- config path;
- artifact path;
- eval report path;
- decision.

Do not commit model weights or adapters by default.

## 6. Comparative Eval

Compare:

- shared baseline;
- prompt-only candidate;
- supervised/LoRA candidate.

Reject candidates that increase false answers, invent sources or reduce abstention quality.

## 7. Go / No-Go

Go only if:

- no increase in false answers;
- no 0-score grounding failures in reviewed samples;
- out-of-scope refusals remain short and clear;
- unsupported abstention improves or remains strong;
- Italian regulatory style remains concise;
- runtime changes are not required.

No-go if training makes the model more confident without stronger retrieved evidence.
