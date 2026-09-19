# HOS-EXEC-CONTRACTS-001 — Compiled Execution Contracts

Status: VERIFIED / PROMOTION PENDING  
Branch: `feature/execution-contracts-v1`  
Baseline: `13f22ee4310e4385b164d163d72c251e39a92055` (`runtime-0.1`)

## Objective

Create the first deterministic contract boundary between rich architectural context and bounded execution context: a strict Execution Work Order schema, a strict FRIEND packet schema, and fail-closed stale-baseline enforcement.

## Scope

1. Define Execution Work Order v1 with explicit scope, out-of-scope, baseline, constraints, acceptance tests, security requirements, rollback, assigned workers, known unknowns, provenance references, done condition, approval, and privacy class.
2. Define FRIEND Packet v1 with explicit known evidence, constraints, UNKNOWN / DO NOT ASSUME, allowed scope, prohibited actions, acceptance criteria, expected output, verification requirements, ownership boundaries, and fixed untrusted-output semantics.
3. Require FRIEND packets to bind to the exact Work Order ID, baseline commit, and privacy class.
4. Add a deterministic repository HEAD observation using argument-vector `git rev-parse HEAD` with no shell.
5. Refuse execution unless a Work Order is structurally valid, explicitly APPROVED, and matches the observed exact commit SHA.
6. Add focused regressions and run the existing full matrices.

## Out of scope

- Automatic FRIEND/model selection.
- Cloud dispatch.
- Packet sanitization automation.
- Cost scoring or empirical model routing.
- Automatic Work Order compilation from conversations.
- Automatic merge/deployment/promotion.
- Changes to existing swarm/model router behavior.
- BodyFixOS.

## Security requirements

- Unknown top-level contract fields fail closed.
- Baselines use immutable 40-hex commit SHAs, not moving branch names alone.
- Stale baseline mismatch raises a dedicated error.
- FRIEND content is always `DATA_ONLY`, never authority.
- FRIEND output is always `PROPOSAL_UNVERIFIED`.
- Bounded writers require explicit owned paths.
- Contract validation grants no filesystem, tool, model, merge, or deployment authority.

## Acceptance tests

- Valid APPROVED Work Order + exact observed SHA is executable.
- DRAFT Work Order is not executable.
- Baseline mismatch fails closed as STALE.
- Missing/unknown fields fail closed.
- FRIEND packet cannot rebind to another Work Order or baseline.
- FRIEND packet cannot elevate analyzed content to authority or declare its own output verified.
- Bounded write packet requires explicit paths.
- Formal JSON Schema required fields match runtime validator required fields.
- Existing full regression and encrypted-backup matrices remain green.

## Rollback

Revert the candidate branch. No Notebook/runtime data migration is part of this slice.

## Provenance

- Owner approval: current conversation, 2026-09-18.
- Parent canonical commit: `13f22ee4310e4385b164d163d72c251e39a92055`.
- HumanOS Work Loop v1.1 design: approved architecture distinguishes rich architectural context from compiled execution state and requires stale work orders to be revalidated.

## Verification evidence

- Candidate head: `5070f299471f52f1fccf61fd66bc2f5c4a7cbd3d`.
- Regression run `35415184009`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Representative regression job: 485 tests, 8 skipped, no failures.
- Encrypted-backup/full-suite run `35415184001`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Candidate comparison at verification: five intended files added; no runtime dispatcher, router, swarm, Notebook schema, or BodyFixOS files changed.
- No merge, release, tag, deployment, or data migration performed.

## Done condition

The schemas and fail-closed validation primitives are verified on all supported CI matrix variants, with no dispatcher integration or authority expansion.

## Next candidate

Packet sanitization/privacy firewall or a minimal Work Order compiler, subject to a new Jon Gate.
