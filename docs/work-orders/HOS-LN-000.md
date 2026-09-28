# HOS-LN-000 — Life Notebook LN-0 Consolidation

**Status:** V-01–V-05 accepted (V-03/V-04/V-05 promoted); initial external review found one payload-integrity schema blocker; documentation-only correction prepared for V2 review; owner implementation-ready decision pending
**Workspace:** `WS-HUMANOS`  
**Branch:** `life-notebook-ln0`
**Baseline:** promoted LN-0 branch head before this documentation/evidence reconciliation @ `5eec801abc498a0325350004b7a816cfac1a5bb8` (includes promoted V-05)
**Architecture contract:** `docs/life-notebook/LN0_CONSOLIDATED_ARCHITECTURE.md`  
**Baseline map:** `docs/life-notebook/LN0_BASELINE_MAPPING.md`  
**Verification plan:** `docs/life-notebook/LN0_VERIFICATION_PLAN.md`

## Outcome

Merge the existing HumanOS Life Notebook/runtime foundation with the new Life Notebook architecture so that LN-1 can be implemented without creating a competing runtime, rewriting working components unnecessarily, or reopening constitutional work.

## Why now

The current runtime already has real Life Notebook capture, recovery, context, capability, browser, and conversation-capture infrastructure. Recent architecture work added stronger requirements for intelligence sovereignty, the Canonical State / Knowledge Graph separation, source authority, provider isolation, encrypted durable storage, deletion fan-out, and enterprise-grade SDLC/agent roles.

These must be reconciled into one implementation path before schema/security work begins.

## Classification

`EXTEND` — this is not a new HumanOS system. It extends the existing `runtime-0.1` Life Notebook and Context work.

## Existing foundation found

Repository inspection on 2026-09-25 confirmed:

- default/canonical branch is `runtime-0.1`;
- current branch head at inspection: `0cf78d9abe5dcfcc6114bb43167dcf7406478657`;
- the repository is Python-first today;
- `notebook.py` already has a process writer lock, SQLite WAL, append-only transcript/events, recovery tables, HMAC-keyed content integrity, transaction helpers, and readback/integrity enforcement;
- `conversation_capture.py` already provides provider-neutral exact host-turn capture with keyed idempotency and checkpoint verification;
- `conversation_ledger.py` already provides append-only external-message import with source identity and conflict detection;
- `context_registry.py`, `context_runtime.py`, `context_graph.py`, and related work orders already form an active Context/Brain lineage;
- `AGENTS.md` and `docs/foundation/WORKFLOW_STANDARD.md` already define repository routing, focused workstreams, evidence-based promotion, independent review, rollback, and preservation rules;
- `README.md` explicitly distinguishes verified runtime behavior from planned work and documents current Life Notebook boundaries/limitations.

## Preserve

Do not replace these without a proven reason:

1. exact transcript fidelity;
2. read-back verification before checkpoint claims;
3. single-writer discipline;
4. idempotent/retry-safe capture;
5. truthful recovery/degraded states;
6. append-only evidence/correction history;
7. local-first authority;
8. model/provider abstraction;
9. Context Registry / Context Runtime lineage;
10. capability/authorization separation;
11. test/CI/rollback discipline;
12. existing runtime evidence and frozen history.

## New architecture to integrate

The LN-0 architecture adds/refines:

- three semantic planes: Notebook evidence, Canonical State, Knowledge Graph;
- authority order: Notebook > State > Graph;
- sole Ingestor kernel writer;
- sole State Applier State writer;
- least-privilege projection workers;
- source authority ceilings;
- four policy axes: epistemic, sensitivity, delegation, provider;
- models consume ContextPackets and do not browse the Brain;
- unique independently deletable payload objects;
- State watermark/poison-event semantics;
- mention-first reversible entity resolution;
- projection checkpoints/impact invalidation;
- deletion fan-out to all persistent derived bytes;
- encrypted storage/key-recovery direction;
- external-provider isolation as an enforceable boundary;
- mobile v1 as capture-only, not replicated Brain.

## Explicit non-goals

This slice does **not**:

- rewrite the Constitution or Foundation;
- ratify old Foundation candidates;
- rewrite HumanOS in Rust;
- start LN-1 schema implementation;
- build the Knowledge Graph;
- build embeddings;
- add cloud providers;
- solve distributed/multi-device Brain replication;
- create a second Notebook/runtime;
- migrate or delete existing Notebook evidence.

## Risks

1. redesigning around old candidate documents instead of current runtime reality;
2. accidental schema rewrite before migration/recovery design exists;
3. conflating Graph confidence with Canonical State authority;
4. giving local/external models direct Brain retrieval;
5. treating encryption/security recipes from model reviews as verified facts;
6. adding governance artifacts that duplicate existing workflow/status systems;
7. breaking current exact-capture/recovery behavior while trying to improve architecture.

## Acceptance criteria

HOS-LN-000 is complete when:

- [x] current repository/runtime foundation has been inspected read-only;
- [x] merge map (preserve/refine/defer) is documented;
- [x] consolidated LN-0 architecture contract exists on this branch;
- [x] exact current Notebook schema/capture/recovery behavior is mapped to proposed `NotebookEventV1` / `PayloadObjectV1` without assuming destructive migration;
- [x] Context Compiler/current Context Runtime integration point is mapped;
- [x] component capability matrix is translated into implementable writer/model/worker boundaries at architecture level;
- [x] encryption/key-recovery spike plan is written;
- [x] SQLCipher/SQLite WAL behavior is verified from primary technical evidence and a reproducible spike on the target Mac; canonical tracked evidence: `docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md`;
- [x] deletion fan-out dependency contract is turned into test cases/spec packet;
- [x] source-authority/ingestion abuse cases are turned into test cases/spec packet;
- [x] bounded LN-1 work order is written below with executable acceptance tests; it is a proposal and does not authorize implementation;
- [ ] independent architecture/security review finds no unresolved schema-blocking defect;
- [ ] one explicit owner decision promotes LN-0 from candidate to implementation-ready.

