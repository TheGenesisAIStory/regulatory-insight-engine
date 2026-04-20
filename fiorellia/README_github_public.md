# Fiorell.IA v0.1.0-beta

Fiorell.IA is an Italian-first product layer for a local banking-regulatory RAG assistant.

It is designed for source-grounded answers and explicit refusals when local retrieved sources are insufficient.

## What It Covers Best Today

- Prudential supervision
- Internal controls
- Own funds and capital terminology
- Selected default / credit-risk regulatory context

## What It Does Not Claim

- Complete banking-regulatory coverage
- Full IFRS 9 coverage
- Full Pillar 3 coverage
- Full EBA/Basel consolidated perimeter
- Current rankings or market data
- Production-ready advice

## Evaluation Snapshot

| Run | Cases | No-answer accuracy | False answers | False no-answers |
|---|---:|---:|---:|---:|
| Shared baseline score-only | 32 | 15.6% | 27 | 0 |
| Shared domain gate diagnostic | 32 | 93.8% | 2 | 0 |
| Fiorell.IA score-only | 16 | 31.2% | 11 | 0 |
| Fiorell.IA domain-gate diagnostic | 16 | 75.0% | 4 | 0 |

## Current Status

Fiorell.IA is a narrow beta product/spec package. The recent evaluation is no-go as-is for controlled beta validation because four unsupported-abstention cases remain problematic:

- broad IFRS 9 overview;
- full EBA/Basel perimeter;
- CRR II vs CRR III article-by-article;
- 2026 Italian bank ranking by total assets.

## Runtime Boundary

Fiorell.IA does not modify backend, serving, retrieval, indexing, domain gate or runtime behavior. It defines product behavior, prompts, eval assets and release packaging only.
