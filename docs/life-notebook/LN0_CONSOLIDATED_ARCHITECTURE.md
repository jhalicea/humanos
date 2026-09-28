# HumanOS Life Notebook — LN-0 Consolidated Architecture

**Status:** CANDIDATE — LN-0 INVARIANTS PROVISIONALLY LOCKED  
**Date:** 2026-09-25  
**Owner:** Jon Alicea  
**Workstream:** `HOS-LN-000`  
**Baseline:** `runtime-0.1`  
**Purpose:** Merge the existing HumanOS runtime/foundation with the new Life Notebook architecture without creating a competing system or reopening constitutional work.

---

## 1. Working rule

HumanOS already has a real runtime and a real Life Notebook foundation. This document **extends that foundation**. It does not authorize a rewrite, a competing runtime, or a new governance project.

The implementation rule is:

> Preserve working behavior, preserve evidence, add the missing architecture in vertical slices, and change only what a verified requirement forces us to change.

Constitution/Foundation work is **not a blocking workstream** for LN-0. Existing non-conflicting principles are preserved. A governance review is opened only if a concrete implementation decision creates an actual conflict that cannot be resolved at the architecture/work-order level.

---

## 2. Verified repository baseline to preserve

The current `runtime-0.1` repository already provides the foundation we need:

- local Python runtime and Mirror front door;
- SQLite Life Notebook with a single-writer process lock;
- exact append-only transcript capture;
- durable task/transaction state;
- append-only hashed events and recovery records;
- read-back verification before successful checkpoint claims;
- human-readable page projections;
- explicit recovery/degraded states;
- local Ollama model protocol isolated from Notebook logic;
- explicit bounded context selection rather than dumping all Notebook history into prompts;
- governed tools/capability checks;
- CI/test evidence and rollback discipline;
- Universal Conversation Capture for host conversations;
- append-only external conversation ledger/import logic;
- Context Registry / Context Runtime / Context Graph infrastructure already present in the repository.

The existing runtime is therefore a **baseline to evolve**, not scaffolding to discard.

### Existing limitations that LN-0 must respect

The current runtime also states its limits truthfully:

- Notebook SQLite is not application-encrypted;
- automatic historical retrieval is not complete;
- remote/cloud adapters are not active;
- current provider isolation is not the final Context Airlock architecture;
- Knowledge Graph and Canonical State are not yet the full Life Notebook planes defined here;
- external ChatGPT/host capture is not yet universally automatic in the running product;
- the current Life Notebook schema predates the new event/payload and authority model.

These are migration inputs, not reasons to restart.

---

## 3. Product definition

The **Life Notebook is the HumanOS continuity system**.

It owns the durable answer to:

> What happened, what was captured, what changed, what was decided, what failed, and what evidence supports the current system's understanding?

It is not Notion, Obsidian, provider chat history, a vector database, or an LLM memory feature.

### Three semantic planes

```text
LIFE NOTEBOOK / KERNEL
"What was captured?"
        |
        v
CANONICAL STATE
"What is true now?"
        |
        v
KNOWLEDGE GRAPH
"What is connected?"
```

Authority order:

```text
Notebook Evidence > Canonical State > Knowledge Graph
```

- Kernel evidence is historical authority.
- Canonical State is the authoritative present interpretation, justified by kernel events.
- Knowledge Graph is a provenance-backed semantic/navigation projection and may be stale, incomplete, or hypothetical.

---

## 4. Intelligence sovereignty

HumanOS owns the Brain. Models are replaceable intelligence providers.

### Frozen invariant

> **Models consume compiled context. Models do not browse the Brain.**

This applies to both local and hosted models.

```text
HumanOS Brain
    |
Local Retrieval
    |
Context Compiler
    |
    +--> Local Model (packet only)
    |
    +--> Context Airlock --> Provider Gateway --> Hosted Model
```

No model receives:

- Notebook database handles;
- Knowledge Graph query handles;
- filesystem access to the Brain;
- Brain credentials;
- unrestricted retrieval APIs.

If a model needs more information, it asks HumanOS. HumanOS locally retrieves, minimizes, authorizes, and compiles a **new ContextPacket**.

External-provider results return as untrusted evidence/proposals and cannot directly mutate the kernel or Canonical State.

---

## 5. Writer authority

### Ingestor

The **Ingestor is the sole kernel writer**.

Every source — UI, Mirror, connector, import job, future mobile capture, or conversation adapter — submits a CaptureRequest. Nothing else directly inserts kernel rows.

### State Applier

