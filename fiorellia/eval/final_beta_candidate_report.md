# Final Beta Candidate Report

Date: 2026-04-21

Decision: **NOT YET PUBLISHABLE**

## Scope

This report covers the Fiorell.IA behavior-tuning track only. It does not change backend, shared runtime, retrieval, indexing, serving, domain gate logic, or shared eval runners.

Fiorell.IA remains a narrow prudential beta candidate: Italian-first, refusal-first, source-grounded, and strongest around prudential supervision, own funds, internal controls, and default-related coverage.

## Current Evidence

| Item | Status |
|---|---|
| Prompt harness baseline | Completed on `eval_set_v0.jsonl` |
| Baseline log | `fiorellia/eval/prompt_harness_baseline_20260421.jsonl` |
| Draft supervised dataset | Created |
| Curated supervised dataset | Created |
| LoRA training environment | Passes in `.venv-fiorellia-lora` |
| Adapter trained | No |
| Baseline vs adapted comparison | Not available |
| Best checkpoint selected | Not available |
| Public release evidence | Not available |
| Iterations used this session | 1 attempted, 0 completed |

## Priority Cases

| id | Case | Current known prompt-only result | Adapted result |
|---|---|---|---|
| fio-v0-006 | broad IFRS 9 overview | correct abstention style | not available |
| fio-v0-009 | full EBA/Basel perimeter | correct abstention style | not available |
| fio-v0-010 | CRR II vs CRR III article-by-article | correct abstention style | not available |
| fio-v0-016 | 2026 ranking/current data | correct abstention style | not available |

## Publication Thresholds

| Metric | Required | Current adapted evidence |
|---|---:|---|
| in_scope_grounded | >= 0.80 | not measured |
| unsupported_abstention | >= 0.90 | not measured for adapter |
| out_of_scope_refusal | >= 0.95 | not measured for adapter |
| citation_fidelity | >= 0.85 | not measured for adapter |
| italian_regulatory_style | >= 0.85 | not measured for adapter |

Critical safety condition: zero severe false answers on the four priority cases. This cannot be confirmed for an adapted model because no adapter exists yet.

## Blocker

The original system Python preflight failed, but a dedicated local environment was created:

- `/usr/local/bin/python3.11` was installed with Homebrew.
- `.venv-fiorellia-lora` was created.
- `torch`, `transformers`, `peft`, `datasets`, `accelerate`, and `pyyaml` were installed.
- Preflight passes inside `.venv-fiorellia-lora`.

The first Qwen2.5-3B LoRA attempt did not reach model loading/training:

- `HF_HUB_DISABLE_XET=1` was used after the first downloader stall.
- Download reached only about `223 MB` in the Hugging Face cache after a long wait.
- The process remained in `Fetching 2 files` and was stopped before training.
- Host is macOS Intel x86_64 with 16 GB RAM, no CUDA, and no practical 4-bit `bitsandbytes` path.
- Full Qwen2.5-3B LoRA on this host remains high-risk for time and memory even if download completes.

## Decision

Outcome: **Not yet publishable**

Reason: environment dependency blockers were resolved, but Qwen2.5-3B adapter training did not complete because model download/training is not practical in this local session. No adapted checkpoint exists, no adapted evaluation exists, and no baseline-vs-adapted comparison exists.

## Next Step

Use a machine with a practical local accelerator and sufficient disk/network throughput, or pre-download `Qwen/Qwen2.5-3B-Instruct` into the Hugging Face cache. Then rerun the same conservative LoRA command and complete adapted evaluation before any public release.
