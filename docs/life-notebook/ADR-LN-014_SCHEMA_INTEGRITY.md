# ADR-LN-014 — Notebook Event / Payload Integrity and Erasure Boundary

**Status:** CANDIDATE — REVIEW BLOCKERS REMEDIATED / FINAL CLEAN REVIEW REQUIRED  
**Date:** 2026-09-30  
**Workstream:** `HOS-LN-001`  
**Baseline:** `life-notebook-ln0` at `85e0308e19a9c145fa44bd922c2010bd87675658`

## Context

LN-0 is CLOSED / IMPLEMENTATION-READY, but LN-1 implementation is blocked on a
mandatory Schema / Integrity ADR. The design must preserve all of these at once:

- the kernel event chain remains immutable and verifiable;
- payload bytes remain independently erasable;
- authorized erase does not rewrite old kernel events;
- no ordinary plaintext-derived payload digest survives `ERASE.COMPLETED` in a
  governed persistent store;
- immutable metadata cannot become a covert channel for erasable content;
- idempotency and conflict detection remain truthful across retries and key rotation;
- event, payload and idempotency state survive crash boundaries without hidden partial
  commits;
- LIVE payload integrity remains verifiable across integrity-key rotation without an
  unauthenticated or guessed key selector;
- restore cannot resurrect erased payloads;
- the promoted V-04 ErasureTag contract remains valid;
- existing Runtime 0.1 integrity behavior is migrated, not blindly copied.

Runtime 0.1 already uses keyed HMAC-SHA-256 content/record integrity for new transcript
rows and binds record metadata together with the content digest. LN-1 preserves that
useful separation between record integrity and event chronology while removing
payload-derived values from the immutable event chain.

Independent review of earlier revisions found five reproducible blockers: LIVE payload
integrity did not bind event/object identity; event/payload/idempotency atomic creation
was not explicit; immutable metadata was not constrained to content-free values; the
LIVE payload HMAC referenced a content-integrity key ID without making that selector
required/authenticated; and the LIVE keyed idempotency fingerprint had no versioned,
authenticated key-selector contract across rotation. This revision remediates those
findings without changing the central erasure model.

## Decision summary

LN-1 V1 separates **immutable event integrity** from **erasable payload integrity**.

1. `NotebookEventV1.event_hash` authenticates only the immutable structural event
   envelope plus `prev_event_hash`.
2. Every immutable event field that survives erasure is HumanOS-normalized and
   content-free: controlled vocabulary, bounded scalar, or opaque identifier. Arbitrary
   source text, paths, URLs, subjects, labels and descriptive metadata belong in the
   erasable payload, not the immutable envelope.
3. The immutable event binds to its payload by opaque `payload_object_id`, not by a
   permanent plaintext-derived digest.
4. `NotebookEventV1.payload_commitment` is **NULL / unused in LN-1 V1**. No content
   commitment is retained in the original immutable event.
5. Payload integrity while the payload exists is enforced inside `PayloadObjectV1`
   using keyed content integrity that binds the exact persisted payload bytes to the
   exact event/object identity, immutable payload metadata, algorithm version and exact
   `content_integrity_key_id`. That integrity state is erasable.
6. The authoritative idempotency reservation, payload object and kernel event are
   committed as one LN-1 V1 durable transaction. Crash/retry semantics preserve the
   promoted V-03 behavior: no partial pre-commit identity and no duplicate event after
   commit-before-ack.
7. Idempotency is source-identity based. While LIVE, semantic equality/conflict is
   proven with a versioned keyed `request_fingerprint` whose exact key selector is
   authenticated by the fingerprint itself. Fingerprint proof state is erased at
   `ERASE.COMPLETED`; a later retry of the historical tuple returns ERASED identity
   without content comparison or recreation.
8. V-04 ErasureTags remain a separate deletion-verification mechanism. They are not
   original-event payload commitments and are never ordinary plaintext hashes.
9. Restore is quarantined until authoritative deletion state has been reconciled and
   all surviving LIVE integrity proofs verify under their exact historical keys.

---

## 1. Immutable `NotebookEventV1` hash envelope

### Event-hash algorithm

LN-1 V1 uses a versioned keyed event-chain MAC:

```text
event_hash_version = hmac-sha256-notebook-event-v1

event_hash = HMAC-SHA-256(
    K_kernel_integrity[event_integrity_key_id],
    "HumanOS NotebookEventV1\0" || JCS(event_hash_envelope)
)
```

