# Gen.Is.IA RAG Evaluation Report

- Dataset: `eval/dataset.jsonl`
- Generated at: `2026-04-20T22:10:01.808142+00:00`
- Top-K: `6`
- Generation enabled: `False`

## Aggregate Metrics

- Case count: `32`
- Source hit rate: `100.0%`
- In-domain coverage: `100.0%`
- No-answer accuracy: `93.8%`
- Schema validity rate: `100.0%`
- Average latency: `485 ms`
- P50 latency: `466 ms`
- Average groundedness: `n/a`
- False answers: `2`
- False no-answers: `0`
- Errors: `0`

## Metrics By Category

| Category | Cases | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `banca_ditalia` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 479 ms |
| `crr_capital` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 506 ms |
| `crr_default` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 743 ms |
| `ifrs9_ecl` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 464 ms |
| `ifrs9_sicr` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 620 ms |
| `no_answer` | 2 | n/a | n/a | 100.0% | 0 | 0 | 501 ms |
| `no_answer_plausible_regulatory` | 5 | n/a | n/a | 100.0% | 0 | 0 | 504 ms |
| `ood_plausible_asset_management` | 1 | n/a | n/a | 100.0% | 0 | 0 | 470 ms |
| `ood_plausible_consulting` | 1 | n/a | n/a | 100.0% | 0 | 0 | 401 ms |
| `ood_plausible_consumer_banking` | 1 | n/a | n/a | 100.0% | 0 | 0 | 411 ms |
| `ood_plausible_corporate_finance` | 1 | n/a | n/a | 100.0% | 0 | 0 | 463 ms |
| `ood_plausible_credit_retail` | 1 | n/a | n/a | 100.0% | 0 | 0 | 505 ms |
| `ood_plausible_data` | 1 | n/a | n/a | 0.0% | 1 | 0 | 565 ms |
| `ood_plausible_esg` | 1 | n/a | n/a | 100.0% | 0 | 0 | 461 ms |
| `ood_plausible_general_accounting` | 1 | n/a | n/a | 100.0% | 0 | 0 | 414 ms |
| `ood_plausible_hr` | 1 | n/a | n/a | 100.0% | 0 | 0 | 434 ms |
| `ood_plausible_insurance` | 1 | n/a | n/a | 100.0% | 0 | 0 | 398 ms |
| `ood_plausible_investment_advice` | 1 | n/a | n/a | 100.0% | 0 | 0 | 435 ms |
| `ood_plausible_law` | 1 | n/a | n/a | 0.0% | 1 | 0 | 486 ms |
| `ood_plausible_legal` | 1 | n/a | n/a | 100.0% | 0 | 0 | 417 ms |
| `ood_plausible_macro` | 1 | n/a | n/a | 100.0% | 0 | 0 | 525 ms |
| `ood_plausible_market_data` | 1 | n/a | n/a | 100.0% | 0 | 0 | 468 ms |
| `ood_plausible_markets` | 1 | n/a | n/a | 100.0% | 0 | 0 | 530 ms |
| `ood_plausible_nonbank_regulation` | 1 | n/a | n/a | 100.0% | 0 | 0 | 473 ms |
| `ood_plausible_payments` | 1 | n/a | n/a | 100.0% | 0 | 0 | 405 ms |
| `ood_plausible_tax` | 1 | n/a | n/a | 100.0% | 0 | 0 | 479 ms |
| `ood_plausible_trading` | 1 | n/a | n/a | 100.0% | 0 | 0 | 449 ms |

## Failed Cases

### ood-19

- Category: `ood_plausible_law`
- Query: Quali differenze ci sono tra amministratore indipendente e non esecutivo in una banca quotata?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3341`
- Error: `none`

### ood-20

- Category: `ood_plausible_data`
- Query: Mi fai una classifica delle prime 10 banche italiane per total assets aggiornata al 2026?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3708`
- Error: `none`

## Failure Cases By Category

### ood_plausible_data

- `ood-20`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3708`

### ood_plausible_law

- `ood-19`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3341`

