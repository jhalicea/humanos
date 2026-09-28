# Life Notebook LN-0 — Verification Plan

**Status:** ACTIVE / DESIGN-VERIFICATION PLAN  
**Date:** 2026-09-25  
**Workstream:** `HOS-LN-000`  
**Baseline:** `runtime-0.1` @ `0cf78d9abe5dcfcc6114bb43167dcf7406478657`

This plan converts the remaining architecture claims into evidence-producing verification packets before LN-1 implementation begins.

No packet may use Jon's active Life Notebook. All destructive/failure testing uses isolated temporary vaults and synthetic fixtures.

---

## Operating rule

A model recommendation is not evidence. A document is not implementation. Each packet must produce one of:

- executable test evidence;
- primary-source technical evidence tied to the tested behavior;
- an explicit unresolved result that blocks the dependent ADR.

If a packet fails, capture continues as architecture work; no implementation is allowed to silently work around the failed invariant.

---

# V-01 — Current-Schema Migration Fixture

## Question

Can the current Runtime 0.1 Life Notebook evidence be migrated into the new kernel/payload model without losing exact transcript, identity, recovery, privacy, or provenance information?

## Inputs

Create a synthetic current-schema vault containing representative rows for:

- `identities`;
- `transactions`;
- `transcript`;
- `tasks`;
- `events`;
- `recovery`;
- `privacy_state`;
- `privacy_operations`;
- `privacy_receipts`;
- page/index/binding projections;
- at least one incomplete/recovery-required transaction;
- at least one correction/privacy operation;
- at least one Universal Conversation Capture turn.

## Test cases

1. Exact HUMAN text survives byte-for-byte / Unicode-for-Unicode.
2. Exact ASSISTANT text survives byte-for-byte / Unicode-for-Unicode.
3. Message ordering and parent/session identity remain reconstructible.
4. Current HCID/page/transaction identities have an explicit stable mapping.
5. Recovery-required evidence remains recovery-required; migration cannot turn failure into success.
6. Privacy operations/receipts remain independently auditable.
7. Existing integrity/digest values remain preserved as legacy provenance even if the new kernel introduces a new integrity envelope.
8. Duplicate/retry identities do not become duplicate canonical events.
9. Projections can be regenerated from the migrated evidence or are explicitly classified as legacy-only artifacts.
10. Migration is repeatable/idempotent against the same source fixture.

## Pass condition

A machine-readable migration report proves every source row is either:

- migrated to one or more named target records;
- intentionally retained as legacy operational evidence;
- explicitly rejected with a blocking reason.

No source record disappears silently.

## Evidence artifact

`evidence/ln0/V-01-migration-fixture/` when executed.

## ADR dependency

Determines whether LN-1 uses:

- additive in-place schema evolution; or
- new encrypted DB + controlled migration/cutover.

---

# V-02 — Encrypted SQLite / SQLCipher Spike

## Question

What exact encrypted-SQLite configuration works safely with the existing HumanOS runtime requirements on the target Mac and supported CI platforms?

## Rules

Do not copy a model-generated pragma recipe into production. Verify against current primary SQLCipher/SQLite documentation and real execution.

## Test matrix

### Initialization

- correct key/init order opens and creates DB;
- wrong key fails closed;
- reopening with correct key succeeds;
- required compatibility/page/KDF settings are explicitly recorded;
- version is pinned for the experiment.

### WAL / sidecars

- WAL mode actually activates;
- DB, `-wal`, `-shm`, temporary artifacts, and backups are scanned for known plaintext fixtures;
- no known plaintext is present where the selected configuration claims encryption;
- crash/reopen works with WAL active.

### Crash

Kill the process at controlled points:

- before transaction commit;
- during write pressure;
- after commit before application acknowledgement;
- during checkpoint/backup where meaningful.

Verify committed data survives, uncommitted data does not appear as committed, and integrity/readback succeeds after restart.

### Backup / restore

- produce an encrypted backup using the supported method;
- restore on a clean isolated environment;
- wrong key fails;
- correct recovery material restores exact fixture evidence;
- tombstone state is preserved.

### Key recovery

Prototype the architecture:

```text
random HumanOS data key
  -> local OS-protected wrapper
  -> independent recovery wrapper
```

The experiment must demonstrate that a backup can be restored without the original machine's live local key store, while not placing the raw data key in Git/config/logs.

## Pass condition

A reproducible script/test plus technical note establishes the exact supported configuration and its known residual risks.

## Evidence artifact

`evidence/ln0/V-02-sqlcipher/` when executed.

## ADR dependency

Produces the evidence for `ADR-LN-013 — Encrypted SQLite implementation` and the key-custody ADR.

---

# V-03 — Ingestor Idempotency, Ordering, and Source Authority

## Question

Can multiple capture clients safely submit evidence through one authoritative writer without duplicate history, hash-chain races, or self-escalated authority?

## Fixture

Implement only a test/spike Ingestor contract against an isolated database. This packet does not authorize LN-1 production schema implementation.

## Test cases

1. Same HumanOS-resolved `(effective_source_id, ingestion_id)` + identical semantic submission fingerprint returns the original event.
2. Same HumanOS-resolved `(effective_source_id, ingestion_id)` + different semantic submission fingerprint fails closed.
3. Same payload under two different ingestion keys produces two distinct events.
4. 1,000 concurrent retry submissions cannot create duplicate canonical events.
5. Concurrent distinct submissions receive one monotonic global sequence.
6. Two events cannot claim the same previous kernel hash/sequence position.
7. A connector cannot set its own `seq`, event hash, owner-decision status, or verified epistemic class.
8. Source Authority Ceiling is applied by HumanOS, not trusted from caller input.
9. Crash after commit/before acknowledgement returns the committed result on retry.
10. Capture remains available if later State/projection processing is down.

## Pass condition

One deterministic commit path with measurable idempotency and no authority escalation.

## Evidence artifact

`evidence/ln0/V-03-ingestor/` when executed.

---

# V-04 — Tombstone Fan-Out / Deletion Dependency Contract

## Question

Can HumanOS delete authorized source content without leaving persistent copies in derived stores?

## Synthetic fixture

Create one source event that produces:

- timeline row;
- page fragment;
- summary;
- FTS entry;
- embedding/vector record;
- Knowledge Graph assertion/edge support;
- thumbnail or other binary derivative fixture;
- retrieval cache entry;
- ContextPacket body retained under a test TTL.

Also create:

- a multi-source derived fact supported by the soon-to-be-deleted event plus a second surviving event;
- an independently owner-ratified State event derived later from the same topic.

## Test cases

After tombstoning the source payload:

- sole-source summary disappears/is invalidated;
- FTS no longer returns deleted content;
- vector retrieval no longer returns deleted content;
- graph support sourced only from deleted evidence disappears;
- multi-source claim is recomputed from surviving evidence;
- independently ratified State survives only because it has its own source authority;
- binary derivatives/caches are removed;
- ContextPacket retained content obeys its deletion/TTL rule;
- the tombstone/audit record remains;
- a second identical-but-independent payload remains intact;
- backup restore replays tombstones before presenting live State.

## Pass condition

No persistent derived representation can return the deleted source text/bytes except audit metadata explicitly permitted by the deletion contract.

The audit contract is explicit: `ERASE.REQUESTED` -> authorization ->
`PAYLOAD.TOMBSTONE` -> fan-out/recomputation -> verification -> `ERASE.COMPLETED`.
Downstream failure must produce `ERASE.RECOVERY_REQUIRED`, never completion. A
content-free append-only `DeletionReceiptV1` must survive payload removal and restore,
prove authorization/completion and zero unresolved derivatives, and use an integrity
hash over receipt metadata only. It must not retain plaintext, PII, summaries,
embeddings, vectors, binary data, reversible encrypted content, or a normal hash of
low-entropy deleted content.

Attempt 4 additionally requires: explicit source/page/block/chronology and deletion
lifecycle provenance; requester/authorizer/executor separation; stable operation-level
idempotency; measured resolver counts; canonical receipt-chain recomputation with
mutation/deletion/reordering/insertion detection; verification of imported receipts
before tombstone replay and LIVE activation; a low-entropy dictionary-hash adversary;
and scanner coverage of every synthetic persistent table. Verification metadata is an
integrity-protected part of `DeletionReceiptV1`; no appearance-only store is added.
Semantic descriptors are not automatically retained.

