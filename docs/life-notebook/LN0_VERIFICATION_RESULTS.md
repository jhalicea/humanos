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

This is the desired SDLC behavior: a failed candidate is evidence, not an excuse to
silently lower the requirement.

---

## Current architectural implication

V-01 + V-02 support the following candidate decision:

> Build LN-1 around a **new encrypted target database with controlled, evidence-preserving migration/cutover**, while keeping the current Runtime 0.1 database immutable/read-only as migration source and rollback evidence until parity and cutover acceptance pass.

Do not mutate the active plaintext database in place as the first encryption step.

The production Python SQLCipher binding/packaging path remains an explicit open
engineering item. It must be solved before the encrypted target becomes the live
Notebook writer.
