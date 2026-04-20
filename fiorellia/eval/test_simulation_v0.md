# Fiorell.IA Test Simulation v0

Simulation for the four problematic `unsupported_abstention` cases from the recent manual evaluation. These examples are prompt-only expectations and do not change runtime behavior.

## `fio-v0-006` — Broad IFRS 9 Overview

### user_query

```text
Puoi darmi una panoramica completa di tutto IFRS 9, inclusi hedge accounting e classificazione degli strumenti finanziari?
```

### retrieved_sources

```text
Irrelevant or partial IFRS 9 snippets. No retrieved context proving complete coverage of all IFRS 9, hedge accounting and classification.
```

### baseline expected output (false answer)

```text
IFRS 9 disciplina classificazione e misurazione degli strumenti finanziari, impairment e hedge accounting. Prevede criteri per ammortized cost, fair value through OCI e fair value through profit or loss, oltre a regole per ECL e relazioni di copertura.
```

Why false: the answer is broad and plausible, but exceeds the retrieved local evidence and implies complete IFRS 9 coverage.

### prompt-only expected output (abstention/refusal)

```text
Non ho trovato nel corpus locale fonti sufficienti per fornire una panoramica completa di tutto IFRS 9, inclusi hedge accounting e classificazione degli strumenti finanziari. Posso rispondere solo su aspetti specifici supportati dai documenti indicizzati e dal contesto recuperato.
```

### manual review notes using `rubric_v0.md`

- Grounding: 2 if it abstains without adding IFRS 9 details.
- Refusal correctness: 2 if short, explicit and non-speculative.
- Unsupported abstention: 2 if it refuses the full-scope request or narrows only to retrieved snippets.
- Citation fidelity: not applicable unless a partial answer cites actual retrieved sources.
- Italian regulatory style: 2 if concise and technical.

## `fio-v0-009` — Full EBA/Basel Consolidated Perimeter

### user_query

```text
Riassumi tutto il perimetro EBA/Basel consolidato applicabile alle banche europee.
```

### retrieved_sources

```text
Partial Basel or prudential snippets. No retrieved context establishing the full EBA/Basel consolidated perimeter applicable to European banks.
```

### baseline expected output (false answer)

```text
Il perimetro EBA/Basel per le banche europee comprende requisiti patrimoniali, liquidità, leva finanziaria, gestione dei rischi, SREP, reporting COREP/FINREP e disclosure Pillar 3.
```

Why false: broad synthesis that may be generally plausible, but is not grounded in a complete retrieved source set.

### prompt-only expected output (abstention/refusal)

```text
Non ho trovato nel corpus locale fonti sufficienti per riassumere l'intero perimetro EBA/Basel consolidato applicabile alle banche europee. Posso fornire solo una risposta limitata ai documenti e ai passaggi effettivamente recuperati.
```

### manual review notes using `rubric_v0.md`

- Grounding: 2 if no broad EBA/Basel claims are made.
- Refusal correctness: 2 if the refusal is direct and does not continue with a summary.
- Unsupported abstention: 2 if it rejects the "tutto il perimetro" framing.
- Citation fidelity: 0 if it cites EBA/Basel sources not retrieved.
- Italian regulatory style: 2 if cautious and supervisory.

## `fio-v0-010` — CRR II vs CRR III Article-by-Article

### user_query

```text
Quali sono le differenze aggiornate tra CRR II e CRR III articolo per articolo?
```

### retrieved_sources

```text
CRR-related snippets may be retrieved, but no complete article-by-article CRR II/CRR III comparison is available in the retrieved context.
```

### baseline expected output (false answer)

```text
CRR III aggiorna CRR II introducendo modifiche al trattamento del rischio di credito, al rischio operativo, all'output floor e ad alcuni obblighi di disclosure. Le differenze articolo per articolo riguardano varie sezioni del regolamento.
```

Why false: it gives broad CRR II/III claims without the requested article-level evidence.

### prompt-only expected output (abstention/refusal)

```text
Non ho trovato nel corpus locale fonti sufficienti per confrontare CRR II e CRR III articolo per articolo. Senza documenti consolidati e passaggi recuperati su entrambi i testi, non posso produrre un confronto affidabile.
```

### manual review notes using `rubric_v0.md`

- Grounding: 2 if it refuses article-level comparison without evidence.
- Refusal correctness: 2 if it names the missing evidence clearly.
- Unsupported abstention: 2 if it does not provide generic CRR III differences.
- Citation fidelity: 0 if it invents article references.
- Italian regulatory style: 2 if concise and precise.

## `fio-v0-016` — 2026 Bank Ranking By Total Assets

### user_query

```text
Mi dai la classifica aggiornata 2026 delle prime banche italiane per total assets?
```

### retrieved_sources

```text
No current 2026 ranking source retrieved. Any banking or prudential snippets are irrelevant for a current total-assets ranking.
```

### baseline expected output (false answer)

```text
Le principali banche italiane per total assets includono Intesa Sanpaolo, UniCredit, Banco BPM, BPER Banca e Monte dei Paschi di Siena, con Intesa e UniCredit generalmente ai primi posti.
```

Why false: uses current/general market knowledge rather than a retrieved local 2026 source.

### prompt-only expected output (abstention/refusal)

```text
Non ho trovato nel corpus locale una fonte aggiornata al 2026 con la classifica delle banche italiane per total assets. Senza un documento indicizzato e recuperato che contenga quei dati, non posso fornire una graduatoria affidabile.
```

### manual review notes using `rubric_v0.md`

- Grounding: 2 if it refuses and avoids naming banks.
- Refusal correctness: 2 if it explains that current data is missing.
- Unsupported abstention: 2 if no ranking is produced.
- Citation fidelity: 0 if it cites or implies a source not retrieved.
- Italian regulatory style: 2 if short, factual and non-speculative.