`JCS(...)` means RFC 8785 JSON Canonicalization Scheme. Production must use one
verified canonicalization implementation and test cross-process stable bytes before
live use.

The key is HumanOS-owned and never stored in the event row. Key generation, custody,
wrapping, rotation, recovery and historical key availability are governed by the
separate PRE-LN-1 SQLCipher Runtime Binding + Key Custody ADR.

### Fields covered by `event_hash`

The V1 hash envelope is exactly:

```text
identity:
  event_id
  seq
  schema_version

classification:
  stream
  event_type

time:
  occurred_at
  occurred_at_trust
  observed_at
  ingested_at
  origin_timezone

actor/source:
  actor_id
  actor_type
  source_system
  source_locator
  source_instance
  ingestion_id

relationships:
  conversation_id
  parent_event_id
  correlation_id
  causation_id
  trace_id

policy:
  epistemic_class
  sensitivity_class
  delegation_lane
  provider_class

payload_binding:
  payload_object_id
  payload_commitment = null

capture:
  capture_status_at_commit

integrity:
  event_integrity_key_id
  prev_event_hash
  event_hash_version
```

Null optional fields are serialized explicitly. `event_hash` itself is excluded from
its own input.

### Immutable metadata admissibility rule

The event envelope is permanent structural evidence, so arbitrary source text is not
allowed in it.

HumanOS must normalize every immutable field before hashing:

- `stream`, `event_type`, `actor_type`, policy classes and provider classes are
  controlled vocabulary;
- `event_id`, `conversation_id`, parent/correlation/causation/trace IDs and source
  instance identifiers are bounded opaque identifiers;
- `actor_id` is a HumanOS-resolved principal identifier, not a display name or source
  claim;
- `source_system` is a controlled source class/name;
- `source_locator` may contain only a bounded opaque locator generated or normalized
  by HumanOS. A path, URL with descriptive/query content, email subject, filename,
  user-entered label, message-body fragment or other content-bearing locator is not
  eligible for immutable storage;
- `ingestion_id` is a bounded retry token. If a provider/source-native ID contains
  user content or sensitive descriptive text, HumanOS uses an internal opaque retry
  identity in the immutable/idempotency plane and keeps the original source-native
  value only in erasable payload/provenance state.

If a capture source tries to place arbitrary content into an immutable field, the
Ingestor must reject it or move it into governed erasable payload state. Source claims
cannot manufacture permanent metadata merely by naming a field.

### Capture status rule

`capture_status_at_commit` is immutable. The original kernel event records only its
durable commit state. Later read-back/checkpoint/recovery progress is represented by
separate transaction/checkpoint/recovery evidence rather than mutating the original
event.

### Explicitly excluded from the immutable event hash

The original event hash MUST NOT include:

- plaintext payload bytes;
- `content_hash` or any ordinary plaintext digest;
- `request_fingerprint` or its erasable key-selector/version state;
- ciphertext bytes or a ciphertext digest;
- payload encryption nonce/tag/material;
- `key_ref` or `storage_ref`;
- payload `size_bytes` or lifecycle state;
- `deleted_at`;
- deletion receipt contents;
- V-04 ErasureTag;
- projection/cache identifiers;
- mutable backup/export location metadata.

---

## 2. `payload_commitment` decision

`NotebookEventV1.payload_commitment` remains present as an optional schema slot but is
**NULL in LN-1 V1**.

Rationale:

- a normal content hash violates the post-erasure privacy contract;
- a permanent keyed content MAC still couples original-event verification to
  payload/key lifecycle;
- a ciphertext hash couples immutable chronology to storage/encryption representation;
- an opaque random value adds no integrity property beyond unique
  `payload_object_id`.

A future non-null payload commitment requires a separate ADR, deletion proof,
migration plan and regression tests. It cannot appear as a silent schema extension.

---

## 3. `PayloadObjectV1` integrity lifecycle

Each event owns exactly one independently deletable payload object when payload exists.
No two events share a payload object or use content hash as storage identity.

Required V1 lifecycle fields include:

```text
object_id
 event_id
 lifecycle_state        # LIVE | TOMBSTONED | ERASED | RECOVERY_REQUIRED
 mime_type
 size_bytes
 sensitivity_class
 encryption_scope
 key_ref
 storage_ref
 content_hash
 content_hash_version
 content_integrity_key_id
 created_at
 deleted_at
```

