# Gen.Is.IA RAG Evaluation Report

- Dataset: `eval/dataset.jsonl`
- Generated at: `2026-04-20T22:09:46.248728+00:00`
- Top-K: `6`
- Generation enabled: `False`

## Aggregate Metrics

- Case count: `32`
- Source hit rate: `100.0%`
- In-domain coverage: `100.0%`
- No-answer accuracy: `15.6%`
- Schema validity rate: `100.0%`
- Average latency: `596 ms`
- P50 latency: `485 ms`
- Average groundedness: `n/a`
- False answers: `27`
- False no-answers: `0`
- Errors: `0`

## Metrics By Category

| Category | Cases | Source hit | In-domain coverage | No-answer accuracy | False answers | False no-answers | Avg latency |
|---|---:|---:|---:|---:|---:|---:|---:|
| `banca_ditalia` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 467 ms |
| `crr_capital` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 469 ms |
| `crr_default` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 506 ms |
| `ifrs9_ecl` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 490 ms |
| `ifrs9_sicr` | 1 | 100.0% | 100.0% | 100.0% | 0 | 0 | 3821 ms |
| `no_answer` | 2 | n/a | n/a | 0.0% | 2 | 0 | 452 ms |
| `no_answer_plausible_regulatory` | 5 | n/a | n/a | 0.0% | 5 | 0 | 505 ms |
| `ood_plausible_asset_management` | 1 | n/a | n/a | 0.0% | 1 | 0 | 476 ms |
| `ood_plausible_consulting` | 1 | n/a | n/a | 0.0% | 1 | 0 | 432 ms |
| `ood_plausible_consumer_banking` | 1 | n/a | n/a | 0.0% | 1 | 0 | 593 ms |
| `ood_plausible_corporate_finance` | 1 | n/a | n/a | 0.0% | 1 | 0 | 651 ms |
| `ood_plausible_credit_retail` | 1 | n/a | n/a | 0.0% | 1 | 0 | 471 ms |
| `ood_plausible_data` | 1 | n/a | n/a | 0.0% | 1 | 0 | 509 ms |
| `ood_plausible_esg` | 1 | n/a | n/a | 0.0% | 1 | 0 | 435 ms |
| `ood_plausible_general_accounting` | 1 | n/a | n/a | 0.0% | 1 | 0 | 442 ms |
| `ood_plausible_hr` | 1 | n/a | n/a | 0.0% | 1 | 0 | 491 ms |
| `ood_plausible_insurance` | 1 | n/a | n/a | 0.0% | 1 | 0 | 506 ms |
| `ood_plausible_investment_advice` | 1 | n/a | n/a | 0.0% | 1 | 0 | 476 ms |
| `ood_plausible_law` | 1 | n/a | n/a | 0.0% | 1 | 0 | 443 ms |
| `ood_plausible_legal` | 1 | n/a | n/a | 0.0% | 1 | 0 | 494 ms |
| `ood_plausible_macro` | 1 | n/a | n/a | 0.0% | 1 | 0 | 493 ms |
| `ood_plausible_market_data` | 1 | n/a | n/a | 0.0% | 1 | 0 | 451 ms |
| `ood_plausible_markets` | 1 | n/a | n/a | 0.0% | 1 | 0 | 527 ms |
| `ood_plausible_nonbank_regulation` | 1 | n/a | n/a | 0.0% | 1 | 0 | 432 ms |
| `ood_plausible_payments` | 1 | n/a | n/a | 0.0% | 1 | 0 | 456 ms |
| `ood_plausible_tax` | 1 | n/a | n/a | 0.0% | 1 | 0 | 591 ms |
| `ood_plausible_trading` | 1 | n/a | n/a | 0.0% | 1 | 0 | 514 ms |

## Failed Cases

### out_of_domain_tax_recipe

- Category: `no_answer`
- Query: Qual è la ricetta tradizionale della carbonara e quali vini abbinare?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.1986`
- Error: `none`

### out_of_domain_sport

- Category: `no_answer`
- Query: Chi ha vinto il campionato NBA nel 1998 e con quale roster?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.1914`
- Error: `none`

### ood_mifid_suitability

- Category: `no_answer_plausible_regulatory`
- Query: Secondo MiFID II, quali informazioni devono essere raccolte per la valutazione di adeguatezza del cliente retail?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3991`
- Error: `none`

### ood_gdpr_retention

- Category: `no_answer_plausible_regulatory`
- Query: Quali sono i tempi massimi di conservazione dei dati personali secondo il GDPR per una banca?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4348`
- Error: `none`

### ood_psd2_sca

- Category: `no_answer_plausible_regulatory`
- Query: Quali esenzioni alla strong customer authentication sono previste dalla PSD2?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3747`
- Error: `none`

### ood_esg_sfdr

- Category: `no_answer_plausible_regulatory`
- Query: Quali disclosure richiede la SFDR per i prodotti finanziari articolo 8 e articolo 9?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4218`
- Error: `none`

### ood_aml_customer_due_diligence

