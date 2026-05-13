# fiorellia_behavior_20260513

**FiorellIA LoRA Behavior Adapter — Run 20260513**

## Overview

This is the first successful LoRA adapter for FiorellIA, a behavior-alignment model for Italian banking regulatory queries.

| Parameter | Value |
|-----------|-------|
| Run ID | `fiorellia_behavior_20260513` |
| Date | 2026-05-13 |
| Base model | `Qwen/Qwen2.5-0.5B-Instruct` |
| Method | QLoRA (PEFT) |
| LoRA r | 16 |
| LoRA alpha | 32 |
| Target modules | `q_proj`, `v_proj` |
| Epochs | 3 |
| Final loss | 3.7390 |
| Split | Walk-forward (9 train / 2 val) |
| Precision | bf16=True, fp16=False |
| Stage | `first_successful_training` |

## Training Setup

- Trained in Google Colab (T4 GPU) using QLoRA/PEFT
- Dataset: `supervised_v1_curated_20260421.jsonl` (11 samples)
- Config: `fiorellia/training/configs/config_lora_behavior_20260513.yaml`
- Notebook: `fiorellia_definitive_v1`

## Behavior Targets

| Metric | Target |
|--------|--------|
| `unsupported_abstention` | >= 0.90 |
| `out_of_scope_refusal` | >= 0.95 |
| `in_scope_grounded` | >= 0.80 |

## Artifacts

- `adapter_config.json` — PEFT adapter configuration
- `adapter_model.safetensors` — trained adapter weights (stored locally in Colab/Drive, not tracked in git)

## Notes

- Inference eval pending: load adapter + base model and run against `eval_set_v0.jsonl`
- Weights are not committed to git due to file size (use Drive or HuggingFace Hub for weights)
