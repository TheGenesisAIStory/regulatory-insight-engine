# Fiorell.IA LoRA Model Card

## Model

- Base model: `Qwen/Qwen2.5-3B-Instruct`
- Previous adapter candidate: `fiorellia_behavior_20260421`
- Recovery candidate to train: `fiorellia_behavior_RC_HARDENED_20260526`
- Active recovery dataset: `fiorellia/training/supervised_v2_behavior_hardening_20260526.jsonl`
- Artifact store: Google Drive, `fiorellia-runs/final_delivery_latest/`

## Intended Use

Fiorell.IA is a narrow experimental assistant for Italian banking-regulatory question answering. It is intended to answer only when local retrieved sources support the response, and to abstain or refuse when sources are missing, scope is unsupported, or the user asks for advice outside the regulatory-document perimeter.

## Verified Status

- OK: previous final Colab run produced real artifacts and a real `NO-GO` verdict.
- OK: behavior-hardening dataset, strict prompt and hardened eval set are versioned.
- OK: app safe-fallback path is tested on the required abstention/refusal cases.
- DA VERIFICARE: recovery adapter `fiorellia_behavior_RC_HARDENED_20260526` must be trained on Colab A100.
- DA VERIFICARE: recovery baseline-vs-adapter evaluation must be rerun with real adapter outputs.

## Evaluation Requirements

Run the final evaluation from Colab A100:

```bash
python fiorellia/eval/colab_drive_final_eval.py
```

Required metrics:

- `in_scope_grounded >= 0.80`
- `unsupported_abstention >= 0.90`
- `out_of_scope_refusal >= 0.95`
- `italian_style >= 0.95`

Priority unsupported cases must not produce severe false answers.

## Limitations

- Not production-ready.
- Not legal, accounting, tax, trading, investment, or supervisory advice.
- Does not claim full IFRS 9, Pillar 3, EBA, Basel, CRR II/III, or current-market-data coverage.
- Local macOS CPU is not a practical runtime for Qwen2.5-3B+LoRA generation; Colab A100 is the required evaluation runtime.

## Current Operational Verdict

**NO-GO**

Reason: the last real Colab certification produced metrics below release thresholds. The recovery candidate is prepared but not yet trained/evaluated.