The **State Applier is the sole Canonical State writer**.

Canonical State changes originate from kernel events, not graph inference, UI mutation, or model output.

### Projection workers

Projection workers:

- read only the evidence they require;
- write only their assigned `proj_*` stores;
- cannot write kernel history;
- cannot write Canonical State;
- do not gain network access by default.

### Models

Models receive ContextPackets only. They do not receive database write authority.

### GREEN rule

> GREEN may write suggestions/projections. GREEN never writes the kernel or Canonical State directly.

---

## 6. Canonical kernel

The kernel must remain small.

### `NotebookEventV1`

Conceptual fields:

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
  conversation_id?
  parent_event_id?
  correlation_id
  causation_id?
  trace_id

policy:
  epistemic_class
  sensitivity_class
  delegation_lane?
  provider_class?

payload:
  payload_object_id?
  payload_commitment?
  payload_size?

capture:
  capture_status

integrity:
  prev_event_hash
  event_hash
```

### Payload integrity across authorized erasure

`payload_commitment?` is a conceptual field, not an approved algorithm or stored
representation. It MUST NOT be interpreted as an ordinary permanent SHA/content
digest of erasable plaintext. No permanent immutable event, receipt, projection,
cache, or backup may retain an ordinary plaintext-derived payload digest after
authorized `ERASE.COMPLETED`.

Before erasure, integrity/idempotency may use content-derived values only under the
lifecycle selected by the Schema/Integrity ADR. At erase completion, no ordinary
plaintext-derived digest may remain in any governed persistent store. Whatever
payload commitment is retained, if any, must satisfy the deletion contract and
permit the immutable event-integrity chain to remain valid after payload erasure
without rewriting kernel history. `event_hash` must not make post-erasure chain
verification depend on an erased plaintext digest. The exact commitment
representation and the exact fields covered by `event_hash` are unresolved until
the mandatory PRE-LN-1 Schema/Integrity ADR is reviewed and accepted.

### Global sequence

V1 uses one monotonic global kernel `seq` assigned by the Ingestor.

`seq` represents **durable ingestion order**, not real-world occurrence order.

The three clocks remain separate:

- `occurred_at` — when the event is said to have happened;
- `observed_at` — when a capture path first observed it;
- `ingested_at` — when HumanOS durably committed it.

### Caller authority

A capture source may submit evidence. It may not self-assign authority.

Callers do not control:

- global sequence;
- event hash/signature;
- owner-decision status;
- verified epistemic status;
- kernel authority;
- State promotion.

HumanOS assigns these according to source identity and policy.

---

## 7. Source Authority Ceiling

Every source has a maximum authority profile.

Example:

```text
chatgpt-connector
  may submit: observed conversation messages
  may not claim: OWNER_DECISION
  may not promote State
  may not write Kernel directly

trusted-humanos-ui
  may submit: owner statement / owner correction / owner decision
  requires: authenticated owner session

local-system-observer
  may submit: runtime health / file hash / test result
  may not claim: owner decision
```

A compromised connector therefore cannot poison HumanOS merely by labeling its own payload as canonical truth.

---

## 8. Payload model

Each event owns a unique payload object.

```text
PayloadObjectV1
  object_id
  event_id
  content_hash
  mime_type
  size_bytes
  sensitivity_class
  encryption_scope
  key_ref
  storage_ref
  created_at
  deleted_at?
```

### No cross-event payload identity

Two identical payloads captured twice remain two independently deletable objects.

`content_hash` is an integrity/duplicate-detection signal, not storage identity.

Deletion-safe deduplication is explicitly deferred until it has a complete proof and test suite.

`content_hash` may exist for integrity/idempotency while the governed payload
exists, but its lifecycle MUST be compatible with authorized deletion. It MUST NOT
survive `ERASE.COMPLETED` as an ordinary dictionary-testable plaintext fingerprint
in this object or any permanent event, receipt, projection, cache, or backup.
Whether it is removed, replaced, or represented otherwise is not decided here;
the Schema/Integrity ADR must specify and test that lifecycle before schema
implementation or real capture.

---

## 9. Event vocabulary v1

Keep the initial vocabulary small and extensible.

```text
CAPTURE.MESSAGE
CAPTURE.NOTE
CAPTURE.FILE
CAPTURE.OBSERVATION

STATE.ASSERT
STATE.RETRACT
STATE.SUPERSEDE

ENTITY.CONFIRM
ENTITY.ALIAS
ENTITY.MERGE
ENTITY.SPLIT

