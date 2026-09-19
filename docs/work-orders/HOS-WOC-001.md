# HOS-WOC-001 — Minimal Work Order Compiler

Status: PROMOTED / CANONICAL MERGE VERIFIED  
Branch: `feature/work-order-compiler-v1`  
Baseline: `2c45256128aed441724660243019643d02e59ec8` (`runtime-0.1`)

## Objective

Compile an already-approved architectural decision into the promoted Execution Work Order v1 contract deterministically, without semantic inference, dispatch, or execution.

## Scope

1. Define Approved Architecture Decision v1 as a strict compiler-input schema.
2. Require all execution-relevant fields to exist before compilation.
3. Require source status `APPROVED` plus non-empty owner approval identity and timestamp.
4. Pin the compiled Work Order to an exact 40-hex repository commit SHA.
5. Provide a repository helper that observes exact HEAD using the already-promoted no-shell baseline observer.
6. Preserve scope, exclusions, constraints, tests, security requirements, rollback, workers, known unknowns, privacy class, and approval verbatim.
7. Compute a deterministic SHA-256 fingerprint of the canonical approved decision content, excluding only its own self-referential compiler fingerprint entry.
8. Append that fingerprint as decision provenance to the compiled Work Order.
9. Fail closed if existing provenance for the same decision ID carries a conflicting fingerprint.
10. Validate every compiler output with the promoted `validate_work_order` contract.
11. Add focused regressions and run the full HumanOS CI matrices.

## Out of scope

- Conversation or natural-language summarization.
- Filling missing decision fields.
- LLM/model inference.
- FRIEND packet creation.
- FRIEND sanitization or dispatch.
- Worker/model selection.
- Automatic execution.
- Automatic merge/promotion/deployment.
- Changes to Browser Bridge, Context Router, swarm, Notebook storage, or BodyFixOS.

## Security requirements

- Unapproved decisions cannot compile.
- Missing or unknown source fields fail closed.
- Moving branch names cannot replace immutable baseline SHAs.
- Compiler input is never mutated.
- Approval and privacy classification cannot be silently changed.
- Conflicting decision fingerprints fail closed.
- Compilation grants no filesystem, network, model, merge, deployment, or execution authority.

## Acceptance tests

- Valid approved decision compiles to a valid `APPROVED` Execution Work Order.
- Approval, privacy class, work-order ID, and baseline are preserved exactly.
- Missing/unknown decision fields fail closed.
- DRAFT/unapproved decisions fail closed.
- Invalid baseline identifiers fail closed.
- Fingerprint is deterministic across dictionary key order and stable when its own matching fingerprint provenance is present.
- Decision fingerprint provenance is added once.
- Conflicting existing decision fingerprint fails closed.
- Repository helper pins the observed exact HEAD.
- Formal JSON Schema required fields match runtime validator required fields.
- Full regression and encrypted-backup matrices remain green.

## Rollback

Revert the candidate branch. No Notebook/runtime migration is part of this slice.

## Provenance

- Owner approval: current conversation, 2026-09-19.
- Parent canonical commit: `2c45256128aed441724660243019643d02e59ec8`.
- Parent promoted foundations: HOS-EXEC-CONTRACTS-001 and HOS-PRIV-001.
- Current canonical branch also contains later Browser Bridge/recovery promotions; this slice does not modify them.

## Verification evidence

- Initial candidate head `c6bb03eac2672d7c3a03043abe9fa5d2ee18abd5` exposed a circular-hash defect: once the compiler-generated decision fingerprint was added to provenance, hashing the entire decision changed the fingerprint itself.
- Minimal repair commit: `e2306d12f6fe07a31713c2a50db414c34404fe74`.
- Repair: fingerprint canonical decision content while excluding only the self-referential compiler fingerprint entry for the same decision ID; all other provenance remains covered.
- Regression run `35471423988`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Representative regression job: 542 tests, 8 skipped, no failures.
- Encrypted-backup/full-suite run `35471424001`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Candidate remains bounded to the compiler, its input schema, tests, and this Work Order.
- No dispatch, execution, merge, deployment, Browser Bridge change, Context Router change, swarm change, Notebook migration, or BodyFixOS integration occurred.

## Done condition

An already-approved architecture decision can be deterministically transformed into a validator-clean Work Order with immutable baseline and stable source fingerprint provenance, while no execution or dispatch capability is added.

## Promotion evidence

- Promotion PR: #95.
- Verified candidate head: `71fe853938ff04021d4b5836902e6820e7040bb9`.
- Canonical merge commit: `52e66077f86726e76d648d7f84a63a7bbc209da7`.
- `runtime-0.1` was verified identical to the merge commit immediately after promotion.
- No release, tag, deployment, automatic dispatch, model routing, execution, Browser Bridge modification, Context Router modification, swarm modification, Notebook migration, or BodyFixOS integration occurred.

## Next candidate

A deterministic FRIEND packet compiler from an approved Work Order, or integration of this compiler into the human-gated Work Loop, subject to a new Jon Gate.
