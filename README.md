# regulatory-insight-engine

![Python](https://img.shields.io/badge/python-3.8%2B-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Status: Experimental](https://img.shields.io/badge/status-experimental-orange)

A lightweight offline-first RAG prototype for CRR, IFRS 9, Banca d'Italia and Italian banking regulatory analysis. It combines a React UI, a local FastAPI backend, Ollama embeddings/generation, evaluation tooling and corpus organization runbooks.

**Beta status:** `v0.1.0-beta` is ready for local experimentation and evaluation. It is not production-ready legal, accounting or regulatory advice. On a fresh clone, `/ready` is expected to be `false` until you provide a coherent document corpus and embeddings cache, or rebuild embeddings locally.

Recommended beta runtime posture:

- keep everything local/offline-first;
- enable `ENABLE_DOMAIN_GATE=true` with `DOMAIN_GATE_MODE=hybrid`;
- use `SCORE_THRESHOLD=0.30` as the current safer baseline from local evaluation;
- validate your corpus with the benchmark before trusting changes.

Quick links:
 - Corpus lifecycle: [docs/CORPUS_LIFECYCLE.md](docs/CORPUS_LIFECYCLE.md)
 - Runtime runbook: [docs/RUNTIME_RAG.md](docs/RUNTIME_RAG.md)
 - Evaluation: [docs/EVALUATION.md](docs/EVALUATION.md)
 - Supervised dataset: [docs/DOMAIN_DATASET.md](docs/DOMAIN_DATASET.md)
 - Fiorell.IA specialization: [docs/FIORELLIA_SPECIALIZATION.md](docs/FIORELLIA_SPECIALIZATION.md)
 - Training prep: [docs/TRAINING_PREP.md](docs/TRAINING_PREP.md)
 - Validation checklist: [docs/CHECKLIST.md](docs/CHECKLIST.md)
 - Production vs experimental: [docs/PRODUCTION_EXPERIMENTAL.md](docs/PRODUCTION_EXPERIMENTAL.md)

Architecture (high level):
 - Frontend: React + Vite (UI, `src/`) — collects queries and renders answers.
 - Backend: FastAPI (`backend/api.py`) — exposes `POST /ask`, `POST /index/rebuild`, health and readiness endpoints.
 - RAG engine: `backend/genisia_rag_engine.py` — chunking, embedding (Ollama), retrieval, scoring (dense + keyword), domain gate, no-answer logic.
 - Local model server: Ollama — used for embeddings and generation; kept local (no cloud required).
 - Evaluation: `backend/eval/` contains dataset, validator, benchmarking and tuning scripts.

Setup (developer quickstart):
1. Frontend, from the repository root:
```bash
npm install
npm run dev
```
2. Backend, from the `backend/` directory:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Evaluation and calibration
 - Use the scripts in `backend/eval/` and follow the Evaluation Runbook: [docs/EVALUATION.md](docs/EVALUATION.md).
 - For threshold calibration, prefer `score_plus_domain_gate` mode and sweep `min_score_gap` and `threshold` first (cheap).

Domain gate & corpus
 - Corpus lives under `docs/` by default. Use `backend/corpus_lifecycle.py` to download/update sources, refresh the corpus manifest, and rebuild the persisted embeddings cache explicitly.
 - Domain gate configuration and terms file are under `backend/` and documented in the runtime runbook.

Training prep
 - Training tooling is isolated in `training/` and exported artifacts live under `training/data/output`.
 - Training is optional and experimental; see `docs/TRAINING_PREP.md`.
 - Fiorell.IA is a documented local specialization track for Italian banking regulation; it remains decoupled from the production RAG runtime.

Troubleshooting
 - See runtime runbook and evaluation docs above. Common issues: Ollama not running, missing models, cache mismatches after chunk changes.

Governance
 - What is production-oriented vs experimental, limits, and risk policy are documented in [docs/PRODUCTION_EXPERIMENTAL.md](docs/PRODUCTION_EXPERIMENTAL.md).

Contributors & next steps
 - See AGENTS.md for project rules and quality constraints.

# Gen.Is.IA - Regulatory Insight Engine

Interfaccia web per un assistente AI dedicato all'analisi della normativa bancaria e finanziaria. Il progetto affianca una UI React a un motore RAG locale Python/Ollama, pensato per interrogare una knowledge base normativa con risposte tracciabili, fonti, riferimenti e punteggi di rilevanza.

L'applicazione e' pensata per team di risk management, compliance, audit e regolamentazione che devono consultare documenti come IFRS 9, CRR, CRR II, linee guida EBA e Basel.

## Funzionalita'

- Dashboard per interrogare l'assistente normativo.
- Configurazione del modello locale e dei parametri RAG:
  - modello LLM;
  - Top-K dei passaggi recuperati;
  - dimensione dei chunk;
  - overlap tra chunk;
  - modalita' rapida.
- Metriche della knowledge base: documenti indicizzati, chunk, modello attivo e configurazione retrieval.
- Libreria documentale con stato di indicizzazione dei documenti.
- Risposte generate dal motore RAG locale, con:
  - livello di confidenza;
  - fonti recuperate;
  - riferimenti a documento, sezione e pagina;
  - punteggio di rilevanza;
  - anteprima degli estratti usati.
- Toast e stati di caricamento per azioni come ricostruzione indice, import PDF ed export.
- Layout responsive con sidebar desktop e pannello mobile.

> Stato attuale: la UI React chiama l'API locale FastAPI inclusa in `backend/`. Se l'API non e' avviata, la libreria documentale mostra ancora dati dimostrativi come fallback visivo, ma le interrogazioni non vengono piu' risolte con risposte mock.

> Limite beta importante: il repository non pubblica una cache embeddings pronta. Un nuovo clone deve preparare il corpus/cache oppure lanciare un rebuild locale, che puo' essere lento. Finche' questo passaggio non e' completato, `GET /ready` puo' rispondere `ready: false`.

## Stack tecnico

- React 18
- TypeScript
- Vite
- Tailwind CSS
- shadcn/ui e Radix UI
- Lucide React per le icone
- React Router
- TanStack Query
- Vitest e Testing Library
- ESLint
- Python 3 per il motore RAG locale
- FastAPI per esporre il motore RAG alla UI
- Ollama per embeddings e generazione

## Requisiti

- Node.js 18 o superiore per il frontend
- npm oppure Bun per installare le dipendenze React
- Python 3.8 o superiore per il motore RAG
- Ollama in esecuzione su `http://localhost:11434`
- Modelli Ollama:
  - `embeddinggemma`
  - `qwen2.5:3b`

Il repository contiene sia `package-lock.json` sia lockfile Bun. Scegli un solo package manager per lavorare in modo consistente.

## Avvio rapido

### Frontend React

Con npm, dalla root del repository:

```bash
npm install
npm run dev
```

Con Bun, dalla root del repository:

```bash
bun install
bun run dev
```

Poi apri l'URL mostrato dal terminale, di solito:

```text
http://localhost:5173
```

### Backend RAG locale

Il backend FastAPI e' incluso in:

```text
backend/
```

Avvia Ollama in un terminale:

```bash
ollama serve
```

Scarica i modelli richiesti, se non sono gia' presenti:

```bash
ollama pull embeddinggemma
ollama pull qwen2.5:3b
```

Installa le dipendenze Python:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Avvia l'API:

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

By default the API uses repository-relative paths so the project is portable after cloning.

Defaults (can be overridden via environment variables):

- `DOCS_PATH=./docs`
- `CACHE_PATH=./backend/cache/embeddings_cache.pkl`

You can override these values by setting `DOCS_PATH`, `CACHE_PATH`, or `RAG_BASE_DIR` in your environment when starting the server.

### Document corpus locale

Il repository usa `DOCS_PATH=./docs` come corpus locale stabile e `CACHE_PATH=./backend/cache/embeddings_cache.pkl` come cache embeddings persistente. Il downloader salva le fonti in cartelle di categoria come `docs/crr/`, `docs/ifrs9/`, `docs/basel/` e `docs/banca_ditalia/`. I documenti scaricati restano su disco tra i riavvii; il backend prova a caricare la cache valida allo startup e non ricostruisce embeddings in background.

Workflow consigliato:

```bash
cd backend
source .venv/bin/activate
python corpus_lifecycle.py download
python corpus_lifecycle.py status
python corpus_lifecycle.py rebuild
python corpus_lifecycle.py ready
```

`download` e' idempotente: salta i file gia' presenti e aggiorna `DOCS_PATH/corpus_manifest.json` con URL sorgente, filename, size, mtime e hash. `rebuild` aggiorna la cache embeddings e il manifest indice. Se il corpus cambia, `/ready` segnala cache stale e richiede un rebuild esplicito. Vedi [docs/CORPUS_LIFECYCLE.md](docs/CORPUS_LIFECYCLE.md), `docs/README.md` e `docs/CONVENTIONS.md`.

### Training preparation (optional)

Per preparare dati per domain adaptation leggera (LoRA / instruction tuning) è disponibile una pipeline opzionale in `training/`. È progettata per essere eseguita offline e separatamente dal backend RAG. Vedi `training/README.md`.


### Variabili ambiente backend

Il backend legge sia i nomi semplici sotto sia, dove già presenti, i vecchi alias `GENISIA_*`.

```text
OLLAMA_HOST=http://localhost:11434
LLM_MODEL=qwen2.5:3b
EMBED_MODEL=embeddinggemma
TOP_K=6
CHUNK_SIZE=420
CHUNK_OVERLAP=80
SCORE_THRESHOLD=0.12
CACHE_PATH=./backend/cache/embeddings_cache.pkl
DOCS_PATH=./docs
LOG_LEVEL=INFO
REQUEST_TIMEOUT_SECONDS=120
CHAT_TIMEOUT_SECONDS=240
CHAT_NUM_PREDICT=64
CHAT_NUM_CTX=2048
AUDIT_LOG_PATH=./docs/log/queries.jsonl
ENABLE_DOMAIN_GATE=false
DOMAIN_GATE_MODE=hybrid
DOMAIN_GATE_TERMS_PATH=
```

Esempio dalla root del repository:

```bash
OLLAMA_HOST=http://localhost:11434 \
LLM_MODEL=qwen2.5:3b \
DOCS_PATH=./docs \
CACHE_PATH=./backend/cache/embeddings_cache.pkl \
uvicorn api:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

### Domain gate runtime opzionale

Il comportamento score-only resta disponibile e disattivato di default:

```bash
cd backend
ENABLE_DOMAIN_GATE=false uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Per testare nel flusso reale la policy score + domain gate:

```bash
cd backend
source .venv/bin/activate
ENABLE_DOMAIN_GATE=true \
DOMAIN_GATE_MODE=hybrid \
SCORE_THRESHOLD=0.30 \
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Modalita' supportate:

- `denylist`: astensione se compaiono termini OOD noti.
- `allowlist`: astensione se non compaiono termini del perimetro indicizzato.
- `hybrid`: combina denylist e allowlist.

`DOMAIN_GATE_TERMS_PATH` puo' puntare a un JSON locale con `allow_terms`, `deny_terms`, `extra_allow_terms` ed `extra_deny_terms`.

### First-run (initialize index and cache)

After cloning and installing dependencies you can either copy an existing embeddings cache into the repository or rebuild the index locally.

Option A — copy an existing cache (faster):

```bash
# from repository root
mkdir -p backend/cache
cp /path/to/genisia_embeddings_cache.pkl backend/cache/embeddings_cache.pkl
```

Option B — download/update the corpus and rebuild the index locally:

```bash
cd backend
source .venv/bin/activate
python corpus_lifecycle.py download
python corpus_lifecycle.py rebuild
python corpus_lifecycle.py ready
```

You can also trigger a controlled rebuild through the running API with `POST /index/rebuild`. The backend does not force an expensive full reindex on startup or first ask when the cache is missing/stale.

If your document corpus lives outside the repository, set the `DOCS_PATH` environment variable to point to your local folder before starting the API:

```bash
cd backend
DOCS_PATH=/absolute/path/to/your/docs uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

If you also reuse an existing embeddings cache from that external corpus, set `RAG_BASE_DIR` consistently with the original corpus path so cache fingerprinting does not force a slow rebuild:

```bash
RAG_BASE_DIR=/absolute/path/to/rag-banca \
DOCS_PATH=/absolute/path/to/rag-banca/normativa \
CACHE_PATH=/absolute/path/to/rag-banca/genisia_embeddings_cache.pkl \
uvicorn api:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Recommendation: set `SCORE_THRESHOLD=0.30` in your environment to reduce false positive answers in typical setups:

```bash
export SCORE_THRESHOLD=0.30
```

After a successful rebuild and backend startup, the `/ready` endpoint should report `true` and the engine will serve queries from the persisted local index.

## Script disponibili

```bash
npm run dev
```

Avvia il server di sviluppo Vite.

```bash
npm run build
```

Genera la build di produzione.

```bash
npm run build:dev
```

Genera una build in modalita' development.

```bash
npm run preview
```

Serve localmente la build generata.

```bash
npm run lint
```

Esegue ESLint sul progetto.

```bash
npm run test
```

Esegue i test con Vitest.

```bash
npm run test:watch
```

Avvia Vitest in modalita' watch.

## Struttura del progetto

```text
.
├── index.html
├── package.json
├── vite.config.ts
├── vitest.config.ts
├── tailwind.config.ts
├── public/
├── backend/
│   ├── api.py
│   ├── genisia_rag_engine.py
│   ├── requirements.txt
│   └── README.md
└── src/
    ├── App.tsx
    ├── main.tsx
    ├── data/
    │   └── mockData.ts
    ├── components/
    │   ├── AppHeader.tsx
    │   ├── AskBox.tsx
    │   ├── AnswerPanel.tsx
    │   ├── ConfigSidebar.tsx
    │   ├── DocumentLibrary.tsx
    │   ├── EmptyState.tsx
    │   ├── MetricCard.tsx
    │   └── ui/
    ├── pages/
    │   ├── Index.tsx
    │   └── NotFound.tsx
    ├── hooks/
    ├── lib/
    │   ├── genisiaApi.ts
    │   └── utils.ts
    └── test/
```

## Come funziona il prototipo

La pagina principale e' definita in `src/pages/Index.tsx`.

Il flusso attuale e':

1. L'utente modifica i parametri nella sidebar di configurazione.
2. La UI controlla `GET /health` e `GET /documents` sul backend locale.
3. L'utente invia una domanda tramite `AskBox`.
4. L'app chiama `POST /ask` con domanda, `topK` e modello selezionato.
5. Il backend inizializza il motore RAG se necessario, recupera i chunk piu' rilevanti e interroga Ollama.
6. `AnswerPanel` mostra risposta, metadati e fonti recuperate.
7. `DocumentLibrary` mostra i documenti reali quando l'API e' disponibile; in caso contrario resta su dati dimostrativi.

La comunicazione frontend-backend e' centralizzata in:

```text
src/lib/genisiaApi.ts
```

## Motore RAG locale

Il motore RAG e' stato portato nel repository:

```text
backend/genisia_rag_engine.py
backend/api.py
```

Il codice mantiene la logica originale di `genisia_rag_best_of_both.py`, ma la espone come servizio HTTP invece che come sola console interattiva.

### `backend/genisia_rag_engine.py`

Script principale del motore Gen.Is.IA. Esegue:

- verifica di Ollama su `http://localhost:11434`;
- download della normativa configurata;
- lettura dei PDF con PyMuPDF;
- chunking dei testi;
- generazione embeddings con `embeddinggemma`;
- salvataggio e riuso della cache `genisia_embeddings_cache.pkl`;
- ricerca ibrida semantic + keyword;
- generazione della risposta con `qwen2.5:3b`;
- restituzione delle fonti usate con score dense, keyword e combinato.

Parametri principali configurati nello script:

```text
EMBED_MODEL = embeddinggemma
CHAT_MODEL = qwen2.5:3b
TOP_K = 6
CHUNK_WORDS = 420
CHUNK_OVERLAP = 80
BATCH_SIZE = 20
MAX_EMBED_CHARS = 1800
SCORE_THRESHOLD = 0.12
```

Le categorie indicizzate di default sono:

```text
ifrs9, crr, banca_ditalia
```

Puoi modificarle senza cambiare codice usando la variabile d'ambiente:

```bash
GENISIA_INDEX_CATEGORIES=ifrs9,crr,basel,banca_ditalia python3 genisia_rag_best_of_both.py
```

### Download normativa

La logica di download e' inclusa in `backend/genisia_rag_engine.py`. Scarica PDF diretti e, dove configurato, analizza pagine HTML per trovare link PDF.

Fonti configurate:

- IFRS 9, da IFRS Foundation;
- CRR 575/2013;
- Basel Framework e Basel III post-crisis reforms;
- Circolare 285 e aggiornamenti da Banca d'Italia.

I file vengono salvati sotto la directory configurata come `GENISIA_RAG_BASE_DIR`, per default:

```text
~/GitHub/rag-banca/normativa
```

### Cache embeddings

Le cache presenti sono:

```text
genisia_embeddings_cache.pkl   circa 6.4 MB
embeddings_cache.pkl           circa 1.0 MB
```

`genisia_embeddings_cache.pkl` e' quella usata dal motore aggiornato. La cache viene invalidata automaticamente quando cambiano modello embedding, parametri di chunking o fingerprint dei PDF indicizzati.

## Integrazione frontend-backend

Il frontend e il motore RAG sono collegati tramite:

- `GET /health`;
- `GET /ready`;
- `GET /documents`;
- `POST /ask`;
- `POST /index/rebuild`.

L'URL API di default e':

```text
http://127.0.0.1:8000
```

Puoi cambiarlo lato frontend con:

```bash
VITE_GENISIA_API_URL=http://127.0.0.1:8000 npm run dev
```

Formato minimo atteso per `POST /ask`:

```json
{
  "question": "Quando un'esposizione passa da Stage 1 a Stage 2 secondo IFRS 9?",
  "topK": 6,
  "model": "qwen2.5:3b"
}
```

Formato minimo consigliato per la risposta:

```json
{
  "answer": "Risposta generata dal contesto recuperato...",
  "model": "qwen2.5:3b",
  "confidence": "high",
  "noAnswer": false,
  "reason": null,
  "durationMs": 1234,
  "sources": [
    {
      "document": "IFRS9.pdf",
      "page": 47,
      "score": 0.82,
      "denseScore": 0.79,
      "keywordScore": 0.18,
      "excerpt": "Estratto usato come contesto..."
    }
  ]
}
```

Quando il retrieval non supera `SCORE_THRESHOLD`, il backend non chiama il modello per inventare una risposta: restituisce `noAnswer: true`, `confidence: "low"` e una motivazione di insufficienza informativa.

## Evoluzione backend

Il motore RAG locale copre gia' download, parsing PDF, chunking, embeddings, cache, retrieval, generazione, API locale, readiness e audit JSONL. I prossimi step consigliati sono:

- persistenza opzionale in un vector database;
- export reale in PDF, DOCX e TXT;
- test end-to-end su domande normative note.

Una possibile architettura futura:

```text
Frontend React
    |
API applicativa
    |
Document ingestion -> Chunking -> Embeddings -> Vector DB
    |
Retriever -> Prompt builder -> LLM locale/privato
    |
Risposta con citazioni e confidenza
```

## Testing

Il frontend usa Vitest. Il backend usa pytest con un motore RAG mockato, cosi' i test non dipendono da Ollama o dai PDF locali.

Frontend:

```bash
npm run test
```

Backend:

```bash
cd backend
source .venv/bin/activate
pytest
```

Verifiche utili:

```bash
python3 -m py_compile backend/api.py backend/genisia_rag_engine.py
npm run lint
npm run build
```

## Evaluation RAG

Il repository include un benchmark locale per misurare la baseline RAG esistente senza ricostruire pipeline, ingestion, embeddings, retrieval, API o frontend.

Dataset versionato:

```text
backend/eval/dataset.jsonl
```

Dataset di dominio CRR/IFRS 9/Banca d'Italia:

```text
backend/eval/domain_dataset.jsonl
```

Esecuzione rapida, deterministica, focalizzata su retrieval e no-answer:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py
```

Benchmark di dominio con metriche per categoria:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py \
  --dataset eval/domain_dataset.jsonl \
  --out eval/reports/domain_latest.json \
  --markdown eval/reports/domain_latest.md
```

Esecuzione completa con generazione LLM locale e groundedness euristica:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py --generate
```

Report generati:

```text
backend/eval/reports/latest.json
backend/eval/reports/latest.md
```

Metriche incluse:

- source hit rate nei top-k;
- no-answer accuracy;
- schema validity;
- latenza media e p50;
- groundedness euristica tramite overlap tra risposta e chunk recuperati, solo con `--generate`;
- casi falliti, false answer, false no-answer e fonti attese non recuperate.
- metriche e failure cases per categoria, utili per il dataset di dominio.

Uso consigliato per regression testing:

```bash
python eval/run_benchmark.py
git diff -- backend/eval/reports/latest.md
```

Esegui il benchmark prima e dopo modifiche a chunking, embeddings, prompt, score threshold o retriever. Un calo in source hit rate, no-answer accuracy o groundedness va trattato come segnale di regressione da ispezionare manualmente.

Per il benchmark di dominio, controlla in particolare:

- `crr`, `ifrs9`, `banca_italia`: source hit rate e false no-answer;
- `bank_specific`, `near_domain_ood`, `no_answer`: no-answer accuracy e false answers;
- failure cases per categoria nel report Markdown.

Lo script termina con exit code non-zero se rileva casi falliti. Questo comportamento e' intenzionale per usarlo come controllo di regressione.

Calibrazione soglia no-answer:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py --calibrate-thresholds 0.12,0.18,0.22,0.25,0.30
```

Calibrazione con astensione OOD euristica opzionale:

```bash
python eval/run_benchmark.py \
  --calibrate-thresholds 0.12,0.18,0.22,0.25,0.30 \
  --domain-gate
```

La calibrazione genera una tabella comparativa con source hit rate, copertura in-domain, no-answer accuracy, false answers, false no-answers e latenza media. Il domain gate e' locale e semplice: non cambia il retriever, ma permette di misurare una policy di astensione su domini regolamentari non indicizzati come MiFID II, GDPR, PSD2, SFDR e AML.

## Troubleshooting

- `Ollama non risponde`: avvia `ollama serve` e verifica `curl http://localhost:11434/api/tags`.
- `model not found`: installa il modello richiesto con `ollama pull qwen2.5:3b` oppure imposta `LLM_MODEL` a un modello disponibile.
- `embedding model not found`: installa `ollama pull embeddinggemma`.
- `Indice non ancora caricato`: fai una prima domanda oppure chiama `POST /index/rebuild`.
- `Timeout da Ollama`: il primo giro puo' essere lento per caricare il modello. Se il modello genera lentamente su CPU, riduci `CHAT_NUM_PREDICT`, mantieni `CHAT_NUM_CTX` contenuto oppure aumenta `CHAT_TIMEOUT_SECONDS`.
- `Nessun PDF trovato`: controlla `DOCS_PATH` e la struttura `normativa/<categoria>/*.pdf`.
- `CORS/API non raggiungibile`: controlla che la UI punti a `VITE_GENISIA_API_URL=http://127.0.0.1:8000`.

## Build di produzione

```bash
npm run build
```

L'output viene generato nella directory `dist/`.

Per verificare la build localmente:

```bash
npm run preview
```

## Note operative

- Le risposte mostrate non devono essere considerate consulenza legale, contabile o regolamentare.
- La risposta viene generata solo dal contesto recuperato; se il contesto e' insufficiente viene restituito un no-answer.
- L'audit locale salva hash della query, fonti, score e tempi in `queries.jsonl`; non salva il testo completo della domanda.
- Prima dell'uso in contesti professionali e' necessario validare retrieval, soglie e fonti documentali con controlli di qualita'.

## Licenza

MIT. Vedi [LICENSE](LICENSE).
