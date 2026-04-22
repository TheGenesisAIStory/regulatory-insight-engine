# Current Release Blockers

Fiorell.IA is not ready for a public GitHub / LinkedIn / public demo release yet.

## Blockers

- Adapter not trained yet.
- No baseline-vs-adapted comparison exists yet.
- No validated beta release evidence exists for the LoRA candidate.
- A dedicated `.venv-fiorellia-lora` environment now passes preflight.
- The first Qwen2.5-3B training attempt did not complete: model download remained in `Fetching 2 files`, reached only about `223 MB` of Hugging Face cache, and was stopped before training.
- Current host is macOS Intel x86_64 with 16 GB RAM and no CUDA; 4-bit QLoRA via `bitsandbytes` is not practical here.
- No trained adapter exists.

## Conditions To Lift Blockers

These blockers can be lifted only when:

1. the local LoRA training environment passes preflight;
2. `Qwen/Qwen2.5-3B-Instruct` is available locally or download completes reliably;
3. the first behavior adapter is trained successfully;
4. adapted outputs are generated for `eval_set_v0.jsonl`;
5. the four priority unsupported cases are manually reviewed;
6. the full eval set is reviewed for regressions;
7. `fiorellia/training/experiments/fiorellia_runs.jsonl` records the result;
8. the go/no-go decision is explicit and conservative.

Until then, Fiorell.IA remains an internal, evaluation-stage beta candidate.
