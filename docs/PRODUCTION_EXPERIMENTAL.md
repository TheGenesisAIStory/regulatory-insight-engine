# Production vs Experimental

Production-oriented components (stable, governable)
- `backend/api.py` and `backend/genisia_rag_engine.py` — runtime RAG service and answering logic.
- Embeddings cache management and index rebuild: stable process, audited in logs.
- Domain gate (after validation) — recommended to keep enabled in production to reduce hallucinations.

Experimental components (research / fast-moving)
- `training/` — dataset splits, export scripts, and any training experiments are experimental by design.
- `backend/eval/tune_retrieval.py` and chunking sweeps with `--vary-chunk` — expensive and experimental.
- Any custom rerankers or model fine-tuning code — treat as experiments until validated against the evaluation suite.

Limits and known risks
- Hallucinations: even with domain gate, the generator may hallucinate if retrieved context is weak.
- Coverage: corpus gaps cause false negatives; ensure `docs/` contains authoritative sources for the domain.
- Threshold tuning: overly aggressive thresholds increase false no-answers; conservative thresholds increase hallucinations.
- Re-embedding cost: changing chunk parameters requires recomputing embeddings which is time and resource intensive.

No-answer policy (summary)
- Abstain when evidence is insufficient (score < `SCORE_THRESHOLD`), domain gate fails, or `min_score_gap` indicates low confidence.
- This conservative policy prioritizes safety over coverage for regulated use-cases.

Residual risks (must be acknowledged)
- Legal/regulatory risk if model output is used without human review.
- Data leakage if sensitive documents are included in `docs/` by mistake.
- Drift: models and corpus evolve — schedule periodic re-evaluation.
