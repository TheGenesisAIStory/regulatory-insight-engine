# Comparative RAG Modes Report

- Dataset: `eval/dataset.jsonl`
- Generated at: `2026-04-20T22:10:16.929083+00:00`

## Summary table

| Mode | Source hit rate | No-answer accuracy | False answers | False no-answers | Avg latency |
|---|---:|---:|---:|---:|---:|
| `score_only` | 100.0% | 15.6% | 27 | 0 | 595.8125 ms |
| `score_plus_domain_gate` | 100.0% | 93.8% | 2 | 0 | 485.09375 ms |
| `retrieval_opt` | 100.0% | 15.6% | 27 | 0 | 471.28125 ms |

**Recommended mode:** `score_plus_domain_gate`

## Notes & Trade-offs

- The recommended mode is chosen prioritizing no-answer accuracy, then source hit rate, and penalizing false answers and latency.
- Inspect per-mode reports in this folder for full failure case lists and detailed diagnostics.

## Per-mode failure samples

### score_only — 27 failed cases

- `out_of_domain_tax_recipe` (category: `no_answer`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.1986
- `out_of_domain_sport` (category: `no_answer`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.1914
- `ood_mifid_suitability` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3991
- `ood_gdpr_retention` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4348
- `ood_psd2_sca` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3747
- `ood_esg_sfdr` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4218
- `ood_aml_customer_due_diligence` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4050
- `ood-01` (category: `ood_plausible_markets`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3235
- `ood-02` (category: `ood_plausible_asset_management`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.2779
- `ood-03` (category: `ood_plausible_trading`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.2878

### score_plus_domain_gate — 2 failed cases

- `ood-19` (category: `ood_plausible_law`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3341
- `ood-20` (category: `ood_plausible_data`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3708

### retrieval_opt — 27 failed cases

- `out_of_domain_tax_recipe` (category: `no_answer`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.1986
- `out_of_domain_sport` (category: `no_answer`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.1914
- `ood_mifid_suitability` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3991
- `ood_gdpr_retention` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4348
- `ood_psd2_sca` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3747
- `ood_esg_sfdr` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4218
- `ood_aml_customer_due_diligence` (category: `no_answer_plausible_regulatory`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.4050
- `ood-01` (category: `ood_plausible_markets`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.3235
- `ood-02` (category: `ood_plausible_asset_management`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.2779
- `ood-03` (category: `ood_plausible_trading`): expectedNoAnswer=True, predictedNoAnswer=False, sourceHit=True, topScore=0.2878

