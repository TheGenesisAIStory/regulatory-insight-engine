# Fiorell.IA Document Map v0

Operational map for the current known local corpus. This is a cautious product-layer view, not an exhaustive inventory.

| filename | likely authority | year | main area | strength for Fiorell.IA v0 | suggested RAG tags | best use | abstention risk | short note |
|---|---:|---:|---|---|---|---|---|---|
| `CRR.pdf` | EU regulation | 2013, consolidated later | CRR, own funds, credit risk, prudential requirements | high for own funds/prudential grounding when relevant pages are retrieved | `crr`, `own_funds`, `credit_risk`, `prudential` | grounding, eval, dataset | medium | Use for narrow CRR questions; avoid broad claims without retrieved articles. |
| `IFRS9.pdf` | IFRS Foundation / IASB | 2021 source file in current downloader | IFRS 9 financial instruments, impairment, ECL, SICR | medium; useful but not full product claim for all IFRS 9 | `ifrs9`, `ecl`, `sicr`, `impairment`, `staging` | grounding, eval | medium-high | Strong only where retrieved context directly supports the answer. |
| `Basel_Framework.pdf` | Basel Committee / BIS | not fixed here | Basel prudential framework | medium; supporting context for prudential concepts | `basel`, `prudential`, `capital`, `risk` | grounding, dataset | medium | Use as supporting material, not as a complete consolidated Basel claim. |
| `Basel_III_Post_Crisis.pdf` | Basel Committee / BIS | 2017 | Basel III reforms | medium for reform context | `basel_iii`, `capital`, `prudential`, `reforms` | eval, dataset | medium | Good for cautious comparison when retrieved context is explicit. |
| `Circ_285_Atto_emanazione_28_agg.pdf` | Banca d'Italia | inferable as 28th update act | supervisory provisions, internal controls, prudential supervision | high for Italian supervisory tone and internal controls when context matches | `banca_italia`, `vigilanza`, `controlli_interni`, `prudential` | grounding, eval, dataset | medium | Use for Italian supervisory language; avoid treating it as all Banca d'Italia material. |
| bank-specific Pillar 3 / annual reports, if added locally | individual bank | depends on file | bank disclosures, Pillar 3, financial reporting | low until present and mapped | `pillar3`, `disclosure`, `bank_specific`, `<bank_name>` | abstention boundary, eval | high | Fiorell.IA should refuse bank-specific questions when the relevant file is absent. |

## Current v0 Strength

The strongest current claims remain:

- default;
- internal controls;
- own funds;
- prudential supervision.

## Use Notes

- Do not infer article-level coverage from filenames alone.
- Treat this map as a routing and evaluation aid.
- If a document is absent from the local corpus, prefer abstention over general knowledge.
