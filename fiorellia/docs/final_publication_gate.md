# Final Publication Gate

This gate must be completed before GitHub release, LinkedIn announcement, or public demo.

## Required Artifacts

- [ ] Passing `fiorellia/training/preflight_check_training.py`
- [ ] Trained adapter under `fiorellia/training/lora/`
- [ ] Adapted eval JSONL output
- [ ] Completed priority-case review
- [ ] Completed full eval review
- [ ] Best checkpoint selected
- [ ] `fiorellia/training/experiments/fiorellia_runs.jsonl` updated
- [ ] `fiorellia/eval/final_beta_candidate_report.md` updated with GO decision

## Publication Language Constraints

Allowed:

- narrow prudential beta
- Italian-first
- source-grounded
- refusal-first
- local/offline-first evaluation track

Not allowed:

- production-ready
- full banking regulatory coverage
- complete IFRS 9 / Pillar 3 / EBA / Basel coverage
- autonomous legal, accounting, tax, trading, or investment advice

## Current Gate Result

Result: **BLOCKED / NO-GO FOR PUBLICATION**

Reason: no trained adapter and no adapted evaluation evidence. Preflight now passes in `.venv-fiorellia-lora`, but Qwen2.5-3B training did not complete on this host.
