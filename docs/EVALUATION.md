# Evaluation Runbook

Purpose
- Describe how to run reproduction-grade evaluations, interpret metrics, and calibrate thresholds without changing runtime code.

Key scripts
- `backend/eval/run_benchmark.py` — runs single benchmark over a dataset (JSONL) and writes JSON/MD report.
- `backend/eval/compare_modes.py` — compares modes (score-only, score+domain_gate, retrieval-optimized).
- `backend/eval/tune_retrieval.py` — orchestrates parameter sweeps (top_k, threshold, optional min_score_gap).

Typical workflow
1. Validate dataset:
```bash
python3 backend/eval/validate_supervised_dataset.py --input backend/eval/supervised_seed.jsonl --output backend/eval/supervised_seed.cleaned.jsonl
```
2. Run baseline benchmark:
```bash
python3 backend/eval/run_benchmark.py --dataset backend/eval/dataset.jsonl --out backend/eval/reports/baseline.json
```
3. Compare modes (fast, safe):
```bash
python3 backend/eval/compare_modes.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/compare_modes --top-k 6 --threshold 0.12
```
4. Tune retrieval thresholds (cheap):
```bash
python3 backend/eval/tune_retrieval.py --dataset backend/eval/dataset.jsonl --outdir backend/eval/reports/tune_retrieval_default --top-ks 4,6 --thresholds 0.10,0.12 --min-score-gaps 0.02,0.05
```

Metrics (what they mean)
- `sourceHitRate`: fraction of queries where at least one retrieved chunk maps to an expected source.
- `inDomainCoverage`: fraction of queries labeled in-domain that had any retrieved evidence.
- `noAnswerAccuracy`: fraction where the system abstained correctly on ground-truth no-answer cases.
- `falseAnswerCount`: count of cases answered incorrectly (hallucinations or incorrect grounding).
- `falseNoAnswerCount`: count of cases where system abstained but ground-truth expected an answer.
- `avgLatencyMs`: average end-to-end latency (useful for perf trade-offs).

Calibration strategy
- Start with `score_plus_domain_gate` (recommended) and baseline threshold `0.12`.
- Sweep `min_score_gap` (0.02–0.10) and `threshold` (0.08–0.20) to find knee where `noAnswerAccuracy` rises without large increases in `falseNoAnswerCount`.
- Only after gating + threshold tuning, consider chunking parameter sweep (`--vary-chunk`) — expensive because embeddings must be recomputed.

Output artifacts
- Per-run JSON and Markdown reports are written under the `--outdir` path. `tuning_summary.json` aggregates run summaries.

Interpreting results
- Prefer configurations with high `noAnswerAccuracy` and low `falseAnswerCount` while maintaining `inDomainCoverage` > 0.9.
- If `sourceHitRate` is 1.0 but `noAnswerAccuracy` is low, you likely have hallucination downstream — domain gate or answering logic should be adjusted.

Notes
- Keep evaluation offline and isolated from production caches by using separate `CACHE_PATH` when necessary.
