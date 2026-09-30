# ADR-LN-014 — Notebook Event / Payload Integrity and Erasure Boundary

**Status:** CANDIDATE — REVIEW BLOCKERS REMEDIATED / FRESH REVIEW REQUIRED  
**Date:** 2026-09-30  
**Workstream:** `HOS-LN-001`  
**Baseline:** `life-notebook-ln0` at `85e0308e19a9c145fa44bd922c2010bd87675658`

## Context

LN-0 is CLOSED / IMPLEMENTATION-READY, but LN-1 implementation is blocked on a
mandatory Schema / Integrity ADR. The unresolved design problem is subtle:

- the kernel event chain must remain immutable and verifiable;
- payload bytes must be independently erasable;
- authorized erase must not require rewriting old kernel events;
- no ordinary plaintext-derived payload digest may survive `ERASE.COMPLETED` in a
  governed persistent store;
- immutable metadata must not become a covert channel for erasable content;
- idempotency and conflict detection must still behave truthfully;
- event, payload and idempotency state must survive crash boundaries without hidden
  partial commits;
- restore must not resurrect erased payloads;
- the promoted V-04 ErasureTag contract must remain valid;
- existing Runtime 0.1 integrity behavior must be migrated, not blindly copied.

The current Runtime 0.1 already uses keyed HMAC-SHA-256 content/record integrity for
new transcript rows and binds record metadata together with the content digest. LN-1
preserves that useful separation between record integrity and event chronology while
removing payload-derived values from the immutable event chain.

The first independent review of this ADR found three reproducible blockers: LIVE
payload integrity did not bind event/object identity, event/payload/idempotency atomic
creation was not explicit, and immutable metadata was not constrained to content-free
values. This revision remediates those findings without changing the central erasure
model.

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
   exact event/object identity plus immutable payload metadata. That content-derived
   integrity value is erasable state and is removed at authorized erase completion.
6. The authoritative idempotency reservation, payload object and kernel event are
   committed as one LN-1 V1 durable transaction. Crash/retry semantics preserve the
   already-proven V-03 rule: no partial pre-commit identity and no duplicate event
   after commit-before-ack.
7. Idempotency is source-identity based. A payload-derived request fingerprint may be
   used only while the payload is LIVE; it is removed at erase completion. A retry of
   an erased idempotency key returns the tombstoned/erased identity and never silently
   recreates the payload.
8. V-04 ErasureTags remain a separate deletion-verification mechanism. They are not
   original-event payload commitments and are never ordinary plaintext hashes.
9. Restore is quarantined until authoritative deletion state has been reconciled and
   all erased objects remain erased.

This design lets HumanOS preserve immutable chronology while giving payload deletion a
real lifecycle boundary.

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

`JCS(...)` means RFC 8785 JSON Canonicalization Scheme. The production implementation
must use one verified canonicalization implementation and test cross-process stable
bytes before live use.

The key is HumanOS-owned and never stored in the event row. Key custody, wrapping,
rotation, recovery, and historical key availability are governed by the separate
PRE-LN-1 SQLCipher Runtime Binding + Key Custody ADR.

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
  user-entered label, message body fragment or other content-bearing locator is not
  eligible for immutable storage;
- `ingestion_id` is a bounded retry token. If a provider/source-native ID contains
  user content or sensitive descriptive text, HumanOS stores an internal opaque retry
  identity in the immutable/idempotency plane and keeps the original source-native
  value only in erasable payload/provenance state.

If a capture source tries to place arbitrary content into an immutable field, the
Ingestor must reject it or move it into governed erasable payload state. Source claims
cannot manufacture permanent metadata merely by naming a field.

This is both a deletion rule and a source-authority rule: payload erasure must not be
bypassed by metadata smuggling.

### Capture status rule

`capture_status_at_commit` is immutable. In LN-1 V1 the original kernel event records
the durable commit state only. Later read-back/checkpoint/recovery progress is recorded
by separate transaction/checkpoint/recovery evidence rather than mutating the original
event row.

This preserves the existing HumanOS rule that a later verification state cannot be
fabricated by editing earlier evidence.

### Explicitly excluded from the immutable event hash

The original event hash MUST NOT include:

- plaintext payload bytes;
- `content_hash` or any ordinary plaintext digest;
- ciphertext bytes or a ciphertext digest;
- payload encryption nonce/tag/material;
- `key_ref`;
- `storage_ref`;
- payload `size_bytes`;
- payload lifecycle state;
- `deleted_at`;
- deletion receipt contents;
- V-04 ErasureTag;
- projection/cache identifiers;
- mutable backup/export location metadata.