`object_id` and `event_id` survive erasure as structural identity. Content-bearing or
content-derived payload-integrity fields do not. `content_integrity_key_id` is required
while `content_hash` exists, is authenticated by that MAC, and is removed with LIVE
payload-integrity state at `ERASE.COMPLETED` unless a later reviewed Key Custody ADR
proves a deletion-safe structural reason to retain a content-free historical key label.

### One-to-one structural binding

LN-1 V1 requires:

```text
event.payload_object_id == payload.object_id
payload.event_id         == event.event_id
```

For an event with payload:

- `object_id` is unique and never reassigned;
- `event_id` is unique in the payload table;
- a payload cannot be rebound to another event;
- an event cannot acquire a second payload;
- a LIVE event referencing a missing/mismatched payload fails verification;
- an orphan LIVE payload fails verification.

The SQL implementation must enforce this with primary/unique and foreign-key
constraints or an equivalently strong fail-closed invariant. The verifier checks both
directions.

### Exact payload-byte rule

`content_hash` authenticates the **exact logical bytes HumanOS durably stores**, not a
later semantic reserialization.

- text uses exact captured UTF-8 bytes; the integrity layer performs no Unicode,
  newline, whitespace or line-ending normalization;
- binary/file capture uses exact captured bytes;
- structured capture is serialized once by a versioned capture codec before the
  durable transaction; exact resulting bytes are stored and verified;
- verification never parses and reserializes arbitrary payload content to recreate
  integrity input.

### LIVE state

While LIVE:

- bytes are stored only in the approved encrypted payload representation;
- authenticated encryption provides cryptographic integrity for stored ciphertext;
- `content_hash` is a versioned keyed HMAC binding exact payload identity, immutable
  payload metadata, exact integrity-key selector and exact persisted bytes;
- `content_hash`, `content_hash_version` and `content_integrity_key_id` remain only in
  erasable payload-integrity state.

V1 format:

```text
content_hash_version = hmac-sha256-payload-content-v1

payload_integrity_envelope = {
  object_id,
  event_id,
  mime_type,
  size_bytes,
  sensitivity_class,
  content_hash_version,
  content_integrity_key_id,
  created_at
}

content_hash = HMAC-SHA-256(
    K_payload_integrity[content_integrity_key_id],
    "HumanOS PayloadObjectV1\0" ||
    JCS(payload_integrity_envelope) || "\0" || exact_payload_bytes
)
```

The verifier resolves exactly the named `content_integrity_key_id`. Unknown,
unavailable, malformed, revoked-without-valid-historical-verification-path or otherwise
unresolvable IDs fail closed. No guessing, try-all, current/default-key fallback or
silent selector rewrite is permitted.

`encryption_scope`, `key_ref` and `storage_ref` are excluded from this content MAC so
authorized re-encryption/storage relocation can change them. They cannot downgrade
policy. Effective read/use authorization derives from immutable event sensitivity plus
current HumanOS policy; payload sensitivity must equal event sensitivity. Operational
metadata changes require governed lifecycle code and new operational evidence.

### TOMBSTONED / ERASED state

At `ERASE.COMPLETED`, governed persistent copies of the following must be absent or
cryptographically inaccessible under the accepted deletion contract:

- plaintext payload bytes;
- payload ciphertext/key material required to recover them;
- `content_hash`, `content_hash_version`, and `content_integrity_key_id` for the erased
  LIVE proof unless later explicitly proven deletion-safe;
- idempotency `request_fingerprint`, version and key selector;
- usable payload `key_ref` / wrapper;
- `storage_ref` resolving recoverable content;
- payload-derived projection/cache/search/vector/summary artifacts.

The payload row may retain only content-free structural evidence such as:

```text
object_id
 event_id
 lifecycle_state = ERASED
 deleted_at
 deletion_id
```

---

## 4. Atomic event / payload / idempotency commit

For the LN-1 V1 first vertical slice, the authoritative capture unit is one local
SQLCipher/SQLite transaction owned by the Ingestor.

Within one `BEGIN IMMEDIATE`-equivalent transaction, HumanOS must:

