# Life Notebook LN-0 — Verification Results

**Status:** ACTIVE EVIDENCE RECORD  
**Date:** 2026-09-26  
**Workstream:** `HOS-LN-000`

This file records what the LN-0 experiments have actually established. It does not
promote experiments into production runtime behavior.

---

## V-01 — Current-schema migration fixture

**Result:** PASS

Evidence implementation:

- `experiments/ln0_migration_spike.py`
- `tests/test_ln0_migration_spike.py`

Verified behaviors include:

- every synthetic Runtime 0.1 source DB row / selected projection has an explicit mapping;
- exact transcript text including whitespace, CR/LF and Unicode survives as payload bytes;
- identical HUMAN/ASSISTANT text produces distinct payload object identities while retaining equal content hashes;
- stable current identities remain explicitly mapped rather than silently discarded;
- unresolved recovery evidence remains unresolved instead of becoming a successful history record;
- privacy operation and receipt evidence remain distinct;
- existing digest / record-integrity fields remain preserved as legacy provenance;
- current projections remain classified as projections rather than source evidence;
- an unchanged migration rerun is idempotent;
- changing source evidence after migration causes a fail-closed conflict;
- candidate event/payload chain verification passes.

GitHub regression evidence:

- run `36216014250`
- tested commit `94be3b4cb34bacad23106044a5afc213d53fcc50`
- result: SUCCESS
- matrix: Ubuntu 24.04 + macOS 15, Python 3.11 + 3.13; all four jobs succeeded.

**What this proves:** a controlled application migration from representative
Runtime 0.1 evidence into a new event/payload model is feasible without requiring a
destructive rewrite of the source database.

**What this does not prove:** every owner/live Notebook edge case, production-scale
migration duration, or final target schema performance.

---

## V-02 — Encrypted SQLite / SQLCipher storage spike

### Revision 1

**Result:** FAILED

Run `36216169403` reached the dedicated encrypted-storage verification step and
failed. Installation/setup succeeded. The test used stdout timing as a live-process
readiness signal, which was not a reliable synchronization primitive for this
experiment. The failure was preserved rather than reclassified as success.

### Revision 2

**Result:** PASS

Revision 2 replaced stdout timing with an explicit filesystem readiness marker
created by the live SQLCipher shell after the tested SQL statement completed while
the database process remained alive. The parent then SIGKILLed the writer.

Evidence implementation:

- `experiments/ln0_sqlcipher_spike_v2.py`
- `tests/test_ln0_sqlcipher_spike_v2.py`
- `.github/workflows/ln0-sqlcipher-spike-v2.yml`
- `docs/life-notebook/LN0_SQLCIPHER_PRIMARY_EVIDENCE.md`

GitHub evidence:

- run `36216565273`
- job `108333571688`
- tested commit `7b83d797c6310ae3d4432bc8e4c733b073b06a66`
- runner: macOS 15 / Python 3.13
- SQLCipher installation: SUCCESS
- recovery-wrapper dependency installation: SUCCESS
- package/version recording: SUCCESS
- V-02 revision 2 verification: SUCCESS

The passing spike verifies, on that isolated GitHub macOS environment:

- a stable SQLCipher 4.x within the experiment's allowed range is usable;
- random 32-byte key initialization and exact readback work;
- a wrong key fails closed;
- standard-library SQLite cannot read the encrypted database;
- WAL mode can be active while DB/WAL/SHM are scanned for known random plaintext fixtures;
- known plaintext fixtures are absent from the tested encrypted DB/WAL/SHM paths;
- the encrypted DB does not expose a standard plaintext SQLite header;
- committed WAL data survives SIGKILL/reopen;
- an uncommitted transaction does not become committed after SIGKILL;
- encrypted `sqlcipher_export()` backup/restore works under a separate key;
- wrong-key backup access fails;
- a functional independent AES-GCM key-wrapper proof can recover the backup key;
- plaintext SQLite -> NEW encrypted SQLCipher export preserves synthetic data and an append-only trigger.

