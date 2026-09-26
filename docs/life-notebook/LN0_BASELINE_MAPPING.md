# Life Notebook LN-0 — Existing Runtime Baseline Mapping

**Status:** CANDIDATE / READ-ONLY BASELINE MAP  
**Date:** 2026-09-25  
**Workstream:** `HOS-LN-000`  
**Baseline inspected:** `runtime-0.1` @ `0cf78d9abe5dcfcc6114bb43167dcf7406478657`

This document maps the current repository into the LN-0 target architecture. It is deliberately migration-oriented: **preserve working evidence and behavior, then evolve it.**

---

## 1. Current runtime reality

The existing runtime is not an empty prototype. It already implements several Life Notebook properties that the new design requires:

- one local writer lock for the Notebook;
- SQLite WAL storage;
- exact transcript rows with immutable update/delete triggers;
- durable transactions/tasks/events/recovery;
- HMAC-keyed content digests and record-integrity enforcement;
- checkpoint/read-back verification;
- human-readable JSON/Markdown projections;
- retry-safe Universal Conversation Capture;
- append-only external conversation import/conflict detection;
- bounded recent-history/context routing;
- local model abstraction and governed capability execution;
- CI/recovery/rollback documentation.

The new design must therefore be implemented as a migration/evolution of this evidence model, not as a clean-room replacement.

---

## 2. Current storage -> target-plane map

| Current object | Current role | LN-0 target | Action |
|---|---|---|---|
| `identities` | HCID/page/binding identity | Kernel identity metadata / stable page-conversation identity | **Preserve and map.** Do not discard stable IDs. Determine whether rows remain operational metadata or become kernel identity events. |
| `transactions` | durable turn/work unit and status | Operational runtime state + provenance link to kernel | **Preserve.** Do not force all task machinery into the Notebook event model. Emit/link evidence events where historically meaningful. |
| `transcript` | exact HUMAN/ASSISTANT evidence | `NotebookEventV1` + unique `PayloadObjectV1` | **Primary migration target.** Exact bytes/text and order must survive. |
| `tasks` | serialized runtime task state | Operational state machine | **Keep separate from Canonical State.** Task execution state is not human-life truth. |
| `events` | append-only content-light runtime/audit events | Kernel event/audit lineage | **Refine.** Map kinds/payloads into versioned kernel event envelopes or preserve as legacy evidence linked by migration events. |
| `recovery` | durable unresolved failures | Recovery subsystem + `SYSTEM.RECOVERY` evidence | **Preserve.** Recovery failure must never disappear during migration. |
| `privacy_state` | current hidden/visible state | privacy/retention projection | **Refine into projection/state.** Current state is derived from operations. |
| `privacy_operations` | explicit hide/unhide actions | policy/privacy kernel events | **Preserve as authority-bearing operations.** |
| `privacy_receipts` | append-only operation evidence | audit/receipt evidence | **Preserve.** Never collapse into current state only. |
| `pages/*.json` | exact readable per-conversation projection | Notebook Page projection | **Rebuildable projection.** Not canonical authority. |
| `pages/*.md` | human-readable materialization | Notebook Page projection | **Rebuildable projection.** |
| `active-index.json` | active lookup projection | projection / Canonical State candidate depending field | **Classify field-by-field.** Do not promote caches into kernel. |
| `bindings.json` | verified binding projection | identity/state projection | **Preserve semantics; make rebuildable where evidence supports it.** |
| `recovery.jsonl` | fallback capture when normal storage fails | recovery ingress/evidence queue | **Preserve and reconcile.** It must remain readable until all entries are durably resolved. |
| `recovery-copies/` | preserved projections before repair | recovery artifacts | **Retain under backup/recovery policy.** Not live truth. |

---

## 3. Current code -> target-component map

### `notebook.py`

**Today:** local authoritative Notebook adapter, writer lock, SQLite schema, exact transcript, tasks/events/recovery, integrity, checkpoint/reconciliation.

**Target:** becomes/contains the foundation for:

- Ingestor storage adapter;
- kernel event/payload persistence;
- projection reads;
- recovery and verification.

**Do not:** turn it into a model/agent layer or let future workers acquire its raw DB handle by convenience.

### `conversation_capture.py`

**Today:** provider-neutral exact host conversation capture with keyed host identity, retry safety, exact assistant/human text verification, and checkpoint semantics.

**Target:** becomes a **capture adapter** that submits an authenticated CaptureRequest to the sole Ingestor.

