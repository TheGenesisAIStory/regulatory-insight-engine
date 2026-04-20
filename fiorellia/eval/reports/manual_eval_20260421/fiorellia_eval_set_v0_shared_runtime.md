# Gen.Is.IA RAG Evaluation Report

- Dataset: `/tmp/fiorellia_eval_set_v0_runner.jsonl`
- Generated at: `2026-04-20T22:09:38.425915+00:00`
- Top-K: `6`
- Generation enabled: `False`

## Aggregate Metrics

- Case count: `16`
- Source hit rate: `n/a`
- In-domain coverage: `100.0%`
- No-answer accuracy: `31.2%`
- Schema validity rate: `100.0%`
- Average latency: `703 ms`
- P50 latency: `490 ms`
- Average groundedness: `n/a`
- False answers: `11`
- False no-answers: `0`
- Errors: `0`

## Metrics By Category

| Category | Cases | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `in_scope_grounded` | 5 | n/a | 100.0% | 100.0% | 0 | 0 | 1163 ms |
| `out_of_scope_refusal` | 5 | n/a | n/a | 0.0% | 5 | 0 | 490 ms |
| `unsupported_abstention` | 6 | n/a | n/a | 0.0% | 6 | 0 | 497 ms |

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

### fio-v0-007

- Category: `unsupported_abstention`
- Query: Quali sono tutte le disclosure Pillar 3 richieste alle banche italiane nel 2026?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4342`
- Error: `none`

### fio-v0-008

- Category: `unsupported_abstention`
- Query: Quali metriche Pillar 3 specifiche pubblica Intesa Sanpaolo nell'ultimo report disponibile?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3209`
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

### fio-v0-011

- Category: `out_of_scope_refusal`
- Query: Quale ETF UCITS consigli per espormi ai Treasury USA?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2985`
- Error: `none`

### fio-v0-012

- Category: `out_of_scope_refusal`
- Query: Conviene comprare azioni bancarie italiane questo trimestre?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2792`
- Error: `none`

### fio-v0-013

- Category: `out_of_scope_refusal`
- Query: Come posso ottimizzare fiscalmente le plusvalenze da ETF?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2830`
- Error: `none`

### fio-v0-014

- Category: `out_of_scope_refusal`
- Query: Quanti giorni di smart working spettano a un analista in banca?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2941`
- Error: `none`

### fio-v0-015

- Category: `out_of_scope_refusal`
- Query: Scrivi una strategia di trading su Intesa Sanpaolo con covered call.
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3355`
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

### out_of_scope_refusal

- `fio-v0-011`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2985`
- `fio-v0-012`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2792`
- `fio-v0-013`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2830`
- `fio-v0-014`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2941`
- `fio-v0-015`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3355`

### unsupported_abstention

- `fio-v0-006`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.5428`
- `fio-v0-007`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4342`
- `fio-v0-008`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3209`
- `fio-v0-009`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4976`
- `fio-v0-010`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3349`
- `fio-v0-016`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3920`

