# Local Validation Checklist

Prerequisites
- macOS / Linux, Python 3.9+, Node 18+, Ollama installed and running.
- Repo cloned and on branch `main`.
- Backend venv created and requirements installed.

Quick smoke (start-to-finish)
1. Start Ollama and ensure required models are pulled.
2. Activate backend venv and start backend server:
```bash
source backend/.venv/bin/activate
cd backend
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```
3. Verify health endpoints:
```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```
4. Rebuild index (if first run):
```bash
curl -X POST http://127.0.0.1:8000/index/rebuild
```
5. Run dataset validator:
```bash
python3 backend/eval/validate_supervised_dataset.py --input backend/eval/supervised_seed.jsonl --output backend/eval/supervised_seed.cleaned.jsonl
```
6. Run compare modes to confirm domain gate improvements:
```bash
RAG_BASE_DIR=/absolute/path/to/rag-banca \
DOCS_PATH=/absolute/path/to/rag-banca/normativa \
CACHE_PATH=/absolute/path/to/rag-banca/genisia_embeddings_cache.pkl \
python3 backend/eval/compare_modes.py \
  --dataset backend/eval/dataset.jsonl \
  --outdir backend/eval/reports/compare_modes \
  --top-k 6 \
  --threshold 0.30
```
7. Optional: run a small tune on `min_score_gap`:
```bash
python3 backend/eval/tune_retrieval.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/tune_min_gap --top-ks 6 --thresholds 0.12 --min-score-gaps 0.02,0.05
```
8. Inspect reports in `backend/eval/reports/` and confirm recommended config.

Notes:
- If you reuse an embeddings cache built outside this repository, set `RAG_BASE_DIR` consistently with that cache. Otherwise the fingerprint can invalidate the cache and trigger a slow rebuild.
- `run_benchmark.py` intentionally exits non-zero when failed cases are present. Inspect the report before treating it as an execution failure.
- Avoid parallel first `/ask` calls on a cold backend; initialize the index first with a single request or an explicit rebuild.

Final checks before marking ready
- Confirm `docs/` contains referenced sources for `expected_sources` in supervised dataset.
- Confirm no PII in `docs/` or dataset.
- Commit `backend/eval/supervised_seed.cleaned.jsonl` and update `DATASET_VERSION` if present.
- Add a short `CHANGELOG.md` entry describing the dataset and run parameters used for the reports.
