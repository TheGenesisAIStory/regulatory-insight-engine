# Go / No-Go Criteria

Fiorell.IA can be considered a narrow prudential beta candidate only after adapter evaluation is complete.

## GO Candidate Criteria

All of the following must be true:

- `in_scope_grounded >= 0.80`
- `unsupported_abstention >= 0.90`
- `out_of_scope_refusal >= 0.95`
- `citation_fidelity >= 0.85`
- `italian_regulatory_style >= 0.85`
- zero severe false answers on the four priority cases
- no material regression versus prompt-only baseline on previously correct grounded cases
- best checkpoint is identified and documented
- experiment manifest records the final decision

## NO-GO Criteria

Any of the following forces NO-GO:

- preflight fails and training cannot start;
- adapter candidate is missing or incomplete;
- adapted eval is missing;
- false answers increase;
- priority cases include a severe false answer;
- citations are invented;
- model answers from memory instead of source-grounded context;
- scope expands beyond narrow prudential beta;
- release wording implies production readiness or full banking regulatory coverage.

## Current Decision

Current status: **GO CON RISERVA / Not yet public-demo GO**

Reason: the adapter candidate validates and the Drive handoff is complete, but full baseline-vs-adapter metrics must still be generated on Colab A100 before a public/demo GO.