PAYLOAD.TOMBSTONE
POLICY.DECISION
SYSTEM.GENESIS
SYSTEM.SCHEMA
SYSTEM.RECOVERY
```

AI-produced work is represented through actor/source/policy metadata, not a privileged agent event type.

---

## 10. Four orthogonal policy axes

HumanOS keeps these dimensions separate:

### E — Epistemic
How warranted is the claim?

### S — Sensitivity
Who may see/process the data?

### D — Delegation
How much judgment may an AI exercise?

### P — Provider/counterparty
Who is processing or receiving the data?

Policy composes them. One axis never substitutes for another.

Examples:

```text
S3 + external provider -> DENY
E1 + RED decision -> insufficient evidence
GREEN + kernel write -> DENY
S1 + local model -> policy-dependent allow
```

Deny-by-default; first deny wins.

---

## 11. Capture reliability

The existing HOS-006 principle is preserved: a model saying "saved" is not proof of saving.

The runtime already has durable capture/checkpoint/recovery concepts. LN-0 evolves them into the kernel ingestion contract rather than throwing them away.

Required truthful states include the existing HumanOS concepts:

```text
PENDING
PARTIAL / INCOMPLETE
WRITTEN
READ_BACK_VERIFIED
CHECKPOINTED / VERIFIED
FAILED
RECOVERY_REQUIRED
```

Exact naming may be normalized during the schema ADR, but semantic distinctions must not be collapsed.

### Capture before compute

Human input/event evidence is durably captured before model-dependent enrichment whenever the path permits it.

### Degraded mode

Capture is more important than enrichment.

A broken summary worker, graph worker, embedding job, or State projection does not stop raw capture.

---

## 12. Canonical State contract

Canonical State is replayable from kernel state events but is operationally authoritative for present truth.

It maintains:

```text
cs_applied_seq
```

representing the highest contiguous kernel sequence successfully applied.

If a State event fails:

- do not advance the watermark;
- record/park the poison event;
- continue Notebook capture;
- surface `STATE DEGRADED` truthfully;
- repair/replay State without rewriting kernel history.

Frozen invariant:

> Lag is acceptable. Hidden divergence is not.

---

## 13. Knowledge Graph contract

The Knowledge Graph is a derived semantic projection.

Rules:

- Graph cannot write Kernel.
- Graph cannot write Canonical State.
- Every important edge carries provenance.
- Graph may be stale/incomplete.
- Hypotheses/candidates are permitted but must remain labeled.
- Canonical State overrides Graph.
- Notebook evidence overrides Canonical State when they conflict.

### Mention-first identity

Evidence permanently binds to immutable **mentions**, not to mutable resolved entity clusters.

```text
Event -> Mention M1 --\
                     -> Entity Cluster E1
Event -> Mention M2 --/
```

If resolution changes, the mention remains stable while the cluster mapping changes.

Entity merges in v1 require owner confirmation. Model-only evidence may propose but does not merge canonical identities.

---

## 14. Derived projections

The following are rebuildable projections, not historical authority:

- Daily Timeline;
- readable pages;
- summaries;
- derived annotations;
- Knowledge Graph;
- FTS;
- embeddings;
- retrieval caches;
- UI caches.

Normal operation is incremental using outbox/impact records and projection checkpoints.

Full replay remains a recovery/audit capability, not the normal read path.

### Projection checkpoint

Each projection records at least:

```text
projection_name
projection_version
schema_version
algorithm_version
last_processed_seq
model/extractor version if applicable
updated_at
checkpoint_hash
```

Late-arriving historical events invalidate affected partitions (date, conversation, project, entity, search records) without requiring a full rebuild.

---

## 15. Deterministic vs model-derived projections

Deterministic projections (timeline ordering, explicit state application, FTS structure, explicit graph assertions) should rebuild identically for the same input/version.

Model-derived projections (summaries, semantic labels, entity suggestions, embeddings) must carry:

```text
source_hash
producer/provider
model/version
extractor version
prompt/schema version
created_at
```

They remain replaceable interpretations and never replace source evidence.

---

## 16. Deletion and tombstone fan-out

Deleting source content is not complete while persistent derivatives remain.

Every derived artifact must preserve machine-readable source lineage (`source_event_ids` or equivalent).

On `PAYLOAD.TOMBSTONE`:

```text
source event
   -> dependency resolver
      -> FTS
      -> vector index
      -> summary
      -> graph edge/node support
      -> thumbnail/waveform
      -> cached page/retrieval artifact
      -> retained ContextPacket body (if any)
