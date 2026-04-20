# Gen.Is.IA RAG API

Backend locale FastAPI per collegare la UI React al motore RAG originale di Gen.Is.IA.

## Avvio

Run these commands from the `backend/` directory. If you prefer to start the API from the repository root, use `uvicorn api:app --app-dir backend` instead of `uvicorn api:app`.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

In un altro terminale deve essere attivo Ollama:

```bash
ollama serve
ollama pull embeddinggemma
ollama pull qwen2.5:3b
```

Per impostazione predefinita l'API usa percorsi relativi nel repository. I valori di default sono:

- `DOCS_PATH=./docs`
- `CACHE_PATH=./backend/cache/embeddings_cache.pkl`

Puoi comunque cambiare la base directory con:

```bash
RAG_BASE_DIR=/percorso/rag-banca uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

## Configurazione

Variabili principali:

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
AUDIT_LOG_PATH=./docs/log/queries.jsonl
ENABLE_DOMAIN_GATE=false
DOMAIN_GATE_MODE=hybrid
DOMAIN_GATE_TERMS_PATH=
```

Gli alias legacy `GENISIA_*` sono ancora supportati dove già usati.

## Document corpus locale

Il progetto supporta una struttura documentale locale pensata per raccogliere normativa, guide di vigilanza e disclosure bancarie. Per default il backend legge i documenti da `DOCS_PATH` (vedi sezione Configurazione sopra). Per lavorare con il corpus consigliato all'interno di questo repository:

- Posiziona i documenti sotto la cartella `docs/` seguendo la struttura suggerita (es.: `docs/regulation/crr/`, `docs/accounting/ifrs9/`, `docs/italy/banca_italia/`, `docs/eu/eba/`, `docs/banks/intesa_sanpaolo/`, `docs/banks/other_italian_banks/`).
- Per ogni file sorgente crea un file YAML sidecar con lo stesso base name (es. `miofile.pdf` + `miofile.yaml`) contenente i campi minimi (`title`, `source`, `doc_type`, `date`, `language`, `jurisdiction`, `bank` se applicabile). Vedi `docs/metadata_template.yaml` e `docs/CONVENTIONS.md` per convenzioni e template.
- Per aggiornare l'indice esistente usa l'endpoint `POST /index/rebuild` oppure imposta `DOCS_PATH` sulla cartella e riavvia il servizio; questo evita di dover modificare la pipeline di ingestion.

Questa organizzazione è pensata per essere compatibile con la pipeline offline-first: evita dipendenze cloud e mantiene il runtime inalterato.

## Runtime domain gate

Score-only remains the default behavior:

```bash
ENABLE_DOMAIN_GATE=false uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

To test score + domain gate in the real API flow:

```bash
ENABLE_DOMAIN_GATE=true \
DOMAIN_GATE_MODE=hybrid \
SCORE_THRESHOLD=0.30 \
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Supported modes:

- `denylist`: abstain when known out-of-domain terms are present.
- `allowlist`: abstain unless at least one indexed-domain term is present.
- `hybrid`: combine both checks.

Optional custom terms file:

```json
{
  "allow_terms": ["ifrs", "crr", "sicr"],
  "deny_terms": ["mifid", "gdpr"],
  "extra_allow_terms": ["banca"],
  "extra_deny_terms": ["psd2"]
}
```

Set it with `DOMAIN_GATE_TERMS_PATH=/absolute/path/to/domain_gate_terms.json`.

## Endpoint

- `GET /health`
- `GET /ready`
- `GET /documents`
- `POST /ask`
- `POST /index/rebuild`

`/ready` controlla Ollama, modelli, PDF, cache e indice. L'indice è caricato lazy alla prima domanda oppure tramite rebuild.

## Test

```bash
source .venv/bin/activate
pytest
```

I test usano un motore mockato e non richiedono Ollama.

## Evaluation benchmark

Dataset versionato:

```text
eval/dataset.jsonl
```

Benchmark rapido su retrieval/no-answer:

```bash
python eval/run_benchmark.py
```

Benchmark completo con generazione locale e groundedness euristica:

```bash
python eval/run_benchmark.py --generate
```

Report generati localmente:

```text
eval/reports/latest.json
eval/reports/latest.md
```

## Supervised domain dataset (seed)

Per creare e validare dataset supervisionati (esempi QA, classificazione, no-answer, source-grounded) abbiamo aggiunto una cartella di lavoro sotto `backend/eval/` con strumenti di validazione.

- Seed dataset: [backend/eval/supervised_seed.jsonl](backend/eval/supervised_seed.jsonl)
- Schema JSON: [backend/eval/supervised_schema.json](backend/eval/supervised_schema.json)
- Validator + dedupe: [backend/eval/validate_supervised_dataset.py](backend/eval/validate_supervised_dataset.py)
- Linee guida di annotazione: [backend/eval/ANNOTATION_GUIDELINES.md](backend/eval/ANNOTATION_GUIDELINES.md)

Comando rapido per validare e pulire il seed:

```bash
python backend/eval/validate_supervised_dataset.py --input backend/eval/supervised_seed.jsonl --output backend/eval/supervised_seed.cleaned.jsonl
```

Segui le regole in `ANNOTATION_GUIDELINES.md` per aggiungere nuovi esempi. Mantieni sempre `expected_sources` per preservare la provenance.

## Training preparation (optional)

Una pipeline minima per preparare dati e artefatti per una domain adaptation leggera è fornita nella cartella `training/`. Questa pipeline è opzionale e disaccoppiata dal runtime RAG — non modifica `backend/` e non è eseguita automaticamente in produzione.

Vedi `training/README.md` per dettagli su configurazione, split, esportazione in formato instruction-tuning e salvataggio artefatti.

## Retrieval tuning (experimental)

Uno script sperimentale per confrontare configurazioni di retrieval è disponibile in `backend/eval/tune_retrieval.py`.

Uso rapido (griglia sicura, non ricampiona chunk):

```bash
python3 backend/eval/tune_retrieval.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/tune_retrieval --top-ks 4,6,8 --thresholds 0.10,0.12,0.18
```

Per variare `chunk_size` e `chunk_overlap` (RICHIAMA ricostruzione indice ed embeddings, costoso):

```bash
python3 backend/eval/tune_retrieval.py --vary-chunk --chunk-sizes 200,420,800 --chunk-overlaps 40,80 --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/tune_retrieval
```

I risultati sono salvati in `--outdir` come file JSON `benchmark_<run>.json` e `tuning_summary.json`.

## Operational runbook & docs

This repository now includes operator-facing runbooks and checklists under the top-level `docs/` folder. See:

- Runtime runbook: [docs/RUNTIME_RAG.md](../docs/RUNTIME_RAG.md)
- Evaluation runbook: [docs/EVALUATION.md](../docs/EVALUATION.md)
- Validation checklist: [docs/CHECKLIST.md](../docs/CHECKLIST.md)
- Production vs experimental guidance: [docs/PRODUCTION_EXPERIMENTAL.md](../docs/PRODUCTION_EXPERIMENTAL.md)

Follow those docs for operational procedures, threshold calibration and safety checks before changing runtime parameters.