**What this proves:** the new encrypted-database / controlled cutover direction is
technically viable at the SQLCipher storage layer.

**What this does not prove:** Jon's exact local installation, final Keychain
integration, final KDF/key-wrap policy, every temp-file packaging/build setting,
production-scale durability, or a qualified Python runtime binding.

---

## V-02B — Python SQLCipher runtime binding candidate

**Candidate tested:** `sqlcipher3==0.6.2`

**Result:** REJECTED / INVESTIGATION ACTIVE

The candidate wheel installed successfully on all four HumanOS CI matrix targets,
but the qualification step failed on:

- macOS 15 / Python 3.11;
- macOS 15 / Python 3.13;
- Ubuntu 24.04 / Python 3.11;
- Ubuntu 24.04 / Python 3.13.

Evidence run: `36216699091`.

HumanOS therefore does **not** add this package to the runtime dependency set and
does not weaken the SQLCipher freshness/security requirement merely to make a
binding pass. A diagnostic workflow records the bundled core version and separates
basic DB-API functionality from the security freshness gate.

## V-04 — Tombstone fan-out / deletion dependency contract

**Result:** Attempts 1–7 FAIL / rejected; Attempt 8 PASS / PROMOTED

Attempt 1 is preserved as rejected evidence. Independent review found three blockers:
State survival was hard-coded to artifact kind/name, lineage was not structurally
validated against real source event IDs, and restore proof did not establish that
deleted content was unpresentable before replay.

Attempt 2 evidence implementation:

- `experiments/ln0_v04_deletion_fanout.py`
- `tests/test_ln0_v04_deletion_fanout.py`

Focused command: `python3 -W error::ResourceWarning -m unittest tests.test_ln0_v04_deletion_fanout -v` — **8/8 passed**.
The fixture uses only temporary synthetic SQLite databases. It proves lineage-required
derivatives across timeline, page, sole-source summary, FTS, vector, graph, binary,
cache, and retained ContextPacket classes; sole-source invalidation; multi-source
recomputation; independent owner-ratified State survival; identical-but-independent
payload isolation; idempotent tombstones; degraded fan-out with `RECOVERY_REQUIRED`;
retry recovery; partition locality; and pre-delete backup restore with tombstone
replay before live-state presentation. Focused count: 8/8. V-03 regression: 8/8.
Broader suite: 600 tests, 11 skipped, 1 sandbox loopback error.

The adversarial scanner searches all persistent synthetic stores. A byte-identical
independent payload is explicitly permitted by identity (`E1-copy`), so the scanner
excludes only that independently identified source; no E1 payload or derived copy is
permitted. This identity exception is required by the contract and is not a deletion
weakening.

Acceptance-condition matrix:

| Condition | Fixture evidence | Result |
|---|---|---|
| Source payload bytes removed; append-only tombstone retained | `tombstone`, `events.payload=NULL` | PASS |
| Every persistent derivative has lineage | insert guard and lineage test | PASS |
| Sole-source, FTS, vector, graph, page/timeline, binary, cache, ContextPacket fan-out | nine sole-source artifact kinds | PASS |
| Multi-source recomputes from E2 | `multi` lineage becomes `E2` | PASS |
| Independent owner-ratified State survives | `OWNER_RATIFIED` artifact | PASS |
| Byte-identical independent payload survives | `E1-copy` distinct event identity | PASS |
| Degraded processing is truthful and recoverable | `RECOVERY_REQUIRED`, retry | PASS |
| Backup restore replays tombstone before live state | fresh restore plus retained tombstone | PASS |
| Only affected partition changes | `p2` artifact equality | PASS |
| No forbidden E1 copy remains after completion | all-store scanner with identity exception | PASS |

Regression commands:

- `python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**.
- `python3 -m unittest discover -s tests -v` — **600 tests, 11 skipped, 1 error**:
  the known sandbox loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 tests
  passed. Do not modify `test_swarm.py` for V-04.
- `git diff --check` — passed.

Attempt 2 candidate SHA-256 (rejected):

```text
ae4a152835087d268e3cbe4f0eec37ed73be0c70cf62797e06c2a0040cc6d677  experiments/ln0_v04_deletion_fanout.py
cf85fac2fd8a801257ee71a26aa66d09fd0261d823c59d53f3707b4001287bb2  tests/test_ln0_v04_deletion_fanout.py
```

Known limitations: payload=NULL proves logical deletion semantics only; it does not
prove secure physical erasure, page-level SQLite remanence removal, or cryptographic
erasure. Synthetic FTS/vector/graph/binary stores are contract fixtures, not
production-engine verification. V-04 must not be marked PASS or PROMOTED.

This is the desired SDLC behavior: a failed candidate is evidence, not an excuse to
silently lower the requirement.

### V-04 Attempt 3 record — 2026-09-26

Attempt 2 was independently rejected because authority semantics remained tied to
fixture assumptions and lineage enforcement was not at the persistent storage
boundary. Attempt 3 was submitted for independent review, not marked PASS or PROMOTED. The
focused command with ResourceWarnings elevated passed **8/8** with no warning
output; V-03 regression passed **8/8**. The broader suite ran **600 tests, 11
skipped, 1 sandbox loopback error** in `test_swarm.SwarmTests.test_live_loopback_and_attribution`.

Attempt 3 adds generic `OBSERVED_EVIDENCE` / `OWNER_RATIFIED` authority,
`required_authority`, one fail-closed ordered rule, SQLite lineage triggers for
direct inserts and updates, replay of two tombstones, and a common live-read gate.

The bounded deletion-audit extension adds `ERASE.REQUESTED` -> authorization ->
`PAYLOAD.TOMBSTONE` -> fan-out/recomputation -> verification -> `ERASE.COMPLETED`,
with `ERASE.RECOVERY_REQUIRED` on downstream failure. Its immutable, content-free
`DeletionReceiptV1` survives payload NULL and restore, chains permitted receipt
metadata only, and never stores the deleted plaintext or a content-derived hash.
Payload `NULL` proves logical deletion only, not physical SQLite erasure. Synthetic
FTS/vector/graph/page/timeline/binary/cache/ContextPacket stores prove the contract
only, not production engine behavior.

Attempt 3 candidate SHA-256 (rejected):

```text
b5badb17344c171af1f1ccbcb3dae6ebd4091b9cc5fcb0ac7ab1c813f08c1b3e  experiments/ln0_v04_deletion_fanout.py
733017722ec1d7c75bce00af90690cb129b9577067ef616a8cfeafd068520831  tests/test_ln0_v04_deletion_fanout.py
```

Attempt 3 independent promotion review returned **FAIL**. Exact blockers: the event
store permanently retained `SHA256(plaintext)`; the receipt lacked required page,
position/block, source-event-type, and capture/ingestion chronology; lifecycle actors
and integer times were fabricated; retry could append another `ERASE.COMPLETED`;
receipt hashes were stored but never recomputed as a chain; restore trusted arbitrary
receipt rows; recomputation metrics were hard-coded; and verification/scanner evidence
did not close every persistent-store path. The generic authority, lineage, fan-out,
restore quarantine, and identity-isolation architecture was not rejected.

### V-04 Attempt 4 record — 2026-09-26

Attempt 4 was submitted for review as not PASS and not PROMOTED. The fixture
uses opaque payload-object IDs and hashes only the synthetic object identity, never
plaintext. It preserves content-free structural provenance, distinguishes request,
authorization, and execution principals with injectable UTC timestamps, derives all
fan-out counts from resolver results, and permits exactly one tombstone, receipt, and
`ERASE.COMPLETED` per stable deletion ID. Receipt verification canonicalizes permitted
metadata, recomputes every hash/link, and detects mutation and chain-structure damage
without erased content. Restore verifies imported receipts before replay and denies
LIVE activation on alteration or incomplete replay/count reconciliation.

The adversarial low-entropy case erases `Jon` and proves neither it nor its ordinary
SHA-256 remains in any persistent synthetic table. Dynamic scanning includes event
payload/metadata, payload-object metadata, tombstones, lifecycle audit, derivatives,
fan-out results, receipts and their integrity-protected verification fields, plus
cache and ContextPacket fixture artifacts. No semantic descriptor is generated.

Required execution:

- `python3 -W error::ResourceWarning -m unittest tests.test_ln0_v04_deletion_fanout -v` — **9/9 passed**.
- `python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**, first run.
- `python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**, second run.
- `python3 -m unittest discover -s tests -v` — **601 tests, 11 skipped, 1 error**:
  the known sandbox loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 passed.
- `git diff --check` — passed.

Attempt 4 candidate SHA-256 (rejected):

```text
d8fb0bf9be8aef3a369b78ae138c0e5ed96b4aae3f79fc9f490b28da83f26fb8  experiments/ln0_v04_deletion_fanout.py
b11b2853d9d443e40ba01eb4c946a6b5cb1681c0f2f7ebab143a91e39eddf0fd  tests/test_ln0_v04_deletion_fanout.py
```

Limitations remain: synthetic contract fixture only; logical erase,
not proof of SQLite physical remanence destruction; and production encrypted-payload
integrity/object commitment depends on the later kernel/storage ADR.

### V-04 Attempt 5 record — 2026-09-26

Attempt 4 independent review returned **FAIL** for exactly three blockers:

1. restore accepted a deletion receipt without its tombstone and could resurrect the
   pre-delete plaintext;
2. receipt verification accepted deletion of the tail receipt or whole chain;
3. deletion authorization trusted caller-supplied principal strings.

Attempt 5 preserves the already-correct Attempt 4 privacy, provenance, generic
authority/lineage, measured fan-out, idempotency, quarantine, logical-erasure, and
receipt-mutation behavior. It adds complete deletion-ledger reconciliation,
truthful incomplete-deletion recovery, a separate append-only chain anchor, and a
HumanOS-owned opaque-token authenticator/policy boundary. The anchor is included in
the dynamic persistent-store privacy scanner. Production tamper-resistant anchoring
remains a kernel/checkpoint responsibility outside this synthetic fixture.

Focused adversarial coverage includes missing/mismatching/duplicate tombstones,
unknown deletion IDs, completion evidence gaps, interrupted recovery before LIVE,
tail and whole-chain deletion, missing/mutated anchors, empty/unknown/fabricated
principals, worker/connector denial, owner authorization, and resolved receipt
provenance. Attempt 5 remains **awaiting independent review**, not PASS or PROMOTED.

The earlier generic V-04 execution record reporting 8/8 and 600 tests is historical
Attempt 2 evidence; it is not current Attempt 5 evidence.

Required Attempt 5 execution:

- focused V-04 with ResourceWarnings elevated — **16/16 passed**;
- V-03 regression, first run — **8/8 passed**;
- V-03 regression, second run — **8/8 passed**;
- full discovery — **608 tests, 11 skipped, 1 error**, solely the known sandbox
  loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 passed;
- `git diff --check` — passed.

Attempt 5 candidate SHA-256 (awaiting independent review):

```text
3ef13c97490a5a03f0ec29895dffee5632c250329ec5f3bfb67c41b0d0205542  experiments/ln0_v04_deletion_fanout.py
acd9fc7181f705c3c6516dc0a1cd35ada94f7fa3399fc8d0fcee47b9310b792a  tests/test_ln0_v04_deletion_fanout.py
```

Attempt 5 subsequently failed independent review. The reviewer reproduced completion
while an unrelated persistent artifact retained the deleted bytes, plaintext access
through public `db()` during RESTORING, and receipt-chain acceptance after coordinated
receipt/projected-anchor/completion truncation. The recorded test hash and execution
counts also did not match the reviewed files. This record remains rejected evidence.

### V-04 Attempt 6 record — 2026-09-26

Attempt 6 is a bounded remediation of those findings. `_verify_erasure()` now invokes
the dynamic all-persistent-table forbidden-content scanner before any receipt or
`ERASE.COMPLETED` is written. The scanner exempts only byte-identical payload cells
owned by explicitly identified independent events; unrelated artifacts are not
exempted by declared lineage. Public `db()` now enforces the same LIVE-state gate as
typed content access.

The fixture accepts a separately supplied `KernelCheckpointBoundary`. The SQLite
anchor table is a projection only, and receipt verification also requires the external
expected count, head hash, and final sequence. Coordinated removal of the final
receipt, projected anchor, and completion row therefore fails. Existing receipts are
reverified on idempotent deletion and recovery paths.

Adversarial regressions prove:

- unrelated persistent forbidden bytes prevent completion and leave no receipt or
  `ERASE.COMPLETED`;
- public raw database access fails during RESTORING;
- coordinated receipt/anchor/completion truncation conflicts with the independent
  kernel checkpoint and fails receipt-chain verification.

Attempts 1–5 remain **FAIL / rejected evidence**. Attempt 6 is **awaiting independent
review**, not PASS or PROMOTED. The fixture remains synthetic logical-erasure evidence;
it does not prove SQLite physical remanence destruction or implement the production
kernel/checkpoint store.

Required Attempt 6 execution:

- focused V-04 with ResourceWarnings elevated — **19/19 passed**;
- V-03 regression, first run — **8/8 passed**;
- V-03 regression, second run — **8/8 passed**;
- full discovery — **611 tests, 11 skipped, 1 error**, solely the known sandbox
  loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 passed;
- `git diff --check` — passed.

Attempt 6 frozen candidate SHA-256 (awaiting independent review):

```text
71f4e5e05806ad36bc98528215144e7802e0adf44c85be26f6d7703ab9d0f0f1  experiments/ln0_v04_deletion_fanout.py
2ac1391b8bafa72881f3183a609a7d13deadc01e138a36d0ed1b6c14de3b6a56  tests/test_ln0_v04_deletion_fanout.py
```

### V-04 Attempt 7 record — 2026-09-27

Attempt 6 independent review returned **FAIL** for four exact blockers:

- durable restore verification depended on volatile retained plaintext bytes and
  could not identify an arbitrary unlineaged restored copy after process restart;
- activation lacked final all-store verification after reconciliation/replay/fan-out;
- public `search_persistent()` bypassed RESTORING quarantine;
- final scan, receipt/checkpoint update, and `ERASE.COMPLETED` were not atomic against
  a competing persistent writer.

Attempt 7 adds an external synthetic kernel ErasureTag contract:
`HMAC(kernel_erasure_secret, deletion_id || canonical_deleted_bytes)`. Ordinary
SHA-256 of plaintext and deleted plaintext are not retained. The receipt contains
neither plaintext nor secret. The supplied authoritative kernel boundary retains the
tag and receipt checkpoint outside the Notebook SQLite database; its secret is
injected independently. Production key storage belongs to the encrypted-kernel/key
architecture.

Restore activation is now ordered as checkpoint verification, deletion-ledger
reconciliation, tombstone replay, fan-out, all-store ErasureTag verification,
unresolved-zero verification, then LIVE. The reproduced old-backup attack retains an
unrelated persistent copy, restarts with only external authoritative tag/checkpoint
state plus the independently supplied secret, detects the copy, denies activation and
all public reads, then permits activation only after removal and recomputation.

The fixture test enumerates and classifies every public method and invokes every
content-returning/scanning path during RESTORING. All fail closed; private scan helpers
serve internal deletion/restore verification. Completion uses `BEGIN EXCLUSIVE`, and
a synchronized second connection proves it cannot insert between final scan and
completion evidence. A pre-scan copy fails completion, while a post-completion attempt
is a new governed write rejected by the ordinary erased-content write boundary.

The V-03 forged-token test changes only its mutation construction so the forged token
is guaranteed to differ from the random valid token. This is a deterministic test-only
flake correction, not a reopened V-03 architecture or implementation change.

Required Attempt 7 execution:

- focused V-04 with ResourceWarnings elevated — **22/22 passed**;
- V-03 regression, first run — **8/8 passed**;
- V-03 regression, second run — **8/8 passed**;
- full discovery — **614 tests, 11 skipped, 1 error**, solely the known sandbox
  loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 passed;
- `git diff --check` — passed.

Attempt 7 frozen candidate SHA-256 (awaiting independent review):

```text
e0e6e20c7e406fb6ed46af17985bbeedc704b17ae1de967a8bd1cef9267bd348  experiments/ln0_v04_deletion_fanout.py
b5912d10bd522020b859224fbddbda7d39c4981edb831b2cd34b12dba806c1a4  tests/test_ln0_v04_deletion_fanout.py
b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6  tests/test_ln0_v03_ingestor.py
```

Attempts 1–6 remain **FAIL / rejected evidence**. Attempt 7 is **awaiting independent
review**, not PASS or PROMOTED. The logical-versus-physical SQLite deletion limitation
remains unchanged. No runtime source, owner Notebook data, commit, or remote changed.

### V-04 Attempt 8 record — 2026-09-27

Attempt 7 independent review returned **FAIL** for exactly one blocker: equality-only
keyed ErasureTag matching detected a whole-cell match but not the erased byte sequence
embedded in a larger persistent value such as `PREFIX + erased_bytes + SUFFIX`.

Attempt 8 derives a deletion-specific matching key from the independently held kernel
secret and `deletion_id`. Its authoritative checkpoint retains only `deletion_id`,
permitted structural `match_length`, keyed `erasure_tag`, and the pre-existing exact
independent-source identity exemption. Candidate text/blob values are converted to
canonical bytes and every contiguous window of `match_length` is keyed and compared
to the tag. Plaintext, ordinary SHA-256 of plaintext, the kernel secret, and the
derived deletion key are not persisted in the Notebook DB or receipt.

New regression coverage includes beginning, end, middle, exact equality, repeated
occurrences, and binary/blob values. Normal deletion fails closed with
`ERASE.RECOVERY_REQUIRED`, no `ERASE.COMPLETED`, and no VERIFIED receipt when an
unrelated artifact embeds the erased bytes. Restore from a pre-delete snapshot with
the same embedded bytes is denied before LIVE and every public content path remains
quarantined until the artifact is sanitized. An explicitly independent source is
exempt only when its payload cell is exactly the allowed canonical payload; an
embedded occurrence in that cell is detected.

Required Attempt 8 final execution:

- `python3 -W error::ResourceWarning -m unittest tests.test_ln0_v04_deletion_fanout -v`
  — **26/26 passed**;
- `python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**;
- repeated `python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**;
- `python3 -m unittest discover -s tests -v` — **618 tests, 11 skipped, 1 error**,
  solely the known sandbox loopback `PermissionError` in
  `test_swarm.SwarmTests.test_live_loopback_and_attribution`; V-04 and V-03 passed;
- `git diff --check` — passed.

Attempt 8 reviewed candidate SHA-256 (promoted unchanged):

```text
8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39  experiments/ln0_v04_deletion_fanout.py
e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03  tests/test_ln0_v04_deletion_fanout.py
b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6  tests/test_ln0_v03_ingestor.py
```

Attempts 1–7 remain **FAIL / rejected evidence**. Independent promotion review of the
exact frozen Attempt 8 candidate returned **PASS**, with **no blocking findings** and
promotion decision **YES**. V-04 Attempt 8 is **PASS / PROMOTED**.

Promotion verification preserved focused V-04 **26/26 passed**, V-03 **8/8 passed
twice**, and broad discovery **618 tests, 11 skipped, 1 error**, solely the known
sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`. The reviewed hashes above
remained identical. This is synthetic logical-erasure evidence and does not claim
physical SQLite remanence destruction.

