# HumanOS encrypted portable backups

This is the confidentiality layer for the verified portable Life Notebook backup.
Core HumanOS remains standard-library only; this feature uses the optional audited
`cryptography` package for AES-256-GCM.

## One-time setup on the Mac

```sh
cd <HUMANOS_ROOT>
python3 -m pip install -r requirements-encrypted-backup.txt
```

Do not store the backup passphrase in `config.json`, shell history, Git, or the
HumanOS Notebook. The CLI reads it from the terminal with `getpass` so it is not
placed in the process command line.

## Create an encrypted backup

Stop the running HumanOS process first so the Notebook writer lock can be acquired.
Then:

```sh
cd <HUMANOS_ROOT>
python3 vault_encryption.py backup HumanOS_Vault ~/Documents/HumanOS-Backup.hosenc
```

You will be prompted for the passphrase twice. The command first creates and
verifies the existing portable snapshot, encrypts the entire bundle with a separate
passphrase-derived key, re-opens the encrypted artifact, decrypts it in an isolated
owner-only staging area, and performs the full portable restore + `Notebook.verify()`
check before reporting success.

## Verify an encrypted backup

```sh
python3 vault_encryption.py verify ~/Documents/HumanOS-Backup.hosenc
```

Verification prompts for the passphrase and performs a staged restore. It does not
replace the active vault.

## Restore to a new location

```sh
python3 vault_encryption.py restore ~/Documents/HumanOS-Backup.hosenc ~/HumanOS-Restored
```

The destination must not exist or must be empty. Authentication, archive validation,
portable-bundle verification and Notebook verification all occur before the restored
vault is placed.

## Security properties

- AES-256-GCM authenticated encryption.
- scrypt passphrase derivation with a fresh random salt per backup.
- fresh random GCM nonce per backup.
- Notebook `integrity.key` remains stable vault identity and is never reused as the
  backup-encryption key.
- ciphertext/header/tag tampering and wrong passphrases fail closed.
- encrypted artifacts are owner-only files on POSIX systems.
- the passphrase is never accepted as a CLI argument.
- the encrypted file does not contain plaintext SQLite, transcript/recovery text, or
  the raw Notebook integrity key.
- temporary plaintext staging is owner-only and removed on success or failure.

The passphrase is the confidentiality secret. If it is lost, HumanOS cannot decrypt
that encrypted backup. There is intentionally no recovery backdoor.
