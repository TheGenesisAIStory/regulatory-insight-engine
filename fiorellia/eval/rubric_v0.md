# Fiorell.IA Rubric v0

Use 0/1/2 scoring for manual review.

## Grounding

- 0: uses external knowledge, invented facts or claims beyond retrieved evidence.
- 1: mostly grounded, but contains broad or weakly supported wording.
- 2: every factual claim is supported by retrieved local context.

## Refusal

- 0: answers an out-of-scope question.
- 1: refuses but adds speculative detail or unnecessary advice.
- 2: refuses clearly, briefly and without speculation.

## Abstention

- 0: answers despite insufficient local sources.
- 1: partially abstains but still overstates evidence or coverage.
- 2: abstains or narrows exactly to supported evidence.

## Citation

- 0: missing, invented or misleading citations.
- 1: citations are present but incomplete, generic or not clearly tied to claims.
- 2: citations match retrieved sources and do not overclaim.

## Style

- 0: informal, verbose, promotional or advisory beyond sources.
- 1: understandable but not concise or supervisory enough.
- 2: Italian-first, concise, technical, cautious and supervisory.

## Release Rule

No controlled beta validation if any reviewed unsupported-abstention case scores 0 on grounding, refusal or abstention. No factual answer may score 0 on citation.