1. resolve authenticated effective source identity and normalized retry token;
2. check/reserve the idempotency tuple;
3. allocate global `seq`, `event_id` and `payload_object_id`;
4. persist encrypted payload + LIVE integrity state;
5. persist immutable kernel event referencing that exact payload;
6. persist authoritative idempotency binding and LIVE fingerprint proof state;
7. persist any same-transaction outbox/commit marker required by capture;
8. commit once.

Required crash semantics:

- failure/process death before commit leaves no durable event, LIVE payload, consumed
  sequence or authoritative idempotency reservation;
- retry after pre-commit failure may capture normally;
- commit then crash before acknowledgement is a completed capture; retry returns the
  original event/object and never creates a second event;
- projection/enrichment occurs after authoritative commit; failure cannot roll back or
  duplicate capture;
- uncertain event/payload/idempotency linkage is `RECOVERY_REQUIRED`, never silent
  success.

Authoritative payload bytes outside this transactional store require a separate
reviewed durability protocol and cannot weaken these observable semantics.

---

## 5. Idempotency and duplicate-conflict semantics

The primary namespace is source identity, not content address:

```text
(effective_source_id, ingestion_id)
```

`effective_source_id` is resolved by HumanOS from authenticated principal/source
identity and policy. `ingestion_id` is the bounded opaque retry token admitted by the
immutable metadata rule. Caller claims cannot widen the namespace.

### LIVE fingerprint proof

A LIVE idempotency row contains at least:

```text
event_id
payload_object_id        # nullable only for a legitimately payload-less event
lifecycle_state
request_fingerprint
request_fingerprint_version
request_fingerprint_key_id
```

V1 fingerprint contract:

```text
request_fingerprint_version = hmac-sha256-capture-request-v1

request_fingerprint_envelope = {
  effective_source_id,
  ingestion_id,
  capture_request_schema_version,
  normalized_source_claims,
  payload_present,
  payload_size_bytes,
  request_fingerprint_version,
  request_fingerprint_key_id
}

request_fingerprint = HMAC-SHA-256(
    K_idempotency[request_fingerprint_key_id],
    "HumanOS CaptureRequestV1\0" ||
    JCS(request_fingerprint_envelope) || "\0" || exact_payload_bytes
)
```

`normalized_source_claims` means the complete versioned set of source-supplied semantic
claims accepted by the capture-request schema, canonicalized for fingerprint input.
It is MAC input, not separately persisted inside immutable kernel history. The
fingerprint excludes host-assigned `seq`, `event_id`, `payload_object_id`, ingest time,
resolved authority labels, and other values that are outputs of HumanOS processing
rather than source submission. Thus the proof preserves promoted V-03 semantics:
same source tuple + same semantic submission is the same request; same tuple + changed
payload or source-supplied semantic claims is conflicting reuse.

The exact persisted fingerprint selector and version are authenticated because they
are included inside the fingerprint envelope. Verification resolves exactly
`request_fingerprint_key_id`; unknown, unavailable, malformed, or otherwise
unresolvable selectors fail closed. No guessing, try-all or default/current-key
fallback is permitted.

The exact generation/custody/rotation mechanism for `K_idempotency` belongs to the Key
Custody ADR, which must preserve historical LIVE verification for every still-LIVE
fingerprint proof.

### LIVE behavior

- same idempotency tuple + valid same fingerprint -> return existing event/object;
- same tuple + different fingerprint -> fail closed as conflicting reuse;
- invalid/unverifiable stored fingerprint proof -> `RECOVERY_REQUIRED` / fail closed;
- distinct tuple -> normal new capture.

Before returning an existing LIVE event, HumanOS verifies the authoritative event,
payload linkage/integrity where present, and stored fingerprint proof rather than
trusting the idempotency row in isolation.

### After `ERASE.COMPLETED`

`request_fingerprint`, `request_fingerprint_version` and
`request_fingerprint_key_id` are deleted together. The idempotency tuple remains bound
to historical `event_id` / `payload_object_id` with state `ERASED`.

A later retry using that tuple:

- returns truthful ERASED identity;
- performs no payload-equality/content comparison;
- recreates no payload bytes;
- creates no new event under that tuple;
- requires an explicit new ingestion identity for a genuinely new capture.

---

## 6. Event-chain validity after payload erasure

Authorized payload erasure never modifies the original `NotebookEventV1`. Because its
hash covers immutable structural fields plus opaque `payload_object_id`, chain
verification remains valid after payload deletion.

