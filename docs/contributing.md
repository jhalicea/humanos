---
layout: default
---

# Contributing

HumanOS welcomes careful review, reproducible bug reports, tests, documentation improvements, and narrowly scoped pull requests.

## Before proposing a change

1. State the user-visible outcome.
2. Identify the current behavior and evidence.
3. Define the smallest reversible change.
4. Include normal, failure, restart, duplication, and regression tests where relevant.
5. Distinguish verified behavior from assumptions and future design.

## Foundation increment workflow

Foundation work proceeds as small, reversible, evidence-gated increments. Each
increment uses the same sequence:

1. **Problem** — name one observable failure or missing primitive and its
   explicit non-goals.
2. **Evidence** — inspect the governing contract, current implementation,
   focused tests, and Git state. Separate repository facts from proposals and
   unproven integrations.
3. **Slice** — implement one narrow vertical capability on an isolated branch.
   Do not bundle downstream integrations that are not required to prove it.
4. **Qualification** — test the normal path, invalid input, restart or replay,
   duplicate/conflict behavior, and an injected failure at the claimed
   durability boundary.
5. **Review** — inspect the diff for authority, privacy, exactness,
   idempotency, recovery, migration, and accidental private data.
6. **GitHub handoff** — commit the exact tested revision, push the branch, and
   open a pull request that records scope, commands and results, limitations,
   reproduction steps, and rollback. Merge remains an owner decision.

Passing an increment proves only its stated acceptance criteria. It does not
prove that a future connector, projection, relay, backup, or live deployment is
already implemented.

## Pull requests

- Keep changes bounded and explain rollback.
- Do not include personal Notebook content, credentials, private paths, or client information.
- Do not weaken permission or privacy boundaries without explicit review.
- Report exact commands and results for tests actually run.
- Use synthetic fixtures for public examples.

Public contributions are proposals until reviewed and verified against the repository's acceptance criteria.