## Evidence plan

Use:

- current repository files and exact commit SHAs;
- automated tests and CI for existing behavior;
- isolated test vaults only;
- primary SQLite/SQLCipher/macOS documentation for implementation claims;
- targeted local spikes for crash, encryption, key recovery, and process/egress behavior;
- independent reviewer packets containing the same requirements/diff/evidence;
- no owner Notebook content in Git or hosted-model review packets.

## Rollback

This closure-reconciliation pass changes LN-0/status documentation and adds synthetic
verification/review evidence only. `runtime-0.1`, owner Notebook data, and V-03/V-04/V-05
fixtures/tests remain untouched. Reverting this pass must preserve promoted V-03/V-04/V-05
history and must not be treated as a reason to delete or rewrite the promoted branch.

## V-02 target Mac SQLCipher proof — 2026-09-28

The existing `experiments/ln0_sqlcipher_spike_v2.py` ran unchanged on this Apple
Silicon Mac and returned **PASS**, exit status 0. The target is macOS 26.6.2
(`25G83`), arm64, Python 3.13.15, SQLCipher 4.19.0 community at
`/opt/homebrew/bin/sqlcipher`. Both `sqlcipher --version` and
`PRAGMA cipher_version;` identify SQLCipher 4.19.0. The full result, exact command,
environment, and spike source hash are preserved in
`docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md` (SHA-256
`a335daa5fc99595a60dc0644d25697598ed52c69822fafa441b672a15818c02e`).

The spike verified encrypted creation/readback, wrong-key and standard-SQLite
rejection, observed WAL operation, no governed synthetic marker in the DB/WAL/SHM,
committed data recovery and uncommitted transaction rollback after SIGKILL,
encrypted export/restore under a separate key, and the independent AES-GCM wrapper
round-trip. A separate ephemeral synthetic check verified SQLCipher no-key access
fails. No Homebrew-specific runtime or production dependency was added. Homebrew is
workstation development tooling only, not a HumanOS runtime, production, or
deployment dependency.

This establishes storage-layer feasibility and synthetic wrapper behavior, not
production key custody. The Mac Keychain integration, final KDF/wrapping format,
recovery-secret distribution/custody, rotation, and backup/deletion policy remain
explicit design/ADR decisions before production implementation. SQLCipher's tested
WAL configuration was exercised; rollback-journal mode and temp-file packaging
were not separately qualified by this spike.

### V-02 evidence durability

The original evidence file under ignored `evidence/ln0/` is preserved unchanged,
SHA-256 `a335daa5fc99595a60dc0644d25697598ed52c69822fafa441b672a15818c02e`.
Because that directory is ignored by Git, its complete safe Markdown contents are
also copied byte-for-byte into the canonical tracked path
`docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md` with the same SHA-256. The
tracked copy is the authoritative reference for the future LN-0 closure commit;
neither version contains keys, passwords, owner data, or raw logs.

## LN-0 closure criteria reconciliation — 2026-09-28

The Architecture Definition of Done (items 1–12) and the overlapping HOS-LN-000
acceptance criteria are reconciled here; overlapping items are mapped once rather
than treated as additional independent requirements.

| Criterion | Status | Existing evidence | Missing evidence | Next action |
|---|---|---|---|---|
| 1. Current repository baseline is inventoried | PASS | HOS-LN-000 existing-foundation inventory; V-01/V-02 evidence | None for LN-0 scope | None |
| 2. Existing runtime behavior to preserve is documented | PASS | HOS-LN-000 Preserve list; baseline mapping | None identified | None |
| 3. Event/payload contracts are specified | PASS — deletion-safe invariant and pre-LN-1 ADR gate explicit | Consolidated architecture §§6,8,16; mandatory Schema/Integrity ADR gate below | Final commitment representation and exact event-hash coverage remain unresolved by design | Resolve in accepted Schema/Integrity ADR before schema persistence or real capture |
| 4. Source-authority and writer-authority matrices are specified | PASS | Consolidated architecture; V-03 source-authority proof | None identified | None |
| 5. Capture/recovery semantics are mapped from existing HOS-006 behavior | PASS | Consolidated architecture and baseline mapping; V-01/V-03 evidence | None identified | None |
| 6. State watermark/poison semantics are specified | PASS | Consolidated architecture §12 | None identified | None |
| 7. Deletion fan-out semantics are specified | PASS — V-04 contract plus permanent-digest prohibition and ADR gate | Consolidated architecture §16; V-04 PASS / PROMOTED; low-entropy erase acceptance below | Final lifecycle/backup/idempotency interaction must be resolved in the ADR | Resolve in accepted Schema/Integrity ADR before schema persistence or real capture |
| 8. Model/context boundary is specified | PASS | Consolidated architecture §§15,18; V-05 PASS / PROMOTED | None identified | None |
| 9. Encryption/key-recovery design is verified enough to bound LN-1 | PASS — bounded feasibility only | Existing V-02 CI evidence plus this target-Mac V-02 proof and synthetic independent-wrapper round-trip | Production Keychain/KDF/custody/rotation/backup decisions remain open | Keep those decisions as LN-1 pre-implementation ADR gates; external reviewer assesses sufficiency |
| 10. SQLCipher/storage spike produces target-stack evidence | PASS | `docs/life-notebook/LN0_V02_TARGET_MAC_EVIDENCE.md`; SQLCipher 4.19.0 on macOS 26.6.2 arm64 | Rollback-journal mode and temp-file packaging not separately tested | Carry explicit limits into LN-1 tests/design |
| 11. LN-1 work order has bounded scope and executable acceptance tests | PASS — proposed below | Proposed LN-1 work order in this document | Not implemented; no implementation readiness claimed | External review, then owner readiness decision |
| 12. No frozen/runtime evidence is overwritten or falsely superseded | PASS | V-03/V-04/V-05 hashes recorded in this reconciliation; runtime untouched | None identified | Recheck hashes before review package freeze |
| Independent architecture/security review finds no unresolved schema-blocking defect | REVIEW — initial review found one schema blocker; this documentation-only correction addresses it | Initial external review result and this V2 packet | Independent review of the correction | Submit V2 package; do not close LN-0 before PASS |
| Explicit owner decision promotes LN-0 to implementation-ready | OWNER DECISION | None | Explicit owner approval after review | Await owner decision after review PASS |

