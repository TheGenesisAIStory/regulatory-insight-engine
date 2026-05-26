# Final Publication Gate

This gate must be completed before a public GitHub/LinkedIn/demo claim that Fiorell.IA has passed adapter evaluation.

## Required Artifacts

- [x] Passing `fiorellia/training/preflight_check_training.py` in `.venv-fiorellia-lora`.
- [x] Validated adapter directory under `fiorellia/training/lora/fiorellia_behavior_20260421/`.
- [x] Clean adapter ZIP generated without checkpoints or `.bin` files.
- [x] App smoke test executed on the required abstention/refusal cases.
- [ ] Adapted eval JSONL output from Colab A100.
- [ ] `comparison.csv` baseline-vs-adapter output.
- [ ] `metrics_summary.json` with real float metrics.
- [ ] `final_verdict.md` from real adapter outputs.
- [ ] Completed priority-case review.
- [ ] Full eval review for regressions.

## Publication Language Constraints

Allowed:

- narrow prudential beta;
- Italian-first;
- source-grounded;
- refusal-first;
- local/Colab/Drive-first evaluation track.

Not allowed:

- production-ready;
- full banking regulatory coverage;
- complete IFRS 9 / Pillar 3 / EBA / Basel coverage;
- autonomous legal, accounting, tax, trading, or investment advice.

## Current Gate Result

Result: **GO CON RISERVA FOR INTERNAL DRIVE HANDOFF**

Reason: the adapter exists and validates, the app fallback path is tested, and the final Colab/Drive evaluation script is versioned. The remaining reserve is real: full baseline-vs-adapter metrics must be produced on Colab A100 because local CPU inference is not a practical runtime for Qwen2.5-3B+LoRA.

Public/demo GO remains pending until `fiorellia/eval/colab_drive_final_eval.py` writes real final outputs to Drive.