Preserve:

- exact text;
- provider/source identity;
- stable retry identity;
- fail-closed conflicting retries;
- no model call merely to save evidence.

### `conversation_ledger.py`

**Today:** append-only import/staging ledger for already-observed provider messages with `(source, source_id)` conflict detection.

**Target:** import/capture staging adapter, not a second canonical Notebook.

Once successfully ingested, the kernel is authoritative; the staging ledger may remain as import provenance until retention rules say otherwise.

### `context_runtime.py`

**Today:** deterministic routing/continuity layer that explicitly says it is a precursor to the future Context Engine, not a competing memory system.

**Target:** preserve and evolve into the host-side routing/context-selection layer feeding the Context Compiler.

Important existing property to keep: it already minimizes model-facing context and strips host-private routing details where appropriate.

### `context_registry.py`

**Today:** public/private workspace/workstream registry and routing metadata.

**Target:** remains development/operational context metadata. It is not the Life Notebook Knowledge Graph.

### `context_graph.py` / `context_graph_bridge.py`

**Today:** existing context/workstream graph infrastructure.

**Target:** preserve as Context Layer infrastructure. **Do not silently rename this into the personal Life Notebook Knowledge Graph.** The two may later share graph primitives, but they have different semantics and authority.

### `capabilities.py`

**Today:** tool contract / argument validation / authorization-facing capability surface.

**Target:** precursor/supporting implementation for Permission Broker / capability-authority separation. Keep separate from Notebook evidence authority.

### model protocol / Ollama adapter

**Today:** local provider abstraction.

**Target:** local model adapter behind the Context Compiler. Local models eventually receive bounded ContextPackets rather than raw Notebook database access.

---

## 4. Existing semantics that become hard compatibility requirements

### Exact transcript fidelity

The current runtime preserves exact text, speaker order, corrections, Unicode, whitespace, and read-back evidence. LN-1 must not regress this.

### Single-writer behavior

The current Notebook already holds an exclusive process writer lock. The new Ingestor must preserve one authoritative commit path even if many capture clients exist.

### Idempotency

Current host capture and import paths already reject conflicting replays. The new `ingestion_id` contract should generalize this behavior, not replace it with weaker semantics.

### Recovery honesty

The runtime distinguishes incomplete/uncertain/output states and refuses to fabricate missing assistant responses. This must survive the migration.

### Integrity honesty

Current documentation correctly says hashes detect accidental tampering and do not make the system tamper-proof against an attacker able to rewrite the DB. LN-0 preserves that claim.

### Context minimization

The runtime already avoids dumping full Notebook history into the model prompt. The new Context Compiler formalizes and expands this principle.

---

## 5. New structures not present as complete runtime contracts today

LN-0 introduces the following explicit concepts that require additive design/work:

1. `NotebookEventV1` envelope across all capture sources;
2. unique `PayloadObjectV1` per event;
3. source authority ceilings;
4. four policy axes (E/S/D/P);
5. sole Ingestor API/IPC contract;
6. explicit Canonical State plane;
7. `cs_applied_seq` watermark + poison-event behavior;
8. formal least-privilege projection worker contracts;
9. mention-first reversible entity resolution;
10. Life Notebook Knowledge Graph as a distinct provenance-backed projection;
11. projection checkpoints + impact invalidation;
12. deletion/tombstone fan-out across every persistent derivative;
13. application encryption/key recovery;
14. ContextPacket schema + Context Airlock;
15. enforceable external-provider isolation.

None of these justify deleting working current behavior before a migration is verified.

---

## 6. Schema migration principle

LN-1 must use an **additive, evidence-preserving migration**.

Forbidden:

- dropping current transcript/history tables as the first step;
- rewriting prior text to fit a new schema;
- renumbering/reidentifying current evidence without a durable mapping;
- silently treating projections as source evidence;
- converting old recovery failures into successful history;
- resetting the Notebook because a cleaner schema is easier.

Every migrated record must be traceable from old identity to new identity.

### Migration strategy remains to be verified

Two implementation strategies remain open until the storage/encryption spike:

**A. Additive in-place schema evolution**

- retain current DB;
- add kernel/payload/receipt tables;
- migrate/envelop existing evidence;
- later encrypt using a verified SQLCipher migration procedure.

**B. New encrypted DB with controlled migration/cutover**

- preserve current DB read-only as migration source/rollback evidence;
- create new encrypted kernel;
- migrate records with exact readback/hash verification;
- cut over only after parity tests;
- preserve old source under a defined retention policy.