- Category: `no_answer_plausible_regulatory`
- Query: Quali obblighi di adeguata verifica della clientela prevede la normativa antiriciclaggio italiana?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4050`
- Error: `none`

### ood-01

- Category: `ood_plausible_markets`
- Query: Qual è la duration modificata ottimale di un portafoglio obbligazionario corporate in uno scenario di taglio dei tassi BCE?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3235`
- Error: `none`

### ood-02

- Category: `ood_plausible_asset_management`
- Query: Quali ETF UCITS consigli per esporsi ai Treasury USA a breve termine?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2779`
- Error: `none`

### ood-03

- Category: `ood_plausible_trading`
- Query: Qual è una buona strategia di covered call su Intesa Sanpaolo in un contesto laterale?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2878`
- Error: `none`

### ood-04

- Category: `ood_plausible_macro`
- Query: Quale impatto avrebbe un taglio dei tassi Fed sul cambio euro-dollaro nei prossimi sei mesi?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2838`
- Error: `none`

### ood-05

- Category: `ood_plausible_tax`
- Query: Come si calcola la tassazione italiana sulle plusvalenze da ETF armonizzati?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3349`
- Error: `none`

### ood-06

- Category: `ood_plausible_corporate_finance`
- Query: Qual è la differenza tra WACC e costo del capitale proprio in una valutazione DCF?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3043`
- Error: `none`

### ood-07

- Category: `ood_plausible_hr`
- Query: Quanti giorni di smart working spettano di norma a un analista finanziario in banca?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2876`
- Error: `none`

### ood-08

- Category: `ood_plausible_legal`
- Query: Come funziona il patto di non concorrenza per un dirigente bancario in Italia?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3939`
- Error: `none`

### ood-09

- Category: `ood_plausible_consumer_banking`
- Query: Qual è il miglior conto corrente per studenti universitari in Italia nel 2026?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3295`
- Error: `none`

### ood-10

- Category: `ood_plausible_payments`
- Query: Quali sono le commissioni medie dei POS per piccoli esercenti in Italia?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2877`
- Error: `none`

### ood-11

- Category: `ood_plausible_insurance`
- Query: Qual è la differenza tra una polizza ramo I e una unit linked?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3268`
- Error: `none`

### ood-12

- Category: `ood_plausible_investment_advice`
- Query: Conviene comprare BTP a 10 anni o obbligazioni corporate investment grade in questo momento?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3081`
- Error: `none`

### ood-13

- Category: `ood_plausible_general_accounting`
- Query: Qual è la differenza tra ammortamento civilistico e ammortamento fiscale?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3327`
- Error: `none`

### ood-14

- Category: `ood_plausible_nonbank_regulation`
- Query: Quali requisiti deve rispettare una compagnia assicurativa secondo Solvency II?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.4166`
- Error: `none`

### ood-15

- Category: `ood_plausible_esg`
- Query: Come si calcola l’impronta di carbonio finanziata di un portafoglio prestiti?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.3062`
- Error: `none`

### ood-16

- Category: `ood_plausible_consulting`
- Query: Puoi preparare una SWOT analysis di UniCredit rispetto ai principali competitor europei?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2466`
- Error: `none`

### ood-17

- Category: `ood_plausible_market_data`
- Query: Qual è stato l’andamento del FTSE MIB nell’ultimo trimestre?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2681`
- Error: `none`

### ood-18

- Category: `ood_plausible_credit_retail`
- Query: Qual è il TAN medio di un prestito personale in Italia nel 2026?
- Expected no-answer: `True`
- Predicted no-answer: `False`
- Source hit: `True`
- Missing expected sources: `none`
- Top score: `0.2640`
- Error: `none`

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

### no_answer

- `out_of_domain_tax_recipe`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.1986`
- `out_of_domain_sport`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.1914`

### no_answer_plausible_regulatory

- `ood_mifid_suitability`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3991`
- `ood_gdpr_retention`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4348`
- `ood_psd2_sca`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3747`
- `ood_esg_sfdr`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4218`
- `ood_aml_customer_due_diligence`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4050`

### ood_plausible_asset_management

- `ood-02`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2779`

### ood_plausible_consulting

- `ood-16`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2466`

### ood_plausible_consumer_banking

- `ood-09`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3295`

### ood_plausible_corporate_finance

- `ood-06`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3043`

### ood_plausible_credit_retail

- `ood-18`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2640`

### ood_plausible_data

- `ood-20`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3708`

### ood_plausible_esg

- `ood-15`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3062`

### ood_plausible_general_accounting

- `ood-13`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3327`

### ood_plausible_hr

- `ood-07`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2876`

### ood_plausible_insurance

- `ood-11`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3268`

### ood_plausible_investment_advice

- `ood-12`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3081`

### ood_plausible_law

- `ood-19`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3341`

### ood_plausible_legal

- `ood-08`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3939`

### ood_plausible_macro

- `ood-04`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2838`

### ood_plausible_market_data

- `ood-17`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2681`

### ood_plausible_markets

- `ood-01`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3235`

### ood_plausible_nonbank_regulation

- `ood-14`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.4166`

### ood_plausible_payments

- `ood-10`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2877`

### ood_plausible_tax

- `ood-05`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.3349`

### ood_plausible_trading

- `ood-03`: expected no-answer `True`, predicted `False`, source hit `True`, top score `0.2878`

