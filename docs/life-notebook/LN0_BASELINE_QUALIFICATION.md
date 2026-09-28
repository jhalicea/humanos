# LN-0 Baseline Qualification

Status: **PASS — synthetic qualification remediation candidate; external review resubmission pending.**
LN-0 remains ACTIVE / NOT CLOSED. Owner implementation-ready approval has not been
given. No LN-1 implementation is authorized or started by this qualification.

## Baseline and environment

- Qualification branch: `ln0-baseline-qualification`
- Exact baseline commit: `2d034a235c90ef56d40be4c4d355fe419da5891a`
- Host: macOS 26.6.2, arm64
- Python: 3.13.15
- SQLCipher: 4.19.0 community; executable path/version recorded in canonical target evidence.
- V-01–V-05 fixture/test hashes and qualification artifact hashes are in
  `docs/life-notebook/LN0_BASELINE_MANIFEST.md`.
- Manifest SHA-256: `573bda53f6a427f3ca793b067e54c789da58a8b38863e3dfd4ea42810717670d`
- Runner: `tooling/ln0_baseline_qualification.py`, SHA-256
  `0e0b7efc4615990acf91c8f42110a4b6399ed527e3b291e967fe6a374c5035ff`.

## Individual contract proofs

- **V-01:** focused migration tests 2/2 PASS. Qualification-era fixture and test
  hashes equal their bytes at the accepted CI-tested commit
  `94be3b4cb34bacad23106044a5afc213d53fcc50`; they were frozen now, not
  retroactively described as historically frozen.
- **V-02:** unchanged revision-2 target proof PASS using the explicitly configured
  `--v02-python /tmp/ln0-v02-target-venv-20260928/bin/python`; SQLCipher 4.19.0, correct-key
  reopen, wrong-key rejection, WAL/SHM scan, committed/uncommitted crash behavior,
  encrypted export/restore, and synthetic independent recovery-wrapper assertions
  passed. The V-02 CLI also created/read back an encrypted BLOB containing the
  serialized post-erasure KernelStore state; wrong-key, no-key, and standard-SQLite
  access were rejected. This is separate CLI snapshot evidence, not one integrated
  process-level encrypted store or production binding.
- **V-03:** focused 8/8 PASS; frozen hashes verified.
- **V-04 Attempt 8:** focused 26/26 PASS; frozen hashes verified.
- **V-05 Pass 4:** focused 31/31 PASS; frozen hashes verified.

All accepted artifact hash gates and manifest self-hash passed. No accepted V
fixture/test changed.

## Composition proof

The test-only reference composition harness operates on one shared governed SQLite
KernelStore for event/payload identity, ingestion, lineage, erasure, derivatives,
receipts, restore, retrieval, and packet dispatch. It reuses V-01 deterministic ID
helpers. V-03, V-04, and V-05 behavior is reproduced from their accepted contracts
because the frozen fixtures expose no common store API; this is explicitly contract
reuse, not code reuse. SQLCipher protects a separately serialized snapshot as
described above.

`tests.test_ln0_cross_v_lifecycle`: 15/15 PASS. Covered two identical-content legacy
events with distinct V-01 identities, controlled import, source-authority downgrade,
idempotent retry/conflict, shared-store lineage, local-only denial, interrupted erase
and restart recovery, low-entropy embedded-byte fan-out, surviving chronology and
content-free receipt, old-backup restore quarantine/reconciliation before LIVE,
post-erasure hash/marker scan, stale packet revocation, ContextRequest denial for
erased/provider-denied sources, and continued hosted use of unaffected authorized
content. New records default to UNCLASSIFIED/provider-denied. Connector claims and a
migrated `HOSTED_ALLOWED` claim do not grant authority; only an explicit Core policy
operation does. A stale packet is denied after provider revocation with no adapter
call.

The V-05 owner dispatch decision is encoded as: compiled context is not disclosure
authority; immediately before external dispatch, Core revalidates issuer, provider,
single-use/unexpired/unrevoked lease, current source/provider/privacy/deletion
eligibility, packet digest, and governed-state generation. Authorization is consumed
immediately before the test adapter call under one in-process lock. This does not
prove production transaction/process/network atomicity. Already transmitted bytes
cannot be recalled; provider retention/deletion and local packet/response retention
remain later Privacy Lifecycle work.