Frozen implementation/test SHA-256 values verified for this reconciliation:

| Evidence | SHA-256 |
|---|---|
| V-03 fixture `experiments/ln0_v03_ingestor.py` | `57b3916a316543de8afc928e3784189fc7bf9baccf6ae3ecfb7d73ca14420c50` |
| V-03 tests `tests/test_ln0_v03_ingestor.py` | `b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6` |
| V-04 fixture `experiments/ln0_v04_deletion_fanout.py` | `8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39` |
| V-04 tests `tests/test_ln0_v04_deletion_fanout.py` | `e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03` |
| V-05 fixture `experiments/ln0_v05_context_boundary.py` | `7a1aebf8d6556ee8c6380340759794bfd0854df94861b2a3e216bb552a5c7693` |
| V-05 tests `tests/test_ln0_v05_context_boundary.py` | `8fc5427ec9502a50f2d585a9830ece9f1dbbccdbd85e377eb0584b05fd794333` |

V-01 and V-02 are accepted; V-03, V-04, and V-05 remain PASS / PROMOTED. The
verification-plan exit criteria, architecture DoD, and HOS-LN-000 acceptance list
are aligned by this mapping. LN-0 remains **ACTIVE / NOT CLOSED** until the review
gate passes and the owner separately records implementation readiness.

## Proposed bounded executable work order — LN-1 Capture → Encrypted Kernel

**State:** review candidate only. This section does not authorize LN-1 implementation.

### Objective

Add the smallest additive path that durably captures an authorized `CaptureRequest`
as an encrypted `NotebookEventV1` plus its independently deletable
`PayloadObjectV1`, then reads it back and reports truthful capture/checkpoint state.
Preserve existing Runtime 0.1 behavior until migration/cutover acceptance proves
equivalence.

### Prerequisites

- LN-0 external architecture/security review returns PASS with no unresolved
  schema/security blocker.
- Jon explicitly records the implementation-ready decision.
- A separate PRE-LN-1 Schema/Integrity ADR is reviewed and accepted before any
  `NotebookEventV1` / `PayloadObjectV1` persistence implementation or real capture.
  It resolves the payload commitment representation; whether/how `event_hash`
  commits payload information; `content_hash` lifecycle; erase behavior;
  idempotency/duplicate detection; backup/restore; and interaction with V-04
  ErasureTag/deletion semantics. This gate does not select an algorithm in LN-0.
- Before production encryption code, an owner-reviewed ADR selects the SQLCipher
  runtime integration, key creation and local/recovery wrapper formats, platform
  key storage, KDF parameters, custody/recovery process, rotation, and backup policy.
  Homebrew is not an allowed runtime/deployment assumption.
- Baseline the exact production commit and the existing migration/rollback path.

### Scope and non-goals

Scope is one additive capture-to-kernel vertical slice: capture adapter → Ingestor
(sole kernel writer) → encrypted durable event and unique payload object → exact
readback → truthful status/checkpoint. Integrate the existing `notebook.py`,
`conversation_capture.py`, and `conversation_ledger.py` behavior as appropriate;
limit changes to the smallest selected storage/capture modules, migrations, and
focused tests. Exact new module names are chosen after the implementation baseline
is inspected.

Do not build Canonical State, Knowledge Graph, summaries, embeddings, external
providers, autonomous identity resolution, multi-device replication, or a new
runtime. Do not destructively migrate, delete, or rewrite existing Notebook data.
Backup product features are not required in this slice; any implemented export or
restore must use a separately keyed encrypted destination and prove restore with
the correct key and rejection with an incorrect key.

### Mandatory schema/integrity ADR gate

This gate is distinct from the SQLCipher/key-custody ADR. It blocks all kernel
event/payload schema implementation and real capture until the exact commitment
representation and `event_hash` coverage are reviewed and accepted, and until
content-hash lifecycle, deletion, idempotency/duplicate detection, backup/restore,
and V-04 ErasureTag interaction are specified with tests. No final cryptographic
algorithm is selected by this proposal.

### Authority and data contracts

- Capture occurs before model-dependent compute whenever the path permits.
- The Ingestor is the sole kernel writer. Sources submit evidence; Core resolves
  source authority, sequence, hashes, timestamps, classification, and status.
  Callers/models cannot self-assign owner authority, `seq`, hashes, or verified
  capture status.
