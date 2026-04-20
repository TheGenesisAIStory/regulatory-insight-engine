# Runtime RAG Runbook

Purpose
- Operational runbook to run and maintain the production RAG runtime (FastAPI backend + embeddings + local LLM via Ollama).

Core components
- Backend API: `backend/api.py` (FastAPI) — exposes health, ask, index rebuild endpoints.
- RAG engine: `backend/genisia_rag_engine.py` — retrieval, scoring, domain-gate, and answer assembly.
- Local model server: Ollama (embeddings + generation). Must be running and have required models pulled.
- Corpus: `docs/` (PDF/HTML/MD). Embeddings cached in `CACHE_PATH` (see config).
- Corpus lifecycle: `backend/corpus_lifecycle.py` handles download/update, manifest refresh and explicit index rebuild.

Quick start (local)
1. Start Ollama and ensure models are available.
2. Create and activate Python venv, install requirements (see `backend/requirements.txt`):
```bash
python3 -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```
3. Set environment variables (example):
```bash
export DOCS_PATH=$(pwd)/docs
export CACHE_PATH=$(pwd)/backend/cache/embeddings_cache.pkl
export ENABLE_DOMAIN_GATE=true
export DOMAIN_GATE_MODE=hybrid
export SCORE_THRESHOLD=0.30
```

If you reuse a cache built in another local corpus directory, keep `RAG_BASE_DIR`, `DOCS_PATH`, and `CACHE_PATH` aligned with that corpus so cache fingerprinting can match:

```bash
export RAG_BASE_DIR=/absolute/path/to/rag-banca
export DOCS_PATH=/absolute/path/to/rag-banca/normativa
export CACHE_PATH=/absolute/path/to/rag-banca/genisia_embeddings_cache.pkl
```

4. Run the backend:
```bash
cd backend
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Health & admin endpoints
- `GET /health` — basic liveness
- `GET /ready` — readiness after index loaded
- `POST /ask` — query endpoint (JSON payload)
- `POST /index/rebuild` — rebuild embeddings/index from `DOCS_PATH`

Indexing and caches
- Embeddings are fingerprinted on chunk parameters; changing `CHUNK_SIZE`, `CHUNK_OVERLAP` or embedding model requires cache rebuild.
- Startup reuses a valid persisted cache when available. It does not perform hidden full rebuilds.
- To manage the local lifecycle:
```bash
cd backend
python corpus_lifecycle.py download
python corpus_lifecycle.py status
python corpus_lifecycle.py rebuild
python corpus_lifecycle.py ready
```
- To rebuild:
  - call `POST /index/rebuild`.
  - watch logs for "Indice pronto" confirmation.

Domain gate
- Purpose: reduce hallucinations by requiring lexical/domain signals before answering.
- Config via env vars: `ENABLE_DOMAIN_GATE`, `DOMAIN_GATE_MODE` (`allowlist|denylist|hybrid`), `DOMAIN_GATE_TERMS_PATH` (JSON/lines file).
- Policy: When domain gate fails, runtime returns a controlled no-answer or abstains depending on `DOMAIN_GATE_MODE`.

No-answer policy (how abstention is decided)
- Factors combined:
  - top retrieval score < `SCORE_THRESHOLD`
  - optionally `min_score_gap` (difference between top and runner-up)
  - domain gate rejects query (if enabled)
- Result: backend returns a standardized no-answer response. See `backend/genisia_rag_engine.py` for implementation details.

Production vs local testing
- Production: run with an immutable `CACHE_PATH`, monitored Ollama instance, and audited logs. Keep `ENABLE_DOMAIN_GATE=true` until gate is validated.
- Local testing: safe to toggle thresholds, `top_k`, and `ENABLE_DOMAIN_GATE` but keep changes isolated to experiment cache paths.

Troubleshooting
- Ollama errors: ensure Ollama service is running and models installed.
- Missing documents: ensure `DOCS_PATH` points to the corpus folder; check log lines for file discovery.
- Index build hangs or slow: increase memory or reduce chunk parallelism; re-run `POST /index/rebuild`.
- Unexpected answers: raise `SCORE_THRESHOLD`, enable domain gate, or run evaluation scripts (see `docs/EVALUATION.md`).

Monitoring & logs
- Backend writes structured logs with info on index build and query routing. Keep an audit log for answered queries for later evaluation.

Where to look next
- Evaluation and calibration: `docs/EVALUATION.md`
- Supervised dataset and validator: `backend/eval/` and `docs/DOMAIN_DATASET.md`
