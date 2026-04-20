# Linee guida di annotazione — dataset supervisionato (CRR / IFRS9 / banche italiane)

Scopo: definire regole chiare per creare esempi supervisionati riutilizzabili per domain adaptation senza introdurre dati sensibili.

Campi richiesti per ogni record (JSONL):
- `id` : stringa univoca (es. `ifrs9_factual_001`).
- `category` : dominio principale (`ifrs9`, `crr`, `banca_ditalia`, `eba`, `banks`, `annotation`).
- `subcategory`: tag libero per dettaglio (es. `sicr`, `pillar3`, `definitions`).
- `input` : la query o testo sorgente annotato.
- `target` : la risposta attesa o etichetta per task di classification. Per `no_answer` lasciare stringa vuota.
- `expected_sources`: lista di nomi di file o identificatori di documento presenti nel corpus (mantieni provenance).
- `rationale` : opzionale, breve spiegazione del perché del target.
- `language` : codice lingua (es. `it`).
- `example_type` : uno dei tipi base (`factual_qa`, `definitional_qa`, `comparison_qa`, `no_answer`, `classification`, `source_grounded`) oppure uno dei tipi sperimentali Fiorell.IA (`answer_with_citations`, `refuse_out_of_scope`, `regulatory_comparison`, `italian_supervisory_language`, `bank_specific_disclosure_style`).

Regole di creazione esempi
- Evita di inserire dati personali o informazioni sensibili.
- Preferisci risposte concise e verificabili nel corpus (1-4 frasi per risposte testuali).
- In `expected_sources` inserisci il nome del file così come presente in `docs/` (o l'identificatore usato nel processo di indexing) per mantenere tracciabilità.
- Per `no_answer` includi un `rationale` che spiega perché il corpus non contiene la risposta.

## Estensione Fiorell.IA

Fiorell.IA è una traccia sperimentale di specializzazione locale e offline-first. Non sostituisce il RAG runtime e non deve insegnare al modello a rispondere senza fonti.

Tipi aggiuntivi:

- `answer_with_citations`: risposta in italiano con citazioni esplicite e `expected_sources` non vuoto.
- `refuse_out_of_scope`: domanda fuori perimetro o non supportata; `target` deve essere una breve astensione o stringa vuota, con `rationale`.
- `regulatory_comparison`: confronto tra concetti normativi/contabili, es. CRR default vs IFRS 9 staging.
- `italian_supervisory_language`: stile di risposta in linguaggio di vigilanza italiano, conciso e prudente.
- `bank_specific_disclosure_style`: domande su disclosure/Pillar 3/bilanci di banche italiane; risponde solo se la fonte banca-specifica è presente.

Regole Fiorell.IA:

- Lingua predefinita: italiano.
- Rispondere solo su CRR, IFRS 9, Banca d'Italia, EBA, Basel, Pillar 3 e disclosure bancarie indicizzate.
- Ogni risposta fattuale deve avere `expected_sources`.
- Le domande plausibili ma non supportate sono esempi positivi di rifiuto, non errori da coprire con conoscenza esterna.
- Per banca-specific disclosure, non usare informazioni generali sulla banca se il documento locale non è presente.

ID e versioning
- Usa prefissi significativi: `<category>_<type>_<nnn>`. Mantieni `id` unico nel dataset.
- Aggiungi versione del dataset a livello di repository modificando il file `backend/eval/DATASET_VERSION` (optional).

Validazione e deduplicazione
- Usa lo script `backend/eval/validate_supervised_dataset.py` per validare i record e rimuovere duplicati (per `id` o per hash di `category|input|target`).
- Non eseguire dump automatici dei PDF nel dataset: il dataset deve puntare a fonti già archiviate nel corpus con `expected_sources`.

Processo di review
- Ogni nuovo batch di esempi deve essere revisionato da almeno un revisore domain-expert.
- Se un esempio cambia (target aggiornato), aggiorna l'`id` con suffisso di versione oppure registra la modifica in `CHANGELOG.md` del dataset.
