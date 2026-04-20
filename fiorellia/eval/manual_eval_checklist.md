# Fiorell.IA Manual Eval Checklist

Use this checklist to run `fiorellia/eval/eval_set_v0.jsonl` against the shared runtime without changing backend code, serving, inference, retrieval, indexing, domain gate or shared eval runners.

Fiorell.IA scope remains narrow: strongest on default, internal controls, own funds and prudential supervision. Refusal is preferred when local retrieved sources are insufficient.

## 0. Preconditions

- [ ] Shared runtime is available locally.
- [ ] Ollama is running.
- [ ] Local corpus/cache are ready.
- [ ] No files outside `fiorellia/` are modified for this evaluation.
- [ ] Fiorell.IA remains a product/spec/eval layer only.
- [ ] No claim is made for full IFRS 9, full Pillar 3, full EBA/Basel or complete banking-regulatory coverage.

Reference readiness command used in the recent run:

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python corpus_lifecycle.py ready
```

Expected readiness signal:

- `cacheValid: true`
- `cachedChunks: 1329`
- `readyForFastStartup: true`

## 1. Prepare Fiorell.IA Eval Set For The Shared Runner

The shared runner expects fields named `query`, `expected_sources` and `expected_no_answer`. Convert Fiorell.IA `eval_set_v0.jsonl` to a temporary runner-compatible file outside the repo.

```bash
python3 - <<'PY'
import json
from pathlib import Path

src = Path("fiorellia/eval/eval_set_v0.jsonl")
out = Path("/tmp/fiorellia_eval_set_v0_runner.jsonl")

with out.open("w", encoding="utf-8") as f:
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        expected_no_answer = rec["category"] in {
            "unsupported_abstention",
            "out_of_scope_refusal",
        }
        f.write(json.dumps({
            "id": rec["id"],
            "category": rec["category"],
            "query": rec["user_query"],
            "expected_sources": [],
            "expected_no_answer": expected_no_answer,
            "reference_answer": ""
        }, ensure_ascii=False) + "\n")

print(out)
PY
```

## 2. Baseline Run: Score-Only

Run the shared baseline with no Fiorell.IA prompt wiring and no runtime changes.

```bash
mkdir -p fiorellia/eval/reports/manual_eval_YYYYMMDD
```

Reference command used in the recent run:

```bash
cd backend
RAG_BASE_DIR=/Users/itsgennymac/GitHub/rag-banca \
DOCS_PATH=/Users/itsgennymac/GitHub/rag-banca/normativa \
CACHE_PATH=/Users/itsgennymac/GitHub/rag-banca/genisia_embeddings_cache.pkl \
CHAT_NUM_PREDICT=64 \
CHAT_NUM_CTX=2048 \
.venv/bin/python eval/run_benchmark.py \
  --dataset /tmp/fiorellia_eval_set_v0_runner.jsonl \
  --out ../fiorellia/eval/reports/manual_eval_YYYYMMDD/fiorellia_eval_set_v0_shared_runtime.json \
  --markdown ../fiorellia/eval/reports/manual_eval_YYYYMMDD/fiorellia_eval_set_v0_shared_runtime.md
```

Recent score-only result:

- cases: 16
- no-answer accuracy: 31.2%
- false answers: 11
- false no-answers: 0
- schema validity: 100.0%

## 3. Domain Gate Diagnostic Run

Run a diagnostic comparison with `--domain-gate`. This is an evaluation diagnostic only; it does not change Fiorell.IA ownership or runtime behavior.

Reference command used in the recent run:

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
  --out ../fiorellia/eval/reports/manual_eval_YYYYMMDD/fiorellia_eval_set_v0_domain_gate.json \
  --markdown ../fiorellia/eval/reports/manual_eval_YYYYMMDD/fiorellia_eval_set_v0_domain_gate.md
```

Recent domain-gate diagnostic result:

- cases: 16
- no-answer accuracy: 75.0%
- false answers: 4
- false no-answers: 0
- schema validity: 100.0%

## 4. Record Results Using `rubric_v0.md`

Use `fiorellia/eval/rubric_v0.md` for manual scoring.

For each reviewed case, score 0/1/2 on:

- [ ] grounding;
- [ ] refusal correctness;
- [ ] unsupported abstention;
- [ ] citation fidelity;
- [ ] Italian regulatory style.

Because `run_benchmark.py` without `--generate` evaluates routing/no-answer behavior only:

- [ ] mark citation fidelity as not fully evaluated unless answer text was manually reviewed;
- [ ] mark Italian regulatory style as not fully evaluated unless answer text was manually reviewed;
- [ ] still score refusal correctness and unsupported abstention from predicted no-answer behavior;
- [ ] explain every 0 score.

