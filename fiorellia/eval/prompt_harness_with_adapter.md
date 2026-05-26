# Prompt Harness With Adapter

This guide describes the supported Fiorell.IA baseline-vs-adapter evaluation path.

## Active Adapter ZIP

Use a clean ZIP that contains the LoRA adapter root files and excludes checkpoint directories:

```text
/content/drive/MyDrive/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip
```

Required members:

```text
adapter_config.json
adapter_model.safetensors
```

## Final Colab Command

Run from `/content/regulatory-insight-engine` on Colab A100:

```bash
python fiorellia/eval/colab_drive_final_eval.py
```

The script:

1. validates the adapter ZIP;
2. executes `fiorellia/eval/prompt_harness.py` in adapter mode;
3. reads the baseline JSONL;
4. scores real adapter outputs;
5. writes JSONL, CSV, metrics, diagnostics, and final verdict to Drive.

## Direct Harness Command

For debugging only:

```bash
python fiorellia/eval/prompt_harness.py \
  --adapter_zip /content/drive/MyDrive/fiorellia-runs/final_delivery_latest/fiorellia_behavior_20260421_clean.zip \
  --eval_set fiorellia/eval/eval_set.jsonl \
  --system_prompt fiorellia/prompts/system_prompt.md \
  --output /content/drive/MyDrive/fiorellia-runs/final_delivery_latest/reports/
```

## Priority Cases

Review these first after the script writes `comparison.csv`:

- `fio-v0-006`: broad IFRS 9 overview;
- `fio-v0-009`: full EBA/Basel perimeter;
- `fio-v0-010`: CRR II vs CRR III article-by-article;
- `fio-v0-016`: 2026 ranking of Italian banks by total assets.

Use `fiorellia/eval/rubric_v0.md` for manual review. The adapter must improve unsupported abstention without weakening grounded answers.
