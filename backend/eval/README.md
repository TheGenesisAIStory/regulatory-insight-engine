# RAG Evaluation

Local, repeatable benchmark for the current Gen.Is.IA RAG baseline.

This layer does not rebuild ingestion, embeddings, retrieval, API or frontend. It imports the existing `genisia_rag_engine` and measures the behavior of the current pipeline.

## Dataset

The versioned dataset is:

```text
backend/eval/dataset.jsonl
```

The domain-focused benchmark for CRR, IFRS 9, Banca d'Italia and Italian-bank disclosure boundaries is:

```text
backend/eval/domain_dataset.jsonl
```

The Fiorell.IA supervised seed also has a benchmark view derived from the training seed:

```text
backend/eval/fiorellia_supervised_seed_eval.jsonl
```

Regenerate it from the chat-style supervised file with:

```bash
python3 backend/eval/build_fiorellia_seed_eval.py
```

Each JSONL row can include:

- `id`
- `category`
- `query`
- `expected_sources`
- `expected_no_answer`
- `reference_answer`

## Run

Fast deterministic retrieval/no-answer benchmark:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py
```

Domain benchmark:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py \
  --dataset eval/domain_dataset.jsonl \
  --out eval/reports/domain_latest.json \
  --markdown eval/reports/domain_latest.md
```

Fiorell.IA seed benchmark:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py \
  --dataset eval/fiorellia_supervised_seed_eval.jsonl \
  --out eval/reports/fiorellia_seed_latest.json \
  --markdown eval/reports/fiorellia_seed_latest.md
```

Full local benchmark with LLM generation and groundedness heuristic:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py --generate
```

Custom output:

```bash
python eval/run_benchmark.py \
  --dataset eval/dataset.jsonl \
  --out eval/reports/run.json \
  --markdown eval/reports/run.md \
  --top-k 6
```

## Threshold Calibration

Compare multiple no-answer thresholds in one run:

```bash
python eval/run_benchmark.py \
  --calibrate-thresholds 0.12,0.18,0.22,0.25,0.30
```

The report includes a comparison table with:

- source hit rate;
- in-domain coverage;
- no-answer accuracy;
- false answers;
- false no-answers;
- average latency.

Optional stronger abstention gate for out-of-domain regulatory questions:

```bash
python eval/run_benchmark.py \
  --calibrate-thresholds 0.12,0.18,0.22,0.25,0.30 \
  --domain-gate
```

The domain gate is intentionally simple and local: it allows terms covered by the current corpus (IFRS 9, CRR, Basel, Banca d'Italia) and abstains on known non-indexed regulatory domains such as MiFID II, GDPR, PSD2, SFDR and AML.

Optional score-gap abstention:

```bash
python eval/run_benchmark.py \
  --calibrate-thresholds 0.12,0.18,0.22,0.25,0.30 \
  --min-score-gap 0.03
```

## Reports

Reports are written to:

```text
backend/eval/reports/latest.json
backend/eval/reports/latest.md
```

Reports include aggregate metrics, failed cases, false answers, false no-answers and missing expected sources.

For the domain dataset, the JSON and Markdown reports also include metrics and failure cases grouped by category:

- `crr`
- `ifrs9`
- `banca_italia`
- `bank_specific`
- `near_domain_ood`
- `no_answer`

For the Fiorell.IA seed benchmark, category metrics are grouped as:

- `fiorellia_grounded_answer`
- `fiorellia_insufficient_context`
- `fiorellia_out_of_scope`
- `fiorellia_refusal_safe`

The script exits with a non-zero status when failed cases are present. This is intentional for regression testing and CI-style checks.

## Metrics

- `sourceHitRate`: expected source/document appears in retrieved top-k.
- `noAnswerAccuracy`: predicted no-answer matches `expected_no_answer`.
- `schemaValidityRate`: generated response has the expected response contract. Only meaningful with `--generate`.
- `avgLatencyMs` and `p50LatencyMs`: per-case benchmark latency.
- `avgGroundedness`: simple token-overlap heuristic between answer and retrieved chunks. Only computed with `--generate`.

## Regression Testing

Use this benchmark before and after changing chunking, embeddings, prompt, score threshold or retriever logic.

Recommended workflow:

```bash
python eval/run_benchmark.py
git diff -- backend/eval/reports/latest.md
```

For slower answer-level checks:

```bash
python eval/run_benchmark.py --generate
```

Treat drops in source hit rate, no-answer accuracy or groundedness as regression signals to inspect manually.

For domain regression testing, run:

```bash
python eval/run_benchmark.py \
  --dataset eval/domain_dataset.jsonl \
  --out eval/reports/domain_latest.json \
  --markdown eval/reports/domain_latest.md
```

Use the category table to spot whether a change improves CRR/IFRS 9 retrieval while accidentally weakening near-domain abstention.
