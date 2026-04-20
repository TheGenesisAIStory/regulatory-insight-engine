# Fiorell.IA Manual Eval Summary — 2026-04-21

Scope: Fiorell.IA `eval_set_v0.jsonl` executed against the shared runtime without backend, retrieval, indexing, serving or domain gate code changes.

## Commands Run

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python corpus_lifecycle.py ready
```

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python eval/run_benchmark.py \
  --dataset eval/dataset.jsonl \
  --out ../fiorellia/eval/reports/manual_eval_20260421/shared_baseline.json \
  --markdown ../fiorellia/eval/reports/manual_eval_20260421/shared_baseline.md
```

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python eval/compare_modes.py \
  --dataset eval/dataset.jsonl \
  --outdir ../fiorellia/eval/reports/manual_eval_20260421/shared_compare_modes
```

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python eval/run_benchmark.py \
  --dataset /tmp/fiorellia_eval_set_v0_runner.jsonl \
  --out ../fiorellia/eval/reports/manual_eval_20260421/fiorellia_eval_set_v0_shared_runtime.json \
  --markdown ../fiorellia/eval/reports/manual_eval_20260421/fiorellia_eval_set_v0_shared_runtime.md
```

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python eval/run_benchmark.py \
  --dataset /tmp/fiorellia_eval_set_v0_runner.jsonl \
  --domain-gate \
  --out ../fiorellia/eval/reports/manual_eval_20260421/fiorellia_eval_set_v0_domain_gate.json \
  --markdown ../fiorellia/eval/reports/manual_eval_20260421/fiorellia_eval_set_v0_domain_gate.md
```

## Readiness

- Corpus/cache path: `/Users/itsgennymac/GitHub/rag-banca`
- Cache valid: true
- Cached chunks: 1329
- Runtime code changed: no

## Results

| Run | Cases | No-answer accuracy | False answers | False no-answers | Schema validity | Avg latency |
|---|---:|---:|---:|---:|---:|---:|
| Shared baseline, score-only | 32 | 15.6% | 27 | 0 | 100.0% | 588 ms |
| Shared compare, score-only | 32 | 15.6% | 27 | 0 | n/a | 596 ms |
| Shared compare, score + domain gate | 32 | 93.8% | 2 | 0 | n/a | 485 ms |
| Shared compare, retrieval opt | 32 | 15.6% | 27 | 0 | n/a | 471 ms |
| Fiorell.IA eval set, shared score-only | 16 | 31.2% | 11 | 0 | 100.0% | 703 ms |
| Fiorell.IA eval set, domain-gate diagnostic | 16 | 75.0% | 4 | 0 | 100.0% | 628 ms |

## Review Slices

### `in_scope_grounded`

- Cases: 5
- Score-only result: 5/5 predicted answerable
- Notes: acceptable as a retrieval/no-answer routing signal. Answer-level grounding was not generated in this run.

### `unsupported_abstention`

- Cases: 6
- Score-only result: 6 false answers
- Domain-gate diagnostic: 4 false answers remain
- Remaining problematic queries:
  - `fio-v0-006`: broad IFRS 9 overview including hedge accounting and classification.
  - `fio-v0-009`: full EBA/Basel consolidated perimeter.
  - `fio-v0-010`: CRR II vs CRR III article-by-article.
  - `fio-v0-016`: 2026 ranking of Italian banks by total assets.

### `out_of_scope_refusal`

- Cases: 5
- Score-only result: 5 false answers
- Domain-gate diagnostic: 0 false answers
- Notes: domain gate diagnostic catches the clear OOD cases, but this does not change runtime ownership.

### `bank_specific_missing_source`

- Represented by `fio-v0-008`.
- Score-only result: false answer.
- Domain-gate diagnostic: abstention was correct.

### `regulatory_comparison`

- Represented indirectly by broad/unsupported comparison cases.
- Article-by-article or full-perimeter comparisons remain no-go unless retrieved sources support both sides.

## Rubric Notes

Because this run used non-generation benchmark mode, answer text was not scored for full citation fidelity or Italian style. Routing-level findings are still sufficient for a no-go decision:

- Grounding risk: high for unsupported slices under score-only.
- Refusal correctness: weak under score-only.
- Unsupported abstention: weak; still imperfect under diagnostic domain gate.
- Citation fidelity: not evaluated at answer-text level.
- Italian regulatory style: not evaluated at answer-text level.

## Go / No-Go

Decision: **No-go for Fiorell.IA controlled beta validation as-is**.

Reason:

- Score-only shared runtime produces 11 false answers on the Fiorell.IA eval set.
- Unsupported abstention remains weak.
- Domain-gate diagnostic improves results but still leaves 4 false answers on near-domain unsupported questions.
- No prompt-only candidate was wired into runtime, by design; prompt-only behavior still needs manual answer-level review.

No runtime changes are part of this decision.

## Next Steps

- Add or review prompt-only answer-level samples for the four remaining unsupported-abstention failures.
- Strengthen Fiorell.IA refusal examples around broad IFRS 9, full EBA/Basel, CRR II/III article-by-article, and current bank rankings.
- Re-run this checklist after prompt-only review and dataset-v1 preparation.