Deletion is new evidence:

```text
ERASE.REQUESTED
  -> authorization
  -> PAYLOAD.TOMBSTONE
  -> fan-out / recomputation
  -> verification
  -> ERASE.COMPLETED
```

Failure records `ERASE.RECOVERY_REQUIRED`; no history rewrite is permitted merely to
make deletion pass.

---

## 7. V-04 ErasureTag reconciliation

Promoted V-04 ErasureTag remains a separate deletion-verification primitive:

```text
ErasureTag = HMAC(deletion_specific_key, canonical_deleted_bytes)
```

with a deletion-specific key derived from HumanOS-held erasure secret + `deletion_id`
and the promoted match-length/sliding-window scan contract.

Rules:

1. ErasureTag is not `payload_commitment`.
2. ErasureTag is not part of original event hash.
3. No ordinary plaintext SHA/content digest is stored alongside it.
4. Erasure secret/derived keys are not stored in Notebook DB, deletion receipt,
   restored backup, or provider-visible material.
5. ErasureTag exists only for deletion/restore verification under V-04.
6. Historical erasure-secret custody/rotation belongs to Key Custody ADR.

---

## 8. Backup / export / restore implications

An old backup cannot become LIVE merely because its SQLCipher key is valid.

Every restored Notebook enters `RESTORING` quarantine before any public content path.
Before LIVE transition HumanOS must:

1. verify kernel/checkpoint integrity;
2. verify every surviving LIVE event↔payload binding, payload MAC and exact historical
   `content_integrity_key_id` resolution;
3. verify each surviving LIVE idempotency fingerprint proof and exact historical
   `request_fingerprint_key_id` resolution;
4. load authoritative deletion identities/checkpoint state;
5. replay missing tombstones;
6. remove/invalidate payload bytes, payload keys/wrappers, content hashes/selectors,
   request fingerprints/selectors and derived artifacts for erased objects;
7. run V-04 all-store ErasureTag scan under correct retained erasure authority;
8. verify zero unresolved derivatives;
9. verify deletion receipt/checkpoint consistency;
10. only then transition to LIVE.

`ERASE.COMPLETED` may be asserted only for the backup/export scope covered by accepted
deletion policy. Any governed backup that can restore deleted content without mandatory
tombstone reconciliation is an unresolved derivative.

Backup product behavior remains outside the first LN-1 capture vertical slice. If
export/restore is included, destination encryption, correct/wrong-key behavior,
quarantine, LIVE integrity proof verification, and deletion reconciliation must all be
tested.

---

## 9. Legacy Runtime 0.1 migration implications

Runtime 0.1 contains legacy naked SHA-256 transcript rows and newer keyed-HMAC
integrity rows. They are source-side migration evidence and are not copied blindly into
immutable LN-1 events.

Migration rules:

1. verify legacy/source row under its existing content and record-envelope rules;
2. preserve exact verified payload bytes;
3. normalize new immutable metadata under the content-free rule; inadmissible
   descriptive metadata becomes erasable payload/provenance;
4. create encrypted payload + LIVE content MAC bound to new object/event IDs and exact
   `content_integrity_key_id`;
5. create structural event with `payload_commitment = null`;
6. create LIVE idempotency proof under the same versioned fingerprint/key-selector
   contract when migration uses a retryable ingestion identity;
7. preserve source-to-target mapping without embedding legacy plaintext digest into
   immutable event;
8. commit target event/payload/idempotency atomically;
9. keep legacy source read-only during parity/cutover;
10. before future erase completion, Migration/Cutover must define how retained legacy
    rollback sources/digests are deleted, made cryptographically inaccessible, or
    otherwise prevented from resurrecting erased content.

This is not permission to alter owner Notebook data.

---

## 10. Consequences

### Positive

- immutable chronology survives payload deletion without rewriting;
- immutable metadata cannot be an unchecked content side channel;
- LIVE payload integrity detects byte, identity, metadata and key-selector tamper;
- LIVE idempotency equality/conflict remains deterministic across key rotation;
- crash/retry has one explicit authoritative commit boundary;
- no normal plaintext-derived payload digest must survive erase;
- V-04 ErasureTag remains deletion-specific;
- storage/encryption representation can evolve without invalidating event hashes;
- legacy digests do not become permanent LN-1 liabilities.

### Costs

