# Append Experiment Template v1

Append experiment records to the active Fiorell.IA manifest only after the run artifacts exist and the evaluation summary is available.

## Baseline Prompt-Only Example

```json
{"run_id":"fiorellia-prompt-baseline-YYYYMMDD","date":"YYYY-MM-DD","base_model":"qwen2.5:3b","dataset_version":"eval_set_v0","config_path":"fiorellia/prompts/system_prompt.txt","adapter_path":"","eval_summary":{"unsupported_abstention_false_answers":4,"out_of_scope_false_answers":0,"notes":"Prompt-only baseline for comparison."},"decision":"baseline_only","notes":"No adapter used; shared runtime unchanged."}
```

## Behavior LoRA v1 Candidate Example

```json
{"run_id":"fiorellia-behavior-lora-v1-YYYYMMDD","date":"YYYY-MM-DD","base_model":"Qwen/Qwen2.5-3B-Instruct","dataset_version":"supervised_v1_unsupported_seed","config_path":"fiorellia/training/configs/config_lora_behavior_v1.yaml","adapter_path":"fiorellia/training/lora/fiorellia_behavior_v1","eval_summary":{"unsupported_abstention_false_answers":null,"out_of_scope_false_answers":null,"improved_problem_cases":[],"regressions":[]},"decision":"pending_manual_eval","notes":"Candidate must reduce unsupported false answers without inventing citations or broadening beyond retrieved evidence."}
```

## Reminder

The manifest record documents an experiment. It does not promote the adapter into the shared runtime.
