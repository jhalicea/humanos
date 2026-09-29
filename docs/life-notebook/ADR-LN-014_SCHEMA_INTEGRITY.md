# ADR-LN-014 — Notebook Event / Payload Integrity and Erasure Boundary

**Status:** CANDIDATE — PRE-LN-1 REVIEW REQUIRED  
**Date:** 2026-09-29  
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
- idempotency and conflict detection must still behave truthfully;
- restore must not resurrect erased payloads;
- the promoted V-04 ErasureTag contract must remain valid;
- existing Runtime 0.1 integrity behavior must be migrated, not blindly copied.

The current Runtime 0.1 already uses keyed HMAC-SHA-256 content/record integrity for
new transcript rows and a separate append-only event hash chain. LN-1 should preserve
the useful separation between record integrity and event chronology while removing
payload-derived values from the immutable event chain.

## Decision summary

LN-1 V1 separates **immutable event integrity** from **erasable payload integrity**.

1. `NotebookEventV1.event_hash` authenticates only the immutable structural event
   envelope plus `prev_event_hash`.
2. The immutable event binds to its payload by opaque `payload_object_id`, not by a
   permanent plaintext-derived digest.
3. `NotebookEventV1.payload_commitment` is **NULL / unused in LN-1 V1**. No content
   commitment is retained in the original immutable event.
4. Payload integrity while the payload exists is enforced inside `PayloadObjectV1`
   using keyed content integrity plus authenticated encryption. That content-derived
   integrity value is erasable state and is removed at authorized erase completion.
5. Idempotency is source-identity based. A payload-derived request fingerprint may be
   used only while the payload is LIVE; it is removed at erase completion. A retry of
   an erased idempotency key returns the tombstoned/erased identity and never silently
   recreates the payload.
6. V-04 ErasureTags remain a separate deletion-verification mechanism. They are not
   original-event payload commitments and are never ordinary plaintext hashes.
7. Restore is quarantined until authoritative deletion state has been reconciled and
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

### LIVE state

While the payload is LIVE:

- bytes are stored only in the approved encrypted payload representation;
- authenticated encryption provides cryptographic integrity for stored ciphertext;
- `content_hash` is a versioned keyed HMAC over the canonical payload bytes, using a
  HumanOS-owned content-integrity key distinct in purpose from the event-chain key;
- `content_hash` is used for read-back verification and duplicate/conflict detection;
- it is stored only in erasable payload/idempotency state, never copied into immutable
  kernel history, receipts, projections, or public routing metadata.

Candidate format:

```text
content_hash_version = hmac-sha256-payload-content-v1
content_hash = HMAC-SHA-256(
    K_payload_integrity[content_integrity_key_id],
    "HumanOS PayloadObjectV1\0" || canonical_payload_bytes
)
```

The exact key custody/rotation mechanism is deferred to the Key Custody ADR, but the
semantic separation is fixed here.

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
content-derived fingerprint.

---

## 4. Idempotency and duplicate-conflict semantics

Idempotency identity is source-based, not content-addressed.

The primary key is the trusted source tuple:

```text
(source_system, source_instance, ingestion_id)
```

The Ingestor owns normalization and reservation of this tuple. A source cannot use an
idempotency value to self-assign kernel sequence, authority, or event hash.

### While payload is LIVE

The idempotency record may contain:

- event_id;
- payload_object_id;
- lifecycle state;
- a keyed transient `request_fingerprint` covering the normalized capture request,
  including payload bytes where applicable.

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

## 5. Event-chain validity after payload erasure

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

## 6. V-04 ErasureTag reconciliation

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

## 7. Backup / export / restore implications

An old backup cannot be treated as LIVE merely because its SQLCipher key is valid.

### Restore quarantine

Every restored Notebook enters `RESTORING` / quarantined state before any public
content path is enabled.

Before transition to LIVE, HumanOS must reconcile the restored data against an
authoritative deletion checkpoint that is at least as recent as the restore target's
known deletion frontier.

The restore process must:

1. verify kernel/checkpoint integrity;
2. load authoritative deletion identities/checkpoint state;
3. replay tombstones missing from the restored snapshot;
4. remove/invalidate payload bytes, payload keys/wrappers, content hashes, transient
   request fingerprints, and derived artifacts for erased objects;
5. run the V-04 all-store ErasureTag scan under the correct retained erasure-key
   authority;
6. verify zero unresolved derivatives;
7. verify deletion receipt/checkpoint consistency;
8. only then transition to LIVE.

### Completion and backup scope

