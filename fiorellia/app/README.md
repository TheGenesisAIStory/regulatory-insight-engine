# Fiorell.IA App Layer

This folder is reserved for Fiorell.IA-specific presentation notes, public copy, screenshots and future app-shell experiments.

The app layer is a product-facing presentation shell. It is not the runtime owner and does not define serving, inference, retrieval, indexing or API behavior.

Current rules:

- do not connect this folder to the production UI or backend without an explicit task and evaluation pass;
- do not duplicate runtime configuration here;
- do not imply production readiness or complete regulatory coverage;
- keep public wording aligned with `../docs/scope_v0.md`.

The current live app remains the shared React + FastAPI + Ollama runtime outside this folder.