Lineage-first fan-out regressions pass: transformed sole-source derivative is
invalidated; transformed multi-source derivative is recomputed from surviving
lineage; an unlineaged embedded-byte leak stays RECOVERY_REQUIRED. A different
event/object identity without Core authorization is not exempt. A Core-named exact
payload cell may survive, but a Core-named source with PREFIX + erased bytes +
SUFFIX fails closed.

Restore with an already-ERASED receipt always reconciles and reapplies its
authoritative checkpoint, re-scans every content-capable field, verifies unresolved
state is zero, then and only then becomes LIVE. A resurrected embedded value in
`auxiliary_content.content` kept public reads quarantined until explicit
sanitization and replay. The scanner covers event payload/provenance/ingestion ID,
derivative body, and auxiliary store key/content; erased-event content hash and
submission fingerprint must be null.

Core policy regressions pass: connector claims cannot grant HOSTED_ALLOWED or
STANDARD/PUBLIC classification; migration HOSTED_ALLOWED claims remain denied;
unclassified hosted compilation is denied without adapter calls; explicit Core
authorization permits dispatch; later provider revocation invalidates compiled
context. Policy mutation requires the harness's Core-owned capability. The V-02
interpreter is configurable via `--v02-python` or `LN0_V02_PYTHON`; the runner has no
hard-coded temporary interpreter path and discovers SQLCipher through caller PATH.

Composition adversarial runner gates: 14/14 PASS, also covering privacy classification
change, unauthorized migration/erase, packet issuer/provider/expiry/single-use,
ContextRequest provider/single-use, and SQLCipher serialization behavior.
Manifest-tamper adversarial tests: 2/2 PASS, including current manifest hash and
modified manifest rejection.

## Environment qualification

The latest broad command, run once by the qualification runner with the accepted V-02
interpreter explicitly configured, ran 666 tests, 11 skipped, and returned one error:
`test_swarm.SwarmTests.test_live_loopback_and_attribution`
could not bind `127.0.0.1` in the restricted sandbox (`PermissionError: [Errno 1]
Operation not permitted`). No other test failed or errored. Full output is preserved
locally at
`/var/folders/9f/p6ms55b11nz45nk7wmccyyh40000gn/T/ln0-baseline-qualification-fs68kn2p/99-broad-suite.txt`.

The exact test's existing native-host evidence is PASS 1/1. Its source/hash was
unchanged during remediation, so it was not rerun:

```text
PYTHONPYCACHEPREFIX=/tmp/ln0-qualification-pycache python3 -m unittest tests.test_swarm.SwarmTests.test_live_loopback_and_attribution -v
test_live_loopback_and_attribution (tests.test_swarm.SwarmTests.test_live_loopback_and_attribution) ... ok
Ran 1 test in 0.002s
OK
```

Therefore the broad suite is **not GREEN under the restricted sandbox**, but its sole
error is the previously established sandbox permission boundary. The existing
native 1/1 PASS remains applicable because the test did not change; the broad suite
was not rerun natively in full.

The V-02 target proof used the existing evidence virtualenv supplied explicitly to
the runner. The runner accepts `--v02-python` or `LN0_V02_PYTHON`, otherwise tries the
current interpreter and fails closed if prerequisites are unavailable. No test was
skipped to obtain a green result.

## Future PRE-LN-1 gates and limitations

- Mandatory Schema/Integrity ADR: deletion-safe payload commitment, `event_hash`,
  content-hash lifecycle, idempotency, erasure, backup/restore, and V-04 ErasureTag.
- Mandatory SQLCipher/runtime-binding and key-custody ADR: supported binding,
  packaging, key creation/wrapping/recovery authority, KDF/OS custody, rotation,
  backup, and deletion.
- Controlled production migration/cutover plan and rollback remain required.
- This harness is synthetic and test-only. It does not qualify Runtime 0.1, the
  production encrypted kernel, physical SQLite remanence, real provider networking,
  cross-process atomic send, OS isolation, provider-side recall, owner Notebook data,
  or production key custody.
- Historical rejected V-03 attempts, the V-02 runtime-binding candidate, V-04
  Attempts 1–7, and V-05 failed/remediation passes remain unchanged evidence.

Qualification is a bounded baseline result, not an external architecture/security
review, LN-0 closure, or owner implementation-ready decision.