The independent reviewer also retained the non-blocking routing-hygiene finding that
the public Context Registry lacks an explicit HOS-LN-000 entry. The router is not fixed
or changed as part of this promotion. The next verification gate is **V-05**.

## Requirements / Planning Retrospective — V-04

V-04 intentionally remains bounded to the ERASE, structural-provenance,
deletion-evidence, and anti-resurrection foundation. The broader owner intent spans a
unified `HIDE / LOCK / REDACT / ERASE` privacy lifecycle, including selective fields,
derived stores and AI context, reversibility, authorization/audit, and backup/restore
semantics. That broader domain was decomposed too narrowly before implementation; the
lesson concerns requirements traceability and scope planning, not the later V-04
implementation work. Green tests establish conformity to the specified contract, not
completeness of owner intent.

Do not expand V-04 now. After its promotion, the tentative separate workstream
`HOS-LN-PRIV-001 — Life Notebook Privacy Lifecycle` should branch from the promoted
V-04 foundation, research and map the complete privacy domain, obtain owner approval
of the capability map, and only then define implementation slices. The governing
retrospective and required SDLC sequence are preserved in `HOS-LN-000.md`.

---

## Current architectural implication

V-01 + V-02 support the following candidate decision:

> Build LN-1 around a **new encrypted target database with controlled, evidence-preserving migration/cutover**, while keeping the current Runtime 0.1 database immutable/read-only as migration source and rollback evidence until parity and cutover acceptance pass.

