# LN-0 V-02 — SQLCipher Primary Evidence Basis

**Status:** EVIDENCE INPUT — EXPERIMENT MUST STILL PASS  
**Date:** 2026-09-25  
**Workstream:** `HOS-LN-000`

This note records the primary technical claims used to design V-02. It is not a
substitute for the executable spike and does not ratify a production SQLCipher
configuration.

## Sources

- SQLCipher API: https://www.zetetic.net/sqlcipher/sqlcipher-api/
- SQLCipher design/security: https://www.zetetic.net/sqlcipher/design/
- Encrypting plaintext SQLite databases: https://www.zetetic.net/sqlcipher/encrypting-plaintext-databases/
- Database key material: https://www.zetetic.net/sqlcipher/database-key-material/
- SQLCipher upstream releases/changelog: https://github.com/sqlcipher/sqlcipher/releases and https://github.com/sqlcipher/sqlcipher/blob/master/CHANGELOG.md

## Claims used by the spike

1. **Key before database operations.** SQLCipher requires the database key to be
   provided before the first operation that touches an encrypted database. The
   spike therefore makes `PRAGMA key` the first SQL statement on keyed handles.

2. **Random raw keys are supported.** SQLCipher supports an exact 32-byte / 256-bit
   random key using raw hex BLOB key syntax. This fits the HumanOS direction of a
   random data key protected by separate local/recovery wrappers rather than a key
   derived solely from provider or machine identity.

3. **WAL page data is encrypted.** SQLCipher documentation states that page data in
   WAL files is encrypted using the database key. The documentation itself suggests
   verifying this by creating an encrypted WAL database and inspecting the WAL. V-02
   therefore scans the main DB, WAL and SHM for random known plaintext fixtures while
   the WAL writer is live.

4. **Temporary-file behavior needs separate care.** SQLCipher's design documentation
   warns that not every transient file is automatically encrypted and recommends
   disabling file-backed temporary storage in suitable builds. V-02 therefore does
   not claim that passing the DB/WAL/SHM scan proves all temporary-file policy is
   solved. Production packaging/build flags remain an ADR concern.

5. **Existing plaintext SQLite is not encrypted in place by simply applying a key.**
   The documented migration is to create a new encrypted database and copy the
   plaintext source into it using `ATTACH ... KEY ...` plus `sqlcipher_export()`.
   V-02 directly tests that pattern on synthetic data/schema. This is an important
   input to choosing between LN-1 in-place evolution and controlled encrypted
   migration/cutover.

6. **`sqlcipher_export()` is the supported whole-database copy primitive.** It copies
   schema, triggers, virtual tables and data, with documented exceptions such as
   `user_version`/`auto_vacuum` handling that HumanOS must account for explicitly.

7. **WAL users require a modern stable SQLCipher 4.x baseline.** SQLCipher 4.14.0
   updated its SQLite baseline to include a critical WAL-reset corruption fix and
   upstream strongly advised WAL users to upgrade. The experiment therefore refuses
   SQLCipher older than 4.14.0. It also refuses SQLCipher 5 beta behavior for this
   evidence packet because SQLCipher 5 was still a breaking-change beta at the time
   of this work. The final production version is not frozen by this note.

8. **Current stable upstream is newer than the historical model suggestions.** As of
   this verification pass the SQLCipher project lists stable 4.19.0, while 5.0.0 is
   beta. HumanOS therefore records the runtime version from the experiment instead
   of hard-coding an older model-suggested version.

9. **Key material must not be stored beside the database or logged.** SQLCipher's key
   guidance recommends platform key stores such as Apple Keychain for random keys
   and warns against plaintext keys in config/preferences/logs. V-02 never prints
   generated raw keys. Its recovery-wrapper test is functional proof only; actual
   Keychain access controls, recovery-secret handling and key rotation remain separate
   implementation decisions.

## What V-02 can prove

If the dedicated macOS job passes, it proves on that GitHub macOS environment that:

- a supported stable SQLCipher is present;
- correct-key readback works and wrong-key access fails;
- standard SQLite cannot read the encrypted DB;
- WAL can be observed without known plaintext fixture bytes;
- committed data survives SIGKILL/reopen;
- uncommitted data does not become committed after SIGKILL;
- encrypted `sqlcipher_export()` backup/restore works with a separate key;
- an independently wrapped backup key can restore the backup in the proof model;
- documented plaintext SQLite -> new encrypted DB export preserves synthetic data
  and an append-only trigger.

It does **not** prove Jon's local Homebrew/runtime packaging, Keychain integration,
all temporary-file build flags, long-duration corruption resistance, or final key
custody. Those need later local/package-specific verification before production
promotion.
