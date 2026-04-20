# Local Corpus Lifecycle

This project keeps the RAG runtime offline-first: documents are downloaded once into a local corpus directory, embeddings are persisted to disk, and startup reuses a valid cache whenever possible.

The runtime answer-generation pipeline is unchanged. This workflow only manages document availability and index readiness.

## Paths

Default paths are repository-relative:

```text
DOCS_PATH=./docs
CACHE_PATH=./backend/cache/embeddings_cache.pkl
```

Generated state files:

```text
DOCS_PATH/corpus_manifest.json
CACHE_PATH with .manifest.json suffix
```

The corpus manifest records local files, source URL when known, size, mtime and SHA-256. The index manifest records the cache metadata, chunking settings and embedding model used for the persisted cache.

## Commands

Run these from `backend/` with the backend virtualenv active:

```bash
source .venv/bin/activate
python corpus_lifecycle.py status
```

Download or update the configured regulatory corpus:

```bash
python corpus_lifecycle.py download
```

The download is idempotent. Existing files are kept and skipped; the manifest is refreshed from disk.

Rebuild the embeddings cache from the current local corpus:

```bash
python corpus_lifecycle.py rebuild
```

Download first, then rebuild:

```bash
python corpus_lifecycle.py rebuild --download
```

Check whether startup can be fast because corpus and cache are already aligned:

```bash
python corpus_lifecycle.py ready
```

`ready` exits with status `0` when a valid persisted cache exists for the current corpus and config. It exits with status `1` when a rebuild is needed.

## Startup Behavior

On backend startup, the API tries to preload an existing valid embeddings cache. It does not rebuild embeddings in the background.

`GET /ready` is `true` when:

- Ollama is reachable;
- configured chat and embedding models are available;
- local documents exist;
- the persisted cache matches the current corpus and chunking/embedding config;
- the index is loaded in memory.

If documents changed after the cache was built, readiness reports a stale cache and asks for an explicit rebuild.

## Freshness Tradeoff

There are two separate freshness concerns:

- **Corpus freshness:** whether local PDFs mirror the latest upstream sources.
- **Index freshness:** whether embeddings match the local PDFs and runtime chunking config.

Downloading updated documents does not automatically rebuild embeddings. This is intentional: automatic rebuilds can be slow and hard to debug locally. Prefer:

```bash
python corpus_lifecycle.py download
python corpus_lifecycle.py status
python corpus_lifecycle.py rebuild
```

Use the benchmark after meaningful corpus changes.

## Troubleshooting

- `documents: 0`: check `DOCS_PATH` and the expected category folders.
- `cacheValid: false` and `cacheStale: true`: documents or chunking settings changed; run `python corpus_lifecycle.py rebuild`.
- `cacheExists: false`: no persisted embeddings cache exists yet; run `python corpus_lifecycle.py rebuild`.
- `/ready` false after startup: inspect `python corpus_lifecycle.py status`, then rebuild if needed.
- Slow rebuild: this is expected on CPU-only Ollama. Keep the process explicit rather than hidden in app startup.
