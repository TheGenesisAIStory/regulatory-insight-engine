# Next Operator Actions

1. Create the local training environment.
2. Install PyTorch using the official PyTorch selector.
3. Install LoRA requirements from `fiorellia/training/requirements-lora.txt`.
4. Run `python fiorellia/training/preflight_check_training.py`.
5. Train the adapter with `fiorellia/training/configs/config_lora_behavior_20260421.yaml`.
6. Compare baseline vs adapted outputs with `fiorellia/eval/compare_baseline_vs_adapter_20260421.md`.
7. Update `fiorellia/training/experiments/fiorellia_runs.jsonl`.
8. Only then decide on GitHub release, LinkedIn post, or public demo.