- Implement only the approved `NotebookEventV1` and `PayloadObjectV1` fields and
  relationships from the consolidated architecture. Each event owns a unique,
  independently deletable payload object. `payload_commitment?` is not an
  ordinary permanent digest of erasable plaintext. `content_hash` may be used only
  while the governed payload exists and must not survive ERASE as a
  dictionary-testable plaintext fingerprint. Exact lifecycle and event-hash
  coverage come from the accepted Schema/Integrity ADR. Content hashes are not
  shared object identity.
- Preserve exact text, speaker order, Unicode, whitespace, provenance, idempotency,
  and read-back-before-checkpoint behavior.
- Preserve distinct truthful states: `PENDING`, `PARTIAL/INCOMPLETE`, `WRITTEN`,
  `READ_BACK_VERIFIED`, `CHECKPOINTED/VERIFIED`, `FAILED`, and
  `RECOVERY_REQUIRED`; naming may normalize only in the schema ADR, not collapse
  semantics.

### Encryption, WAL, and recovery contract

- Use a random data-encryption key and the two-wrapper direction: local OS secure
  storage plus an independent recovery wrapper. The model/provider is never key
  authority. No plaintext fallback is permitted.
- Apply the key before any page access. Use only the SQLCipher configuration
  selected in the reviewed ADR; do not copy unverified model-generated settings.
- Under the chosen journal mode, demonstrate encrypted main DB and all active WAL,
  SHM, rollback-journal, and temporary storage artifacts in scope. Known governed
  synthetic plaintext markers must be absent from persistent database/journal
  bytes. A SQLCipher/key failure must not expose raw plaintext.
- Correct local/recovery authorization opens the database; wrong, absent, corrupt,
  or unavailable key material fails closed and reports `RECOVERY_REQUIRED` (or
  `FAILED` before durable capture). Loss of both independent wrappers is
  irrecoverable and must be stated truthfully; no provider can recover it.
- Test crash recovery for committed and uncommitted writes. Backup/export/restore
  behavior is tested if included; encrypted exports use separate key material.

### Executable acceptance tests

1. Exact synthetic capture is durable before enrichment; forced enrichment failure
   does not lose capture or fabricate a successful checkpoint.
2. Readback byte-compares original text/provenance before checkpoint status.
3. Duplicate retry returns the same event; conflicting reuse fails closed;
   concurrent distinct captures preserve one global sequence/previous-hash chain.
4. Only the Ingestor can append; source/model attempts to self-authorize or forge
   canonical fields are rejected.
5. Payload objects are unique per event and independently addressed/deletable.
6. Wrong/no key and corrupt/missing wrapper fail closed; authorized recovery
   restores access without provider participation.
7. SQLCipher correct-key reopen succeeds; standard SQLite and wrong-key access
   fail. WAL/crash tests preserve committed work and roll back uncommitted work.
8. Synthetic marker scans cover DB, WAL, SHM, rollback journal when used, and
   selected temporary files. No marker appears in governed persistent bytes.
9. Existing exact-capture, idempotency, recovery visibility, and migration fixtures
   remain green; no destructive migration or owner-data test is used.
10. Capture a synthetic low-entropy payload and complete the authorized erase
    lifecycle. Verify governed plaintext is gone; an ordinary plaintext-derived
    digest is absent from immutable kernel/event history, receipt, projections,
    caches, and backup state in scope; structural chronology/tombstone/deletion
    evidence survives; the event/integrity chain remains valid; and no kernel
    history rewrite was required. Include V-04 ErasureTag reconciliation in the
    same acceptance proof.

### Failure, rollback, evidence, and promotion

Storage/key failure never becomes a false `WRITTEN` or `CHECKPOINTED` claim. Keep
the old path available until additive migration and readback equivalence pass.
Rollback disables the new capture path and restores the prior runtime selection;
it does not delete evidence, decrypt/overwrite the prior store, or discard events
already durably committed.

Preserve exact tested commit, target OS/architecture, runtime/native SQLCipher
versions, key-configuration reference (never secret material), commands, full
focused output, hashes, recovery/crash results, known limitations, and rollback
confirmation in the LN-1 evidence location. Promotion requires focused and affected
regressions, migration/readback proof, `git diff --check`, scope/hash audit,
independent review of the immutable candidate, and owner-authorized promotion under
the HumanOS SDLC. No implementation or promotion is authorized by this proposal.

## V-03 execution record — 2026-09-26

Attempts 1–4 are preserved as **FAILED / rejected evidence**. Independent
Review #2 rejected Attempt 2's caller-created trusted-principal boundary. Attempt
3's isolated fixture added authenticated-session resolution, resolved-source
idempotency, exact-byte canonical hashing, mutation verification, actual-path
SIGKILL recovery, and projection-failure isolation. Attempt 4 was rejected for
omitting persisted `ingested_at` from the commitment, lacking real concurrent
distinct-event ancestry coverage, and recording stale/contradictory counts.
The completed independent review of Attempt 5 returned **PASS WITH FINDINGS**,
with no blocking findings. The promotion decision is **YES**. V-03 status:
**PASS / PROMOTED**.

### V-03 review lineage

- Attempt 1 — FAIL — caller-controlled source label granted authority.
- Attempt 2 — FAIL — trusted principal remained caller-created; crash/integrity proof inadequate.
- Attempt 3 — FAIL — authentication remained forgeable; canonical commitment incomplete.
- Attempt 4 — FAIL — `ingested_at` uncommitted; distinct concurrent ancestry not tested; evidence inconsistent.
- Attempt 5 — PASS WITH FINDINGS / PROMOTED — no blocking findings; promotion decision YES.

