"""Owner-opt-in *encrypted* custody of a selected Codex turn + Notebook.

Composes the existing verified portable-vault backup and AES-GCM archive
envelope. The authenticated custody package has an explicit finite allowlist;
no real session discovery, arbitrary source enumeration, or implicit restore.
"""
import argparse
import getpass
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import tarfile
import tempfile

from conversation_ledger import read_ledger, verify_ledger, _messages
from ledger_notebook_projection import _existing_exact
from notebook import Notebook
from vault_portability import (
    DB_FILE, KEY_FILE, MANIFEST as VAULT_MANIFEST, RECOVERY_FILE,
    _encode, _read_private_file, _write_private, _fsync_directory,
    create_portable_backup, restore_portable_backup, verify_portable_backup,
)
from vault_encryption import (
    _encrypt_tar, _decrypt_to_tar, EncryptedBackupError,
)

FORMAT = "humanos-selected-conversation-custody"
VERSION = 1
ENCRYPTED_PAYLOAD = "humanos-conversation-custody-v1-tar"
CUSTODY_MANIFEST = "custody-manifest.json"
EXTERNAL = ("source.jsonl", "ledger.jsonl", "capture-receipts.jsonl")
PREFIX = "vault__"
ARCHIVE_NAMES = {PREFIX + DB_FILE, PREFIX + KEY_FILE,
                 PREFIX + VAULT_MANIFEST, PREFIX + RECOVERY_FILE,
                 *EXTERNAL, CUSTODY_MANIFEST}
MAX_FILE = 256 * 1024 * 1024
MAX_SOURCE = 16 * 1024 * 1024


class CustodyError(ValueError):
    pass


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _private_existing(path):
    path = Path(path)
    if not path.is_absolute() or path.is_symlink():
        raise CustodyError("Custody requires explicit absolute non-symlink paths")
    info = path.lstat()
    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise CustodyError("Custody evidence must be owner-private regular files")
    return _read_private_file(path)



def _require_isolated_source(source_bytes):
    """Fail closed on raw records outside the exact one-turn custody contract.

    The archive retains original source bytes. Parsed-message counts alone
    cannot establish the scope of records ignored by the message importer.
    """
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise CustodyError("Duplicate JSON object key in custody source")
            result[key] = value
        return result

    try:
        lines = source_bytes.decode("utf-8").splitlines()
        if len(lines) != 3 or not all(line.strip() for line in lines):
            raise CustodyError("Custody requires exactly three isolated source records")
        records = [json.loads(line, object_pairs_hook=unique_object) for line in lines]
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CustodyError("Custody source has invalid JSONL") from error
    for record in records:
        if (not isinstance(record, dict)
                or set(record) - {"type", "payload", "timestamp"}
                or not isinstance(record.get("payload"), dict)):
            raise CustodyError("Custody source contains unapproved raw record fields")
        if "timestamp" in record and (not isinstance(record["timestamp"], str)
                                      or len(record["timestamp"]) > 64):
            raise CustodyError("Custody source has unapproved timestamp")
    metadata = records[0]
    if (metadata["type"] != "session_meta"
            or set(metadata["payload"]) not in ({"id"}, {"session_id"})
            or not all(isinstance(v, str) and bool(v) for v in metadata["payload"].values())):
        raise CustodyError("Custody source contains unapproved session metadata")
    for record, role, types in (
            (records[1], "user", {"input_text", "text"}),
            (records[2], "assistant", {"output_text", "text"})):
        payload = record["payload"]
        if (record["type"] != "response_item" or payload.get("role") != role
                or set(payload) - {"id", "role", "content", "thread_id"}
                or ("id" in payload and
                    (not isinstance(payload["id"], str) or not payload["id"]))
                or ("thread_id" in payload and
                    (not isinstance(payload["thread_id"], str) or not payload["thread_id"]))):
            raise CustodyError("Custody source contains unapproved response metadata")
        content = payload.get("content")
        if (not isinstance(content, list) or not content
                or any(not isinstance(item, dict)
                       or set(item) != {"type", "text"}
                       or item.get("type") not in types
                       or not isinstance(item.get("text"), str)
                       for item in content)):
            raise CustodyError("Custody source contains unapproved response content")