Attempt 5 additionally requires bidirectional receipt/tombstone/lifecycle identity;
union reconciliation keyed by `deletion_id`; fail-closed missing, mismatching, or
duplicate evidence; truthful tombstone-without-receipt recovery before LIVE; a
separate immutable fixture anchor for receipt count, head hash, and final sequence;
detection of tail/whole-chain and anchor loss or mutation; and a HumanOS-owned
authenticator/policy resolver whose resolved requester/authorizer identities plus an
internal executor are the only authoritative receipt provenance. Required probes
`MISSING_TOMBSTONE_ACTIVATED`, `TAIL_DELETION_CHAIN_ACCEPTED`,
`EMPTY_CHAIN_ACCEPTED`, and `EMPTY_PRINCIPALS_ACCEPTED` must all fail closed.

Attempt 6 additionally requires the captured pre-erasure bytes to be scanned across
every synthetic persistent table before `ERASE.COMPLETED`, with an exception only for
the payload cell of explicitly identified independent source events. Unrelated
lineage cannot exempt a byte-identical cache or derivative. Every public content or
raw-database access path must reject reads while RESTORING. Receipt count, head hash,
and final sequence must match an independently supplied kernel/checkpoint expectation
outside the SQLite fixture, so coordinated receipt, projected-anchor, and completion
truncation fails receipt-chain verification. Attempts 1–5 remain rejected evidence.

Attempt 7 additionally replaces volatile retained bytes with an authoritative
secret-keyed ErasureTag held outside the restored Notebook database. The kernel/key
boundary supplies the secret independently; ordinary plaintext SHA-256, plaintext,
and the secret must not enter the receipt or restored DB. Before LIVE, restore must
execute checkpoint verification -> deletion-ledger reconciliation -> tombstone replay
-> fan-out -> all-store ErasureTag verification -> unresolved==0. Every public
content-returning or scanning API must require LIVE; internal verification uses
private helpers. Final all-store scan, receipt/checkpoint update, and
`ERASE.COMPLETED` must be atomic against persistent writers. Required adversaries are
an unlineaged old-backup copy after restart, exhaustive public RESTORING-path access,
a pre-scan forbidden write, and a synchronized second writer between scan and
completion. Attempts 1–6 remain rejected evidence.

Attempt 8 preserves Attempt 7 except for its independently reproduced equality-only
matching defect. Authoritative erasure metadata adds the canonical deleted-byte
`match_length`; a deletion-specific key is derived from the kernel erasure secret and
`deletion_id`, and the keyed tag is computed over the deleted canonical bytes. Every
eligible persistent text/blob value must be scanned over all contiguous windows of
that length. Exact equality, beginning, end, middle, repeated, and binary occurrences
must match. The independent-source exemption applies only to the exact explicitly
identified payload cell, never to a larger containing value. Normal deletion and
old-backup restore regressions must fail closed on embedded bytes. Attempts 1–7 remain
rejected evidence.

Attempt 8 independent promotion review returned **PASS**, with no blocking findings
and promotion decision **YES**. V-04 Attempt 8 is **PASS / PROMOTED** on the exact
reviewed candidate: focused V-04 **26/26**, V-03 **8/8 twice**, and broad discovery
**618 tests / 11 skipped / 1 known sandbox loopback `PermissionError`**. This remains
a synthetic logical-erasure contract and does not claim physical SQLite remanence
destruction. The non-blocking public-registry routing-hygiene finding is preserved for
separate follow-up; this promotion does not modify the router. The next gate is V-05.

## Evidence artifact

`evidence/ln0/V-04-deletion-fanout/` when executed.

---

# V-05 — Model Context Boundary / No Brain Retrieval Handle

## Question

Can local and hosted model adapters perform work while receiving only bounded ContextPackets and no capability to browse the Brain?

## Contract under test

```text
Brain -> Retrieval -> Context Compiler -> ContextPacket -> Model Adapter
```