```

Rules:

- sole-source derivative -> delete/invalidate;
- multi-source derivative -> recompute without deleted source;
- independently owner-ratified state -> may survive because it has independent authority.

Backups require explicit retention/restoration semantics so a restore does not silently resurrect deleted live state.

Deletion is also an auditable lifecycle: `ERASE.REQUESTED` -> authorization ->
`PAYLOAD.TOMBSTONE` -> fan-out/recomputation -> verification -> `ERASE.COMPLETED`.
Failure records `ERASE.RECOVERY_REQUIRED`; completion is forbidden while unresolved
derivatives remain. The durable `DeletionReceiptV1` is append-only and content-free:
it identifies the governed object, authorization, scope, fan-out counts, restore
tombstone status, verification, and chained receipt integrity, but retains no
plaintext, PII, summary, embedding, binary, reversible copy, or content-derived
hash of the erased payload.

The same prohibition applies to every permanent immutable event, projection,
cache, and backup after authorized erase completion. `NotebookEventV1.payload_commitment?`
is not an ordinary plaintext hash, and `PayloadObjectV1.content_hash` must not
survive completion as a dictionary-testable plaintext fingerprint. Structural
chronology, object/event identity, tombstone, and deletion evidence survive; the
event/integrity chain remains valid without rewriting kernel history. The mandatory
PRE-LN-1 Schema/Integrity ADR must specify how this interacts with `event_hash`,
idempotency/duplicate detection, backup/restore, and the V-04 ErasureTag contract.
It is separate from the SQLCipher/key-custody ADR.

V-04 Attempt 4 refines this as a privacy/integrity contract: permanent event and
receipt integrity may bind opaque payload-object identity or an encrypted/non-plaintext
representation, but must not retain a dictionary-testable plaintext fingerprint after
erasure. Structural provenance (event/object/page/block identity, event type,
chronology, deletion scope and lifecycle principals/times) survives so a page can
truthfully render `13:43 — [CONTENT ERASED] — DEL-184` without retaining the original
content. Production encrypted-payload integrity is intentionally deferred to the
mandatory Schema/Integrity ADR; this synthetic fixture does not select that design.

V-04 Attempt 5 binds every completed operation bidirectionally by `deletion_id`:
exactly one tombstone, one receipt, one completion lifecycle event, and matching
event/payload-object targets. Restore reconciles the union of all three evidence
stores. An interrupted `ERASE.RECOVERY_REQUIRED` operation may truthfully have a
tombstone and no receipt, but cannot become LIVE until replay, fan-out verification,
single receipt completion, and reconciliation succeed.

Receipt-chain verification compares the receipt projection to authoritative
count/head/final-sequence anchor state. The isolated append-only anchor table models
that contract only; production anchoring belongs in HumanOS kernel checkpoint and
storage-integrity architecture. ERASE authority comes from a HumanOS-owned
credential-to-policy resolver. Caller-provided names are not principals, and the
executor is an internal identity distinct from requester and authorizer.

V-04 Attempt 6 makes the kernel/checkpoint boundary explicit in the fixture. The
SQLite anchor table is only a local projection; authoritative receipt count, head
hash, and final sequence are supplied separately and must match on every verification,
including idempotent retries and restore. Completion also requires a dynamic scan of
all persistent fixture tables for the captured source bytes. Only the payload cell of
an explicitly identified independent source event may be exempt. Restore quarantine
covers the public raw-database accessor as well as typed reads and retrieval aliases.
This remains a synthetic contract, not a production kernel implementation.

V-04 Attempt 7 preserves that architecture and adds a synthetic production-contract
ErasureTag: `HMAC(kernel_erasure_secret, deletion_id || canonical_deleted_bytes)`.
The authoritative kernel checkpoint may retain the tag but never plaintext or an
ordinary plaintext SHA-256. The independently supplied secret is not stored in the
restored Notebook DB or receipt; production key storage belongs to the encrypted
kernel/key architecture. Restore must verify checkpoint state, reconcile the deletion
ledger, replay tombstones, run fan-out, scan every persistent store by recomputing the
ErasureTag, verify zero unresolved derivatives, and only then transition to LIVE.
All public content paths remain quarantined until LIVE. Final scan, receipt/anchor,
kernel checkpoint, and `ERASE.COMPLETED` form one exclusive-writer completion boundary
in the SQLite fixture. This is a logical-erasure contract and does not change the
physical-remanence limitation.

V-04 Attempt 8 preserves the Attempt 7 boundary and corrects its equality-only
matching defect. The kernel checkpoint also carries the canonical deleted-byte
`match_length`; a deletion-specific key is derived from the independently held kernel
secret and `deletion_id`, and the erasure tag is HMAC over the canonical deleted
bytes. Verification scans every contiguous candidate window of that length. Only the
exact payload cell belonging to the explicitly identified independent source may be
exempt; containing strings, other artifacts, caches, metadata, and unrelated lineage
are never exempt. Plaintext, ordinary plaintext SHA-256, the kernel secret, and the
derived key remain outside Notebook persistence and receipts.

The exact V-04 Attempt 8 candidate passed independent promotion review with no
blocking findings and is **PASS / PROMOTED**. Qualification preserved focused V-04
**26/26**, V-03 **8/8 twice**, and broad discovery **618 tests / 11 skipped / 1 known
sandbox loopback `PermissionError`**. Attempts 1–7 remain rejected historical evidence.
This promotion proves only the synthetic logical-erasure contract; it does not claim
physical SQLite remanence destruction. The reviewer's non-blocking routing-hygiene
finding remains deferred and the router is unchanged. The next gate is V-05.

---

## 17. Encryption and key recovery direction

Application encryption is an LN-0 verification area, not a reason to rewrite the runtime prematurely.

Target architecture:

```text
random HumanOS data key
   |
   +-- local wrapper (OS secure key storage)
   +-- independent recovery wrapper
