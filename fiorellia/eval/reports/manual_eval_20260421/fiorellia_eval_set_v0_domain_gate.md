# Gen.Is.IA RAG Evaluation Report

- Dataset: `/tmp/fiorellia_eval_set_v0_runner.jsonl`
- Generated at: `2026-04-20T22:10:58.292270+00:00`
- Top-K: `6`
- Generation enabled: `False`

## Aggregate Metrics

- Case count: `16`
- Source hit rate: `n/a`
- In-domain coverage: `100.0%`
- No-answer accuracy: `75.0%`
- Schema validity rate: `100.0%`
- Average latency: `628 ms`
- P50 latency: `422 ms`
- Average groundedness: `n/a`
- False answers: `4`
- False no-answers: `0`
- Errors: `0`

## Metrics By Category

| Category | Cases | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `in_scope_grounded` | 5 | n/a | 100.0% | 100.0% | 0 | 0 | 1102 ms |
| `out_of_scope_refusal` | 5 | n/a | n/a | 100.0% | 0 | 0 | 403 ms |
| `unsupported_abstention` | 6 | n/a | n/a | 33.3% | 4 | 0 | 421 ms |

## Failed Cases

### fio-v0-006

- Category: `unsupported_abstention`
- Query: Puoi darmi una panoramica completa di tutto IFRS 9, inclusi hedge accounting e classificazione degli strumenti finanziari?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.5428`
- Error: `none`

### fio-v0-009

- Category: `unsupported_abstention`
- Query: Riassumi tutto il perimetro EBA/Basel consolidato applicabile alle banche europee.
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4976`
- Error: `none`

### fio-v0-010

- Category: `unsupported_abstention`
- Query: Quali sono le differenze aggiornate tra CRR II e CRR III articolo per articolo?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3349`
- Error: `none`

### fio-v0-016

- Category: `unsupported_abstention`
- Query: Mi dai la classifica aggiornata 2026 delle prime banche italiane per total assets?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3920`
- Error: `none`

## Failure Cases By Category

### unsupported_abstention

- `fio-v0-006`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.5428`
- `fio-v0-009`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4976`
- `fio-v0-010`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3349`
- `fio-v0-016`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3920`

