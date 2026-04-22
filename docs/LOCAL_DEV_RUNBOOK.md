# Local Developer Runbook

This runbook keeps local setup, smoke checks, evaluation, and Fiorell.IA training commands in one place. It does not change runtime behavior.

## Repository Location

Avoid running day-to-day Git operations from an iCloud-synced working tree when possible. This repository has been observed under:

```bash
/Users/itsgennymac/Library/Mobile Documents/com~apple~CloudDocs/Documents/GitHub/regulatory-insight-engine
```

iCloud can create duplicate files such as `.git/index 2` or stale `* 2.*` copies. If Git or VS Code reports missing `.git/HEAD`, `.git/config`, or ref lock errors, close VS Code, inspect the working tree, and consider moving a fresh clone outside iCloud Drive.

## Git Preflight

Run from the repository root:

```bash
git status -sb
git fetch --prune origin
git fsck --full
find .git -name '*.lock' -print
```

If `main` is behind `origin/main`, commit or stash local work before rebasing:

```bash
git pull --rebase origin main
```

## Frontend

Install dependencies and run the Vite app from the repository root:

```bash
npm install
npm run dev
```

Useful checks:

```bash
npm run test
npm run build
npm run lint
```

The frontend uses `VITE_GENISIA_API_URL` from `.env` or `.env.example`. Default local backend:

```bash
VITE_GENISIA_API_URL=http://127.0.0.1:8000
```

## Backend

Run backend commands from `backend/`:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Equivalent from the repository root:

```bash
uvicorn api:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

Backend checks:

```bash
cd backend
pytest
cd ..
python3 -m py_compile backend/api.py backend/genisia_rag_engine.py backend/config.py backend/schemas.py
```

## Ollama

Start Ollama and ensure required models are present:

```bash
ollama serve
ollama pull embeddinggemma
ollama pull qwen2.5:3b
curl http://localhost:11434/api/tags
```

## Corpus And Index

The default local paths are:

```bash
DOCS_PATH=./docs
CACHE_PATH=./backend/cache/embeddings_cache.pkl
```

Useful lifecycle commands:

```bash
python3 backend/corpus_lifecycle.py status
python3 backend/corpus_lifecycle.py ready
python3 backend/corpus_lifecycle.py download
python3 backend/corpus_lifecycle.py rebuild
```

Use explicit paths when working with an external corpus:

```bash
DOCS_PATH=/absolute/path/to/docs \
CACHE_PATH=/absolute/path/to/embeddings_cache.pkl \
uvicorn api:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

## Evaluation Smoke Checks

Run from the repository root:

```bash
cd backend
python3 eval/run_benchmark.py --help
python3 eval/compare_modes.py --help
cd ..
```

For Fiorell.IA prompt-only checks:

```bash
python3 fiorellia/eval/prompt_harness.py --help
```

Only run full evals when Ollama and the local corpus/cache are ready.

## Fiorell.IA Training Preflight

Training is optional and experimental. It must remain decoupled from the shared runtime.

```bash
python3 fiorellia/training/preflight_check_training.py
python3 fiorellia/training/train_lora_behavior_v1.py --config fiorellia/training/configs/config_lora_behavior_20260421.yaml
```

Do not publish a trained adapter until:

- the preflight passes,
- adapted outputs are generated,
- the four priority unsupported cases are manually reviewed,
- the full eval set is reviewed for regressions,
- the experiment manifest is updated.

## Minimal Release Smoke Checklist

```bash
git status -sb
npm run test
npm run build
cd backend && pytest && cd ..
python3 -m py_compile backend/api.py backend/genisia_rag_engine.py backend/config.py backend/schemas.py
```

If any command fails, document the failure before publishing or tagging.
