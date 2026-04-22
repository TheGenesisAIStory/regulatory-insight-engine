# Build Supervised v1 From Logs

This script converts Fiorell.IA prompt-harness logs into a reviewable supervised dataset draft for behavior tuning.

It only extracts records in these categories:

- `unsupported_abstention`
- `out_of_scope_refusal`

The script does not generate ideal answers. It writes `TODO_CURATED_IDEAL_ANSWER` so a human reviewer can curate the desired refusal or abstention response before training.

## Example

```bash
python3 fiorellia/training/build_supervised_v1_from_logs.py \
  --in fiorellia/eval/prompt_harness_logs.jsonl \
  --out fiorellia/training/supervised_v1_from_logs_draft.jsonl
```

## Workflow

1. Run `fiorellia/eval/prompt_harness.py` on `eval_set_v0.jsonl`.
2. Build a supervised draft with this script.
3. Manually replace every `TODO_CURATED_IDEAL_ANSWER`.
4. Keep only high-quality examples with clear refusal or abstention behavior.
5. Train the LoRA behavior adapter with the curated JSONL.

This workflow improves model behavior without changing retrieval, serving, indexing, domain gate logic, or the shared backend runtime.