Attempt 5 replaces only the isolated fixture and tests. It uses a HumanOS-owned
test authenticator with opaque signed tokens, resolved principal/policy, semantic
submission fingerprints, and one complete authoritative envelope. It does not
modify Runtime 0.1 production code or Notebook data. Focused execution:
`python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**.
The fixture has no separately persisted payload store, so no separate-payload
orphan claim is made. The actual event transaction SIGKILL proof left no
committed event. The independent verdict is **PASS WITH FINDINGS** with no
blocking findings; the promotion decision is **YES**.

Required broader execution: `python3 -m unittest discover -s tests -v` — **592
tests run, 11 skipped, and 1 sandbox loopback PermissionError** in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`. This is unrelated to
V-03 and prevents claiming a completely green repository suite. Record it as a
separate known environment/test issue for later investigation; do not alter
`test_swarm.py` as part of V-03. No Runtime 0.1 production source or owner
Notebook data was modified.

## V-04 execution record — 2026-09-26

The isolated fixture in `experiments/ln0_v04_deletion_fanout.py` and focused tests in
`tests/test_ln0_v04_deletion_fanout.py` cover the V-04 acceptance contract without
touching Runtime 0.1 or owner Notebook data. Focused execution was **8/8 passed**.
V-03 regression was **8/8 passed**. Full regression was **600 tests, 11 skipped,
1 error**, the known sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; no V-04 or V-03 test
failed, and `test_swarm.py` was not modified. `git diff --check` passed.

The fixture proves lineage-driven sole-source deletion, multi-source recomputation,
independent State survival, payload-identity isolation, immediate ContextPacket
invalidation, idempotent tombstones, visible degraded recovery, retry completion,
partition locality, and tombstone-first backup restore. Its final scanner searches
all synthetic persistent stores and permits the byte-identical payload only under its
independent event identity. SHA-256 hashes and limitations are recorded in
`docs/life-notebook/LN0_VERIFICATION_RESULTS.md`.

V-04 remains **not PASS / not PROMOTED** pending independent review and does not
authorize production implementation.

## V-04 Attempt 2 execution record — 2026-09-26

Attempt 1 remains **FAIL / rejected** and is not rewritten as success. The blocking
reasons were hard-coded State survival, unchecked lineage rather than real event IDs,
and restore proof that did not deny live presentation before tombstone replay.
Attempt 2 is limited to the synthetic fixture and tests. It validates mandatory
non-empty `source_event_ids` lineage, derives survival from an independent
`E3_OWNER_RATIFICATION` event, gates restore reads until replay/activation, scopes the
identical-payload exception to the independent event identity, and exercises a real
fan-out exception through the orchestrator. Its independent review later returned
FAIL for insufficient generic authority and persistent-boundary lineage enforcement.
It did not modify Runtime 0.1 or owner Notebook data.

## Next action

Preserve the completed independent review and investigate the separate sandbox
loopback environment/test issue later. V-03 implementation and tests remain
unchanged by this promotion documentation update.

V-04 Attempt 8 is promoted. Proceed to the **V-05** verification gate, then reconcile
the LN-0 exit criteria and remaining LN-1 work. Investigate the separate sandbox
loopback and public-registry routing-hygiene findings outside this promotion slice.

## V-04 Attempt 3 execution record — 2026-09-26

Attempt 1 — **FAIL / rejected** for hard-coded State survival, unchecked lineage,
and restore presentation before replay. Attempt 2 — **FAIL / rejected** by
independent review because authority and lineage enforcement did not meet the
generic/storage-boundary contract. Both remain preserved as failed evidence.

Attempt 3 was submitted for independent review, not marked PASS or PROMOTED. Focused
execution was **8/8 passed** with ResourceWarnings elevated; V-03 was **8/8**;
the broader suite was **600 tests, 11 skipped, 1 sandbox loopback PermissionError**
in `test_swarm.SwarmTests.test_live_loopback_and_attribution`. `git diff --check`
passed. Payload `NULL` proves logical deletion only, not physical SQLite erasure;
synthetic derived stores prove the contract only, not production engine behavior.
No commit or push was made.

### V-04 Attempt 3 deletion-audit extension

The bounded pre-review extension adds explicit erase lifecycle evidence and an
append-only, content-free `DeletionReceiptV1`. It proves durable deletion identity,
payload tombstone retention, immutable receipt integrity, recovery-required failure,
idempotent retry, zero unresolved derivatives before completion, scanner coverage of
tombstone/audit/receipt stores, and restore proof without content resurrection.
Attempts 1 and 2 remain preserved as rejected evidence. This extension does not
change the already-qualified authority, lineage, restore, or fan-out architecture.
The subsequent independent promotion review returned **FAIL** for the blockers listed
in the Attempt 4 record below.

## V-04 Attempt 4 execution record — 2026-09-26

Attempt 1 — **FAIL**: hard-coded State survival, unchecked source lineage, and no
pre-replay presentation denial. Attempt 2 — **FAIL**: insufficient generic authority
and storage-boundary lineage enforcement. Attempt 3 — **FAIL** after independent
promotion review: ordinary plaintext SHA-256 retention; incomplete structural
provenance; hard-coded actors and integer times; duplicate completion on retry;
receipt hashes without chain verification; trusted receipt restore/import; hard-coded
fan-out metrics; and incomplete integrity-protected verification/scanner proof.

