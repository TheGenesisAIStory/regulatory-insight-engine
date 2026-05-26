# Fiorell.IA LoRA Model Card

## Model

- Base model: `Qwen/Qwen2.5-3B-Instruct`
- Adapter candidate: `fiorellia_behavior_20260421`
- Active artifact ZIP: `fiorellia_behavior_20260421_clean.zip`
- Artifact store: Google Drive, `fiorellia-runs/final_delivery_latest/`

## Intended Use

Fiorell.IA is a narrow experimental assistant for Italian banking-regulatory question answering. It is intended to answer only when local retrieved sources support the response, and to abstain or refuse when sources are missing, scope is unsupported, or the user asks for advice outside the regulatory-document perimeter.

## Verified Status

- OK: adapter directory validates locally with `adapter_config.json` and `adapter_model.safetensors`.
- OK: clean adapter ZIP validates and excludes checkpoints, `.bin` files, and local metadata.
- OK: app safe-fallback path is tested on the required abstention/refusal cases.
- OK: Gradio UI loads locally in safe-fallback mode.
- DA VERIFICARE: full baseline-vs-adapter generation must run on Colab A100.
- DA VERIFICARE: final `metrics_summary.json` and `final_verdict.md` must come from real adapter outputs.

## Evaluation Requirements

Run the final evaluation from Colab A100:

```bash
python fiorellia/eval/colab_drive_final_eval.py
```

Required metrics:

- `in_scope_grounded >= 0.80`
- `unsupported_abstention >= 0.90`
- `out_of_scope_refusal >= 0.95`
- `italian_style >= 0.80`

Priority unsupported cases must not produce severe false answers.

## Limitations

- Not production-ready.
- Not legal, accounting, tax, trading, investment, or supervisory advice.
- Does not claim full IFRS 9, Pillar 3, EBA, Basel, CRR II/III, or current-market-data coverage.
- Local macOS CPU is not a practical runtime for Qwen2.5-3B+LoRA generation; Colab A100 is the required evaluation runtime.

## Current Operational Verdict

**GO CON RISERVA**

Reason: adapter and app packaging are verified locally and saved on Drive, but full adapter evaluation metrics still require Colab A100 execution.
