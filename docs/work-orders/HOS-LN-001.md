# HOS-LN-001 — PRE-LN-1 Schema / Integrity ADR

**Status:** ACTIVE — review blockers remediated; final CI/review and owner acceptance pending  
**Workspace:** `WS-HUMANOS`  
**Project:** Life Notebook  
**Branch:** `life-notebook-ln1-schema-integrity`  
**Baseline:** `life-notebook-ln0` at `85e0308e19a9c145fa44bd922c2010bd87675658`  
**Parent:** `HOS-LN-000 — Life Notebook LN-0 Consolidation` (CLOSED / IMPLEMENTATION-READY)  
**Classification:** CONTINUE Life Notebook program / CREATE_SEPARATE bounded PRE-LN-1 gate  
**Primary artifact:** `docs/life-notebook/ADR-LN-014_SCHEMA_INTEGRITY.md`

## Outcome

Resolve the first mandatory PRE-LN-1 gate without starting LN-1 implementation.
Define the event/payload/idempotency integrity and erasure boundary so exact capture,
retry safety, crash recovery, deletion, restore and key rotation remain truthful.

## Scope

This slice is architecture/documentation plus the minimum CI-harness repair required
to execute already-existing LN-0 SQLCipher-dependent tests on current GitHub runners.
It does not implement LN-1, modify the live writer, migrate owner data, select the
production SQLCipher binding, or finalize key custody/migration/cutover.

## Preserved authority/invariants

1. HumanOS remains local-first authority; models/providers are not schema/key authority.
2. Ingestor remains the sole kernel writer.
3. Exact transcript fidelity, read-back-before-checkpoint, retry safety, recovery
   truthfulness and append-only evidence remain mandatory.
4. Each event owns one independently deletable payload object.
5. `payload_commitment = null` in LN-1 V1; erasable payload bytes/digests do not enter
   immutable event history.
6. No ordinary plaintext-derived payload digest survives `ERASE.COMPLETED` in governed
   persistent state.
7. Immutable event/idempotency identity metadata is HumanOS-normalized/content-free.
8. LIVE payload integrity binds exact bytes to exact object/event identity and an
   authenticated exact `content_integrity_key_id`.
9. LIVE idempotency equality/conflict uses a versioned keyed request fingerprint with
   an authenticated exact `request_fingerprint_key_id`.
10. Unknown/unavailable integrity-key selectors fail closed; no guessing, try-all or
    current/default-key fallback.
11. Event + payload + authoritative idempotency state have one durable commit boundary
    in the first LN-1 vertical slice.
12. V-04 ErasureTag remains separate deletion-verification evidence.

## Acceptance criteria

- [x] Exact immutable event-hash envelope/exclusions defined.
- [x] Immutable metadata admissibility/content-smuggling rule defined.
- [x] LN-1 V1 `payload_commitment` decision defined.
- [x] One-to-one event↔payload structure defined and verifiable both directions.
- [x] Exact payload-byte semantics defined.
- [x] LIVE payload MAC binds identity, metadata, algorithm version, exact key selector,
      and exact persisted bytes.
- [x] Payload integrity selector tamper/unknown/rotation behavior defined.
- [x] Atomic event/payload/idempotency crash/retry semantics defined.
- [x] V-03-compatible `(effective_source_id, ingestion_id)` namespace preserved.
- [x] LIVE request fingerprint has exact versioned envelope and authenticated key
      selector; rotation/tamper/fallback semantics defined.
- [x] Post-erasure retry returns historical ERASED identity without content comparison
      or recreation.
- [x] V-04 ErasureTag interaction defined without turning it into event commitment.
- [x] Restore quarantine verifies surviving LIVE payload/idempotency integrity plus
      deletion reconciliation before LIVE.
- [x] Legacy migration rules prevent old naked hashes/content metadata from becoming
      immutable LN-1 event history.
- [x] GitHub SQLCipher CLI runner gap repaired in CI harness only.
- [ ] Final clean architecture/security review finds no remaining schema blocker.
- [ ] Final branch-head CI passes.
- [ ] Jon explicitly accepts ADR-LN-014.