Do not mutate the active plaintext database in place as the first encryption step.

The production Python SQLCipher binding/packaging path remains an explicit open
engineering item. It must be solved before the encrypted target becomes the live
Notebook writer.

## V-05 local candidate record — 2026-09-27

This record captures Pass 3 and is superseded by the Pass 4 record below.

Workstream `HOS-LN-000`; branch `experiment/v05-context-boundary-chunk2`; baseline
exact promoted V-04 commit
`e793aca454c087cb68503cb79871a844eb7bde03`. Only the isolated synthetic future
adapter-contract fixture and its tests were added:
`experiments/ln0_v05_context_boundary.py` and
`tests/test_ln0_v05_context_boundary.py`. Router policy was hardened separately in
local commit `7c8c5fc09dbdaade0ee98e6030e9227b79384702`; it is not part
of the V-05 candidate. No unrelated experiment changes were transplanted.

The Pass 3 fixture keeps records, classification, retrieval, policy, provider
authorization, compilation, and parsing Core-owned. Hosted providers receive only
records explicitly authorized by Core for hosted disclosure; Core-denied records do
not enter a hosted ContextPacket or reach the hosted adapter on initial invocation or
ContextRequest-driven recompilation. Source content and model output cannot self-assign
or upgrade export authority. It enforces a canonical 16,384-byte
ContextPacket, 4,096-byte raw response bound, byte-only local/hosted spies, an
untrusted wrappers backed by immutable Core-held issuance state, an explicit context-request state machine,
deny-by-default/first-deny-wins policy, S3 and LOCAL_ONLY hosted denial, and empty
retrieval/omitted-selection preservation. Unknown providers are denied before Core
record access. Classification-based adversarial tests use path-like,
credential-like, `SYNTHETIC_SECRET`, and LOCAL_ONLY content. Core-denied examples fail
before hosted invocation; a same-provider hosted ContextRequest is denied before a
second adapter call; equivalent-looking `HOSTED_ALLOWED` content succeeds, proving the
fixture is not accidental substring DLP. Focused execution:
`python3 -m unittest tests.test_ln0_v05_context_boundary -v` — **29/29 passed**.

