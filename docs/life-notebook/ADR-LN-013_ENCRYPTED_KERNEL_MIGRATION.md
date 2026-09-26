# ADR-LN-013 — Encrypted Kernel Migration and Cutover

**Status:** CANDIDATE — EVIDENCE SUPPORTED, NOT YET PROMOTED  
**Date:** 2026-09-26  
**Workstream:** `HOS-LN-000`

## Context

Runtime 0.1 already contains valuable Life Notebook evidence in a working plaintext
SQLite database. LN-1 requires application-encrypted durable storage while preserving
exact transcript fidelity, current identities, recovery history, corrections,
privacy operations, and rollback evidence.

Two broad migration strategies were considered:

1. mutate/evolve the active existing database in place and add encryption there;
2. create a new encrypted target database, migrate evidence under a verified mapping,
   verify parity, then explicitly cut over while preserving the old source as
   read-only rollback/provenance evidence for a bounded retention period.

## Evidence

### V-01 migration fixture

Run `36216014250` passed the full macOS/Ubuntu × Python 3.11/3.13 regression matrix.
The synthetic Runtime 0.1 fixture can be mapped into a new event/payload target while
preserving exact text, identity mapping, recovery failures, privacy evidence,
legacy integrity metadata, projection classification, idempotency, and fail-closed
source-change detection.

### V-02 encrypted storage

Run `36216565273` passed the revised SQLCipher macOS spike. It verified correct/wrong
key behavior, encrypted DB/WAL handling against known plaintext fixtures, SIGKILL
commit/rollback recovery, encrypted export/restore, independent recovery-wrapper
proof, and plaintext SQLite -> new encrypted SQLCipher export behavior.

Primary-source design notes are recorded in
`LN0_SQLCIPHER_PRIMARY_EVIDENCE.md`.

### Python binding

The first `sqlcipher3==0.6.2` runtime-binding candidate was rejected by qualification
run `36216699091`. This ADR therefore does **not** promote that package or claim the
production Python binding is solved.

## Decision

Subject to LN-0 promotion, HumanOS LN-1 shall use this migration architecture:

```text
CURRENT RUNTIME 0.1 DB
(read-only migration source)
        |
        | deterministic mapped migration
        v
NEW ENCRYPTED KERNEL DB
        |
        | exact parity + integrity + recovery checks
        v
CUTOVER CANDIDATE
        |
        | explicit promotion
        v
LIVE NOTEBOOK WRITER
```

### Rules

1. The current owner Notebook is never used as a destructive migration test fixture.
2. Production migration begins from a verified backup/snapshot and read-only source.
3. Target storage is created encrypted from the beginning; plaintext target creation
   followed by casual in-place conversion is forbidden.
4. Every source record has an explicit migration disposition/mapping.
5. Exact transcript payloads are read back and compared before cutover.
6. Unresolved recovery evidence remains unresolved unless separately reconciled.
7. Existing source identifiers remain traceable to target event/payload identifiers.
8. A migration rerun against the same source is idempotent; a changed source fails
   closed until explicitly reconciled.
9. Projections are rebuilt from target evidence; they are not promoted as source
   truth during migration.
10. Cutover is atomic from HumanOS's perspective: one writer target at a time.
11. The old source is never automatically deleted at cutover. Its retention/destruction
    follows a separate verified retention plan after rollback confidence exists.
12. Rollback means returning application routing to the preserved old runtime state,
    not rewriting the old database with new history.

## Why not in-place first

The new Life Notebook data model is more than encryption: it introduces the unified
kernel event envelope, unique payload objects, source authority, and later derived
State/Graph planes. A controlled new target allows HumanOS to verify the semantic
migration and encryption independently while keeping the original evidence intact.

This is safer than combining schema transformation, encryption conversion, and live
writer mutation in one irreversible step.

## Consequences

### Positive

- original evidence remains available for rollback and forensic comparison;
- migration can be tested repeatedly on copies before cutover;
- the new schema begins encrypted rather than retrofitting encryption after live writes;
- cutover can require exact parity/evidence gates;
- migration failures do not corrupt the current Notebook.

### Costs

- temporary duplicate storage during migration;
- explicit cutover/rollback tooling is required;
- deletion/retention semantics must cover the preserved legacy source;
- the runtime needs a qualified SQLCipher-capable Python access path before live use;
- migration time must eventually be benchmarked on realistic Notebook size.

## Rejected alternatives

### Destructive in-place schema + encryption conversion

Rejected for LN-1 because it increases the blast radius and couples too many changes
into one transition.

### Keep plaintext DB and rely only on FileVault

Rejected as the final target because the Life Notebook architecture requires
application-level encrypted storage independent of full-disk encryption alone.

### Replace the runtime/rewrite in Rust before migration

Rejected. Current evidence does not justify discarding the working Python runtime.
Language/runtime changes remain separate architecture decisions.

## Promotion gates

This ADR may be promoted only after:

- a production-capable Python SQLCipher access path is qualified or an equally
  justified storage adapter is proven;
- LN-1 acceptance tests are executable;
- an independent review finds no schema-blocking migration/security defect;
- Jon explicitly approves promotion/cutover architecture.

Until then this is an evidence-backed candidate, not live behavior.