```

The encrypted Notebook must remain recoverable after loss of the original Mac without depending on an AI vendor.

Exact cryptographic algorithms, KDF parameters, SQLCipher pragma order, key rotation, and macOS integration require direct technical verification before their ADR is ratified.

Do not promote exact model-generated SQLCipher recipes without evidence.

The unchanged V-02 spike passed on the target Mac (macOS 26.6.2 arm64, SQLCipher
4.19.0); the full environment and result are in
`docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md`. This establishes SQLCipher
storage-layer feasibility and a synthetic independent-wrapper round-trip, not
production Keychain integration, KDF/wrapping/custody policy, rotation, or backup
policy. Those remain explicit LN-1 pre-implementation ADR decisions. Homebrew is
workstation development tooling only and is not a HumanOS runtime, production, or
deployment dependency.

---

## 18. Provider isolation

Architecture requirement:

- HumanOS Core has Brain access and no unrestricted provider egress.
- Provider adapters have the network capability required for their provider but no Brain DB/vault/key access.
- ContextPackets are finite, purpose-bound, policy-labeled, and auditable.
- Provider outputs return as untrusted input.

Exact macOS enforcement (separate executable/security identity, sandbox, firewall/egress mechanism, container/VM, etc.) remains an implementation ADR to verify experimentally.

The **security property** is provisionally locked. The exact mechanism is not.

---

## 19. Mobile v1 stance

Mobile is initially a **capture client, not a Brain replica**.

A mobile device may queue signed/authenticated pending capture envelopes while offline and later submit them through the Ingestor path.

Mobile does not initially hold:

- the full Brain;
- the full Canonical State;
- the full Knowledge Graph;
- the Notebook master encryption key;
- independent kernel-writer authority.

Global kernel sequence is assigned at ingestion. `occurred_at` preserves the historical event time.

---

## 20. Existing HumanOS components: merge map

### Preserve directly

- `Notebook` single-writer and transactional discipline;
- exact transcript preservation;
- append-only event/recovery concepts;
- read-back verification/checkpoint honesty;
- Universal Conversation Capture retry/idempotency behavior;
- append-only external conversation import behavior;
- local model-neutral protocol;
- bounded Context Runtime/Context Registry work;
- capability/authorization boundaries;
- existing CI, recovery, rollback, STATUS/work-order evidence discipline.

### Refine in place

- current transcript/events/tasks schema -> migrate toward `NotebookEventV1` + unique payload objects without losing existing evidence;
- current host capture -> route through a single Ingestor contract;
- current context selection -> evolve into Context Compiler retrieval/packet compilation;
- current pages/index/bindings -> formalize as projections;
- current recovery records -> map into the unified capture/recovery state model;
- current audit digests -> integrate with the new kernel integrity model.

### Do not silently preserve as final architecture

- plaintext SQLite at rest;
- direct broad DB handles for future workers/models;
- any hosted-model path that can retrieve the Brain;
- graph inference writing State;
- source-supplied canonical authority;
- provider-specific memory as HumanOS memory.

### Deliberately defer

- constitutional redesign;
- Rust rewrite solely because an older candidate proposed one;
- full distributed/multi-device Brain replication;
- auto entity merge;
- deletion-safe cross-event deduplication;
- graph/vector sophistication before the Daily Timeline works;
- exact provider-isolation mechanism until verified on the target Mac.

---

## 21. Vertical milestone sequence

```text
LN-0  Consolidation, contracts, technical verification
LN-1  Capture -> encrypted durable kernel
LN-2  Daily Timeline (first visible product)
LN-3  Tombstone / export / backup / restore
LN-4A Canonical State
LN-4B Reversible entity identity/resolution
LN-5  Pages + local derivation
LN-6  Local Brain + FTS / evidence retrieval
LN-7  ContextPackets + external-provider isolation
LN-8  Knowledge Graph + local embeddings
LN-9  Multi-source hardening / imports / scale / security regression
```

Nothing in Graph/embedding/provider work may delay the first usable Timeline unless a security/data-model invariant would otherwise be violated.

---

## 22. Human-facing acceptance criteria

Engineering correctness is necessary but not sufficient.

Life Notebook must eventually pass these product tests:

### Continuity
Ask days/months later what was decided and receive the governing decision, date, provenance, and supersession history.

### Chronology
Ask what happened during a period and receive a coherent evidence-backed timeline.

### Contradiction
Ask whether HumanOS previously believed something different and receive the prior belief, correction, and current state.

### Provenance
Ask "Why do you believe this?" and traverse State -> decision/assertion -> source event -> exact original evidence.

### Provider independence
Change OpenAI/Claude/local-model routing without migrating HumanOS memory/history.

### Deletion
Delete authorized source material and prove it is absent from raw payloads and persistent derived artifacts while retaining appropriate tombstone/audit evidence.

---

## 23. LN-0 Definition of Done

LN-0 closes when:

1. current repository baseline is inventoried;
2. existing runtime behavior to preserve is documented;
3. event/payload contracts are specified;
4. source-authority and writer-authority matrices are specified;
5. capture/recovery semantics are mapped from existing HOS-006 behavior;
6. State watermark/poison semantics are specified;
7. deletion fan-out semantics are specified;
8. model/context boundary is specified;
9. encryption/key-recovery design is verified enough for LN-1;
10. SQLCipher/storage spike produces evidence on the target stack;
11. LN-1 work order has bounded scope and executable acceptance tests;
12. no existing frozen/runtime evidence is overwritten or falsely superseded.

The technical criteria are reconciled in `docs/work-orders/HOS-LN-000.md`, including
the bounded feasibility limits above. The independent architecture/security review
and explicit owner implementation-ready decision remain required closure gates.
Until both gates pass, this remains a **candidate architecture contract**, not an
implementation-ready or closed workstream.

### Mandatory PRE-LN-1 Schema/Integrity ADR gate

Before any `NotebookEventV1` / `PayloadObjectV1` persistence implementation or real
capture, a Schema/Integrity ADR MUST be reviewed and accepted. It is separate from
the SQLCipher/key-custody ADR and MUST resolve:

1. exact deletion-safe `payload_commitment` representation (or explicit omission);
2. whether/how `event_hash` commits payload information and how verification works
   after payload erasure without rewriting history;
3. `PayloadObjectV1.content_hash` creation, use, and erase lifecycle;
4. authorized deletion/erasure behavior across kernel, receipts, projections,
   caches, and backups;
5. idempotency and duplicate-detection semantics before and after erasure;
6. backup/export/restore interaction and anti-resurrection behavior; and
7. interaction with V-04 `ErasureTag`, tombstone, receipt, and completion semantics.

This architecture does not select a final cryptographic commitment algorithm.
Implementation is prohibited until the ADR records the chosen representation,
threat analysis, and acceptance tests.

---

## 24. Immediate next actions

1. Preserve this architecture and its evidence on the `life-notebook-ln0` branch.
2. Maintain one LN-0 work order (`HOS-LN-000`) rather than parallel planning documents.
3. Resolve and review the mandatory Schema/Integrity ADR before event/payload
   persistence or real capture begins.
4. The target-Mac SQLCipher/storage feasibility proof is complete; retain its bounded
   results and unresolved production key-policy decisions as explicit evidence.
5. Obtain independent architecture/security review and record findings/disposition.
6. Obtain the owner's explicit implementation-ready decision only after review passes.
7. Only after all gates, begin the separately authorized LN-1 implementation.

The operating principle is:

> **Move fast through automation, not by skipping engineering.**
