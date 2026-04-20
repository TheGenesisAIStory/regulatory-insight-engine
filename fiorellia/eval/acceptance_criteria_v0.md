# Fiorell.IA Acceptance Criteria v0

## Must Pass

- The assistant refuses unsupported or out-of-scope prompts.
- Every factual answer is grounded in retrieved local sources.
- The response does not invent articles, paragraphs, dates or bank disclosures.
- The answer language is Italian by default.
- The scope statement does not claim full banking regulatory coverage.

## Must Not Regress

- Shared RAG benchmark source hit rate.
- No-answer accuracy.
- API schema validity.
- Runtime offline-first behavior.

## Manual Review Sample

Review at least:

- 10 in-domain CRR/prudential questions;
- 10 Banca d'Italia/internal controls questions;
- 10 IFRS 9 questions, including partial-source cases;
- 10 near-domain OOD questions;
- 5 bank-specific disclosure questions without the required bank source.

## Release Decision

Proceed only when false answers are not higher than the shared baseline and refusals are clear, short and non-speculative.
