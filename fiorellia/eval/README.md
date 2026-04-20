# Fiorell.IA Evaluation

Fiorell.IA evaluation is product-layer validation only. It reuses shared runtime reports where useful, but does not modify backend, serving, retrieval, indexing or domain gate code.

## Suite Structure

- `eval_set_v0.jsonl`: 16 Fiorell.IA cases.
- `rubric_v0.md`: manual 0/1/2 scoring rubric.
- `manual_eval_checklist.md`: executable checklist with recent commands.
- `test_simulation_v0.md`: prompt-only simulations for the 4 remaining unsupported cases.
- `go_no_go_v1.md`: decision rules.
- `reports/manual_eval_20260421/`: recent local evaluation artifacts.

## Recent Results

| Run | Cases | No-answer accuracy | False answers | False no-answers | Notes |
|---|---:|---:|---:|---:|---|
| Shared baseline score-only | 32 | 15.6% | 27 | 0 | Default score-only abstention too weak. |
| Shared domain gate diagnostic | 32 | 93.8% | 2 | 0 | Best shared diagnostic mode in recent run. |
| Fiorell.IA score-only | 16 | 31.2% | 11 | 0 | Fails refusal-first target. |
| Fiorell.IA domain-gate diagnostic | 16 | 75.0% | 4 | 0 | Improves OOD refusal; 4 unsupported cases remain. |

## Four Remaining Unsupported Cases

- `fio-v0-006`: broad IFRS 9 overview including hedge accounting and classification.
- `fio-v0-009`: full EBA/Basel consolidated perimeter.
- `fio-v0-010`: CRR II vs CRR III article-by-article.
- `fio-v0-016`: 2026 ranking of Italian banks by total assets.

## Evaluation Posture

Fiorell.IA v0.1.0-beta remains no-go as-is for controlled beta validation until unsupported abstention is stronger. The package is ready for localhost demo and GitHub narrow beta release only as an honest product/spec layer, not as a production-ready assistant.
