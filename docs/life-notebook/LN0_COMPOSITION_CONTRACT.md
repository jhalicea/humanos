# LN-0 Synthetic Composition Contract

Status: test-only qualification contract; not a production API or LN-1 schema.

## Purpose and authority

This contract defines the minimum shared-state seam for composing accepted V-01
through V-05 invariants in one synthetic lifecycle. It does not change those frozen
contracts, implement the production Life Notebook kernel, or claim production
integration. The reference harness may reproduce contract behavior where the
accepted fixtures expose no common API; it must cite the defining accepted evidence
and must not call such reproduction code reuse.

The Core/Ingestor is the sole authority for governed identity, source authentication,
event commit/sequence, source and privacy classification, selection, erasure, and
disclosure authorization. Models consume compiled context. Models do not browse the
Brain. Source records and model output cannot grant authority.

## Governed identity and ingestion

Each governed event has one stable `event_id` and one stable `payload_object_id`.
These identities survive migration/import, ingestion, storage, lineage derivation,
erasure, restore/replay, and Context Compiler selection. No stage may silently mint
replacement identities to make two stores appear integrated. Equal payload bytes do
not collapse independently identified events or objects.

V-01 migration/import and new sources enter through an explicit Core/Ingestor
boundary. Only that boundary commits authoritative events and allocates sequence and
integrity metadata. A narrowly authorized migration mode preserves identities and
legacy provenance while applying the same uniqueness, lineage, and integrity checks;
it does not permit source-controlled OWNER authority or direct table writes.
Idempotent retry of the same source/key/semantic submission returns the same
identities; conflicting reuse fails closed.

## Conceptual KernelStore port

The harness uses one shared governed store. The conceptual port is limited to:

- `commit_event(...)` — sole-writer commit, authority resolution, stable identity,
  idempotency/conflict check, sequence and event integrity;
- `read_event(event_id)` / `read_payload(payload_object_id)` — Core-only reads,
  denied while restore is quarantined and denied for erased payloads;
- `lineage_for(event_id)` / `enumerate_derivatives(event_id)` — lineage-bound
  projection discovery;
- `apply_tombstone(event_id, authorization)` — authorized, durable deletion intent
  before fan-out;
- `read_deletion_state(event_id)` — Core-visible pending/completed state;
- `replay_or_recover()` — complete interrupted fan-out and reconcile deletion state;
- `authorized_retrieval(selection, provider_id)` — current-state retrieval, filtered
  and authorized by Core immediately before context compilation and dispatch.

Names are conceptual. This does not select final production schema or API names.

## Encryption boundary

V-02 encryption is below event, payload, source-authority, privacy, and provider
semantics. SQLCipher protects the serialized governed store; it does not own event
authority, erasure authority, model policy, or source classification. The composition
harness uses one temporary semantic KernelStore and separately encrypts a serialized
snapshot through the already-qualified SQLCipher CLI/configuration. This is not a
single-process production SQLCipher binding and does not close the PRE-LN-1
SQLCipher/runtime-binding/key-custody ADR.

New and migrated records begin `UNCLASSIFIED` and provider-denied in this synthetic
contract. Connector claims, migration metadata, content, and model output cannot
grant provider disclosure or upgrade privacy classification. Only an explicit
Core-owned policy operation may grant `HOSTED_ALLOWED`; that operation requires a
Core-held capability in the harness. This is a deterministic composition boundary,
not the final production classification schema.

## Derivatives, erasure, and restore

Every derived representation, including cached ContextPackets, is a projection with
lineage to the same governed event and payload-object identities. Fan-out is derived
from that shared lineage, never from a separate shadow deletion database. For each
governed derivative, lineage is evaluated first: sole-source derivatives are
invalidated and multi-source derivatives are recomputed from surviving lineage even
when transformed body bytes do not contain the deleted plaintext. Only a matching-
byte derivative without erased-event lineage is an unlineaged leak and fails closed
as `RECOVERY_REQUIRED`. After fan-out/recomputation, the final all-store ErasureTag
scan remains mandatory. The narrow accepted V-04 exact payload-cell exemption is
retained only when Core records an explicit authorization bound to the exact
independent event ID and payload-object ID. Different IDs or an ErasureTag match
alone do not establish independence; provenance, source claims, and content cannot
grant the exemption. A longer payload containing the erased bytes is never exempt.
The authorization is represented by test-only Core policy state, separate from
source-submitted records. Structural chronology, tombstones, and content-free deletion receipts
survive. Erased plaintext and ordinary plaintext-derived fingerprints do not survive
completion in the modeled governed stores. Integrity remains verifiable without
rewriting history; the harness's test-only integrity representation is not a final
cryptographic design.

