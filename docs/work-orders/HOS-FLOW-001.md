# HOS-FLOW-001 — Effortless Work Preparation

Status: VERIFIED / PROMOTION PENDING  
Branch: `feature/effortless-work-prep-v1`  
Baseline: `563cd3abd3a9af6c2ebd85b4c790a41d4a6880aa` (`runtime-0.1`)

## Experience goal

Make HumanOS work preparation feel calm and obvious: one concise review surface by default, with the full governance machinery available only when requested.

The design principle is progressive disclosure:

**simple surface, rigorous core, details on demand.**

## Scope

1. Add a deterministic FRIEND assignment compiler.
2. Inherit baseline, privacy, constraints, known unknowns, acceptance criteria, and Work Order identity instead of asking the human to repeat them.
3. Require assignment paths to be a strict subset of Work Order `relevant_files`.
4. Add protected actions automatically: no unapproved merge/deploy, deletion, scope widening, or approval/privacy changes.
5. Compose the promoted Work Order compiler, FRIEND compiler, and privacy firewall in one `prepare_work()` call.
6. Return a compact default review card containing only:
   - readiness;
   - objective;
   - scope size + ownership mode;
   - worker role;
   - privacy/destination;
   - verification count;
   - whether work has started.
7. Keep IDs, hashes, schema names, raw privacy findings, and full contracts behind `details()`.
8. For eligible external preparation, summarize privacy changes without exposing redacted values.
9. Do not dispatch or execute anything.
10. Run focused tests plus full HumanOS regression/encrypted-backup matrices.

## Out of scope

- Automatic model/provider selection.
- Automatic dispatch or execution.
- Natural-language generation of missing architecture fields.
- Replacing the existing owner approval model.
- Mirror conversational wiring in this slice.
- Browser Bridge, Context Router, swarm, Notebook schema, or BodyFixOS changes.

## UX rules

- Default view is short enough to scan instantly.
- No SHA, schema name, packet ID, or Work Order ID in the normal view.
- Technical evidence remains available without loss.
- Privacy protection is visible as a status, not as secret content.
- HumanOS never says work ran when it only prepared it.
- Errors should fail closed in the core rather than adding choices to the default surface.

## Security requirements

- A FRIEND assignment cannot exceed Work Order `relevant_files`.
- Work Order governance is inherited, never weakened by assignment input.
- FRIEND content remains `DATA_ONLY` and output `PROPOSAL_UNVERIFIED`.
- Protected actions are always included.
- External privacy policy is enforced through the promoted privacy firewall.
- Inputs are not mutated.
- Preparation grants no execution, network, filesystem, model, merge, or deployment authority.

## Acceptance tests

- Valid work compiles through Decision → Work Order → FRIEND → privacy preparation.
- Governance fields are inherited exactly.
- Path escape fails closed.
- Empty Work Order file scope cannot produce a FRIEND assignment.
- Default review card omits hashes, IDs, and schema noise.
- Full details retain all audit artifacts.
- External redaction is summarized without exposing the original sensitive value.
- Sensitive privacy classes remain blocked from external preparation.
- Formal assignment schema matches runtime-required fields.
- Full regression and encrypted-backup matrices remain green.

## Rollback

Revert the candidate branch. No local Notebook/runtime data migration is part of this slice.

## Provenance

- Owner direction: make the experience “perfect, effortless and Apple like.”
- Parent canonical commit: `563cd3abd3a9af6c2ebd85b4c790a41d4a6880aa`.
- Parent promoted foundations: HOS-EXEC-CONTRACTS-001, HOS-PRIV-001, HOS-WOC-001.

## Verification evidence

- Verified candidate head before evidence preservation: `dd7cdbf9d90e554e68c9046e5b4dd45caa965203`.
- Regression run `35472481062`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Representative regression job: 552 tests, 8 skipped, no failures.
- Encrypted-backup/full-suite run `35472481085`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Exact candidate diff remained bounded to the FRIEND assignment compiler, preparation/presentation layer, assignment schema, tests, and this Work Order.
- Default review-card tests verify that hashes, schema names, packet IDs, and Work Order IDs are not exposed in the normal surface.
- Full audit artifacts remain available through `details()`.
- No dispatch, execution, model/provider selection, Mirror wiring, Browser Bridge change, Context Router change, swarm change, Notebook migration, deployment, or BodyFixOS integration occurred.

## Done condition

HumanOS can prepare a complete, governed, privacy-checked unit of work with one deterministic call while exposing a minimal review surface by default and retaining full audit detail on demand.

## Next candidate

Wire this prepared-work review into Mirror as a durable human-gated conversation flow, so the human can review naturally and say “do it” without handling schemas or IDs.
