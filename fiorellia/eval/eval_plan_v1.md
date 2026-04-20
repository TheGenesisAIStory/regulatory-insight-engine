# Fiorell.IA Evaluation Plan v1

Purpose: validate Fiorell.IA as an evaluation-ready beta candidate without changing the shared runtime. Evaluation checks behavior, not runtime ownership.

## Stages To Compare

1. **Shared baseline**: current shared RAG behavior and benchmark results.
2. **Prompt-only candidate**: Fiorell.IA prompt/refusal/answer templates, no training.
3. **Dataset-v1 candidate**: reviewed behavior-first dataset, no model claim by itself.
4. **LoRA-v1 candidate**: optional local LoRA candidate after dataset review.

Each stage must be compared against the shared baseline for false answers, no-answer behavior, source fidelity and Italian regulatory style.

## Review Slices

- `in_scope_grounded`: answerable from retrieved local sources.
- `unsupported_abstention`: plausible but not sufficiently documented.
- `out_of_scope_refusal`: outside banking regulation or advice request.
- `bank_specific_missing_source`: bank-specific question without the required local disclosure.
- `regulatory_comparison`: comparison only when both sides are supported.

## Reviewer Checklist

Reviewers inspect:

- grounding;
- refusal correctness;
- unsupported abstention;
- citation fidelity;
- Italian regulatory style.

Use `rubric_v0.md` for 0/1/2 scoring. Use `go_no_go_v1.md` for the release decision.

## Operating Notes

- Do not change runtime thresholds, retrieval settings, domain gate modes or serving behavior for this decision.
- Do not accept broad answers that exceed retrieved evidence.
- Keep failures by slice visible in the report.
- Treat missing bank-specific sources as abstention cases, not coverage gaps to fill from memory.
