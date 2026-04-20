# Architecture Boundary

Fiorell.IA should be developed as a separate product layer over the shared local RAG runtime.

## Current Repository Mapping

```text
backend/          shared runtime RAG: indexing, retrieval, serving, API, generation
backend/eval/     shared evaluation runner and datasets
docs/             current local corpus structure and runbooks
training/         shared optional training preparation utilities
fiorellia/        Fiorell.IA identity, scope, prompts, eval plans, releases and app notes
```

## Target Conceptual Mapping

```text
core/             retrieval, indexing, serving and runtime
corpora/          versioned corpora and manifests
fiorellia/        product definition and specialization layer
shared/           shared schemas/assets/utilities
```

Do not move the working runtime into this layout during the beta hardening phase. Use this document as a planning boundary only.

## Ownership Rules

Fiorell.IA owns:

- assistant identity and public positioning;
- behavior specification;
- prompt specifications;
- specialized eval datasets and acceptance criteria;
- training experiment manifests;
- release notes and limitations;
- branding and presentation guidance.

Fiorell.IA does not own:

- `backend/api.py`;
- live serving path;
- retrieval/indexing pipeline;
- production answer-generation implementation;
- shared corpus downloader/runtime lifecycle.
- thresholds, domain gate modes, retrieval parameters or model-serving settings.

## Change Policy

Allowed in Fiorell.IA layer:

- add docs, configs, prompt specs and eval plans;
- add product-specific release notes;
- add experiment manifests;
- add app notes or mock presentation files.

Not allowed without explicit approval:

- modifying runtime serving behavior;
- changing generation path;
- replacing RAG with fine-tuning;
- silently changing thresholds or domain gate behavior;
- introducing cloud-only dependencies.

Runtime recommendations belong in the shared backend documentation and evaluation reports. Fiorell.IA may state behavioral expectations, but it must not become the source of truth for runtime parameters.
