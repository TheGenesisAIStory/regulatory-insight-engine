# Fiorell.IA Go / No-Go v1

This decision applies only to the Fiorell.IA beta product/spec layer. No runtime changes are part of this decision.

## Go Criteria

Proceed to controlled beta validation only if:

- false answers do not increase versus the shared baseline;
- out-of-scope refusals are clear, short and non-speculative;
- unsupported questions abstain or narrow correctly;
- factual answers cite retrieved local sources;
- citations are not invented or misleading;
- answers stay within retrieved evidence;
- Italian wording is concise, technical and supervisory;
- scope wording remains narrow: strongest on default, internal controls, own funds and prudential supervision.

## No-Go Criteria

Reject the candidate if it:

- increases false answers;
- invents citations, page references, articles or bank disclosures;
- weakens abstention for unsupported or near-domain questions;
- becomes broader than the retrieved evidence;
- answers bank-specific questions without the relevant local source;
- claims full IFRS 9, full Pillar 3, full EBA/Basel or complete banking-regulatory coverage;
- requires runtime, serving, retrieval, indexing or domain gate changes to pass.

## Decision Record

Record the final decision in `fiorellia/training/experiments_manifest.jsonl` or a future release validation note, including the compared stage, report path and reason.