Those values are either erasable, operational, storage-specific, or belong to a
separate lifecycle.

---

## 2. `payload_commitment` decision

`NotebookEventV1.payload_commitment` remains present as an optional schema slot but is
**NULL in LN-1 V1**.

Rationale:

- a normal content hash violates the post-erasure privacy contract;
- a keyed content MAC would couple original event verification to payload/key
  lifecycle and complicate key deletion/rotation;
- a ciphertext hash couples the immutable event to storage/encryption representation;
- an opaque random value adds no integrity property beyond the already unique
  `payload_object_id`.

The original event therefore commits only to the existence/identity of one payload
slot through `payload_object_id`.

A future non-null payload commitment requires a separate ADR, explicit deletion proof,
migration plan, and regression tests. It must not be introduced as a silent schema
extension.

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
 created_at
 deleted_at
```

`object_id` and `event_id` survive erasure as structural identity. Content-bearing or
content-derived fields do not.

### One-to-one structural binding

LN-1 V1 requires a verifiable one-to-one binding:

```text
event.payload_object_id == payload.object_id
payload.event_id         == event.event_id
```

For an event with a payload:

- `object_id` is unique and never reassigned;
- `event_id` is unique in the payload table;
- a payload object cannot be rebound to another event;
- an event cannot acquire a second payload object;
- an event row referencing a missing/mismatched payload fails verification while the
  lifecycle says a payload should exist;
- an orphan LIVE payload fails verification.

The SQL implementation must enforce the one-to-one relation with primary/unique and
foreign-key constraints or an equivalently strong fail-closed invariant. The verifier
must check both directions rather than trusting only one stored pointer.

### Exact payload-byte rule

`content_hash` authenticates the **exact logical bytes that HumanOS durably stores as
the payload**, not a later semantic reserialization.

- text capture uses the exact captured UTF-8 bytes; no Unicode normalization,
  newline rewriting or whitespace normalization is performed by the integrity layer;
- binary/file capture uses the exact captured bytes;
- structured capture is serialized once by a versioned capture codec before the
  durable transaction; the exact resulting bytes are stored and later verified;
- a verifier never parses and reserializes arbitrary payload content to recreate the
  integrity input.

Any future alternate codec changes the payload/content-integrity version and requires
migration/compatibility tests.

### LIVE state

While the payload is LIVE:

- bytes are stored only in the approved encrypted payload representation;
- authenticated encryption provides cryptographic integrity for stored ciphertext;
- `content_hash` is a versioned keyed HMAC that binds exact payload identity and
  immutable payload metadata to the exact persisted payload bytes;
- `content_hash` is used for read-back verification and duplicate/conflict detection;
- it is stored only in erasable payload/idempotency state, never copied into immutable
  kernel history, receipts, projections, or public routing metadata.

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
  created_at
}

content_hash = HMAC-SHA-256(
    K_payload_integrity[content_integrity_key_id],
    "HumanOS PayloadObjectV1\0" ||
    JCS(payload_integrity_envelope) || "\0" || exact_payload_bytes
)
```

This closes the payload-swap gap: moving otherwise valid bytes under a different
`object_id` or `event_id`, changing bound immutable payload metadata, or changing the
payload bytes must fail LIVE payload-integrity verification.

`encryption_scope`, `key_ref` and `storage_ref` are intentionally excluded from this
content MAC because authorized re-encryption/storage relocation may change them. They
are not trusted to downgrade policy. Read/use authorization is derived from the
immutable event `sensitivity_class` and current HumanOS policy; payload
`sensitivity_class` must equal the event value. Changes to operational encryption or
storage metadata must be performed by governed lifecycle code and recorded as new
operational evidence.

The exact key custody/rotation mechanism remains deferred to the Key Custody ADR, but
the semantic separation and identity binding are fixed here.

### TOMBSTONED / ERASED state

At authorized erase completion all governed persistent copies of the following must
be absent or cryptographically inaccessible under the accepted deletion contract:

- plaintext payload bytes;
- payload ciphertext/key material required to recover those bytes;
- `content_hash`;
- transient request fingerprint;
- `key_ref` / usable payload-key wrapper;
- `storage_ref` that still resolves to recoverable payload content;
- payload-derived projection/cache/search/vector/summary artifacts.

