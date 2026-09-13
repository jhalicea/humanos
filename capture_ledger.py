"""Durable, provider-neutral pending ledger for host-observed visible chat turns."""
import hashlib
import sqlite3
from pathlib import Path
from urllib.parse import urlparse


MAX_TEXT_BYTES = 2 * 1024 * 1024
ROLES = frozenset({"USER", "ASSISTANT"})


def _digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CaptureConflict(RuntimeError):
    pass


class CaptureLedger:
    """One local WAL shared by every captured chat; models never access it directly."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(self.path), timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          PRAGMA foreign_keys=ON;
          PRAGMA busy_timeout=5000;
          CREATE TABLE IF NOT EXISTS pending_turns(
            message_id TEXT PRIMARY KEY,
            chat_id TEXT NOT NULL,
            chat_title TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('USER','ASSISTANT')),
            text TEXT NOT NULL,
            text_sha256 TEXT NOT NULL,
            observed_at TEXT NOT NULL,
            source_url TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'PENDING' CHECK(state='PENDING'));
          CREATE TABLE IF NOT EXISTS capture_conflicts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT NOT NULL,
            existing_sha256 TEXT NOT NULL,
            rejected_sha256 TEXT NOT NULL,
            observed_at TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS pending_turns_no_update
            BEFORE UPDATE ON pending_turns BEGIN
              SELECT RAISE(ABORT, 'append-only pending turn');
            END;
          CREATE TRIGGER IF NOT EXISTS pending_turns_no_delete
            BEFORE DELETE ON pending_turns BEGIN
              SELECT RAISE(ABORT, 'pending turns require verified compaction');
            END;
          CREATE TRIGGER IF NOT EXISTS capture_conflicts_no_update
            BEFORE UPDATE ON capture_conflicts BEGIN
              SELECT RAISE(ABORT, 'append-only capture conflict');
            END;
          CREATE TRIGGER IF NOT EXISTS capture_conflicts_no_delete
            BEFORE DELETE ON capture_conflicts BEGIN
              SELECT RAISE(ABORT, 'append-only capture conflict');
            END;
        """)

    def close(self):
        self.db.close()

    def capture(self, record):
        required = {"message_id", "chat_id", "chat_title", "role", "text",
                    "observed_at", "source_url"}
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("Unexpected or missing capture fields")
        for name in ("message_id", "chat_id", "chat_title", "observed_at", "source_url"):
            value = record[name]
            if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 4096:
                raise ValueError(name + " must be nonempty bounded text")
        if record["role"] not in ROLES:
            raise ValueError("Capture role must be USER or ASSISTANT")
        if not isinstance(record["text"], str) or not record["text"]:
            raise ValueError("Captured text must be nonempty")
        if len(record["text"].encode("utf-8")) > MAX_TEXT_BYTES:
            raise ValueError("Captured text exceeds the 2 MiB turn limit")
        parsed = urlparse(record["source_url"])
        if parsed.scheme != "https" or parsed.hostname not in ("chatgpt.com", "www.chatgpt.com"):
            raise PermissionError("Capture source must be ChatGPT HTTPS")
        digest = _digest(record["text"])
        prior = self.db.execute(
            "SELECT * FROM pending_turns WHERE message_id=?", (record["message_id"],)
        ).fetchone()
        if prior:
            # Capture time, page title and URL can legitimately differ on page reload.
            same_evidence = (
                prior["chat_id"] == record["chat_id"] and
                prior["role"] == record["role"] and
                prior["text_sha256"] == digest and
                prior["text"] == record["text"]
            )
            if same_evidence:
                return {"status": "ALREADY_PENDING", "message_id": record["message_id"],
                        "sha256": digest}
            with self.db:
                self.db.execute(
                    "INSERT INTO capture_conflicts(message_id,existing_sha256,rejected_sha256,observed_at) VALUES(?,?,?,?)",
                    (record["message_id"], prior["text_sha256"], digest, record["observed_at"]))
            raise CaptureConflict("Same message ID arrived with different evidence")
        with self.db:
            self.db.execute(
                """INSERT INTO pending_turns(
                   message_id,chat_id,chat_title,role,text,text_sha256,observed_at,source_url
                   ) VALUES(?,?,?,?,?,?,?,?)""",
                (record["message_id"], record["chat_id"], record["chat_title"],
                 record["role"], record["text"], digest, record["observed_at"],
                 record["source_url"]))
        return {"status": "CAPTURED", "message_id": record["message_id"],
                "sha256": digest}