The exact affected-regression command
`PYTHONPATH=tests python3 -m unittest tests.test_ln0_v03_ingestor tests.test_runtime tests.test_notebook_recall -v`
passed **59/59**. The single Pass 3 broad discovery via
`python3 -m unittest discover -s tests -v` was **647
run, 11 skipped, 1 error**, the known sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; the broad suite is not
green. Tests used Python 3.13.15; `git diff --check` is the final static gate.

Preserved hashes: V-04 fixture
`8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39`; V-04 tests
`e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03`; V-03 tests
`b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6`. V-05
Pass 3 candidate hashes: fixture
`62a23ebd457afb3ae895df493bbae28da2ab912d9ef93103c1ee4c23be0044c0`; tests
`8d3950b0d2f980773fd480a5b69e5e132a925f437920c9f52e89e7de5ba9067f`.

This is **REMEDIATION PASS 3 LOCAL CANDIDATE / EXTERNAL REVIEW NOT YET RUN**. V-05
does not prove automatic discovery of secrets or sensitive content from arbitrary
plaintext. Content-classification/DLP capabilities are outside this synthetic boundary
proof. It also does not prove production integration, an actual hosted provider,
OS/process/filesystem isolation, LN-6/LN-7, or owner Notebook behavior. The public registry
still lacks HOS-LN-000 and was not modified. No owner data, production runtime,
commit, push, PR, or promotion occurred. Rollback is removal/reversion only of the
V-05 fixture, V-05 test, and V-05 documentation append; promoted V-04, router
infrastructure, runtime, and owner data remain unchanged. Next action is Pass 3 evidence
freeze and a compact packet for external fresh read-only review while remaining
uncommitted, unpublished, and unpromoted. The broken local Sol reviewer is excluded.

