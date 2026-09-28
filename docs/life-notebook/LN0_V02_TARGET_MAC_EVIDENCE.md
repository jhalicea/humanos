# LN-0 V-02 target Mac SQLCipher proof

Status: PASS — bounded synthetic experiment only; not production qualification.

## Target and tooling

- Architecture: `arm64`
- macOS: `26.6.2` (`25G83`)
- Developer tools: `/Library/Developer/CommandLineTools`
- Python: `/usr/local/bin/python3`, `3.13.15`
- Isolated proof environment: `/tmp/ln0-v02-target-venv-20260928`
- `cryptography`: `49.0.0`, installed only in that temporary virtualenv from the existing `requirements-encrypted-backup.txt`
- Homebrew: `7.0.6`, `/opt/homebrew/bin/brew`
- SQLCipher: `4.19.0 community`, `/opt/homebrew/bin/sqlcipher`
- `PRAGMA cipher_version;`: `4.19.0 community`
- Homebrew policy: workstation development-tool manager only; not a HumanOS runtime, production, or deployment dependency.

## Reproduction

Existing spike, unchanged:

```sh
PATH=/opt/homebrew/bin:/usr/bin:/bin /tmp/ln0-v02-target-venv-20260928/bin/python experiments/ln0_sqlcipher_spike_v2.py
```

Exit status: `0`.

Spike source SHA-256: `8500b07b4ca159ca297a92ac034124427600f27e78c8f5c24320ee9d23139d84`.

Full stdout (JSON):

```json
{"committed_crash_recovery": true, "correct_key_readback": true, "encrypted_backup_wrong_key_rejected": true, "encrypted_export_restore": true, "independent_recovery_wrapper_proof": true, "keys_logged": false, "note": "Experiment evidence only; final Keychain/KDF/custody and packaging policy remain ADR decisions.", "plaintext_scan": {"humanos-ln0.db": false, "humanos-ln0.db-shm": false, "humanos-ln0.db-wal": false}, "plaintext_to_new_encrypted_export": true, "platform": "macOS-26.6.2-arm64-arm-64bit-Mach-O", "revision": 2, "schema_trigger_exported": true, "sqlcipher_version": "4.19.0 community", "standard_sqlite_rejected": true, "status": "PASS", "supported_version_range": ">=4.14.0,<5.0.0 for this spike", "uncommitted_crash_rollback": true, "wal_observed": true, "wrong_key_rejected": true}
```

The executable's SQLCipher identity was also independently checked with:

```sh
sqlcipher -batch -noheader :memory: 'PRAGMA cipher_version;'
```

Output: `4.19.0 community`.

The spike checks wrong-key rejection and standard SQLite rejection. Because it
does not separately invoke SQLCipher with no key, a second temporary synthetic
database was used only to verify that no-key SQLCipher access also fails. The
supplementary check used an ephemeral 32-byte synthetic key and marker, then
removed its temporary directory. Result:

```json
{"create_exit": 0, "db_header_plain_sqlite": false, "no_key_error": "Parse error near line 2: file is not a database (26)", "no_key_exit": 1, "no_key_rejected": true, "plaintext_marker_in_db": false}
```

The spike's complete test output is the JSON above; its assertions make success
conditional on all listed checks. The separately verified no-key result is not a
change to the spike or a production test.

The existing spike generated only random synthetic markers and ephemeral keys in a temporary directory. It reported `keys_logged: false`. No owner data was used. No spike source or production dependency was changed.

## Limits

This proves the spike configuration on this one workstation stack only. It does not qualify the production HumanOS runtime, Python SQLCipher binding, deployment portability, macOS Keychain integration, KDF parameters, recovery-secret custody, key rotation, or backup/deletion policy. The AES-GCM recovery-wrapper check proves only an independent synthetic KEK round-trip; it does not establish a production recovery authority or custody process. Homebrew-installed tools are local verification tooling, not runtime or deployment requirements.