The payload row may retain only content-free structural evidence such as:

```text
object_id
 event_id
 lifecycle_state = ERASED
 deleted_at
 deletion_id
```

Any additional retained field must separately prove that it is not a prohibited
content-derived fingerprint or user-content surrogate.

---

## 4. Atomic event / payload / idempotency commit

For the LN-1 V1 first vertical slice, the authoritative capture unit is one local
SQLCipher/SQLite transaction owned by the Ingestor.

Within one `BEGIN IMMEDIATE`-equivalent transaction, HumanOS must:

1. resolve the authenticated effective source identity and normalized retry token;
2. check/reserve the idempotency tuple;
3. allocate the global `seq`, `event_id` and `payload_object_id`;
4. persist the encrypted payload object and its LIVE integrity state;
5. persist the immutable kernel event referencing that exact payload object;
6. persist the authoritative idempotency binding to that event/object;
7. persist any same-transaction outbox/commit marker required by the capture contract;
8. commit once.

Required crash semantics:

- failure or process death before commit leaves no durable event, LIVE payload object,
  consumed sequence or authoritative idempotency reservation;
- retry after a pre-commit failure may perform the capture normally;
- commit followed by crash before acknowledgement is a completed capture; retry of the
  same idempotency tuple returns the original event/object and never creates a second
  event;
- projections/enrichment occur after the authoritative commit and their failure does
  not roll back or duplicate the captured event;
- any implementation state where event/payload/idempotency linkage is uncertain is
  `RECOVERY_REQUIRED`, never silently treated as success.

A future design that stores authoritative payload bytes outside the same transactional
store requires a separate reviewed durability protocol (for example staged durable
object + commit marker/outbox) and may not weaken these observable semantics.

---

## 5. Idempotency and duplicate-conflict semantics

Idempotency identity is source-based, not content-addressed.

The primary namespace is:

```text
(effective_source_id, ingestion_id)
```

`effective_source_id` is resolved by HumanOS from authenticated source/principal
identity and policy. It is not a caller-supplied authority claim. `ingestion_id` is the
HumanOS-normalized bounded retry token described by the immutable metadata rule.
`source_system` / `source_instance` remain provenance fields but cannot widen or
replace the authenticated idempotency namespace.

### While payload is LIVE

The idempotency record may contain:

- event_id;
- payload_object_id;
- lifecycle state;
- a keyed transient `request_fingerprint` covering the normalized capture request,
  including exact payload bytes where applicable.

Behavior:

- same idempotency tuple + same fingerprint -> return the existing event/object;
- same tuple + different fingerprint -> fail closed as conflicting reuse;
- distinct tuple -> normal new capture path.

### After `ERASE.COMPLETED`

The content-derived request fingerprint is deleted.

The idempotency tuple remains bound to the historical `event_id` and
`payload_object_id` with state `ERASED`.

Any later retry using that tuple:

- returns a truthful erased/tombstoned result referencing the historical identity;
- does not compare payload equality;
- does not recreate payload bytes;
- does not create a new event under the same idempotency tuple;
- requires an explicit new ingestion identity for a genuinely new capture.

This preserves retry safety without retaining a permanent payload fingerprint.

---

## 6. Event-chain validity after payload erasure

Authorized payload erasure does not modify the original `NotebookEventV1`.

Because the original event hash covers only immutable structural fields and the opaque
`payload_object_id`, event-chain verification remains valid after payload deletion.

The deletion lifecycle is represented by new evidence:

```text
ERASE.REQUESTED
  -> authorization
  -> PAYLOAD.TOMBSTONE
  -> fan-out / recomputation
  -> verification
  -> ERASE.COMPLETED
```

Failure records `ERASE.RECOVERY_REQUIRED` and never fabricates completion.

No kernel-history rewrite is permitted merely to make a deletion pass.

---

## 7. V-04 ErasureTag reconciliation

The promoted V-04 ErasureTag remains valid as a deletion-verification primitive:

```text
ErasureTag = HMAC(deletion_specific_key, canonical_deleted_bytes)
```

with the deletion-specific key derived from a HumanOS-held erasure secret and
`deletion_id`, plus the promoted `match_length` scanning contract.

Rules:

1. ErasureTag is **not** `payload_commitment`.
2. ErasureTag is **not** part of the original event hash.
3. No ordinary plaintext SHA/content digest is stored alongside it.
4. The erasure secret and derived keys are not stored in the Notebook database,
   deletion receipt, restored backup, or provider-visible material.
