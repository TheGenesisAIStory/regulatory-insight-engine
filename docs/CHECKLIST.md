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
uvicorn backend.api:app --reload --port 8000
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
python3 backend/eval/compare_modes.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/compare_modes --top-k 6 --threshold 0.12
```
7. Run a small tune on `min_score_gap`:
```bash
python3 backend/eval/tune_retrieval.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/tune_min_gap --top-ks 6 --thresholds 0.12 --min-score-gaps 0.02,0.05
```
8. Inspect reports in `backend/eval/reports/` and confirm recommended config.

Final checks before marking ready
- Confirm `docs/` contains referenced sources for `expected_sources` in supervised dataset.
- Confirm no PII in `docs/` or dataset.
- Commit `backend/eval/supervised_seed.cleaned.jsonl` and update `DATASET_VERSION` if present.
- Add a short `CHANGELOG.md` entry describing the dataset and run parameters used for the reports.
