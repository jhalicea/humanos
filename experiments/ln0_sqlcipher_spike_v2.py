"""LN-0 V-02 SQLCipher verification spike, revision 2.

Experiment-only code. It operates exclusively on temporary synthetic databases.
Revision 2 removes stdout timing as a synchronization primitive: the SQLCipher
shell creates a harmless filesystem readiness marker after the SQL statement has
completed, while stdin remains open. The parent observes that marker and then
SIGKILLs the still-running process. This makes the crash tests deterministic on
GitHub macOS runners without depending on stdio buffering.
"""

from __future__ import annotations

import json
import os
import platform
import re
import secrets
import shlex
import shutil
import signal
import sqlite3
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Iterable


SUPPORTED_MIN = (4, 14, 0)
SUPPORTED_MAX_EXCLUSIVE = (5, 0, 0)


class SQLCipherSpikeError(RuntimeError):
    pass


def _sql_quote(value: str) -> str:
    return value.replace("'", "''")


def _key_pragma(key: bytes) -> str:
    if len(key) != 32:
        raise ValueError("SQLCipher raw key must be exactly 32 bytes")
    return f'PRAGMA key = "x\'{key.hex().upper()}\'";'


def _attach_key(key: bytes) -> str:
    if len(key) != 32:
        raise ValueError("SQLCipher raw key must be exactly 32 bytes")
    return f'"x\'{key.hex().upper()}\'"'


def _env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env["HOME"] = str(home)
    env["SQLITE_HISTORY"] = os.devnull
    return env


def _script(key: bytes | None, statements: Iterable[str]) -> str:
    # .bail is a shell directive, not a database operation. PRAGMA key remains the
    # first SQL statement on encrypted handles.
    lines = [".bail on"]
    if key is not None:
        lines.append(_key_pragma(key))
    lines.extend(statements)
    return "\n".join(lines) + "\n"


def _run_sqlcipher(
    executable: str,
    database: Path,
    key: bytes | None,
    statements: Iterable[str],
    home: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [executable, "-batch", "-noheader", str(database)],
        input=_script(key, statements),
        text=True,
        capture_output=True,
        timeout=30,
        env=_env(home),
        check=False,
    )


def _nonempty_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _require_ok(result: subprocess.CompletedProcess[str], label: str) -> list[str]:
    if result.returncode != 0:
        raise SQLCipherSpikeError(
            f"{label} failed rc={result.returncode}: "
            f"{result.stderr.strip() or result.stdout.strip()}"
        )
    return _nonempty_lines(result.stdout)


