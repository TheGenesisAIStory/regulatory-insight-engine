# Fiorell.IA Document Map

Scope: local beta corpus planning for Fiorell.IA v0.1.0-beta. This map is prudential-focused and does not imply complete coverage of all banking regulation.

| filename | year | authority | topic | subtopic | RAG_tags | ingest_priority | dataset_use | eval_use | abstention_risk | notes |
|---|---:|---|---|---|---|---|---|---|---|---|
| `Circ285_Testo_Integrale.pdf` | current local copy | Banca d'Italia | Prudential supervision | Supervisory provisions, governance, controls | `bankit`, `circ285`, `prudential`, `controls` | high | answer_with_citations, italian_style | in_scope_grounded | medium | Strong anchor for Italian supervisory tone; cite exact retrieved sections only. |
| `Circ_285_Atto_emanazione_28_agg.pdf` | 28th update act | Banca d'Italia | Prudential supervision | Circular 285 update act | `bankit`, `circ285`, `prudential` | high | italian_style, abstention boundary | in_scope_grounded | medium | Useful for narrow supervisory references; not full Circ. 285 coverage by itself. |
| `Circ_285_pagina_generale.pdf` | local scrape | Banca d'Italia | Prudential supervision | Source page / index material | `bankit`, `circ285`, `source_page` | medium | dataset provenance | abstention boundary | high | Use mainly as provenance; avoid substantive claims unless text is explicit. |
| `Aggiornamento-n-51-del-3-febbraio-2026.pdf` | 2026 | Banca d'Italia | Prudential supervision | Latest local Circ. 285 update | `bankit`, `circ285`, `2026`, `prudential` | high | answer_with_citations, unsupported_abstention | in_scope_grounded | medium | Current-looking local update; still cite retrieved content only. |
| `Aggiornamento-n-50-del-26-agosto-2025.pdf` | 2025 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2025`, `prudential` | high | answer_with_citations | in_scope_grounded | medium | Good for update-aware supervision questions if retrieved. |
| `Aggiornamento-n-49-del-23-luglio-2024.pdf` | 2024 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2024`, `prudential` | high | answer_with_citations | in_scope_grounded | medium | Use for narrow update questions, not broad regulatory summaries. |
| `Aggiornamento_n_48_del_18_giugno_2024.pdf` | 2024 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2024`, `controls` | medium | italian_style, comparison | in_scope_grounded | medium | Potentially useful for controls/governance if retrieved text supports it. |
| `Aggiornamento-n-47-del-7-maggio-2024.pdf` | 2024 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2024`, `prudential` | medium | answer_with_citations | in_scope_grounded | medium | Avoid article-level claims without retrieved context. |
| `Aggiornamento_n_45_del_12_marzo_2024_Circolare_285.pdf` | 2024 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2024`, `controls` | medium | italian_style, answer_with_citations | in_scope_grounded | medium | Candidate for internal controls examples if snippets support it. |
| `Aggiornamento-n.44-del-19-dicembre-2023.pdf` | 2023 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2023`, `prudential` | medium | dataset, abstention boundary | in_scope_grounded | medium | Use cautiously for update-specific supervision content. |
| `Aggiornamento-n-43-del-5-dicembre-2023.pdf` | 2023 | Banca d'Italia | Prudential supervision | Circ. 285 update | `bankit`, `circ285`, `2023`, `prudential` | medium | dataset, answer_with_citations | in_scope_grounded | medium | Narrow source for local supervisory update examples. |
| `CRR.pdf` | 2013 consolidated local copy | EU | Own funds / prudential capital | Capital, credit risk, own funds | `crr`, `own_funds`, `capital`, `credit_risk`, `prudential` | high | answer_with_citations, comparison | in_scope_grounded | medium | Strong for own funds and prudential grounding; not enough for CRR II/III article-by-article claims. |
| `Basel_Framework.pdf` | local copy | BCBS / BIS | Prudential framework | Basel capital and risk framework | `basel`, `prudential`, `capital`, `risk` | medium | comparison, abstention boundary | regulatory_comparison | high | Supporting framework only; do not claim full EBA/Basel consolidated perimeter. |
| `Basel_III_Post_Crisis.pdf` | 2017 | BCBS / BIS | Basel III reforms | Post-crisis reform package | `basel_iii`, `prudential`, `capital`, `reforms` | medium | comparison, unsupported_abstention | regulatory_comparison | high | Useful for narrow reform context; refuse broad consolidated perimeter requests. |

## Prudential v0 Focus

Fiorell.IA v0.1.0-beta is strongest on:

- prudential supervision;
- internal controls;
- own funds and capital terminology;
- selected default/credit-risk regulatory context.

It should abstain on broad IFRS 9, full EBA/Basel, full Pillar 3 and current market/ranking questions unless retrieved local sources directly support the answer.