Attempt 4 is a bounded correction in the synthetic fixture and tests only. It retains
opaque per-payload object identity and a commitment over that identity rather than
erasable plaintext; preserves event/page/block chronology; receives distinct request,
authorization, and execution principals; measures resolver outcomes; completes one
stable deletion exactly once; verifies canonical receipt metadata and chain links;
and fails restore closed before tombstone replay, fan-out reconciliation, completion
verification, and LIVE activation. The scanner dynamically covers every synthetic
persistent table. It does not synthesize semantic descriptors.

Attempt 4 was submitted for review as not PASS and not PROMOTED. It remains a
synthetic logical-erasure contract fixture, not proof of SQLite physical remanence
destruction. Production encrypted-payload integrity and the non-plaintext object
commitment remain to be finalized in the kernel/encryption ADR. No Runtime 0.1 source,
owner Notebook data, commit, or remote branch was changed.

Required execution: focused V-04 **9/9 passed** with ResourceWarnings elevated; both
separate V-03 runs **8/8 passed**; full discovery ran **601 tests, 11 skipped, 1
error**, solely the known sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; `git diff --check` passed.
Candidate hashes are recorded once for Attempt 4 in `LN0_VERIFICATION_RESULTS.md`.

## V-04 Attempt 5 execution record — 2026-09-26

Attempts 1–4 remain **FAIL / rejected evidence**. Attempt 4's independent review
identified exactly three promotion blockers: a completed receipt could be restored
without its tombstone and resurrect plaintext; deleting the final receipt or entire
receipt chain was not detectable; and deletion authority trusted arbitrary
caller-supplied principal strings.

Attempt 5 adds a reconciliation set over tombstones, receipts, and lifecycle evidence
keyed by `deletion_id`; completed operations require exactly one mutually coherent
tombstone, receipt, target identity, and `ERASE.COMPLETED`. A truthful
`ERASE.RECOVERY_REQUIRED` state may retain one tombstone without a receipt, but must
replay, verify fan-out, create one receipt/anchor/completion, and re-reconcile before
LIVE activation. Reads remain gated throughout restore failure or recovery.

The isolated receipt projection is checked against separate append-only
`receipt_chain_anchors` records containing receipt count, head hash, and final
sequence. Normal update/delete APIs are blocked. This is only a fixture stand-in:
production anchoring belongs to HumanOS kernel integrity/checkpoint architecture.
Deletion calls present opaque fixture tokens to a HumanOS-owned authenticator;
receipts retain resolved requester/authorizer identities and the internally assigned
executor. Capability is not authority.

Attempt 5 is **awaiting independent review**, not PASS and not PROMOTED. Runtime 0.1,
owner Notebook data, commits, and remotes remain untouched. The public Context
Registry's lack of an explicit HOS-LN-000 entry is a separate routing/index hygiene
finding, not a V-04 blocker.

Required execution produced focused V-04 **16/16 passed**; both V-03 runs **8/8
passed**; full discovery **608 tests, 11 skipped, 1 error**, solely the known sandbox
loopback `PermissionError`; and `git diff --check` passed. Exact candidate hashes are
recorded in `LN0_VERIFICATION_RESULTS.md`.

## V-04 Attempt 6 execution record — 2026-09-26

Attempts 1–5 remain **FAIL / rejected evidence**. Attempt 5's independent review
reproduced a false `ERASE.COMPLETED` when an unrelated persistent cache retained the
deleted bytes, a public raw `db()` restore-quarantine bypass, coordinated truncation
accepted by receipt-chain verification alone, and inconsistent candidate hashes/counts.

Attempt 6 restores a mandatory all-persistent-table forbidden-content scan before
completion. Its only byte-identical exception is an explicitly identified independent
event payload cell; unrelated artifacts receive no lineage-based exemption. Public
raw database access now requires LIVE state. The SQLite anchor remains a projection,
while receipt count, head hash, and final sequence must match a separately supplied
kernel checkpoint boundary, causing coordinated receipt/anchor/completion truncation
to fail. Idempotent completion and recovery also reverify that boundary.

New adversarial regressions cover all three reproduced failures. All already-correct
Attempt 5 authorization, deletion-ledger reconciliation, provenance, recovery,
idempotency, fan-out, and ordinary receipt-tamper behavior remains covered. This is
still an isolated logical-erasure fixture, not Runtime 0.1 production code or proof
of SQLite physical remanence destruction.

Required execution produced focused V-04 **19/19 passed**; both V-03 runs **8/8
passed**; full discovery **611 tests, 11 skipped, 1 error**, solely the known sandbox
loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; and `git diff --check`
passed. No Runtime 0.1 production source, owner Notebook data, `test_swarm.py`, commit,
or remote was changed. Exact frozen candidate hashes are recorded in
`LN0_VERIFICATION_RESULTS.md`.

## V-04 Attempt 7 execution record — 2026-09-27

Attempts 1–6 remain **FAIL / rejected evidence**. Attempt 6 independent review found
four blockers: its volatile captured-byte scan could not recognize an arbitrary
unlineaged copy after restart without retaining the erased bytes; restore could reach
LIVE without final all-store verification; public `search_persistent()` bypassed the
RESTORING gate; and final scan, receipt/checkpoint update, and `ERASE.COMPLETED` were
not atomic against persistent writers.

Attempt 7 replaces retained deleted bytes with a synthetic production-contract
ErasureTag: `HMAC(kernel_erasure_secret, deletion_id || canonical_deleted_bytes)`.
The authoritative tag and receipt checkpoint live in the supplied kernel boundary;
the secret is independently injected and neither it nor deleted plaintext is stored
in the restored Notebook DB or deletion receipt. Production secret storage belongs to
the encrypted-kernel/key architecture. Restore now performs checkpoint verification,
deletion-ledger reconciliation, tombstone replay, fan-out, all-store ErasureTag
verification, and unresolved-zero verification before LIVE.

