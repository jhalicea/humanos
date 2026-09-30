# HOS-LN-001 — PRE-LN-1 Schema / Integrity ADR

**Status:** ACTIVE — review blockers remediated; fresh CI/review and owner acceptance pending  
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
complete without rewriting immutable kernel history, leaving a permanent
plaintext-derived fingerprint, allowing content to leak through immutable metadata,
creating ambiguous event/payload/idempotency crash state, or losing deterministic
payload-integrity verification across key rotation.

## Why this slice exists

LN-0 closed on 2026-09-28 as implementation-ready, but explicitly blocked LN-1
implementation on three PRE-LN-1 gates. The first gate is the Schema / Integrity ADR.
This gate resolves:

- exact `NotebookEventV1.event_hash` coverage;
- immutable metadata admissibility after erasure;
- whether/how `payload_commitment` is represented;
- `PayloadObjectV1.content_hash` lifecycle, identity binding, and key-version selector;
- one-to-one event↔payload linkage;
- authoritative event/payload/idempotency transaction boundary;
- event/payload integrity before and after authorized erasure;
- idempotency and duplicate-conflict behavior after erasure;
- backup/restore implications;
- compatibility with the promoted V-04 ErasureTag/deletion contract;
- migration implications for legacy Runtime 0.1 digests.

## Scope

This slice is architecture/documentation plus the minimum verification-harness repair
needed to execute already-existing LN-0 tests on current GitHub runners.

It may:

- inspect the promoted LN-0 architecture and current Runtime 0.1 integrity behavior;
- define the LN-1 event-hash envelope and payload-integrity lifecycle;
- define immutable metadata admissibility and content-free identifier rules;
- define one-to-one event/payload binding and crash atomicity requirements;
- define authenticated LIVE payload-integrity key-version selection;
- define idempotency behavior across LIVE -> TOMBSTONED -> ERASED states;
- define deletion/restore invariants that later implementation must test;
- record unresolved dependencies on key custody and migration/cutover;
- repair CI-only dependency setup when an existing required test cannot execute
  because a GitHub runner lacks an already-required tool.

## Explicit exclusions

This slice does **not**:

- implement `NotebookEventV1` or `PayloadObjectV1`;
- change `notebook.py`, capture adapters, SQLCipher bindings, or the live writer;
- migrate or touch owner Notebook data;
- select the production SQLCipher Python binding;
- finalize key generation/custody, Keychain integration, KDF parameters,
  recovery-secret storage, rotation, historical-key retention, or backup transport;
- authorize LN-1 implementation;
- weaken or rewrite promoted V-03/V-04/V-05 evidence.

CI workflow changes in this slice are verification-harness changes only. They do not
change runtime behavior or architecture authority.

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
7. Immutable event/idempotency metadata must be HumanOS-normalized and content-free;
   arbitrary descriptive/source content belongs in erasable payload/provenance state.
8. LIVE payload integrity must bind exact payload bytes to exact event/object identity.
9. The exact LIVE payload-integrity key selector must be required, MAC-authenticated,
   fail closed when unavailable/unknown, and remain part of erasable integrity state.
10. Idempotency reservation, payload object and kernel event must have one authoritative
    durable commit boundary for the LN-1 V1 first slice.

## Acceptance criteria

- [x] The candidate ADR states the immutable `event_hash` envelope and its exclusions.
- [x] The candidate ADR constrains immutable metadata to content-free normalized values.
- [x] The candidate ADR decides the LN-1 V1 `payload_commitment` behavior.
- [x] The candidate ADR defines the `content_hash` / payload-integrity lifecycle.
- [x] LIVE payload integrity binds exact payload bytes to exact `object_id` / `event_id`.
- [x] The LIVE payload MAC authenticates `content_integrity_key_id`, and verification
      rejects unknown/unavailable selectors without guessing or fallback.
- [x] The candidate ADR defines one-to-one event↔payload linkage invariants.
- [x] The candidate ADR defines atomic event/payload/idempotency crash/retry semantics.
- [x] The candidate ADR defines idempotency before and after authorized erase.
- [x] The candidate ADR preserves a valid immutable event chain after payload erasure.
- [x] The candidate ADR reconciles V-04 ErasureTag semantics without turning the tag
      into a normal plaintext fingerprint or original-event payload commitment.
- [x] The candidate ADR defines restore quarantine and deletion-checkpoint requirements.
- [x] The candidate ADR records legacy migration implications.
- [x] Current GitHub runner dependency gap for required SQLCipher CLI tests is repaired
      in CI harness only and proven by a passing full matrix at an immutable head.
