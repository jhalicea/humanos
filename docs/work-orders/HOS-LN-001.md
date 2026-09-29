# HOS-LN-001 — PRE-LN-1 Schema / Integrity ADR

**Status:** ACTIVE — ADR candidate prepared; independent review and owner acceptance pending  
**Workspace:** `WS-HUMANOS`  
**Project:** Life Notebook  
**Branch:** `life-notebook-ln1-schema-integrity`  
**Baseline:** `life-notebook-ln0` at `85e0308e19a9c145fa44bd922c2010bd87675658`  
**Parent:** `HOS-LN-000 — Life Notebook LN-0 Consolidation` (CLOSED / IMPLEMENTATION-READY)  
**Classification:** CONTINUE Life Notebook program / CREATE_SEPARATE bounded PRE-LN-1 gate  
**Primary artifact:** `docs/life-notebook/ADR-LN-014_SCHEMA_INTEGRITY.md`

## Outcome

Resolve the first mandatory PRE-LN-1 gate without starting LN-1 implementation.
Define the exact event/payload integrity boundary so authorized payload erasure can
complete without rewriting immutable kernel history or leaving a permanent
plaintext-derived fingerprint behind.

## Why this slice exists

LN-0 closed on 2026-09-28 as implementation-ready, but explicitly blocked LN-1
implementation on three PRE-LN-1 gates. The first gate is the Schema / Integrity ADR.
The unresolved questions are:

- exact `NotebookEventV1.event_hash` coverage;
- whether/how `payload_commitment` is represented;
- `PayloadObjectV1.content_hash` lifecycle;
- event/payload integrity before and after authorized erasure;
- idempotency and duplicate-conflict behavior after erasure;
- backup/restore implications;
- compatibility with the promoted V-04 ErasureTag/deletion contract;
- migration implications for legacy Runtime 0.1 digests.

## Scope

This slice is architecture/documentation only.

It may:

- inspect the promoted LN-0 architecture and current Runtime 0.1 integrity behavior;
- define the LN-1 event-hash envelope and payload-integrity lifecycle;
- define idempotency behavior across LIVE -> TOMBSTONED -> ERASED states;
- define deletion/restore invariants that the later implementation must test;
- record unresolved dependencies on key custody and migration/cutover.

## Explicit exclusions

This slice does **not**:

- implement `NotebookEventV1` or `PayloadObjectV1`;
- change `notebook.py`, capture adapters, SQLCipher bindings, or the live writer;
- migrate or touch owner Notebook data;
- select the production SQLCipher Python binding;
- finalize key custody, Keychain integration, KDF parameters, recovery-secret storage,
  rotation, or backup transport;
- authorize LN-1 implementation;
- weaken or rewrite promoted V-03/V-04/V-05 evidence.

## Authority and preservation rules

1. HumanOS remains local-first authority; models/providers are not key or schema authority.
2. The Ingestor remains the sole kernel writer.
3. Existing exact transcript fidelity, read-back-before-checkpoint, retry safety,
   recovery truthfulness, and append-only evidence remain preserved requirements.
4. Each event owns one unique independently deletable payload object; no cross-event
   content-addressed identity is introduced.
5. Authorized erase must not require rewriting immutable kernel history.
6. No ordinary plaintext-derived payload digest may survive `ERASE.COMPLETED` in any
   governed persistent event, receipt, projection, cache, or backup state in scope.

## Acceptance criteria

- [x] The candidate ADR states the immutable `event_hash` envelope and its exclusions.
- [x] The candidate ADR decides the LN-1 V1 `payload_commitment` behavior.
- [x] The candidate ADR defines the `content_hash` / payload-integrity lifecycle.
- [x] The candidate ADR defines idempotency before and after authorized erase.
- [x] The candidate ADR preserves a valid immutable event chain after payload erasure.
- [x] The candidate ADR reconciles V-04 ErasureTag semantics without turning the tag
      into a normal plaintext fingerprint or original-event payload commitment.
- [x] The candidate ADR defines restore quarantine and deletion-checkpoint requirements.
- [x] The candidate ADR records legacy migration implications.
- [ ] Independent architecture/security review finds no schema-blocking defect.
- [ ] Jon explicitly accepts the ADR for PRE-LN-1 use.

## Evidence plan

Architecture inputs:

- `docs/work-orders/HOS-LN-000.md`;
- `docs/life-notebook/LN0_CONSOLIDATED_ARCHITECTURE.md`;
- promoted V-04 deletion contract recorded in LN-0 architecture/results;
- current Runtime 0.1 `notebook.py` keyed content/record integrity behavior;
- current Runtime 0.1 `audit.py` append-only event-chain behavior.

Verification for this documentation slice:

1. read back the committed ADR and work order from GitHub;
2. compare the ADR against the frozen LN-0 deletion and writer-authority invariants;
3. verify no runtime implementation file changed on this branch as part of the slice;
4. submit one immutable commit/ref to an independent architecture/security review;
5. preserve findings before any owner promotion decision.

## Risks

- accidentally binding erasable plaintext into immutable history;
- retaining a low-entropy dictionary-testable fingerprint after erase;
- overloading the event hash with mutable storage/key metadata;
- making idempotency depend on a permanent payload digest;
- allowing an old backup to resurrect erased content;
- copying legacy Runtime 0.1 digests into the new immutable kernel;
- selecting key-custody mechanisms in the wrong ADR.

## Rollback

This workstream is documentation-only. Revert the HOS-LN-001/ADR/STATUS commits or
delete the branch before promotion. `life-notebook-ln0`, `runtime-0.1`, all promoted
LN-0 evidence, and owner Notebook data remain untouched.

## Current state

The first ADR candidate is prepared. It is **not accepted** and does not authorize
schema implementation or live capture.

## Next action

Run an independent architecture/security review of
`ADR-LN-014_SCHEMA_INTEGRITY.md` against the frozen LN-0 architecture and V-04
requirements. Resolve only reproducible blockers, then present the reviewed ADR for
Jon's explicit PRE-LN-1 acceptance decision.