Every enumerated public content-returning/scanning fixture method requires LIVE,
including `search_persistent()`. Internal restore verification uses private helpers.
Final all-store scanning, receipt/anchor insertion, kernel-checkpoint update, and
`ERASE.COMPLETED` execute under an exclusive SQLite writer transaction. A synchronized
second connection cannot insert between scan and completion; a pre-scan forbidden
copy fails completion; and the ordinary post-completion write boundary rejects erased
content as a new governed write.

The V-03 test now constructs a forged opaque token by replacing the last character
with a guaranteed-different character. This is a deterministic test-only flake
correction and does not reopen or modify the promoted V-03 implementation architecture.

Required local execution produced focused V-04 **22/22 passed**; both V-03 runs
**8/8 passed**; full discovery **614 tests, 11 skipped, 1 error**, solely the known
sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; and `git diff --check`
passed. Attempts 1–6 and the planning retrospective remain unchanged. Attempt 7 is
**awaiting independent review**, not PASS and not PROMOTED. No commit or push was made.

## V-04 Attempt 8 execution record — 2026-09-27

Attempts 1–7 remain **FAIL / rejected evidence**. Attempt 7 independent review found
exactly one promotion blocker: equality-only keyed ErasureTag matching did not detect
erased bytes embedded inside a larger persistent value.

Attempt 8 preserves all other Attempt 7 behavior and changes only the matching
boundary. The authoritative kernel erasure checkpoint now contains `deletion_id`,
`match_length`, and `erasure_tag`; a fixture-sized KDF derives a deletion-specific key
from the independently supplied kernel erasure secret and deletion ID, and HMAC tags
the canonical deleted bytes. Neither erased plaintext, ordinary plaintext SHA-256,
kernel secret, nor derived deletion key is persisted in the Notebook DB or receipt.

Every eligible persistent text/blob value is canonicalized to bytes and scanned over
every contiguous `match_length` window with constant-time tag comparison. Beginning,
end, middle, exact-cell, repeated, and binary occurrences are covered. The only
exemption remains an exact payload-cell match for an explicitly identified independent
source event; arbitrary artifacts, other lineage, metadata, caches, and larger values
containing the bytes are not exempt.

The two independent-review regressions prove that an unrelated embedded copy prevents
normal completion and leaves recovery-required evidence without a VERIFIED receipt,
and that an old backup containing an embedded copy cannot become LIVE or expose public
content until sanitized. All Attempt 7 regressions remain in place. Required final
execution counts and exact frozen hashes are recorded in
`docs/life-notebook/LN0_VERIFICATION_RESULTS.md`.