## Evidence / review history

### Initial candidate

Original ADR candidate: `af7837d6178f3ab66f0fb66f3cbe72c345260ac7`.
Initial working head: `87e04d27fbc40061cbdafc8481e6f4234e0161c6`.

General CI initially failed because GitHub runners lacked the SQLCipher CLI required by
two already-existing LN-0 cross-V tests. Harness-only repair commits:

- `d07a98f7510ab0e5a9b5b595dc9b5642d03a6067` — regression matrix;
- `a97aa8d37afe85485fdc772b6366bf3681a900dc` — encrypted-backup matrix.

Both workflow families subsequently passed at `a97aa8d...` and `f08eb606...`.

### Review pass 1 — three blockers

Preserved on PR #117 before remediation:

1. LIVE payload MAC did not bind object/event identity;
2. atomic event/payload/idempotency commit semantics were missing;
3. immutable metadata had no explicit content-free admissibility rule.

Remediation ADR commit:
`4d082fcfe1b02bc38bc32a5e3e1700c0bad6b527`.

### Review pass 2 — payload-integrity key selector

Fresh review at `f08eb60681ee72b805aa6779ce47e756549e349d` found
`content_integrity_key_id` was referenced but neither required nor authenticated.
Finding preserved on PR #117 before remediation.

Remediation ADR commit:
`e715af891d05cf092475d3b244ad087d429787c7`.

### Review pass 3 — idempotency-fingerprint key selector

Clean continuation review found the transient keyed `request_fingerprint` had no
versioned/authenticated key-selector contract, which would make LIVE retry comparison
ambiguous across key rotation. Finding preserved on PR #117 before remediation.

Latest ADR remediation commit:
`62f24c7813205b5d7ee6b27054dd4183cf67e188`.

The latest ADR now defines:

- `request_fingerprint_version = hmac-sha256-capture-request-v1`;
- required `request_fingerprint_key_id` while fingerprint state is LIVE;
- HMAC envelope covering authenticated effective source, ingestion token, request schema
  version, complete normalized source-supplied semantic claims, payload presence/size,
  fingerprint version/key selector, plus exact payload bytes;
- exclusion of host-assigned seq/IDs/timestamps from source-submission equality;
- fail-closed unknown/unavailable selector, no fallback/guess/try-all;
- deletion of fingerprint + version + selector together at `ERASE.COMPLETED`;
- implementation tests for tamper, conflict, rotation and post-erasure behavior.

## Verification boundary

PR #117 must remain limited to these five files:

1. `.github/workflows/encrypted-backup-tests.yml`
2. `.github/workflows/tests.yml`
3. `STATUS.md`
4. `docs/life-notebook/ADR-LN-014_SCHEMA_INTEGRITY.md`
5. `docs/work-orders/HOS-LN-001.md`

No runtime implementation file or owner Notebook data may change in this workstream.

## Remaining dependencies — deliberately separate

- SQLCipher Runtime Binding + Key Custody ADR, including exact
  kernel/content/idempotency/erasure key generation, wrapping, storage, rotation,
  recovery and historical-key retention;
- authoritative deletion-checkpoint custody;
- Controlled Migration / Cutover Plan;
- production integration qualification before LIVE owner data.

## Rollback

Revert the HOS-LN-001/ADR/STATUS and CI-harness commits or close/delete the branch.
`life-notebook-ln0`, `runtime-0.1`, promoted LN-0 evidence and owner Notebook data
remain untouched.

## Next action

Run fresh CI on the final branch head containing ADR commit
`62f24c7813205b5d7ee6b27054dd4183cf67e188`, then perform one final clean independent
architecture/security review of that exact ADR against frozen LN-0, V-03/V-04,
Runtime 0.1 integrity behavior and this acceptance contract. If clean, preserve the
PASS evidence and present the exact reviewed ADR commit to Jon for explicit PRE-LN-1
acceptance. No merge or LN-1 implementation before that owner decision.
