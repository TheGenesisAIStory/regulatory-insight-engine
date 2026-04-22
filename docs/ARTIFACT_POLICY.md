# Artifact Policy

This policy keeps source files, reproducibility metadata, and local generated artifacts separate. It does not change application behavior.

## Track In Git

Track files that are required to understand, run, or review the project:

- application source code under `src/` and `backend/`,
- public documentation under `README.md`, `backend/README.md`, `docs/`, and `fiorellia/`,
- small evaluation datasets such as `backend/eval/*.jsonl` and `fiorellia/eval/eval_set_v0.jsonl`,
- training and evaluation scripts,
- small configuration files,
- curated prompt, rubric, manifest, and release notes,
- final human-readable evaluation summaries when they are part of release evidence.

## Keep Local Only

Do not commit local runtime, build, cache, or environment artifacts:

- virtual environments: `.venv/`, `.venv*/`, `backend/.venv/`,
- frontend dependencies and builds: `node_modules/`, `dist/`, `dist-ssr/`,
- Python caches: `__pycache__/`, `.pytest_cache/`,
- local env files: `.env`, `*.local`,
- embedding caches and pickle files: `*.pkl`,
- local logs: `logs/`, `*.log`,
- generated training outputs: `training/data/output/`,
- backup lockfile folders: `lockfile-backup-*/`.

## LoRA / PEFT Adapters

Intermediate training checkpoints are local-only and ignored:

```text
fiorellia/training/lora/**/checkpoint-*/
fiorellia/training/lora/**/runs/
fiorellia/training/lora/**/logs/
*.pt
*.bin
```

The current final Fiorell.IA adapter remains tracked for now:

```text
fiorellia/training/lora/fiorellia_behavior_20260421/
```

This preserves the current repository state while avoiding repeated intermediate checkpoint churn. For future adapters, prefer one of these explicit policies before committing:

1. Store small metadata and manifests in Git, and publish adapter weights as GitHub Release assets.
2. Use Git LFS for `*.safetensors` if the repository is expected to version model weights.
3. Keep adapters local-only when they are experimental and not part of a release candidate.

Do not add new model weights without a matching manifest that records:

- base model,
- dataset version,
- training config,
- evaluation summary,
- adapter path or release artifact,
- go/no-go decision.

## Evaluation Reports

Evaluation reports fall into two groups:

- Curated summaries: suitable for Git when they document a release decision.
- Raw repeated run outputs: usually local-only unless needed for audit evidence.

Current tracked Fiorell.IA evaluation reports are retained as beta evidence. Future repeated reports should be generated under ignored report directories or summarized into a smaller markdown release note.

## Cloud Sync Duplicates

This repository may live inside iCloud Drive. Treat duplicate files such as these as suspicious until inspected:

```text
* 2.*
* copy.*
*.icloud
```

Do not delete duplicate source-looking files blindly. Inspect contents first, especially files such as `backend/api 2.py`.

Duplicate files inside `.git/`, such as `.git/index 2`, should only be removed after closing VS Code and ensuring no Git process is active.

## Recommended Review Before Commit

Before committing, inspect:

```bash
git status -sb
git diff --cached --stat
git diff --cached --name-status
git ls-files | grep -E 'checkpoint|\\.safetensors$|training/data/output|lockfile-backup|\\.pkl$'
```

For ignored generated files, verify:

```bash
git check-ignore -v training/data/output/train.jsonl
git check-ignore -v fiorellia/training/lora/example/checkpoint-epoch-1/adapter_model.safetensors
```
