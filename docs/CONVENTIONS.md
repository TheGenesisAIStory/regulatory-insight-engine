# Convenzioni e metadata per il corpus documentale

Scopo: definire regole semplici e coerenti per nominare i file e fornire metadata sidecar, in modo che il sistema di retrieval possa categorizzare e filtrare i documenti con affidabilità.

1) Principi generali
- Mantieni i file originali (PDF/HTML) e aggiungi un file YAML con lo stesso nome base contenente i metadata.
- Evita di modificare i contenuti originali: salva versioni convertite (`.txt`/`.md`) se serve per processing, ma conserva l'originale.

2) Metadata sidecar (obbligatori consigliati)
- filename: stesso base name del file a cui si riferisce
- `title`: string
- `source`: es. "EBA", "Banca d'Italia", "Intesa Sanpaolo"
- `jurisdiction`: es. `EU`, `IT`
- `regulator`: es. `EBA`, `Banca d'Italia` (se applicabile)
- `doc_type`: es. `regulation`, `guidance`, `circular`, `pillar3`, `annual_report`, `ifrs_policy`
- `date`: YYYY-MM-DD (quando noto)
- `bank`: nome banca se documento bank-specific (es. `Intesa Sanpaolo`)
- `language`: es. `it`, `en`
- `id`: opzionale, identificatore univoco interno
- `tags`: lista opzionale di tag (es. `sicr`, `expected_loss`, `collective_provision`)

3) Naming file consigliato
- Base: `<source>__<doc_type>__<date>__<short-id>.<ext>`
  - esempio: `eba__crr__20230215__rts-q1.pdf`
  - documento banca-specifico: `intesa__pillar3__20231231__report.pdf`

4) Tipi di documento (suggeriti per `doc_type`)
- `regulation` — testi legislativi e regolamentari (CRR, CRD)
- `rts` / `its` — technical standards e implementazioni normative
- `guidance` — linee guida o Q&A pubblicati da regolatori
- `circular` — circolari di vigilanza (Banca d'Italia)
- `pillar3` — disclosure Pillar 3
- `annual_report` — bilanci e relazioni annuali
- `ifrs_policy` — policy e note IFRS 9 della banca

5) Estensioni e processi
- Quando aggiungi una nuova cartella o categoria, aggiungi una `README.md` locale che spiega eccezioni o convenzioni specifiche.
- Non cambiare la pipeline di ingestion: mantieni metadata e nomi coerenti così che lo script di indexing possa continuare a funzionare.
