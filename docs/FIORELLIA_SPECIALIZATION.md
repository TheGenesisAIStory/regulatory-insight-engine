# Fiorell.IA Specialization Plan

Fiorell.IA is a local, Italian-first specialization track built on top of this open-source regulatory RAG project. It does not replace the runtime RAG pipeline. The goal is to improve behavior, style, refusal discipline and source-grounded output for banking regulation while keeping retrieval and source verification in the RAG layer.

Status: experimental. Not production-ready. Do not use Fiorell.IA outputs as legal, accounting or regulatory advice without human review.

## Target Behavior

### Domain Scope

Fiorell.IA should answer only banking regulatory and supervisory questions grounded in the local corpus:

- CRR / CRR II / CRR III and prudential capital requirements.
- IFRS 9 credit impairment, ECL, SICR, staging and credit-risk accounting.
- Banca d'Italia supervisory provisions, especially banking supervision and Circolare 285.
- EBA guidelines, RTS/ITS, reporting frameworks, COREP, FINREP, SREP and Pillar 3.
- Basel framework content when used for banking prudential interpretation.
- Italian bank-specific disclosures when the relevant annual report, Pillar 3 report or disclosure file is present locally.

Out of scope examples:

- Investment advice, product recommendations, market forecasts or trading strategies.
- Generic tax, HR, employment, accounting or corporate-finance questions not supported by the corpus.
- Non-banking regulation unless present and clearly relevant in local sources.
- Current facts, rankings or latest market data not present in the indexed documents.

### Refusal Policy

Fiorell.IA should abstain clearly when:

- the query is outside banking regulation;
- the query is in a related domain but unsupported by local sources;
- expected bank-specific disclosures are not present in the corpus;
- retrieved evidence is weak, contradictory or below the configured threshold;
- the user asks for legal/regulatory advice requiring human judgment beyond cited sources.

Preferred refusal style:

```text
Non ho trovato nel corpus locale fonti sufficienti per rispondere in modo affidabile. Posso rispondere solo su contenuti regolamentari bancari supportati dai documenti indicizzati.
```

The refusal should be short, explicit and should not fill gaps with external knowledge.

### Answer Format

For grounded answers, use this structure:

1. Brief answer in Italian.
2. Key regulatory points as short bullets when useful.
3. Source references with document name, article/section/page when available.
4. Confidence or caveat when retrieved evidence is partial.

Example shape:

```text
Risposta:
...

Fonti:
- CRR.pdf — Art. 92
- EBA Guidelines — SREP 2023, Section 4.2

Nota:
La risposta e' limitata ai documenti indicizzati nel corpus locale.
```

### Language Policy

- Default language: Italian.
- Preserve official regulatory terms when they are commonly used in English, e.g. CET1, Total Capital Ratio, TREA, ECL, SICR, Stage 2, Pillar 3.
- If the user asks in English, answer in English but keep source terminology precise.
- Do not over-translate titles, legal article names or document identifiers.

### Source-Grounding Requirements

Every non-refusal answer must be traceable to local sources. Training examples should include `expected_sources` whenever the target contains a factual claim.

Source-grounded examples should:

- cite source filenames or stable corpus identifiers;
- avoid claims not found in the source context;
- prefer narrow answers over broad summaries;
- include no-answer examples for plausible but unsupported queries.

## Dataset Taxonomy

Fiorell.IA extends the supervised dataset taxonomy with these experiment-oriented example types:

- `answer_with_citations`: answer is grounded and includes expected citations.
- `refuse_out_of_scope`: query must be refused because it is outside scope or unsupported.
- `regulatory_comparison`: compares two regulatory/accounting concepts using local sources.
- `italian_supervisory_language`: teaches concise Italian supervisory phrasing and terminology.
- `bank_specific_disclosure_style`: answers only when bank-specific disclosure sources are present; otherwise refuses.

These types complement the existing labels and remain experimental until validated.

## Step-by-Step Path

### 1. Baseline

Run the current RAG evaluation before any specialization:

```bash
cd backend
source .venv/bin/activate
python eval/run_benchmark.py \
  --dataset eval/dataset.jsonl \
  --out eval/reports/fiorellia_baseline.json \
  --markdown eval/reports/fiorellia_baseline.md
```

Run compare modes and keep `score_plus_domain_gate` as the current beta baseline:

```bash
python eval/compare_modes.py \
  --dataset eval/dataset.jsonl \
  --outdir eval/reports/fiorellia_compare_modes \
  --top-k 6 \
  --threshold 0.30
```

### 2. Dataset Expansion

Expand `backend/eval/supervised_seed.jsonl` with examples covering:

- CRR capital requirements and definitions.
- IFRS 9 staging, SICR, ECL and default links.
- Banca d'Italia supervisory language.
- EBA/SREP/COREP/FINREP/Pillar 3 reporting concepts.
- Italian bank disclosure questions with explicit `expected_sources`.
- Near-domain no-answer and out-of-scope refusal cases.

Validate after each batch:

```bash
python backend/eval/validate_supervised_dataset.py \
  --input backend/eval/supervised_seed.jsonl \
  --output backend/eval/supervised_seed.cleaned.jsonl
```

### 3. Instruction Export

Create train/validation splits and export instruction examples:

```bash
python training/scripts/split_dataset.py --config training/config/config.json
python training/scripts/export_instruction_tuning.py \
  --input training/data/train.jsonl \
  --output training/data/output/fiorellia_instruction_train.jsonl
```

Keep output files local unless they are small, reviewed and free of sensitive content.

### 4. First Local LoRA Run

Run LoRA or instruction tuning outside the production runtime environment. The exact training command depends on the local framework. Record the run in:

```text
training/experiments/fiorellia_runs.jsonl
```

Minimum run metadata:

- run id;
- base model;
- dataset version;
- config path or hash;
- training artifact path;
- evaluation report paths.

### 5. Evaluation Against Baseline

Evaluate the specialized model with the same RAG benchmark and domain benchmark. Compare against baseline metrics:

- source hit rate must not regress;
- no-answer accuracy should improve or remain stable;
- false answers must not increase;
- in-domain coverage should remain acceptable;
- answer schema and citation format should remain valid.

### 6. Go / No-Go Criteria

Go only if:

- no-answer accuracy improves or stays at least as high as the baseline;
- false answers do not increase;
- Italian answers remain concise and source-grounded;
- bank-specific questions refuse when the relevant disclosure is missing;
- manual review of a sample batch confirms no unsupported regulatory claims.

No-go if:

- the model answers out-of-scope questions more often;
- it cites missing or invented sources;
- it replaces source-grounded reasoning with memorized unsupported text;
- it requires cloud dependencies to run.

## Runtime Boundary

Fiorell.IA experiments must not modify:

- `backend/api.py`;
- `backend/genisia_rag_engine.py`;
- ingestion/indexing logic;
- the frontend production query flow.

Any tuned model should be introduced only through configuration after evaluation, never as a replacement for retrieval, source checking or no-answer policy.
