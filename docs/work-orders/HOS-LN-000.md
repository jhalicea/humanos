# HOS-LN-000 — Life Notebook LN-0 Consolidation

**Status:** V-03 PASS / PROMOTED; V-04 Attempt 8 PASS / PROMOTED
**Workspace:** `WS-HUMANOS`  
**Branch:** `life-notebook-ln0`  
**Baseline:** `runtime-0.1` @ `0cf78d9abe5dcfcc6114bb43167dcf7406478657`  
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
- [ ] SQLCipher/SQLite WAL behavior is verified from primary technical evidence and a reproducible spike;
- [x] deletion fan-out dependency contract is turned into test cases/spec packet;
- [x] source-authority/ingestion abuse cases are turned into test cases/spec packet;
- [ ] LN-1 work order is written with executable acceptance tests;
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

This workstream currently changes documentation only. `runtime-0.1` remains untouched. Delete/revert the `life-notebook-ln0` branch to abandon the candidate without affecting runtime behavior or Notebook data.

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