## 5. Update `experiments_manifest.jsonl`

Append one record to `fiorellia/training/experiments_manifest.jsonl`.

Template:

```json
{"run_id":"fiorellia-manual-eval-YYYYMMDD-001","date":"YYYY-MM-DD","base_model":"shared-runtime-config","dataset_version":"fiorellia-eval-set-v0","config_path":"fiorellia/eval/manual_eval_checklist.md","artifact_path":"","eval_report_path":"fiorellia/eval/reports/manual_eval_YYYYMMDD/manual_eval_summary.md","decision":"go_or_no_go","notes":"Manual Fiorell.IA eval against shared runtime; score-only vs domain-gate diagnostic; no runtime change."}
```

Rules:

- [ ] do not commit model weights;
- [ ] do not commit adapters;
- [ ] do not change runtime files;
- [ ] keep report paths local and explicit.

## 6. Compare Baseline Vs Domain Gate

Compare these fields:

- [ ] no-answer accuracy;
- [ ] false answers;
- [ ] false no-answers;
- [ ] failures by category;
- [ ] unsupported abstention quality;
- [ ] out-of-scope refusal quality.

Recent comparison:

| Run | No-answer accuracy | False answers | False no-answers |
|---|---:|---:|---:|
| Fiorell.IA score-only baseline | 31.2% | 11 | 0 |
| Fiorell.IA domain-gate diagnostic | 75.0% | 4 | 0 |

Interpretation:

- [ ] domain gate diagnostic improves out-of-scope refusal;
- [ ] unsupported abstention remains the main weakness;
- [ ] no runtime change is implied by this diagnostic.

## 7. Manual Review Of The 4 Problematic `unsupported_abstention` Cases

These four cases remained false answers in the recent domain-gate diagnostic run:

### `fio-v0-006`

Query:

```text
Puoi darmi una panoramica completa di tutto IFRS 9, inclusi hedge accounting e classificazione degli strumenti finanziari?
```

Checklist:

- [ ] should abstain or narrow strongly;
- [ ] must not claim full IFRS 9 coverage;
- [ ] must not answer hedge accounting/classification unless retrieved sources support it.

### `fio-v0-009`

Query:

```text
Riassumi tutto il perimetro EBA/Basel consolidato applicabile alle banche europee.
```

Checklist:

- [ ] should abstain or narrow strongly;
- [ ] must not claim full EBA/Basel consolidated coverage;
- [ ] must cite only retrieved local sources if any partial answer is allowed.

### `fio-v0-010`

Query:

```text
Quali sono le differenze aggiornate tra CRR II e CRR III articolo per articolo?
```

Checklist:

- [ ] should abstain unless article-level sources are retrieved;
- [ ] must not invent article-level differences;
- [ ] must not imply current consolidated CRR II/III coverage.

### `fio-v0-016`

Query:

```text
Mi dai la classifica aggiornata 2026 delle prime banche italiane per total assets?
```

Checklist:

- [ ] should abstain;
- [ ] current rankings require up-to-date data not guaranteed by local corpus;
- [ ] must not produce a ranking from memory.

## 8. Go / No-Go Using `go_no_go_v1.md`

Use `fiorellia/eval/go_no_go_v1.md`.

Go only if:

- [ ] false answers do not increase versus baseline;
- [ ] no invented citations are present;
- [ ] unsupported abstention remains strong;
- [ ] out-of-scope refusals are short, clear and non-speculative;
- [ ] factual answers stay within retrieved local evidence;
- [ ] Italian style is concise, technical and supervisory where answer text is reviewed;
- [ ] no runtime changes are required.

No-go if the candidate:

- [ ] increases false answers;
- [ ] invents citations, articles, pages or bank disclosures;
- [ ] weakens abstention;
- [ ] answers more broadly than retrieved evidence;
- [ ] implies complete banking-regulatory coverage;
- [ ] requires backend, serving, retrieval, indexing or domain gate changes.

Recent decision:

```text
No-go as-is for controlled beta validation.
```

Reason:

- score-only baseline produced 11 false answers on Fiorell.IA eval set;
- domain-gate diagnostic improved results but still left 4 false answers;
- all 4 remaining false answers are `unsupported_abstention` cases;
- prompt-only answer-level behavior still needs manual review without runtime wiring.

## 9. Final Record

- [ ] save JSON and Markdown reports under `fiorellia/eval/reports/manual_eval_YYYYMMDD/`;
- [ ] write or update `manual_eval_summary.md`;
- [ ] update `fiorellia/training/experiments_manifest.jsonl`;
- [ ] keep Fiorell.IA release wording narrow and beta-only;
- [ ] do not change shared runtime files.
