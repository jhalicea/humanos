# HumanOS Academy v0.1 — Promotion Record

Date: 2026-10-01
Owner authorization: explicit (`promote the Academy`)

## Public runtime promotion

- Workstream: `HOS-LEARN-002 — Adaptive Academy Kernel & Runtime Vertical Slice`
- PR: `jhalicea/humanos#118`
- Base: `runtime-0.1`
- Merge commit: `5e535a2de48b984a90f7ed5ba5d26864cd4fab86`
- Qualified code head: `a3a74a3fdf824aa116d8a03b2833da2b4655047d`
- Final pre-merge head: `52244747da2b5ba5c3d6a00a5d9e54bd2e6b7aec`
- Regression matrix: PASS on Ubuntu 24.04 and macOS 15, Python 3.11 and 3.13
- Encrypted-backup matrix: PASS on Ubuntu 24.04 and macOS 15, Python 3.11 and 3.13

## Private curriculum promotion

- Workstream: `ACADEMY-CONTENT-001 — Master Curriculum Package v0.1`
- PR: `jhalicea/humanos-academy-private#1`
- Base: `main`
- Merge commit: `b2aff930b61d68cb1c6f7eb8596d872783de5615`
- Final pre-merge head: `5d0223e92a6878b152a6ae514dcd107b67c038fc`
- Compatibility validation run: `36824979703`
- Validation matrix: PASS on Ubuntu 24.04 and macOS 15, Python 3.11 and 3.13
- Validated package: 11 courses, 134 shared skills, 20 nested labs, 10 certification overlays, 8 job packs, `current_focus: null`

## Canonical lineage reconciliation

The promotion bookkeeping branch `promotion/academy-v0.1` reconciles `config/context_registry.public.json` so that:

- `HOS-LEARN-001` is preserved as `SUPERSEDED`;
- `HOS-MASTERY-001` records its earlier promoted PR #58 merge `be0ce155c40cdfe33ace858f55df7ca3d2efa0d5`;
- `HOS-LEARN-002` is recorded as `PROMOTED` and points to public merge `5e535a2de48b984a90f7ed5ba5d26864cd4fab86`.

Registry reconciliation was generated and validated on the promotion branch by a temporary one-shot workflow and committed at `d5806c91838b5dcc2463089712b6059204c13535`. The temporary workflow was then removed before promotion bookkeeping is merged.

## Invariants preserved

- Real curriculum and learner state remain outside the public repository.
- The learner-state database defaults to `$HOME/.humanos/private/academy/academy.sqlite3`.
- Curriculum package loading remains provider-neutral.
- `unfinished != current`; historical unfinished work does not become current focus automatically.
- `TTX-001` remains historical unfinished work and is not current focus.
- Certification coverage is not credential readiness.
- No historical learner-state migration occurred during this promotion.

## Rollback

Public runtime rollback: revert merge `5e535a2de48b984a90f7ed5ba5d26864cd4fab86` plus the Academy promotion-bookkeeping merge if necessary.

Private curriculum rollback: revert merge `b2aff930b61d68cb1c6f7eb8596d872783de5615` independently.

## Authorized next action

Create a new bounded Academy workstream for the usable/fun layer: Mission Board + first real Academy session. Do not reopen `HOS-LEARN-002` as an unlimited feature stream and do not auto-resume historical unfinished work.
