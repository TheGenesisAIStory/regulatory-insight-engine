# Fiorell.IA

Fiorell.IA v0.1.0-beta is an Italian-first product layer for a local banking-regulatory RAG assistant.

It is refusal-first and source-grounded: it should answer only when retrieved local sources support the response, and abstain when the query is out of scope or insufficiently documented.

Fiorell.IA is not production-ready legal, accounting, supervisory or regulatory advice.

## Boundary

Fiorell.IA does not own runtime behavior.

- Shared runtime: `backend/`
- Shared eval runner: `backend/eval/`
- Fiorell.IA product/spec/eval layer: `fiorellia/`

No Fiorell.IA file defines thresholds, domain gate modes, retrieval settings, indexing, serving or generation behavior.

## Narrow Beta Scope

Strongest current coverage:

- prudential supervision;
- internal controls;
- own funds and capital terminology;
- selected default and credit-risk regulatory context.

Not claimed:

- full IFRS 9;
- full Pillar 3;
- full EBA/Basel perimeter;
- complete banking-regulatory coverage;
- current market rankings or bank tables.

## Quickstart For Localhost Demo

1. Start the shared app using the repository root/backend docs.
2. Use demo prompts from `app/localhost_demo_guide.md`.
3. Show grounded prompts first.
4. Show unsupported/OOD prompts to demonstrate refusal-first behavior.
5. Do not claim production readiness.

## Evaluation Snapshot

| Run | Cases | No-answer accuracy | False answers |
|---|---:|---:|---:|
| Shared score-only | 32 | 15.6% | 27 |
| Shared domain gate diagnostic | 32 | 93.8% | 2 |
| Fiorell.IA score-only | 16 | 31.2% | 11 |
| Fiorell.IA domain-gate diagnostic | 16 | 75.0% | 4 |

Current decision: no-go as-is for controlled beta validation. The package is suitable for a narrow beta product/spec release and localhost demo with honest limitations.

## Key Files

- `docs/document-map.md`
- `training/fiorellia_behavior_spec.md`
- `eval/manual_eval_checklist.md`
- `eval/test_simulation_v0.md`
- `prompts/system_prompt.txt`
- `app/localhost_demo_guide.md`
