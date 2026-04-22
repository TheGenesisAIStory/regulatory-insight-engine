# Train LoRA Behavior v1

This script trains a small Fiorell.IA behavior adapter for refusal and unsupported-source abstention.

It changes model behavior only through an optional LoRA adapter. It does not modify retrieval, serving, indexing, domain gate logic, or the shared backend runtime.

## Prerequisites

- Local Python environment with GPU support recommended.
- Local or cached access to `Qwen/Qwen2.5-3B-Instruct`.
- Curated JSONL dataset at `fiorellia/training/supervised_v1_unsupported_seed.jsonl`.

## Install Requirements

Use your local environment manager. The training script expects:

```bash
pip install transformers peft datasets pyyaml accelerate
```

For QLoRA on supported CUDA systems:

```bash
pip install bitsandbytes
```

## Example Command

```bash
python3 fiorellia/training/train_lora_behavior_v1.py \
  --config fiorellia/training/configs/config_lora_behavior_v1.yaml
```

## Expected Output

The adapter is saved to:

```text
fiorellia/training/lora/fiorellia_behavior_v1/
```

Expected files include adapter weights, adapter config, tokenizer files, and trainer checkpoint metadata depending on the local training setup.

## Notes

This is an experimental behavior-tuning path. It is intended to reduce false answers on `unsupported_abstention` and `out_of_scope_refusal` cases. It is not a replacement for RAG, local source retrieval, or citation-grounded answering.
