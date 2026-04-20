Fiorell.IA v0.1.0-beta is ready as a narrow, honest beta product layer.

It is an Italian-first banking-regulatory assistant concept built on a local/offline RAG stack. The goal is simple: answer only when retrieved local sources support the response, and refuse clearly when the corpus is insufficient or the question is out of scope.

The current beta is intentionally narrow. It is strongest around prudential supervision, internal controls, own funds and selected default/credit-risk regulatory context. It does not claim full IFRS 9, full Pillar 3, full EBA/Basel perimeter or complete banking-regulatory coverage.

Recent local eval was useful and humbling:

- shared score-only baseline: 27 false answers on 32 cases;
- shared domain-gate diagnostic: reduced false answers to 2;
- Fiorell.IA eval set: 4 unsupported-abstention cases still remain problematic.

Those remaining cases are exactly where a cautious assistant should abstain: broad IFRS 9, full EBA/Basel scope, CRR II/III article-by-article comparison and current 2026 bank rankings.

So the release posture is not “production-ready”. It is: source-grounded, refusal-first, local, narrow beta.

Next step: localhost demo and further behavior-first eval, without changing the shared runtime.
