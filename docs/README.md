# Corpus documentale: overview

Questa cartella contiene il corpus documentale locale pensato per supportare retrieval e specializzazione nel dominio CRR + IFRS 9 con focus su banche italiane.

Cartelle principali (proposta):

- `docs/regulation/crr/` — normativa CRR, RTS/ITS, consolidati.
- `docs/accounting/ifrs9/` — IFRS 9, interpretazioni, linee guida tecniche.
- `docs/italy/banca_italia/` — circolari e istruzioni di Banca d'Italia.
- `docs/eu/eba/` — guideline, technical standards, reporting frameworks (COREP/FINREP/Pillar3).
- `docs/banks/intesa_sanpaolo/` — disclosure e documenti policy di Intesa Sanpaolo.
- `docs/banks/other_italian_banks/` — disclosure e documenti di altre banche italiane.

Cosa mettere in ogni cartella

- Documenti sorgente (preferibilmente PDF/HTML originali).
- File di metadata YAML con lo stesso base name (vedi `docs/metadata_template.yaml`).
- Una `README.md` locale che spiega eccezioni o convenzioni specifiche.

Come aggiungere un documento (passi rapidi)

1. Scegli la cartella corretta seguendo la gerarchia sopra.
2. Copia il file sorgente (`.pdf`, `.html`) nella cartella.
3. Crea un file YAML `<base>.yaml` con i campi minimi (`title`, `source`, `doc_type`, `date`, `language`, `jurisdiction`, `bank` se applicabile).
4. (Opzionale) Aggiungi una versione testuale (`.txt`/`.md`) se vuoi renderlo facilmente inspectable.
5. Ri-build dell'indice: usa l'endpoint `POST /index/rebuild` o imposta `DOCS_PATH` e riavvia come spiegato nel `backend/README.md`.

Per il ciclo completo download/update corpus, manifest locale e rebuild esplicito della cache embeddings, vedi [CORPUS_LIFECYCLE.md](CORPUS_LIFECYCLE.md).

Regole aggiuntive

- Segui le convenzioni in `docs/CONVENTIONS.md` per massimizzare compatibilità con la pipeline di ingestion.
- Mantieni i cambiamenti locali e offline-first: non introdurre dipendenze cloud.