For hosted providers:

```text
ContextPacket -> Context Airlock -> Provider Gateway -> Hosted Provider
```

Hosted providers receive only records explicitly authorized by Core for hosted
disclosure. Records classified by Core as local-only, private, non-exportable, or
otherwise provider-denied must not enter a hosted ContextPacket or reach the hosted
adapter. Core owns record classification, effective provider policy, disclosure
authorization, selection, and initial/recompiled ContextPacket construction. Source
content and model output cannot assign or upgrade disclosure authority.
Missing explicit hosted authorization fails closed; fallback classification alone is
not permission to disclose. The built-in `safe-1` fixture is explicitly authorized by
Core, while caller-supplied records require explicit Core classification.

V-05 does not prove automatic discovery of secrets or sensitive content from
arbitrary plaintext. Content-classification/DLP capabilities are outside this
synthetic boundary proof.

## Test cases

1. Adapter input contains only packet bytes/structured metadata required for the task.
2. Packet contains no DB path, DB handle, Graph query handle, retrieval token, or
   secret/key reference usable outside Core. Private/path-like or credential-like
   content classified provider-denied by Core does not enter a hosted packet;
   equivalent-looking content explicitly classified `HOSTED_ALLOWED` is not rejected
   merely because of its plaintext.
3. Local model adapter has no direct Notebook DB object/reference.
4. Hosted adapter has no filesystem access to Brain storage in the eventual enforcement spike.
5. Model request for additional context returns a structured request to Core; it cannot call retrieval directly.
6. Core recompiles a new packet only after local retrieval/policy evaluation, and
   applies the same hosted-disclosure authorization on every subsequent invocation.
7. External response is classified as untrusted/proposal on return.
8. A hostile prompt in retrieved content cannot cause N2/N3 material to be added to the outbound packet if policy denies it.
9. Equivalent packet can be routed to a different provider without moving/migrating Notebook memory.

## Pass condition

The model boundary is a data contract, not a hidden capability bridge. Initial and
ContextRequest-driven hosted invocations enforce the same Core-owned disclosure
decision without claiming general plaintext DLP.

## Evidence artifact

`evidence/ln0/V-05-context-boundary/` when executed.

---

# Verification order

Run in this order:

```text
V-01 schema migration
  -> V-02 encrypted storage/key recovery
  -> V-03 Ingestor semantics
  -> V-05 context boundary
  -> V-04 deletion fan-out fixture (spec now, full execution as derived stores exist)
```

V-04 has an early contract phase and a later full-system regression phase because several derived stores do not exist yet.

---

# Evidence discipline

Each executed packet records:

- exact repository commit;
- OS/Python/native library versions;
- exact commands;
- test fixtures;
- stdout/stderr where safe;
- pass/fail counts;
- known limitations;
- reviewer findings/dispositions;
- rollback/cleanup confirmation;
- no personal Notebook content.

A packet may be `FAILED` or `INCONCLUSIVE`. Those are valid outcomes. They are preferable to silently promoting an unverified assumption.

---

# Exit from LN-0

LN-0 may be considered for implementation-ready status only after all of the following are true:

- V-01 and V-02 are accepted; V-03, V-04, and V-05 are PASS / PROMOTED.
- The LN0 architecture Definition of Done is evidence-backed, including target-stack encryption/key-recovery feasibility, SQLCipher/WAL behavior, and a bounded executable LN-1 work order.
- V-04 dependency semantics are encoded in the LN-1+ acceptance-test roadmap and V-05 has a frozen adapter contract.
- Independent architecture/security review finds no unresolved schema/security blocker.
- The owner explicitly approves implementation readiness after that review.

The 2026-09-28 target-Mac SQLCipher result and proposed LN-1 work order are
reconciled in `docs/work-orders/HOS-LN-000.md`; the result is also preserved in
the tracked `docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md`. The storage-layer and
synthetic-wrapper feasibility proof does not choose production Keychain, KDF,
recovery-secret custody, rotation, or backup policy. Those remain explicit
pre-implementation ADR decisions. At this date the external review and owner
decision are pending; LN-0 is not closed and LN-1 implementation has not started.
