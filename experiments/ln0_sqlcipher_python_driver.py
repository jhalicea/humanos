"""LN-0 V-02B: qualify a Python DB-API path for SQLCipher.

Experiment only. This does not add sqlcipher3 to the HumanOS runtime dependency
set. The dedicated CI job installs a pinned candidate wheel and this module proves
that the Python API can satisfy the minimum Notebook storage contract on synthetic
temporary data before any LN-1 production decision is made.
"""

from __future__ import annotations

import importlib
import json
import secrets
import sqlite3 as stdlib_sqlite
import tempfile
from pathlib import Path


SUPPORTED_MIN = (4, 14, 0)
SUPPORTED_MAX_EXCLUSIVE = (5, 0, 0)


class PythonSQLCipherSpikeError(RuntimeError):
    pass


def _version_tuple(value: str) -> tuple[int, int, int]:
    pieces = value.split(".")[:3]
    try:
        return tuple(int(piece) for piece in pieces)  # type: ignore[return-value]
    except ValueError as error:
        raise PythonSQLCipherSpikeError(f"Unparseable SQLCipher version: {value!r}") from error


def _key_sql(key: bytes) -> str:
    if len(key) != 32:
        raise ValueError("data key must be 32 bytes")
    return f'PRAGMA key = "x\'{key.hex().upper()}\'"'


def run_python_driver_spike() -> dict[str, object]:
    try:
        driver = importlib.import_module("sqlcipher3")
    except ImportError as error:
        raise PythonSQLCipherSpikeError("sqlcipher3 candidate driver is not installed") from error

    with tempfile.TemporaryDirectory(prefix="humanos-ln0-python-sqlcipher-") as tmp:
        root = Path(tmp)
        db_path = root / "candidate.db"
        key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)
        marker = "HUMANOS_LN0_PYTHON_DRIVER_" + secrets.token_hex(12)

        conn = driver.connect(str(db_path))
        try:
            # Key is the first SQL operation against the encrypted handle.
            conn.execute(_key_sql(key))
            version_row = conn.execute("PRAGMA cipher_version").fetchone()
            if not version_row or not version_row[0]:
                raise PythonSQLCipherSpikeError("Python driver exposes no cipher_version")
            cipher_version = str(version_row[0])
            parsed = _version_tuple(cipher_version)
            if parsed < SUPPORTED_MIN or parsed >= SUPPORTED_MAX_EXCLUSIVE:
                raise PythonSQLCipherSpikeError(
                    f"Python driver SQLCipher must be >=4.14.0,<5.0.0; got {cipher_version}"
                )
            journal = conn.execute("PRAGMA journal_mode=WAL").fetchone()
            if not journal or str(journal[0]).lower() != "wal":
                raise PythonSQLCipherSpikeError(f"Python driver did not enter WAL mode: {journal!r}")
            conn.execute("CREATE TABLE evidence(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("INSERT INTO evidence(value) VALUES(?)", (marker,))
            conn.commit()
            count = conn.execute("SELECT COUNT(*) FROM evidence WHERE value=?", (marker,)).fetchone()[0]
            if count != 1:
                raise PythonSQLCipherSpikeError("Python driver exact readback failed")
        finally:
            conn.close()

        reopened = driver.connect(str(db_path))
        try:
            reopened.execute(_key_sql(key))
            if reopened.execute("SELECT COUNT(*) FROM evidence WHERE value=?", (marker,)).fetchone()[0] != 1:
                raise PythonSQLCipherSpikeError("Python driver reopen/readback failed")
        finally:
            reopened.close()

        wrong_key_rejected = False
        wrong = driver.connect(str(db_path))
        try:
            wrong.execute(_key_sql(wrong_key))
            try:
                wrong.execute("SELECT COUNT(*) FROM evidence").fetchone()
            except driver.DatabaseError:
                wrong_key_rejected = True
        finally:
            wrong.close()
        if not wrong_key_rejected:
            raise PythonSQLCipherSpikeError("Python driver accepted wrong key")

        standard_sqlite_rejected = False
        plain = stdlib_sqlite.connect(str(db_path))
        try:
            try:
                plain.execute("SELECT COUNT(*) FROM evidence").fetchone()
            except stdlib_sqlite.DatabaseError:
                standard_sqlite_rejected = True
        finally:
            plain.close()
        if not standard_sqlite_rejected:
            raise PythonSQLCipherSpikeError("stdlib sqlite3 read the encrypted candidate DB")

        raw = db_path.read_bytes()
        plaintext_marker_absent = marker.encode("utf-8") not in raw
        plaintext_header_absent = not raw.startswith(b"SQLite format 3\x00")
        if not plaintext_marker_absent or not plaintext_header_absent:
            raise PythonSQLCipherSpikeError("Encrypted candidate DB exposes known plaintext")

        package_version = None
        try:
            import importlib.metadata as metadata
            package_version = metadata.version("sqlcipher3")
        except Exception:
            package_version = "UNKNOWN"

        return {
            "status": "PASS",
            "candidate_package": "sqlcipher3",
            "candidate_package_version": package_version,
            "sqlcipher_version": cipher_version,
            "dbapi_surface": all(hasattr(driver, name) for name in ("connect", "DatabaseError", "Row")),
            "wal": True,
            "parameter_binding": True,
            "commit_reopen_readback": True,
            "wrong_key_rejected": wrong_key_rejected,
            "stdlib_sqlite_rejected": standard_sqlite_rejected,
            "plaintext_marker_absent": plaintext_marker_absent,
            "plaintext_header_absent": plaintext_header_absent,
            "runtime_dependency_promoted": False,
        }


def main() -> None:
    print(json.dumps(run_python_driver_spike(), sort_keys=True))


if __name__ == "__main__":
    main()