`ERASE.COMPLETED` may be asserted only for the backup/export set covered by the
accepted deletion policy. A governed backup that can still restore deleted content
without mandatory tombstone reconciliation is an unresolved derivative and blocks
completion for that scope.

For LN-1, backup product behavior remains outside the first capture vertical slice.
If export/restore is included, the destination must be separately encrypted and the
acceptance tests must prove correct-key restore, wrong-key rejection, restore
quarantine, and deletion reconciliation.

The exact durable location/custody of the authoritative deletion checkpoint belongs
to the Key Custody / backup ADR and the controlled Migration/Cutover Plan.

---

## 8. Legacy Runtime 0.1 migration implications

Runtime 0.1 contains both legacy naked SHA-256 transcript rows and newer keyed-HMAC
integrity rows. Those values are source-side migration evidence; they are **not**
blindly copied into immutable LN-1 kernel events.

Migration rules:

1. verify the legacy/source row using its existing integrity rules before mapping;
2. copy exact payload bytes into the new encrypted payload object;
3. compute the LN-1 live `content_hash` under the new payload-integrity key;
4. create the new structural kernel event with `payload_commitment = null`;
5. preserve source-to-target identity mapping without embedding the old plaintext
   digest into the new immutable event;
6. keep the legacy source read-only during parity/cutover verification;
7. before any future erase is called complete, the controlled migration/cutover plan
   must define how retained legacy rollback sources and their old digests are either
   deleted, cryptographically made inaccessible, or otherwise kept from resurrecting
   erased content.

This is a migration dependency, not permission to alter the existing owner Notebook.

---

## 9. Consequences

### Positive

- immutable chronology survives payload deletion without event rewriting;
- event verification does not depend on content that policy may later erase;
- no normal plaintext-derived payload digest needs to remain after erase;
- source-based idempotency remains truthful after content fingerprint removal;
- V-04 ErasureTag remains usable for deletion verification;
- storage/key locations can evolve without invalidating historical event hashes;
- legacy digest formats do not become permanent LN-1 privacy liabilities.

### Costs

- original event hashes do not cryptographically commit to plaintext payload bytes;
- payload/content verification is therefore a separate lifecycle proof rather than a
  single permanent event-chain proof;
- restore depends on durable deletion checkpoint continuity;
- historical event-integrity and erasure-key verification requires key-version
  custody/rotation design in the next ADR;
- migration/cutover must explicitly handle retained legacy rollback databases.

This separation is intentional: HumanOS chooses erasability over permanent
content-addressed proof for owner-controlled payloads.

---

## 10. Rejected alternatives

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

---

## 11. Required implementation tests derived from this ADR

LN-1 implementation must include at least:

1. changing payload bytes while the LIVE payload row remains otherwise valid causes
   payload-integrity/read-back verification failure;
2. changing any event-hash-envelope field causes event-chain verification failure;
3. changing storage/key metadata alone does not require rewriting the original event;
4. duplicate retry while LIVE returns the same event only when the transient keyed
   request fingerprint matches;
5. conflicting reuse while LIVE fails closed;
6. after erase, the content hash and request fingerprint are absent and the original
   event chain still verifies;
7. retry after erase returns the historical erased identity and never recreates the
   payload;
8. V-04 ErasureTag scanning still detects erased bytes embedded in larger persistent
   values under the promoted sliding-window/match-length contract;
9. restore remains quarantined until deletion checkpoint/receipt/tag reconciliation
   succeeds;
10. a restored pre-erasure snapshot cannot become LIVE with recoverable erased payload;
11. migration does not copy legacy naked/plaintext-derived hashes into immutable new
   events;
12. no owner Notebook data is used in these tests.

---

## 12. Open dependencies — intentionally not resolved here

This ADR does not close the remaining PRE-LN-1 gates.

Still required:

- SQLCipher Runtime Binding + Key Custody ADR;
- exact kernel/content/erasure key generation, wrapping, storage, rotation, recovery,
  and historical-key retention policy;
- authoritative deletion-checkpoint storage/recovery location;
- controlled Migration / Cutover Plan;
- production integration qualification before a LIVE writer is trusted with owner data.

---

## 13. Promotion gates

This ADR is accepted for PRE-LN-1 use only when:

1. an independent architecture/security review finds no unresolved schema-blocking
   deletion, integrity, idempotency, restore, or migration defect;
2. required corrections are committed and read back;
3. the reviewed commit is recorded in `HOS-LN-001`;
4. Jon explicitly approves this ADR.

Until then it is a candidate and does not authorize LN-1 implementation.
