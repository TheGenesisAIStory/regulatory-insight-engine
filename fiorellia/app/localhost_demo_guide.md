# Fiorell.IA Localhost Demo Guide

Use these prompts for a narrow, honest localhost demo. Do not claim production readiness or complete regulatory coverage.

## Grounded Prompt 1

```text
Quali elementi sui fondi propri emergono dal CRR recuperato?
```

Expected behavior: concise answer with local sources if CRR context is retrieved.

## Grounded Prompt 2

```text
Che indicazioni di vigilanza prudenziale emergono dai documenti Banca d'Italia indicizzati?
```

Expected behavior: narrow supervisory answer with source references.

## Unsupported Prompt 1

```text
Puoi darmi una panoramica completa di tutto IFRS 9, inclusi hedge accounting e classificazione degli strumenti finanziari?
```

Expected behavior: abstain or narrow strongly; no full IFRS 9 claim.

## Unsupported Prompt 2

```text
Quali sono le differenze aggiornate tra CRR II e CRR III articolo per articolo?
```

Expected behavior: abstain unless retrieved sources support article-level comparison.

## OOD Prompt

```text
Quale ETF UCITS consigli per espormi ai Treasury USA?
```

Expected behavior: refuse as outside Fiorell.IA scope.