def _require_isolated_notebook(book, tx):
    """Reject out-of-scope SQLite state and fallback material before backup."""
    permitted_tables = {
        "identities", "transactions", "transcript", "tasks", "events",
        "recovery", "privacy_state", "privacy_operations", "privacy_receipts",
        "runtime_meta", "transcript_sequence", "sqlite_sequence",
    }
    tables = {row["name"] for row in book.db.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if tables - permitted_tables:
        raise CustodyError("Selected-turn Notebook contains unapproved database tables")
    permitted_meta = {
        "integrity_key_id", "integrity_key_policy",
        "record_integrity_policy", "record_integrity_activation_seq",
        "record_integrity_legacy_row_count", "record_integrity_policy_proof",
    }
    if any(row["key"] not in permitted_meta for row in
           book.db.execute("SELECT key FROM runtime_meta")):
        raise CustodyError("Selected-turn Notebook contains unrelated runtime metadata")
    if any(row["name"] not in {"transcript", "events", "recovery"} for row in
           book.db.execute("SELECT name FROM sqlite_sequence")):
        raise CustodyError("Selected-turn Notebook contains unrelated sequence metadata")
    for table in ("transcript", "tasks", "privacy_state", "privacy_operations"):
        if book.db.execute(
                "SELECT 1 FROM " + table + " WHERE tx IS NULL OR tx != ? LIMIT 1",
                (tx,)).fetchone():
            raise CustodyError("Selected-turn Notebook contains unrelated " + table)
    if book.db.execute("""SELECT 1 FROM privacy_receipts AS r
          LEFT JOIN privacy_operations AS p ON r.op_id=p.op_id
          WHERE p.tx IS NULL OR p.tx != ? LIMIT 1""", (tx,)).fetchone():
        raise CustodyError("Selected-turn Notebook contains unrelated privacy receipts")
    if book.db.execute("SELECT 1 FROM recovery LIMIT 1").fetchone():
        raise CustodyError("Selected-turn Notebook contains recovery records")
    fallback = book.root / RECOVERY_FILE
    if fallback.exists() or fallback.is_symlink():
        raise CustodyError("Selected-turn Notebook has a recovery fallback file")
    identity = dict(book.db.execute("SELECT * FROM identities").fetchone())
    expected_binding = dict(identity, evidence="E1: HumanOS-issued identity")
    for row in book.db.execute("SELECT tx,kind,payload FROM events"):
        if row["tx"] == tx:
            continue
        if (row["tx"] is None and row["kind"] == "IDENTITY_AND_BINDING_CREATED"
                and json.loads(row["payload"]) == expected_binding):
            continue
        raise CustodyError("Selected-turn Notebook contains unrelated audit events")


def _validate_linkage(source_bytes, ledger_bytes, receipts_bytes, vault):
    """Require one verified source pair, capture receipt, and Notebook identity."""
    if len(source_bytes) > MAX_SOURCE:
        raise CustodyError("Selected Codex source exceeds allowed bound")
    _require_isolated_source(source_bytes)
    # Parse source without searching for host sessions or changing its path.
    parsed = list(_messages("explicit-snapshot.jsonl", allow_derived_ids=True,
                            snapshot_bytes=source_bytes))
    if not ledger_bytes.endswith(b"\n") or not receipts_bytes.endswith(b"\n"):
        raise CustodyError("Incomplete custody ledger or capture receipts")
    evidence_rows = [json.loads(line) for line in ledger_bytes.splitlines()]
    if len(evidence_rows) != 2 or [r.get("role") for r in evidence_rows] != ["HUMAN", "ASSISTANT"]:
        raise CustodyError("Custody requires exactly one HUMAN/ASSISTANT evidence pair")
    ledger = []
    for item in evidence_rows:
        if item.get("source") != "codex-rollout":
            raise CustodyError("Only explicitly selected Codex source is supported")
        ledger.append(item)
    relevant = [dict(row, content_digest=_digest(row["text"].encode("utf-8")))
                for row in parsed if row["source_id"] in
                {evidence_rows[0]["source_id"], evidence_rows[1]["source_id"]}]
    if relevant != ledger:
        raise CustodyError("Selected source is not identical to ledger evidence")
    # An encrypted custody artifact includes the entire raw source file.
    # Do not silently export other extracted messages from that file.
    if len(parsed) != 2:
        raise CustodyError("Selected-turn custody source contains other messages")
    if any(r["conversation_id"] != ledger[0]["conversation_id"] for r in ledger):
        raise CustodyError("Ledger pair crosses original conversations")
    receipts = [json.loads(line) for line in receipts_bytes.splitlines()]
    if not receipts or not all(isinstance(x, dict) for x in receipts):
        raise CustodyError("Capture receipt history is incomplete")
    # The archive stores exact receipt bytes, not a filtered last receipt.
    # Historical receipts may refer to other conversations and cannot be
    # included under a one-turn custody authorization.
    if len(receipts) != 1:
        raise CustodyError("Selected-turn custody contains other capture receipts")
    latest = receipts[-1]
    if (latest.get("status") != "CHECKPOINTED"
            or latest.get("ledger_digest") != _digest(ledger_bytes)
            or latest.get("total") != 2
            or latest.get("conversation_id") != ledger[0]["conversation_id"]):
        raise CustodyError("Capture receipt does not attest this exact ledger")
    tx = "CAPTURE-" + ledger[1]["source_id"]
    root = Path(vault)
    if (not root.is_absolute() or root.is_symlink()
            or not (root / "runtime" / "notebook.sqlite3").is_file()):
        raise CustodyError("Existing Notebook vault required for custody")
    book = Notebook(root)
    try:
        book.verify()
        transactions = [
            row["tx"] for row in book.db.execute("SELECT tx FROM transactions")
        ]
        identities = [
            row["hcid"] for row in book.db.execute("SELECT hcid FROM identities")
        ]
        if transactions != [tx] or len(identities) != 1:
            raise CustodyError(
                "Selected-turn custody vault contains unrelated Notebook records")
        _require_isolated_notebook(book, tx)
        if not _existing_exact(book, tx, ledger[0], ledger[1]):
            raise CustodyError("Notebook does not contain checkpointed source pair")
    finally:
        book.close()
    return {"conversation_id": ledger[0]["conversation_id"],
            "human_source_id": ledger[0]["source_id"],
            "assistant_source_id": ledger[1]["source_id"],
            "transaction": tx}


def _archive(tar_path, blobs):
    with os.fdopen(os.open(tar_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600),
                   "wb") as fd:
        with tarfile.open(fileobj=fd, mode="w") as archive:
            for name, data in sorted(blobs.items()):
                if name not in ARCHIVE_NAMES or len(data) > MAX_FILE:
                    raise CustodyError("Unexpected or oversized custody member")
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = 0o600
                info.uid = info.gid = 0
                info.mtime = 0
                archive.addfile(info, io.BytesIO(data))
        fd.flush()
        os.fsync(fd.fileno())


def _unarchive(tar_path):
    blobs = {}
    with tarfile.open(tar_path, mode="r:") as archive:
        for member in archive:
            name = member.name
            if (name not in ARCHIVE_NAMES or name in blobs or not member.isfile()
                    or member.size < 0 or member.size > MAX_FILE):
                raise CustodyError("Custody archive has an unsupported or duplicate member")
            stream = archive.extractfile(member)
            if stream is None:
                raise CustodyError("Unreadable custody member")
            data = stream.read(member.size + 1)
            if len(data) != member.size:
                raise CustodyError("Custody member size mismatch")
            blobs[name] = data
    mandatory = {PREFIX + DB_FILE, PREFIX + KEY_FILE, PREFIX + VAULT_MANIFEST,
                 *EXTERNAL, CUSTODY_MANIFEST}
    if not mandatory.issubset(blobs) or set(blobs) - mandatory - {PREFIX + RECOVERY_FILE}:
        raise CustodyError("Custody archive does not have the required exact files")
    return blobs


def _load_custody(tar_path, stage):
    blobs = _unarchive(tar_path)
    try:
        manifest = json.loads(blobs[CUSTODY_MANIFEST].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CustodyError("Custody manifest is unreadable") from error
    if (not isinstance(manifest, dict) or
            set(manifest) != {"format", "version", "files", "linkage"} or
            manifest["format"] != FORMAT or manifest["version"] != VERSION or
            set(manifest["files"]) != set(blobs) - {CUSTODY_MANIFEST}):
        raise CustodyError("Custody manifest has an unexpected schema")
    for name, data in blobs.items():
        if name == CUSTODY_MANIFEST:
            continue
        if manifest["files"].get(name) != {"bytes": len(data), "sha256": _digest(data)}:
            raise CustodyError("Custody archive bytes diverge from its manifest")
    portable = stage / "portable"
    portable.mkdir(mode=0o700)
    for name, data in blobs.items():
        if name.startswith(PREFIX):
            _write_private(portable / name[len(PREFIX):], data)
    verify_portable_backup(portable)
    restored = stage / "checked"
    restore_portable_backup(portable, restored / "vault")
    evidence = restored / "evidence"
    evidence.mkdir(mode=0o700)
    for name in EXTERNAL:
        _write_private(evidence / name, blobs[name])
    linkage = _validate_linkage(blobs["source.jsonl"], blobs["ledger.jsonl"],
                                blobs["capture-receipts.jsonl"], restored / "vault")
    if linkage != manifest["linkage"]:
        raise CustodyError("Notebook linkage does not match custody manifest")
    return restored, linkage


def _decrypt_and_check(encrypted, passphrase, work):
    tar_path = work / "custody.tar"
    _decrypt_to_tar(encrypted, tar_path, passphrase,
                    expected_payload=ENCRYPTED_PAYLOAD)
    return _load_custody(tar_path, work)


def create_custody_backup(source, ledger, receipts, vault, encrypted, passphrase):
    encrypted = Path(encrypted)
    if not encrypted.is_absolute() or encrypted.exists() or encrypted.is_symlink():
        raise CustodyError("Custody destination must be a new absolute file")
    vault_path = Path(vault)
    if not vault_path.is_absolute() or vault_path.is_symlink():
        raise CustodyError("Existing vault must be specified by an absolute non-symlink path")
    try:
        encrypted.resolve(strict=False).relative_to(vault_path.resolve())
    except ValueError:
        pass
    else:
        raise CustodyError("Encrypted custody output must remain outside the source vault")
    if Path(receipts) != Path(ledger).parent / "capture-receipts.jsonl":
        raise CustodyError("Capture receipts must belong to this evidence ledger")
    if any(Path(p).resolve() == encrypted.resolve() for p in (source, ledger, receipts)):
        raise CustodyError("Destination conflicts with source evidence")
    encrypted.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=".humanos-custody-", dir=encrypted.parent))
    os.chmod(work, 0o700)
    try:
        blobs = {name: _private_existing(path) for name, path in
                 zip(EXTERNAL, (source, ledger, receipts))}
        verify_ledger(ledger)
        linkage = _validate_linkage(blobs["source.jsonl"], blobs["ledger.jsonl"],
                                    blobs["capture-receipts.jsonl"], Path(vault))
        portable = work / "portable"
        create_portable_backup(vault, portable)
        for path in portable.iterdir():
            blobs[PREFIX + path.name] = _read_private_file(path)
        # Abort if a concurrent evidence writer changed a read snapshot.
        if any(_private_existing(path) != blobs[name]
               for name, path in zip(EXTERNAL, (source, ledger, receipts))):
            raise CustodyError("Evidence changed during encrypted custody capture")
        manifest = {"format": FORMAT, "version": VERSION, "linkage": linkage,
                    "files": {name: {"bytes": len(data), "sha256": _digest(data)}
                              for name, data in sorted(blobs.items())}}
        blobs[CUSTODY_MANIFEST] = (_encode(manifest) + "\n").encode("utf-8")
        tar_path = work / "custody.tar"
        _archive(tar_path, blobs)
        # Encrypt and independently staged-restore-verify under the private
        # temporary root. Only then publish a non-overwriting hard link to
        # the owner-selected final output path (atomic existence).
        sealed = work / "sealed.hosenc"
        _encrypt_tar(tar_path, sealed, passphrase, payload=ENCRYPTED_PAYLOAD)
        check = work / "proof"
        check.mkdir(mode=0o700)
        _, restored_linkage = _decrypt_and_check(sealed, passphrase, check)
        if restored_linkage != linkage:
            raise CustodyError("Encrypted custody staged restore lost its source linkage")
        os.link(sealed, encrypted)
        _fsync_directory(encrypted.parent)
        return {"status": "ENCRYPTED_CUSTODY_VERIFIED", "verified": True,
                "transaction": linkage["transaction"], "staged_restore": True}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def verify_custody_backup(encrypted, passphrase):
    encrypted = Path(encrypted)
    work = Path(tempfile.mkdtemp(prefix=".humanos-custody-check-", dir=encrypted.parent))
    os.chmod(work, 0o700)
    try:
        _, linkage = _decrypt_and_check(encrypted, passphrase, work)
        return {"status": "CUSTODY_VERIFIED", "verified": True,
                "transaction": linkage["transaction"]}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def restore_custody_backup(encrypted, destination, passphrase):
    destination = Path(destination)
    if (not destination.is_absolute() or destination.is_symlink()
            or destination.exists()):
        raise CustodyError("Restore requires a new absolute destination directory")
    destination.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=".humanos-custody-restore-",
                                 dir=destination.parent))
    os.chmod(work, 0o700)
    placed = False
    try:
        restored, linkage = _decrypt_and_check(encrypted, passphrase, work)
        # A single rename puts the restored vault and external evidence
        # in place together. Nothing is copied into a preexisting vault.
        os.replace(restored, destination)
        placed = True
        _fsync_directory(destination.parent)
        return {"status": "CUSTODY_RESTORED", "verified": True,
                "transaction": linkage["transaction"], "restored": True}
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Explicit encrypted source/ledger/receipt/Notebook custody")
    cmds = parser.add_subparsers(dest="action", required=True)
    create = cmds.add_parser("create")
    for item in ("source", "ledger", "receipts", "vault", "encrypted"):
        create.add_argument(item)
    verify = cmds.add_parser("verify")
    verify.add_argument("encrypted")
    restore = cmds.add_parser("restore")
    restore.add_argument("encrypted")
    restore.add_argument("destination")
    args = parser.parse_args(argv)
    passphrase = getpass.getpass("Custody passphrase: ")
    if args.action == "create":
        result = create_custody_backup(args.source, args.ledger, args.receipts,
                                       args.vault, args.encrypted, passphrase)
    elif args.action == "verify":
        result = verify_custody_backup(args.encrypted, passphrase)
    else:
        result = restore_custody_backup(args.encrypted, args.destination, passphrase)
    print(_encode(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