- [ ] Fresh independent architecture/security review of the latest remediated ADR finds
      no schema-blocking defect.
- [ ] Jon explicitly accepts the ADR for PRE-LN-1 use.

## Evidence plan

Architecture inputs:

- `docs/work-orders/HOS-LN-000.md`;
- `docs/life-notebook/LN0_CONSOLIDATED_ARCHITECTURE.md`;
- promoted V-03 ingestion/crash/idempotency evidence;
- promoted V-04 deletion/ErasureTag semantics;
- current Runtime 0.1 `notebook.py` keyed content/record-envelope integrity behavior;
- current Runtime 0.1 `audit.py` append-only event-chain behavior.

Verification for this slice:

1. read back the committed ADR and work order from GitHub;
2. compare the ADR against the frozen LN-0 deletion, writer-authority, retry and crash
   invariants;
3. verify no runtime implementation file changed on this branch;
4. preserve independent-review findings before remediation;
5. run the full existing regression/encrypted-backup matrices with SQLCipher available;
6. submit the latest remediated immutable ADR commit/ref to a fresh architecture/security
   review;
7. preserve findings before any owner promotion decision.

## Review remediation record

### Review pass 1

Three blockers were preserved on PR #117 before remediation:

1. LIVE payload MAC did not bind `object_id` / `event_id`;
2. event/payload/idempotency atomic commit semantics were missing;
3. immutable metadata had no explicit content-free admissibility rule.

ADR remediation commit:
`4d082fcfe1b02bc38bc32a5e3e1700c0bad6b527`.

### Review pass 2

Fresh review at branch head `f08eb60681ee72b805aa6779ce47e756549e349d`
found one remaining blocker: `content_integrity_key_id` was referenced by the LIVE
payload HMAC but was not a required payload field and was not authenticated by the MAC
envelope. The finding was preserved on PR #117 before correction.

ADR key-version remediation commit:
`e715af891d05cf092475d3b244ad087d429787c7`.

The latest ADR now requires the selector as LIVE payload-integrity metadata, includes it
in the HMAC envelope, fails closed for unknown/unavailable selectors, removes it with
erased LIVE integrity state by default, and derives implementation tests for tamper,
unknown-key, and historical-key verification after rotation.

These remediations do not change the central decision to keep
`payload_commitment = null`, keep payload integrity erasable, and preserve V-04
ErasureTag as a separate deletion-verification mechanism.

## CI evidence

Initial candidate head `87e04d27fbc40061cbdafc8481e6f4234e0161c6` exposed an
environmental CI gap: two LN-0 cross-V tests could not execute because general GitHub
runner workflows did not install the SQLCipher CLI.

Harness-only repair commits:

- `d07a98f7510ab0e5a9b5b595dc9b5642d03a6067` — regression matrix;
- `a97aa8d37afe85485fdc772b6366bf3681a900dc` — encrypted-backup matrix.

At both `a97aa8d37afe85485fdc772b6366bf3681a900dc` and later
`f08eb60681ee72b805aa6779ce47e756549e349d`, both workflow families completed SUCCESS.
A fresh run is still required at the final candidate branch head after the latest
review-remediation bookkeeping commits.

## Risks

- accidentally binding erasable plaintext into immutable history;
- retaining a low-entropy dictionary-testable fingerprint after erase;
- smuggling erasable content into immutable metadata;
- allowing authenticated payload bytes to be rebound/swapped across event identity;
- accepting an unauthenticated/guessed integrity-key selector after rotation;
- overloading the event hash with mutable storage/key metadata;
- creating hidden partial capture state across crash boundaries;
- making idempotency depend on a permanent payload digest;
- allowing an old backup to resurrect erased content;
- copying legacy Runtime 0.1 digests into the new immutable kernel;
- selecting key-custody mechanisms in the wrong ADR.

## Rollback

Revert HOS-LN-001/ADR/STATUS changes and the two CI-harness commits, or delete/close
the branch before promotion. `life-notebook-ln0`, `runtime-0.1`, all promoted LN-0
evidence, and owner Notebook data remain untouched.

## Current state

The latest remediated ADR candidate is prepared. It is **not accepted** and does not
authorize schema implementation or live capture.

## Next action

Obtain fresh CI at the final candidate head, then run a fresh independent
architecture/security review of ADR commit
`e715af891d05cf092475d3b244ad087d429787c7`. Resolve only any new reproducible blocker.
If review is clean, record the reviewed SHA and present it to Jon for explicit
PRE-LN-1 acceptance.