5. ErasureTag exists only for deletion/restore verification under the V-04 contract.
6. Historical erasure-secret custody/rotation required for restore verification is
   resolved by the Key Custody ADR.

This preserves V-04's ability to scan for erased bytes without turning immutable
kernel history into a dictionary-testable payload index.

---

## 8. Backup / export / restore implications

An old backup cannot be treated as LIVE merely because its SQLCipher key is valid.

### Restore quarantine

Every restored Notebook enters `RESTORING` / quarantined state before any public
content path is enabled.

Before transition to LIVE, HumanOS must reconcile the restored data against an
authoritative deletion checkpoint that is at least as recent as the restore target's
known deletion frontier.

The restore process must:

1. verify kernel/checkpoint integrity;
2. verify every surviving LIVE event↔payload one-to-one binding and LIVE payload MAC;
3. load authoritative deletion identities/checkpoint state;
4. replay tombstones missing from the restored snapshot;
5. remove/invalidate payload bytes, payload keys/wrappers, content hashes, transient
   request fingerprints, and derived artifacts for erased objects;
6. run the V-04 all-store ErasureTag scan under the correct retained erasure-key
   authority;
7. verify zero unresolved derivatives;
8. verify deletion receipt/checkpoint consistency;
9. only then transition to LIVE.

### Completion and backup scope

`ERASE.COMPLETED` may be asserted only for the backup/export set covered by the
accepted deletion policy. A governed backup that can still restore deleted content
without mandatory tombstone reconciliation is an unresolved derivative and blocks
completion for that scope.

For LN-1, backup product behavior remains outside the first capture vertical slice.
If export/restore is included, the destination must be separately encrypted and the
acceptance tests must prove correct-key restore, wrong-key rejection, restore
quarantine, payload-binding verification, and deletion reconciliation.

The exact durable location/custody of the authoritative deletion checkpoint belongs
to the Key Custody / backup ADR and the controlled Migration/Cutover Plan.

---

## 9. Legacy Runtime 0.1 migration implications

Runtime 0.1 contains both legacy naked SHA-256 transcript rows and newer keyed-HMAC
integrity rows. Those values are source-side migration evidence; they are **not**
blindly copied into immutable LN-1 kernel events.

Migration rules:

1. verify the legacy/source row using its existing content and record-envelope
   integrity rules before mapping;
2. preserve the exact legacy payload bytes used by the verified source row;
3. normalize only the new immutable metadata under the content-free rule; descriptive
   legacy metadata that is not admissible becomes erasable payload/provenance state;
4. create the new encrypted payload object and compute the LN-1 LIVE `content_hash`
   bound to its new `object_id`, new `event_id` and exact payload bytes;
5. create the new structural kernel event with `payload_commitment = null`;
6. persist source-to-target mapping without embedding the old plaintext digest into
   the new immutable event;
7. perform the target event/payload/idempotency authoritative commit under the same
   atomicity contract used for native LN-1 capture;
8. keep the legacy source read-only during parity/cutover verification;
9. before any future erase is called complete, the controlled migration/cutover plan
   must define how retained legacy rollback sources and their old digests are either
   deleted, cryptographically made inaccessible, or otherwise kept from resurrecting
   erased content.

This is a migration dependency, not permission to alter the existing owner Notebook.

---

## 10. Consequences

### Positive

- immutable chronology survives payload deletion without event rewriting;
- event verification does not depend on content that policy may later erase;
- immutable metadata cannot be used as an unchecked payload-content side channel;
- LIVE payload integrity detects object/event identity swaps as well as byte changes;
- crash/retry behavior has one explicit authoritative commit boundary;
- no normal plaintext-derived payload digest needs to remain after erase;
- source-based idempotency remains truthful after content fingerprint removal;
- V-04 ErasureTag remains usable for deletion verification;
- storage/key locations can evolve without invalidating historical event hashes;
- legacy digest formats do not become permanent LN-1 privacy liabilities.

### Costs

- original event hashes do not cryptographically commit to plaintext payload bytes;
- payload/content verification is therefore a separate lifecycle proof rather than a
  single permanent event-chain proof;
- source metadata requires normalization/indirection before it may become immutable;
- the first LN-1 capture slice keeps its authoritative event/payload/idempotency state
  within one transactional store; external authoritative blob storage needs a later
  reviewed durability protocol;