The test-only all-store verifier enumerates every content-capable persistent field:
`events.payload`, `events.provenance`, `events.ingestion_id`, `derivatives.body`,
`auxiliary_content.store_key`, and `auxiliary_content.content`. All use the V-04
deletion-specific sliding ErasureTag window scan; only an exact `events.payload`
cell bound to an explicitly Core-authorized independent identity may be exempt.
`events.content_hash` and `events.submission_fingerprint` are separately required
to be cleared for the erased event. Other fields are excluded from plaintext
matching only because the harness schema constrains them to opaque identities,
fixed enums, chronology, hashes, or deletion/checkpoint receipts; tests do not treat
arbitrary metadata text as structural.

Restore begins quarantined. A pre-erasure backup is not readable or LIVE until
authoritative deletion state has been replayed, fan-out reconciled, and forbidden
content checked. Every authoritative checkpoint is reconciled and reapplied
idempotently on every restore even if an `ERASED` receipt already exists; receipts
are evidence to validate, not authority to skip revalidation. Checkpoint/deletion
identity, tombstone/receipt state, all-store ErasureTag results, and unresolved-zero
must pass before `LIVE`. A resurrected match leaves restore quarantined as
`RECOVERY_REQUIRED`; sanitization/reconciliation must finish before public reads.
Interruption leaves a truthful recovery-required state; restart replays the same
stable deletion identity and completes idempotently before public reads are enabled.

## Revocable context and dispatch-time revalidation

**Compiled context is not disclosure authority. External disclosure authority is
revalidated immediately before dispatch.**

A compiled ContextPacket is a revocable derived artifact. Immediately before any
external/hosted adapter call, the Core-controlled Reality + Authority Revalidation
Gate must establish that the packet was Core-issued, is bound to the same provider,
has a live unconsumed/unexpired/unrevoked one-shot lease, every source is still
eligible for that provider, no source is erasing/tombstoned/erased, policy authority
is still valid, and governed source/privacy/deletion state has not changed since
compilation. Any failed or changed condition denies dispatch and purges/revokes the
packet artifact. Recompilation, if requested, reads only current governed state.

The synthetic send boundary is atomic in this limited sense:

`revalidate -> consume one-shot authorization -> invoke adapter`

with no intentional gap or reusable authorization. This does not prove production
transaction/process/network atomicity. The exact production representation of
snapshot/version, source watermark, privacy/deletion generation, lease token, policy
version, and packet digest is deferred to later implementation/ADR work.

An undispatched packet remains under HumanOS control and is revocable. After bytes
have already been transmitted to an external provider, HumanOS cannot claim external
recall. Provider retention/deletion capability where available, disclosure audit,
prevention of future redisclosure, and local packet/response retention belong to the
later Privacy Lifecycle work; post-dispatch external deletion is outside this proof.

Inbound V-05 ContextRequests remain Core-issued, invocation-bound, provider-bound,
untrusted, and single-consumption. Recompilation uses the shared current store and
re-applies classification, erasure, and provider authorization.

## Evidence boundary

The V-01 through V-05 focused artifacts remain the accepted individual contract
proofs. `experiments/ln0_composition_harness.py` and
`tests/test_ln0_cross_v_lifecycle.py` are separate composition qualification
evidence. Neither category implements LN-1 or qualifies production Runtime 0.1.
The Schema/Integrity ADR, SQLCipher runtime-binding/key-custody ADR, controlled
migration/cutover plan, and other canonical PRE-LN-1 decisions remain mandatory.
