# AGENTS.md

## Project rules
- Preserve the current React + FastAPI + Ollama architecture unless a change is strictly necessary.
- Keep the project offline-first; do not add mandatory cloud dependencies.
- Prefer small, reviewable diffs over broad rewrites.
- Reuse existing modules before creating new ones.
- Do not redesign the runtime RAG pipeline unless explicitly requested.

## Quality rules
- Separate config, schemas, services, evaluation, and docs clearly.
- Prefer deterministic checks before adding heuristic or model-based logic.
- When a task is complete, report:
  - files changed
  - commands run
  - tests/validation performed
  - remaining risks or TODOs

## RAG rules
- Responses must be grounded in retrieved local context.
- If the retrieved context is insufficient, the system must abstain clearly.
- Keep evaluation and runtime concerns separated where possible.