LN-0 must test enough to choose A or B on evidence, not aesthetics.

---

## 7. Current tables that must NOT be confused with new planes

### `tasks` != Canonical State

Runtime task state answers "what is this execution doing?" Canonical State answers "what is currently true/governing?"

### current `events` != complete Life Notebook Kernel

Current events are valuable audit evidence, but the new kernel contract adds source/actor/time/policy/payload semantics needed for all-source continuity.

### `context_graph` != Life Notebook Knowledge Graph

Current context graph supports development/context routing. The Life Notebook KG represents evidence-backed entities/relationships in the owner's life/work/system history.

### Markdown/JSON pages != canonical history

They remain human-readable projections.

---

## 8. Smallest LN-1 target

LN-1 should **not** attempt to build all three planes.

Its job is only:

```text
CaptureRequest
   -> Ingestor
   -> encrypted durable kernel event + payload
   -> exact readback
   -> truthful capture status
```

It must coexist with/preserve current Runtime 0.1 behavior until cutover/migration acceptance proves equivalence.

Explicitly not LN-1:

- Canonical State engine;
- Knowledge Graph;
- summaries;
- embeddings;
- external providers;
- autonomous entity resolution;
- multi-device replication.

---

## 9. LN-0 verification packets required before LN-1

### V-01 — Existing schema migration fixture

Create an isolated vault containing representative current identities, transactions, transcript, events, tasks, recovery, and privacy records. Prove the chosen migration preserves exact evidence and identities.

### V-02 — Encrypted SQLite / SQLCipher spike

Verify on the target stack:

- key initialization ordering;
- WAL/SHM encryption behavior;
- crash recovery;
- wrong-key fail-closed behavior;
- backup/export/restore;
- key rotation/recovery direction;
- plaintext scans of DB/WAL/SHM/temp artifacts.

No model-generated SQLCipher recipe is considered verified until this passes against primary documentation and real execution.

### V-03 — Ingestor idempotency/concurrency

Prove:

- one global sequence;
- same HumanOS-resolved `effective_source_id` + `ingestion_id` + same semantic submission fingerprint -> same event;
- same key + different semantic submission fingerprint -> fail closed;
- concurrent clients cannot race `prev_event_hash`;
- source cannot self-assign owner/canonical authority.

### V-04 — Deletion dependency contract

Build test fixtures showing tombstone fan-out through each planned persistent derivative class.

### V-05 — Context/model boundary

Prove the future adapter contract contains context bytes + metadata only and exposes no Brain retrieval/database handle.

---

## 10. Compatibility matrix for current features

| Current behavior | LN-1 requirement |
|---|---|
| exact HUMAN text | MUST preserve |
| exact ASSISTANT text | MUST preserve |
| message order | MUST preserve |
| idempotent host turn | MUST preserve/generalize |
| read-back before checkpoint | MUST preserve |
| unfinished/recovery visibility | MUST preserve |
| no fabricated assistant response | MUST preserve |
| writer lock | MUST preserve/evolve to Ingestor serialization |
| HMAC-keyed content integrity | MUST preserve until replaced by verified stronger contract |
| append-only corrections | MUST preserve |
| bounded model history | MUST preserve principle; implementation may evolve through Context Compiler |
| existing HCID/page identity | MUST migrate with stable mapping |
| current recovery evidence | MUST remain reviewable after migration |

---

## 11. Decision boundaries

### Provisionally locked

- evolve existing runtime, do not rewrite by default;
- one canonical Life Notebook chronology;
- Notebook > State > Graph authority;
- Ingestor-only kernel writes;
- State-Applier-only State writes;
- models consume context and do not retrieve Brain;
- exact evidence/provenance survives migration;
- unique payload object per event for v1;
- deletion fan-out is mandatory;
- graph/entity resolution cannot overwrite evidence;
- Constitution/Foundation work is not a blocker for this workstream.

### Still evidence-dependent

- exact SQLCipher configuration/version;
- in-place vs new-DB encrypted migration;
- exact macOS provider-isolation mechanism;
- exact process split for projection workers;
- key wrapping/recovery implementation;
- exact schema types/indexes/performance tuning.

---

## 12. Next action

Turn V-01 through V-05 into executable acceptance-test/spec packets, beginning with **V-01 current-schema migration fixture** and **V-02 encrypted-storage spike**. Those results decide the LN-1 migration ADR.
