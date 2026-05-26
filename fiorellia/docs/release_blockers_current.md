# Current Release Status

Fiorell.IA is in a Drive-first recovery release state. The local repository now has a validated LoRA adapter candidate, but public/demo GO still requires a completed Colab A100 baseline-vs-adapter evaluation with real metrics.

## Status

- OK: `.venv-fiorellia-lora` passes the local training preflight.
- OK: `Qwen/Qwen2.5-3B-Instruct` is present in the local Hugging Face cache.
- OK: local adapter directory `fiorellia/training/lora/fiorellia_behavior_20260421/` contains `adapter_config.json` and `adapter_model.safetensors`.
- OK: a clean adapter ZIP can be produced without checkpoints or local binary spillover.
- OK: app smoke tests run through the safe fallback path and verify abstention/error handling.
- DA VERIFICARE: full adapter generation and eval must run on Google Colab A100.
- DA VERIFICARE: `metrics_summary.json`, `comparison.csv`, `adapter_eval_scored.jsonl`, and `final_verdict.md` must be produced from real adapter outputs.
- BLOCCANTE LOCALE: macOS Intel CPU can load Qwen2.5-3B+LoRA but does not complete even a 1-token generation probe in practical time.

## Active Closure Path

Run the final eval on Colab A100 from the repository root:

```bash
python fiorellia/eval/colab_drive_final_eval.py
```

Expected Drive artifact root:

```text
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/
```

Public release language remains conservative until the Colab A100 eval produces a real GO:

- narrow prudential beta;
- Italian-first;
- source-grounded;
- refusal-first;
- internal/evaluation-stage until metrics pass.