Independent promotion review returned **PASS**, with **no blocking findings** and
promotion decision **YES**. V-04 Attempt 8 is **PASS / PROMOTED**. Promotion evidence:
focused V-04 **26/26 passed**; V-03 **8/8 passed twice**; broad discovery **618 tests,
11 skipped, 1 error**, solely the known sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`. Attempts 1–7 remain
**FAIL / rejected historical evidence**. This fixture demonstrates synthetic logical
erasure and does not claim physical SQLite remanence destruction.

The independent reviewer retained one non-blocking routing-hygiene finding: the public
Context Registry lacks an explicit HOS-LN-000 entry. This promotion does not modify or
fix the router. The next verification gate is **V-05**.

## Requirements / Planning Retrospective — V-04

Owner intent was broader than the original V-04 scope. The original Life Notebook
requirement included the ability to hide, redact, and delete portions of personal
history without corrupting chronology, provenance, neighboring evidence, or derived
knowledge. V-04 was scoped too narrowly too early around tombstones, derivative
deletion, and anti-resurrection.

The broader privacy domain should have been mapped before implementation as a unified
lifecycle:

`HIDE / LOCK / REDACT / ERASE`

together with:

- structural provenance;
- chronology preservation;
- selective field/subfield treatment;
- derivative invalidation/recomputation across summaries, FTS, vectors, Knowledge
  Graph, caches, and ContextPackets;
- AI context exclusion;
- authorization and audit;
- reversible versus irreversible privacy operations;
- backup and restore semantics;
- protection against recovery of hidden/redacted/erased information through derived
  representations.

The mistake was requirements decomposition and scope planning, not a failure of the
later V-04 implementation work. A green test suite proves that the specified contract
is satisfied; it does not prove that the specification completely represents owner
intent.

Future substantial HumanOS subsystems must therefore follow:

`OWNER INTENT → REQUIREMENTS TRACEABILITY → DOMAIN RESEARCH → COMPLETE CAPABILITY MAP → ARCHITECTURE → THREAT / FAILURE MODEL → ACCEPTANCE CONTRACT → IMPLEMENTATION SLICES → BUILD`

V-04 remains intentionally bounded to the ERASE + structural provenance + deletion
evidence + anti-resurrection foundation. Full HIDE / LOCK / REDACT / ERASE privacy
behavior must not be added to V-04 now.

After V-04 is promoted, create a separate workstream/branch tentatively named
`HOS-LN-PRIV-001 — Life Notebook Privacy Lifecycle`, branched from the promoted V-04
foundation. That future workstream must perform the broader privacy-domain research
and architecture first, obtain owner approval of the capability map, and only then
begin implementation.

Preserve this retrospective as an SDLC lesson for future HumanOS development.

## V-05 local candidate record — 2026-09-27

This record captures Pass 3 and is superseded by the Pass 4 record below.

V-05 is a **REMEDIATION PASS 3 LOCAL CANDIDATE / EXTERNAL REVIEW NOT YET RUN** on
`experiment/v05-context-boundary-chunk2`, from exact promoted V-04 baseline
`e793aca454c087cb68503cb79871a844eb7bde03`. Only
`experiments/ln0_v05_context_boundary.py` and
`tests/test_ln0_v05_context_boundary.py` were added. Router policy was hardened
separately in local commit `7c8c5fc09dbdaade0ee98e6030e9227b79384702` and is not
part of the V-05 candidate.

This isolated synthetic future adapter-contract fixture keeps records, classification,
retrieval, policy, provider authorization, compilation, and parsing Core-owned. Hosted
providers receive only records explicitly authorized by Core for hosted disclosure;
Core-denied records do not enter a hosted ContextPacket or reach the hosted adapter on
either initial invocation or ContextRequest-driven recompilation. Source content and
models cannot self-assign or upgrade export authority. The fixture proves bounded
canonical packet/response sizes, byte-only local/hosted spies,
untrusted wrappers backed by immutable Core-held issuance state, replay-safe context-request recompilation, deny-by-default and
first-deny-wins behavior, S3 and LOCAL_ONLY hosted denial, and empty retrieval
and omitted-selection preservation. Unknown providers are rejected before any Core
record access. Focused V-05 tests passed **29/29** with
`python3 -m unittest tests.test_ln0_v05_context_boundary -v`. Directly affected
regressions passed **59/59** with
`PYTHONPATH=tests python3 -m unittest tests.test_ln0_v03_ingestor tests.test_runtime tests.test_notebook_recall -v`.
The single Pass 3 broad discovery via
`python3 -m unittest discover -s tests -v` recorded **647 run,
11 skipped, 1 error**,
the known sandbox loopback `PermissionError`; it is not green. `git diff --check`
is the final static gate. Tests used Python 3.13.15.

V-05 does not prove automatic discovery of secrets or sensitive content from arbitrary
plaintext. Content-classification/DLP capabilities are outside this synthetic boundary
proof. It also does not prove production integration, actual hosted providers,
OS/process/filesystem isolation, LN-6/LN-7, or owner Notebook behavior. The public
registry still lacks HOS-LN-000 and was not modified. No production runtime, owner
data, V-05 commit, push, PR, or promotion occurred. Rollback removes/reverts only the
V-05 fixture, tests, and this documentation append; the separate router-hardening
commit and promoted V-04 remain intact. Next
action: freeze Pass 3 evidence and provide a compact packet for external fresh read-only
review while remaining uncommitted, unpublished, and unpromoted. Do not invoke the
broken local Sol reviewer.

## V-05 Remediation Pass 4 — 2026-09-28

External review found one blocker: custom records without an explicit classification
received fallback `S1 / LOCAL_OR_EXTERNAL` and could reach the hosted adapter, contrary
to the explicit-authorization contract. Pass 4 changes only the synthetic V-05
fixture/test and evidence documentation. Hosted disclosure now fails closed unless
Core explicitly assigns `HOSTED_ALLOWED`; fallback classification does not grant
external authorization. The built-in `safe-1` receives explicit Core-owned fixture
authorization only on the built-in fixture construction path, so a caller-supplied
record cannot inherit it by using that ID. No content scanning or DLP was added.

Added adversarial tests prove an unclassified custom record with credential/path-like
plaintext is denied with zero hosted adapter calls, a custom `safe-1` ID cannot self-
authorize, and explicitly `HOSTED_ALLOWED` lookalike content still succeeds. Pass 3's
initial hosted denial, same-provider ContextRequest reauthorization, and B1-B4 tests
remain covered. Focused Pass 4 result: **31/31 passed**. Affected regressions:
**59/59 passed**. The single broad-suite run was **649 run, 11 skipped, 1 error**:
the known sandbox loopback `PermissionError` in `test_swarm.SwarmTests.test_live_loopback_and_attribution`; no V-05 failure occurred and the suite is not green. Final
hashes are recorded in the verification results.

V-05 remains synthetic fixture evidence. It does not prove arbitrary plaintext DLP,
production provider integration, OS/process/filesystem isolation, LN-6/LN-7, or owner
Notebook behavior. At Pass 4 candidate freeze, no commit, push, PR, or promotion had
occurred. Rollback remains limited to the V-05 fixture, tests, and V-05 documentation;
promoted V-04 and the separate router-hardening commit remain intact.

## V-05 external promotion review — 2026-09-28

External review result: **PASS**. Blocking findings: **none**. Security/code blockers:
**0**. The reviewer independently verified the frozen Pass 4 fixture and test hashes,
the 31/31 focused suite, unclassified-record and custom-`safe-1` denial, explicit
`HOSTED_ALLOWED` lookalike success, and hosted ContextRequest reauthorization before a
second adapter call. The reviewed hashes are fixture
`7a1aebf8d6556ee8c6380340759794bfd0854df94861b2a3e216bb552a5c7693` and tests
`8fc5427ec9502a50f2d585a9830ece9f1dbbccdbd85e377eb0584b05fd794333`.

Pass 4 evidence remains: focused **31/31 PASS**; affected regressions **59/59 PASS**;
broad suite **649 run / 11 skipped / 1 known sandbox loopback PermissionError**, no
V-05 failure, broad suite **NOT GREEN**. This record documents external review only;
promotion publication state is verified by Git commit and remote push evidence.