- restore depends on durable deletion checkpoint continuity;
- historical event-integrity and erasure-key verification requires key-version
  custody/rotation design in the next ADR;
- migration/cutover must explicitly handle retained legacy rollback databases.

This separation is intentional: HumanOS chooses erasability over permanent
content-addressed proof for owner-controlled payloads.

---

## 11. Rejected alternatives

### Permanent SHA-256 of plaintext in `payload_commitment`

Rejected. Low-entropy payloads remain dictionary-testable after authorized erase.

### Permanent keyed HMAC of plaintext in the original event

Rejected for LN-1 V1. Although stronger than a normal digest, it still couples event
verification to long-lived payload-derived key material and complicates deletion,
rotation, and restore semantics. V-04 already provides a bounded deletion-specific
keyed verification mechanism.

### Hash of ciphertext in the original event

Rejected for LN-1 V1. It unnecessarily couples immutable chronology to a specific
storage/encryption representation and complicates re-encryption/migration.

### Rewriting the old event after payload erase

Rejected. It destroys the append-only historical property and changes all downstream
chain hashes.

### Content-addressed payload identity / cross-event deduplication

Rejected. It conflicts with independent per-event deletion and remains deferred until
there is a complete deletion-safe proof.

### Trusting source-provided descriptive metadata in the immutable envelope

Rejected. It creates an erasure bypass and source-authority escalation path.

### Independent event and payload commits with best-effort cleanup

Rejected for LN-1 V1. It allows ambiguous crash states and hidden divergence between
immutable event identity, payload existence and retry identity.

---

## 12. Required implementation tests derived from this ADR

LN-1 implementation must include at least:

1. changing payload bytes while the LIVE payload row remains otherwise valid causes
   payload-integrity/read-back verification failure;
2. changing any event-hash-envelope field causes event-chain verification failure;
3. changing a LIVE payload `object_id`, `event_id`, bound mime/size/sensitivity field,
   or swapping otherwise valid payload rows between events causes verification failure;
4. event→payload and payload→event one-to-one linkage is verified in both directions;
5. exact UTF-8/binary payload bytes survive write/read/reopen without normalization or
   semantic reserialization;
6. changing storage/key operational metadata alone does not require rewriting the
   original event or LIVE content MAC, but cannot downgrade effective authorization;
7. immutable metadata containing unapproved arbitrary source content is rejected or
   moved to erasable payload/provenance state before commit;
8. duplicate retry while LIVE returns the same event only when the transient keyed
   request fingerprint matches;
9. conflicting reuse while LIVE fails closed;
10. crash/process death before authoritative commit leaves no event, LIVE payload,
    consumed sequence or idempotency reservation;
11. crash after authoritative commit but before acknowledgement returns the same event
    on retry and does not create a duplicate;
12. projection/enrichment failure after commit does not alter or duplicate the capture;
13. after erase, the content hash and request fingerprint are absent and the original
    event chain still verifies;
14. retry after erase returns the historical erased identity and never recreates the
    payload;
15. V-04 ErasureTag scanning still detects erased bytes embedded in larger persistent
    values under the promoted sliding-window/match-length contract;
16. restore remains quarantined until event/payload integrity plus deletion
    checkpoint/receipt/tag reconciliation succeeds;
17. a restored pre-erasure snapshot cannot become LIVE with recoverable erased payload;
18. migration does not copy legacy naked/plaintext-derived hashes or inadmissible
    descriptive metadata into immutable new events;
19. no owner Notebook data is used in these tests.

---

## 13. Open dependencies — intentionally not resolved here

This ADR does not close the remaining PRE-LN-1 gates.

Still required:

- SQLCipher Runtime Binding + Key Custody ADR;
- exact kernel/content/erasure key generation, wrapping, storage, rotation, recovery,
  and historical-key retention policy;
- authoritative deletion-checkpoint storage/recovery location;
- controlled Migration / Cutover Plan;
- production integration qualification before a LIVE writer is trusted with owner data.

---

## 14. Promotion gates

This ADR is accepted for PRE-LN-1 use only when:

1. a fresh independent architecture/security review of the remediated candidate finds
   no unresolved schema-blocking deletion, integrity, metadata-smuggling, atomicity,
   idempotency, restore, or migration defect;
2. required corrections are committed and read back;
3. fresh CI at the reviewed commit passes;
4. the reviewed commit is recorded in `HOS-LN-001`;
5. Jon explicitly approves this ADR.

Until then it is a candidate and does not authorize LN-1 implementation.