## V-05 Remediation Pass 4 — 2026-09-28

External review found one blocker: records with no explicit Core classification
received fallback `S1 / LOCAL_OR_EXTERNAL` and could be sent to the hosted adapter.
Pass 4 makes hosted disclosure fail closed unless Core explicitly authorizes
`HOSTED_ALLOWED`. Fallback classification is not export authority. The built-in
`safe-1` receives Core-owned fixture authorization only when constructing the actual
built-in fixture; caller-supplied records, including a custom record using ID `safe-1`,
do not inherit it. No content scanning or DLP was added.

New adversarial tests prove (1) unclassified credential/path-like content is denied
with zero hosted calls, (2) a custom `safe-1` ID cannot self-authorize, and (3)
explicit `HOSTED_ALLOWED` lookalike content remains eligible. Existing initial hosted
denial, ContextRequest reauthorization, B1-B4, packet validation, bounds, and provider
isolation tests remain in the focused suite. Focused result: **31/31 passed**. Affected
regressions passed **59/59**. The single Pass 4 broad run was **649 run, 11 skipped,
1 error**, the known sandbox loopback `PermissionError` in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`; no V-05 failure occurred
and the broad suite is not green. `git diff --check` passed.

Preserved hashes: V-04 fixture
`8f1778684918174ad36e741d14cd902b3eab1a01da7dbb2a07daedc097386c39`; V-04 tests
`e91c4c487da1acdaca1c1c7742e0d45ddff5657c8f6359c5501fc0be2d8e4e03`; V-03 tests
`b3f1f482c2c8c1f9a751643539bd1bc725b3c41a2ca639dccaae07e95d5771a6`. Pass 4 V-05
hashes: fixture
`7a1aebf8d6556ee8c6380340759794bfd0854df94861b2a3e216bb552a5c7693`; tests
`8fc5427ec9502a50f2d585a9830ece9f1dbbccdbd85e377eb0584b05fd794333`.