def _parse_version(value: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise SQLCipherSpikeError(f"Cannot parse SQLCipher version: {value!r}")
    return tuple(int(part) for part in match.groups())


def _count_value(
    executable: str, database: Path, key: bytes, value: str, home: Path
) -> int:
    result = _run_sqlcipher(
        executable,
        database,
        key,
        [f"SELECT COUNT(*) FROM evidence WHERE value='{_sql_quote(value)}';"],
        home,
    )
    lines = _require_ok(result, "readback")
    if not lines:
        raise SQLCipherSpikeError("Readback returned no count")
    try:
        return int(lines[-1])
    except ValueError as error:
        raise SQLCipherSpikeError(f"Unexpected readback output: {lines[-1]!r}") from error


def _start_live_until_marker(
    executable: str,
    database: Path,
    key: bytes,
    commands: Iterable[str],
    ready_marker: Path,
    home: Path,
    timeout: float = 10.0,
) -> subprocess.Popen[str]:
    proc = subprocess.Popen(
        [executable, "-batch", "-noheader", str(database)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        env=_env(home),
    )
    assert proc.stdin is not None
    proc.stdin.write(".bail on\n")
    proc.stdin.write(_key_pragma(key) + "\n")
    for command in commands:
        proc.stdin.write(command.rstrip(";\n") + ";\n")
    proc.stdin.write(f".shell touch {shlex.quote(str(ready_marker))}\n")
    proc.stdin.flush()

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if ready_marker.exists():
            return proc
        if proc.poll() is not None:
            stderr = proc.stderr.read() if proc.stderr is not None else ""
            raise SQLCipherSpikeError(
                f"SQLCipher exited before readiness marker: rc={proc.returncode} stderr={stderr!r}"
            )
        time.sleep(0.05)
    _kill(proc)
    raise SQLCipherSpikeError("Timed out waiting for SQLCipher readiness marker")


def _kill(proc: subprocess.Popen[str]) -> None:
    if proc.poll() is None:
        proc.send_signal(signal.SIGKILL)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    if proc.stdin is not None:
        proc.stdin.close()
    if proc.stderr is not None:
        proc.stderr.close()


def _scan_for_plaintext(paths: Iterable[Path], markers: Iterable[str]) -> dict[str, bool]:
    marker_bytes = [marker.encode("utf-8") for marker in markers]
    result: dict[str, bool] = {}
    for path in paths:
        if not path.is_file():
            continue
        data = path.read_bytes()
        result[path.name] = any(marker in data for marker in marker_bytes)
    return result


def _recovery_wrap_proof(data_key: bytes) -> tuple[bytes, bytes, bytes]:
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    except ImportError as error:
        raise SQLCipherSpikeError(
            "cryptography is required for the V-02 recovery-wrapper proof"
        ) from error
    recovery_kek = secrets.token_bytes(32)
    nonce = secrets.token_bytes(12)
    aad = b"HumanOS-LN0-recovery-wrap-proof-v1"
    wrapped = AESGCM(recovery_kek).encrypt(nonce, data_key, aad)
    if AESGCM(recovery_kek).decrypt(nonce, wrapped, aad) != data_key:
        raise SQLCipherSpikeError("Recovery wrapper failed round-trip")
    return recovery_kek, nonce, wrapped


def _unwrap_recovery(recovery_kek: bytes, nonce: bytes, wrapped: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    return AESGCM(recovery_kek).decrypt(
        nonce, wrapped, b"HumanOS-LN0-recovery-wrap-proof-v1"
    )


def run_sqlcipher_spike(executable: str | None = None) -> dict[str, object]:
    executable = executable or shutil.which("sqlcipher")
    if not executable:
        raise SQLCipherSpikeError("sqlcipher executable is not installed")

    with tempfile.TemporaryDirectory(prefix="humanos-ln0-sqlcipher-") as tmp:
        root = Path(tmp)
        home = root / "home"
        home.mkdir(mode=0o700)
        db_path = root / "humanos-ln0.db"
        backup_path = root / "humanos-ln0-backup.db"
        plaintext_path = root / "legacy-plaintext.db"
        migrated_path = root / "legacy-encrypted.db"

        data_key = secrets.token_bytes(32)
        backup_key = secrets.token_bytes(32)
        migration_key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)

        version_result = _run_sqlcipher(
            executable, db_path, data_key, ["PRAGMA cipher_version;"], home
        )
        version_lines = _require_ok(version_result, "cipher version")
        if not version_lines:
            raise SQLCipherSpikeError("PRAGMA cipher_version returned no value")
        version_text = version_lines[-1]
        version = _parse_version(version_text)
        if version < SUPPORTED_MIN or version >= SUPPORTED_MAX_EXCLUSIVE:
            raise SQLCipherSpikeError(
                f"V-02 requires SQLCipher >=4.14.0,<5.0.0; got {version_text}"
            )

        base_marker = "HUMANOS_LN0_BASE_" + secrets.token_hex(12)
        committed_marker = "HUMANOS_LN0_COMMITTED_" + secrets.token_hex(12)
        uncommitted_marker = "HUMANOS_LN0_UNCOMMITTED_" + secrets.token_hex(12)
        plaintext_marker = "HUMANOS_LN0_PLAINTEXT_MIGRATION_" + secrets.token_hex(12)

        create_result = _run_sqlcipher(
            executable,
            db_path,
            data_key,
            [
                "PRAGMA journal_mode=WAL;",
                "PRAGMA wal_autocheckpoint=0;",
                "CREATE TABLE evidence(id INTEGER PRIMARY KEY, value TEXT NOT NULL);",
                f"INSERT INTO evidence(value) VALUES('{_sql_quote(base_marker)}');",
                f"SELECT COUNT(*) FROM evidence WHERE value='{_sql_quote(base_marker)}';",
            ],
            home,
        )
        create_lines = _require_ok(create_result, "encrypted database creation")
        if not create_lines or create_lines[-1] != "1":
            raise SQLCipherSpikeError(f"Initial encrypted readback failed: {create_lines!r}")

        standard_sqlite_rejected = False
        plain_reader = sqlite3.connect(db_path)
        try:
            try:
                plain_reader.execute("SELECT COUNT(*) FROM evidence").fetchone()
            except sqlite3.DatabaseError:
                standard_sqlite_rejected = True
        finally:
            plain_reader.close()
        if not standard_sqlite_rejected:
            raise SQLCipherSpikeError("Standard SQLite unexpectedly read encrypted DB")

        wrong = _run_sqlcipher(
            executable, db_path, wrong_key, ["SELECT COUNT(*) FROM evidence;"], home
        )
        wrong_key_rejected = wrong.returncode != 0
        if not wrong_key_rejected:
            raise SQLCipherSpikeError("Wrong SQLCipher key did not fail closed")

        committed_ready = root / "committed.ready"
        committed_proc = _start_live_until_marker(
            executable,
            db_path,
            data_key,
            [
                "PRAGMA journal_mode=WAL",
                "PRAGMA wal_autocheckpoint=0",
                f"INSERT INTO evidence(value) VALUES('{_sql_quote(committed_marker)}')",
            ],
            committed_ready,
            home,
        )
        wal_path = Path(str(db_path) + "-wal")
        shm_path = Path(str(db_path) + "-shm")
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and not wal_path.exists():
            time.sleep(0.05)
        wal_observed = wal_path.exists()
        if not wal_observed:
            _kill(committed_proc)
            raise SQLCipherSpikeError("WAL file was not observable during live WAL writer")

        plaintext_scan = _scan_for_plaintext(
            [db_path, wal_path, shm_path], [base_marker, committed_marker]
        )
        if any(plaintext_scan.values()):
            _kill(committed_proc)
            raise SQLCipherSpikeError(
                f"Known plaintext found in encrypted DB/WAL/SHM: {plaintext_scan}"
            )
        if db_path.read_bytes().startswith(b"SQLite format 3\x00"):
            _kill(committed_proc)
            raise SQLCipherSpikeError("Encrypted DB exposes plaintext SQLite header")
        _kill(committed_proc)

        if _count_value(executable, db_path, data_key, committed_marker, home) != 1:
            raise SQLCipherSpikeError("Committed WAL data did not survive SIGKILL/reopen")

        uncommitted_ready = root / "uncommitted.ready"
        uncommitted_proc = _start_live_until_marker(
            executable,
            db_path,
            data_key,
            [
                "PRAGMA journal_mode=WAL",
                "BEGIN IMMEDIATE",
                f"INSERT INTO evidence(value) VALUES('{_sql_quote(uncommitted_marker)}')",
            ],
            uncommitted_ready,
            home,
        )
        _kill(uncommitted_proc)
        if _count_value(executable, db_path, data_key, uncommitted_marker, home) != 0:
            raise SQLCipherSpikeError("Uncommitted row survived crash recovery")

        backup_result = _run_sqlcipher(
            executable,
            db_path,
            data_key,
            [
                f"ATTACH DATABASE '{_sql_quote(str(backup_path))}' AS backup KEY {_attach_key(backup_key)};",
                "SELECT sqlcipher_export('backup');",
                "DETACH DATABASE backup;",
            ],
            home,
        )
        _require_ok(backup_result, "sqlcipher_export backup")
        if _count_value(executable, backup_path, backup_key, base_marker, home) != 1:
            raise SQLCipherSpikeError("Encrypted backup did not restore exact evidence")
        backup_wrong = _run_sqlcipher(
            executable, backup_path, wrong_key, ["SELECT COUNT(*) FROM evidence;"], home
        )
        if backup_wrong.returncode == 0:
            raise SQLCipherSpikeError("Encrypted backup accepted wrong key")
        backup_scan = _scan_for_plaintext([backup_path], [base_marker, committed_marker])
        if any(backup_scan.values()):
            raise SQLCipherSpikeError("Known plaintext found in encrypted backup")

        recovery_kek, recovery_nonce, wrapped_key = _recovery_wrap_proof(backup_key)
        recovered_backup_key = _unwrap_recovery(recovery_kek, recovery_nonce, wrapped_key)
        if _count_value(executable, backup_path, recovered_backup_key, committed_marker, home) != 1:
            raise SQLCipherSpikeError("Recovered wrapped key could not restore backup")

        plain = sqlite3.connect(plaintext_path)
        try:
            with plain:
                plain.execute("CREATE TABLE legacy(id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
                plain.execute(
                    "CREATE TRIGGER legacy_no_update BEFORE UPDATE ON legacy "
                    "BEGIN SELECT RAISE(ABORT, 'append-only'); END"
                )
                plain.execute("INSERT INTO legacy(text) VALUES(?)", (plaintext_marker,))
        finally:
            plain.close()

        migration_result = _run_sqlcipher(
            executable,
            plaintext_path,
            None,
            [
                f"ATTACH DATABASE '{_sql_quote(str(migrated_path))}' AS encrypted KEY {_attach_key(migration_key)};",
                "SELECT sqlcipher_export('encrypted');",
                "DETACH DATABASE encrypted;",
            ],
            home,
        )
        _require_ok(migration_result, "plaintext to encrypted sqlcipher_export")
        migrated_read = _run_sqlcipher(
            executable,
            migrated_path,
            migration_key,
            [
                f"SELECT COUNT(*) FROM legacy WHERE text='{_sql_quote(plaintext_marker)}';",
                "SELECT COUNT(*) FROM sqlite_master WHERE type='trigger' AND name='legacy_no_update';",
            ],
            home,
        )
        migrated_lines = _require_ok(migrated_read, "migrated encrypted readback")
        if migrated_lines[-2:] != ["1", "1"]:
            raise SQLCipherSpikeError(
                "sqlcipher_export did not preserve synthetic data/schema trigger: "
                f"{migrated_lines!r}"
            )
        migrated_scan = _scan_for_plaintext([migrated_path], [plaintext_marker])
        if any(migrated_scan.values()):
            raise SQLCipherSpikeError("Plaintext marker found in migrated encrypted DB")

        return {
            "status": "PASS",
            "revision": 2,
            "sqlcipher_version": version_text,
            "platform": platform.platform(),
            "supported_version_range": ">=4.14.0,<5.0.0 for this spike",
            "correct_key_readback": True,
            "wrong_key_rejected": wrong_key_rejected,
            "standard_sqlite_rejected": standard_sqlite_rejected,
            "wal_observed": wal_observed,
            "plaintext_scan": plaintext_scan,
            "committed_crash_recovery": True,
            "uncommitted_crash_rollback": True,
            "encrypted_export_restore": True,
            "encrypted_backup_wrong_key_rejected": True,
            "independent_recovery_wrapper_proof": True,
            "plaintext_to_new_encrypted_export": True,
            "schema_trigger_exported": True,
            "keys_logged": False,
            "note": (
                "Experiment evidence only; final Keychain/KDF/custody and packaging "
                "policy remain ADR decisions."
            ),
        }


def main() -> None:
    print(json.dumps(run_sqlcipher_spike(), sort_keys=True))


if __name__ == "__main__":
    main()