- original event hash does not commit to plaintext payload bytes;
- payload integrity and idempotency proof are separate erasable lifecycle proofs;
- source metadata requires normalization/indirection before becoming immutable;
- first LN-1 capture keeps authoritative event/payload/idempotency state in one
  transactional store; external authoritative blob storage needs a later protocol;
- historical LIVE verification requires historical payload-integrity and idempotency
  keys while corresponding proof state remains LIVE;
- restore depends on authoritative deletion checkpoint continuity;
- exact key generation/custody/rotation/recovery remains a mandatory next ADR;
- migration/cutover must handle retained legacy rollback databases explicitly.

---

## 11. Rejected alternatives

- **Permanent SHA-256 plaintext commitment:** dictionary-testable after erase.
- **Permanent keyed plaintext MAC in original event:** couples event verification to
  payload-derived key lifecycle.
- **Ciphertext hash in original event:** couples chronology to storage representation.
- **Rewriting old event after erase:** breaks append-only history/chain.
- **Content-addressed payload identity/cross-event dedup:** conflicts with independent
  per-event deletion; deferred until fully proven.
- **Source descriptive metadata in immutable envelope:** erasure bypass and source
  authority escalation path.
- **Independent event/payload commits with best-effort cleanup:** ambiguous crash state.
- **Unauthenticated/default payload integrity key selection:** rotation/downgrade gap.
- **Unversioned/default idempotency fingerprint key selection:** false conflict,
  fallback and downgrade ambiguity across rotation.

---

## 12. Required implementation tests

LN-1 implementation must include at least:

1. payload byte tamper fails LIVE verification;
2. any event-hash-envelope field tamper fails chain verification;
3. LIVE payload object/event identity or bound metadata swap/tamper fails;
4. unknown/unavailable payload integrity key ID fails closed with no fallback;
5. older LIVE payload still verifies after current content-integrity key rotates;
6. event↔payload linkage verifies both directions and rejects orphan/missing rows;
7. exact UTF-8/binary bytes survive write/read/reopen without normalization;
8. operational storage/key metadata change cannot downgrade effective authorization;
9. unapproved content in immutable metadata is rejected or moved to erasable state;
10. same LIVE idempotency tuple + same exact semantic submission returns same event;
11. same tuple + payload or source-claim change fails closed as conflict;
12. request fingerprint version/key-ID tamper fails verification;
13. unknown/unavailable request-fingerprint key ID fails closed with no fallback;
14. older LIVE request fingerprint still verifies after current idempotency key rotates;
15. pre-commit crash leaves no event/payload/sequence/idempotency reservation;
16. commit-before-ack crash retries to same event without duplicate;
17. post-commit projection failure does not alter/duplicate capture;
18. after erase, payload MAC state and request fingerprint proof state are absent while
    original event chain still verifies;
19. retry after erase returns historical ERASED identity and never recreates payload;
20. V-04 ErasureTag scan still detects erased bytes embedded in larger persistent
    values under promoted sliding-window/match-length contract;
21. restore stays quarantined until event/payload/idempotency/key-version and deletion
    checkpoint/receipt/tag reconciliation succeeds;
22. pre-erasure restore cannot become LIVE with recoverable erased payload;
23. migration copies neither legacy naked hashes nor inadmissible descriptive metadata
    into immutable new events;
24. no owner Notebook data is used in these tests.

---

## 13. Open dependencies — intentionally not resolved here

Still required before LN-1 implementation:

- SQLCipher Runtime Binding + Key Custody ADR;
- exact kernel/content/idempotency/erasure key generation, wrapping, storage, rotation,
  recovery and historical-key retention satisfying authenticated key-ID contracts;
- authoritative deletion-checkpoint storage/recovery location;
- controlled Migration / Cutover Plan;
- production integration qualification before a LIVE writer is trusted with owner data.

---

## 14. Promotion gates

ADR-LN-014 is accepted for PRE-LN-1 use only when:

1. a fresh clean architecture/security review of this remediated candidate finds no
   unresolved schema-blocking deletion, integrity, key-version, metadata-smuggling,
   atomicity, idempotency, restore or migration defect;
2. corrections are committed/read back;
3. fresh CI at the reviewed branch head passes;
4. exact reviewed ADR commit and review evidence are recorded;
5. Jon explicitly approves ADR-LN-014.

Until then it is a candidate and does not authorize LN-1 implementation.
