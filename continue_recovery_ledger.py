#!/usr/bin/env python3
"""Explicit owner command to continue a sealed HumanOS recovery ledger."""
import argparse
import json
import os
from pathlib import Path

from notebook import Notebook, encode
from recovery_continuation import continue_recovery_ledger

BASE = Path(__file__).resolve().parent


def _vault_from_config(config_path, explicit_vault=None):
    if explicit_vault:
        return Path(explicit_vault).expanduser().resolve()
    config_path = Path(config_path).expanduser().resolve()
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    value = config.get('vault', BASE / 'HumanOS_Vault')
    value = Path(value)
    if not value.is_absolute():
        value = (config_path.parent / value).resolve()
    return value


def _event_payload(result):
    return {
        'continuation_id': result['continuation_id'],
        'archive_path': result['archive_path'],
        'predecessor_bytes': result['predecessor_bytes'],
        'predecessor_forensic_sha256': result['predecessor_forensic_sha256'],
        'authorization': 'EXPLICIT_OWNER_CLI',
    }


def apply_continuation(book):
    book.verify()
    result = continue_recovery_ledger(book.root, book.integrity_key)
    payload = _event_payload(result)
    encoded_payload = encode(payload)
    exists = book.db.execute(
        "SELECT 1 FROM events WHERE kind='RECOVERY_LEDGER_CONTINUED' AND payload=? LIMIT 1",
        (encoded_payload,),
    ).fetchone()
    if not exists:
        book.event(None, 'RECOVERY_LEDGER_CONTINUED', payload)
    book.verify()
    return result


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description='Explicitly continue a sealed HumanOS recovery ledger')
    parser.add_argument('--config', default=str(BASE / 'config.json'))
    parser.add_argument('--vault', help='Explicit HumanOS vault path; otherwise config/default vault is used')
    args = parser.parse_args()

    vault = _vault_from_config(args.config, args.vault)
    book = Notebook(vault)
    try:
        book.recover()
        result = apply_continuation(book)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    finally:
        book.close()


if __name__ == '__main__':
    raise SystemExit(main())
