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
- `example_type` : uno dei: `factual_qa`, `definitional_qa`, `comparison_qa`, `no_answer`, `classification`, `source_grounded`.

Regole di creazione esempi
- Evita di inserire dati personali o informazioni sensibili.
- Preferisci risposte concise e verificabili nel corpus (1-4 frasi per risposte testuali).
- In `expected_sources` inserisci il nome del file così come presente in `docs/` (o l'identificatore usato nel processo di indexing) per mantenere tracciabilità.
- Per `no_answer` includi un `rationale` che spiega perché il corpus non contiene la risposta.

ID e versioning
- Usa prefissi significativi: `<category>_<type>_<nnn>`. Mantieni `id` unico nel dataset.
- Aggiungi versione del dataset a livello di repository modificando il file `backend/eval/DATASET_VERSION` (optional).

Validazione e deduplicazione
- Usa lo script `backend/eval/validate_supervised_dataset.py` per validare i record e rimuovere duplicati (per `id` o per hash di `category|input|target`).
- Non eseguire dump automatici dei PDF nel dataset: il dataset deve puntare a fonti già archiviate nel corpus con `expected_sources`.

Processo di review
- Ogni nuovo batch di esempi deve essere revisionato da almeno un revisore domain-expert.
- Se un esempio cambia (target aggiornato), aggiorna l'`id` con suffisso di versione oppure registra la modifica in `CHANGELOG.md` del dataset.
