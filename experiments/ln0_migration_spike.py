"""LN-0 V-01: evidence-preserving migration spike.

This is deliberately NOT production migration code. It operates only on a supplied
SQLite/runtime-root fixture and builds an isolated candidate kernel so LN-0 can
measure whether Runtime 0.1 evidence can be mapped without loss.

Properties under test:
- every source DB row and selected projection/recovery file gets an explicit map;
- exact transcript text becomes a unique payload object per message;
- evidence-producing rows become deterministic candidate kernel events;
- operational/current-state rows are retained, not silently promoted to history;
- rerunning an unchanged source is idempotent;
- changing the source after a migration to the same target fails closed.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
MIGRATION_VERSION = "ln0-v01-spike-1"
NAMESPACE = uuid.UUID("63eeec48-49cf-49b9-a63a-02678c55e8e1")
ZERO_HASH = "0" * 64

EVIDENCE_EVENT_TYPES = {
    "transcript": ("conversation", "CAPTURE.MESSAGE"),
    "events": ("system", "CAPTURE.OBSERVATION"),
    "recovery": ("system", "SYSTEM.RECOVERY"),
    "privacy_operations": ("policy", "POLICY.DECISION"),
    "privacy_receipts": ("policy", "CAPTURE.OBSERVATION"),
}

PROJECTION_FILES = ("active-index.json", "bindings.json")


@dataclass(frozen=True)
class SourceRecord:
    source_kind: str
    source_name: str
    source_key: str
    canonical_bytes: bytes
    decoded: Any

    @property
    def row_hash(self) -> str:
        return hashlib.sha256(self.canonical_bytes).hexdigest()


class MigrationConflict(RuntimeError):
    """Raised when an already-migrated source no longer matches its evidence."""


def _json_safe(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"__blob_base64__": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        _json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _user_tables(db: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def _primary_key_columns(db: sqlite3.Connection, table: str) -> list[str]:
    columns = list(db.execute(f'PRAGMA table_info("{table}")'))
    return [row[1] for row in sorted(columns, key=lambda row: row[5]) if row[5] > 0]


def _row_key(row: sqlite3.Row, pk_columns: list[str], fallback_index: int) -> str:
    if pk_columns:
        return "|".join(
            f"{column}={json.dumps(_json_safe(row[column]), ensure_ascii=False, sort_keys=True)}"
            for column in pk_columns
        )
    return f"ordinal={fallback_index}"


def _db_records(source_db: Path) -> list[SourceRecord]:
    db = sqlite3.connect(str(source_db))
    db.row_factory = sqlite3.Row
    try:
        records: list[SourceRecord] = []
        for table in _user_tables(db):
            pk_columns = _primary_key_columns(db, table)
            order = ",".join(f'"{column}"' for column in pk_columns) if pk_columns else "rowid"
            rows = list(db.execute(f'SELECT * FROM "{table}" ORDER BY {order}'))
            for index, row in enumerate(rows, 1):
                decoded = {key: row[key] for key in row.keys()}
                records.append(
                    SourceRecord(
                        source_kind="DB_ROW",
                        source_name=table,
                        source_key=_row_key(row, pk_columns, index),
                        canonical_bytes=_canonical_json(decoded),
                        decoded=decoded,
                    )
                )
        return records
    finally:
        db.close()


def _file_records(runtime_root: Path) -> list[SourceRecord]:
    records: list[SourceRecord] = []
    candidates: list[Path] = []
    for name in PROJECTION_FILES:
        path = runtime_root / name
        if path.is_file():
            candidates.append(path)
    pages = runtime_root / "pages"
    if pages.is_dir():
        candidates.extend(path for path in pages.rglob("*") if path.is_file())
    recovery = runtime_root / "recovery.jsonl"
    if recovery.is_file():
        candidates.append(recovery)

    for path in sorted(candidates, key=lambda item: item.relative_to(runtime_root).as_posix()):
        relative = path.relative_to(runtime_root).as_posix()
        payload = path.read_bytes()
        records.append(
            SourceRecord(
                source_kind="FILE",
                source_name=relative,
                source_key=relative,
                canonical_bytes=payload,
                decoded=None,
            )
        )
    return records


def inventory_runtime(runtime_root: Path) -> list[SourceRecord]:
    runtime_root = Path(runtime_root).resolve()
    source_db = runtime_root / "notebook.sqlite3"
    if not source_db.is_file():
        raise FileNotFoundError(f"Runtime Notebook not found: {source_db}")
    return _db_records(source_db) + _file_records(runtime_root)


def source_fingerprint(records: Iterable[SourceRecord]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: (item.source_kind, item.source_name, item.source_key)):
        digest.update(record.source_kind.encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.source_name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.source_key.encode("utf-8"))
        digest.update(b"\0")
        digest.update(record.row_hash.encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _init_target(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        PRAGMA foreign_keys=ON;
        CREATE TABLE IF NOT EXISTS migration_meta(
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS legacy_records(
          source_kind TEXT NOT NULL,
          source_name TEXT NOT NULL,
          source_key TEXT NOT NULL,
          row_hash TEXT NOT NULL,
          preserved BLOB NOT NULL,
          status TEXT NOT NULL,
          target_ref TEXT NOT NULL,
          target_event_id TEXT,
          target_payload_id TEXT,
          PRIMARY KEY(source_kind, source_name, source_key)
        );
        CREATE TABLE IF NOT EXISTS payload_objects(
          payload_id TEXT PRIMARY KEY,
          event_id TEXT NOT NULL UNIQUE,
          content_hash TEXT NOT NULL,
          mime_type TEXT NOT NULL,
          size_bytes INTEGER NOT NULL,
          payload BLOB NOT NULL,
          source_name TEXT NOT NULL,
          source_key TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS kernel_events(
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id TEXT NOT NULL UNIQUE,
          schema_version INTEGER NOT NULL,
          stream TEXT NOT NULL,
          event_type TEXT NOT NULL,
          occurred_at TEXT,
          observed_at TEXT,
          ingested_at TEXT,
          actor_type TEXT NOT NULL,
          source_system TEXT NOT NULL,
          source_locator TEXT NOT NULL,
          ingestion_id TEXT NOT NULL UNIQUE,
          payload_id TEXT NOT NULL UNIQUE,
          legacy_source_name TEXT NOT NULL,
          legacy_source_key TEXT NOT NULL,
          prev_event_hash TEXT NOT NULL,
          event_hash TEXT NOT NULL UNIQUE,
          FOREIGN KEY(payload_id) REFERENCES payload_objects(payload_id)
        );
        """
    )


def _meta(db: sqlite3.Connection, key: str) -> str | None:
    row = db.execute("SELECT value FROM migration_meta WHERE key=?", (key,)).fetchone()
    return row[0] if row else None


def _event_payload(record: SourceRecord) -> tuple[bytes, str]:
    if record.source_name == "transcript" and isinstance(record.decoded, dict):
        text = record.decoded.get("text")
        if not isinstance(text, str):
            raise MigrationConflict(f"Transcript row has no text: {record.source_key}")
        return text.encode("utf-8"), "text/plain; charset=utf-8"
    return record.canonical_bytes, "application/json" if record.source_kind == "DB_ROW" else "application/octet-stream"


def _time_fields(record: SourceRecord) -> tuple[str | None, str | None, str | None]:
    if isinstance(record.decoded, dict):
        created = record.decoded.get("created")
        if isinstance(created, str):
            return created, created, created
    return None, None, None


def _deterministic_id(kind: str, record: SourceRecord) -> str:
    material = f"{MIGRATION_VERSION}:{kind}:{record.source_kind}:{record.source_name}:{record.source_key}:{record.row_hash}"
    return str(uuid.uuid5(NAMESPACE, material))


def _event_hash(previous_hash: str, event: dict[str, Any]) -> str:
    envelope = dict(event)
    envelope["prev_event_hash"] = previous_hash
    return hashlib.sha256(_canonical_json(envelope)).hexdigest()


def migrate_runtime_fixture(runtime_root: Path, target_db: Path) -> dict[str, Any]:
    """Migrate an isolated Runtime 0.1 fixture into the candidate LN-0 kernel.

    The function is intentionally strict: once a target records a source
    fingerprint, a changed source is rejected rather than partially remigrated.
    This makes V-01 useful for proving idempotent cutover behavior.
    """
    runtime_root = Path(runtime_root).resolve()
    target_db = Path(target_db).resolve()
    target_db.parent.mkdir(parents=True, exist_ok=True)

    records = inventory_runtime(runtime_root)
    fingerprint = source_fingerprint(records)
    db = sqlite3.connect(str(target_db))
    db.row_factory = sqlite3.Row
    try:
        _init_target(db)
        prior = _meta(db, "source_fingerprint")
        if prior is not None and prior != fingerprint:
            raise MigrationConflict("Source fixture changed after migration; refusing partial remap")

        if prior is None:
            with db:
                db.execute(
                    "INSERT INTO migration_meta(key,value) VALUES('migration_version',?)",
                    (MIGRATION_VERSION,),
                )
                db.execute(
                    "INSERT INTO migration_meta(key,value) VALUES('source_fingerprint',?)",
                    (fingerprint,),
                )

        previous_row = db.execute(
            "SELECT event_hash FROM kernel_events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous_row[0] if previous_row else ZERO_HASH

        migrated_now = 0
        retained_now = 0
        for record in sorted(records, key=lambda item: (item.source_kind, item.source_name, item.source_key)):
            existing = db.execute(
                "SELECT row_hash,status,target_ref,target_event_id,target_payload_id "
                "FROM legacy_records WHERE source_kind=? AND source_name=? AND source_key=?",
                (record.source_kind, record.source_name, record.source_key),
            ).fetchone()
            if existing:
                if existing["row_hash"] != record.row_hash:
                    raise MigrationConflict(
                        f"Source record changed: {record.source_kind}:{record.source_name}:{record.source_key}"
                    )
                continue

            event_contract = EVIDENCE_EVENT_TYPES.get(record.source_name) if record.source_kind == "DB_ROW" else None
            if event_contract is None:
                status = "RETAINED_PROJECTION" if record.source_kind == "FILE" else "RETAINED_OPERATIONAL"
                target_ref = f"legacy:{record.source_kind}:{record.source_name}:{record.source_key}"
                with db:
                    db.execute(
                        "INSERT INTO legacy_records(source_kind,source_name,source_key,row_hash,preserved,status,target_ref) "
                        "VALUES(?,?,?,?,?,?,?)",
                        (
                            record.source_kind,
                            record.source_name,
                            record.source_key,
                            record.row_hash,
                            record.canonical_bytes,
                            status,
                            target_ref,
                        ),
                    )
                retained_now += 1
                continue

            stream, event_type = event_contract
            event_id = _deterministic_id("event", record)
            payload_id = _deterministic_id("payload", record)
            payload, mime_type = _event_payload(record)
            payload_hash = hashlib.sha256(payload).hexdigest()
            ingestion_id = _deterministic_id("ingestion", record)
            occurred_at, observed_at, ingested_at = _time_fields(record)
            source_locator = f"legacy:{record.source_name}:{record.source_key}"
            event_envelope = {
                "event_id": event_id,
                "schema_version": SCHEMA_VERSION,
                "stream": stream,
                "event_type": event_type,
                "occurred_at": occurred_at,
                "observed_at": observed_at,
                "ingested_at": ingested_at,
                "actor_type": "LEGACY_EVIDENCE",
                "source_system": "humanos-runtime-0.1",
                "source_locator": source_locator,
                "ingestion_id": ingestion_id,
                "payload_id": payload_id,
                "payload_hash": payload_hash,
                "legacy_source_name": record.source_name,
                "legacy_source_key": record.source_key,
            }
            event_hash = _event_hash(previous_hash, event_envelope)
            with db:
                db.execute(
                    "INSERT INTO payload_objects(payload_id,event_id,content_hash,mime_type,size_bytes,payload,source_name,source_key) "
                    "VALUES(?,?,?,?,?,?,?,?)",
                    (
                        payload_id,
                        event_id,
                        payload_hash,
                        mime_type,
                        len(payload),
                        payload,
                        record.source_name,
                        record.source_key,
                    ),
                )
                db.execute(
                    "INSERT INTO kernel_events(event_id,schema_version,stream,event_type,occurred_at,observed_at,ingested_at,"
                    "actor_type,source_system,source_locator,ingestion_id,payload_id,legacy_source_name,legacy_source_key,"
                    "prev_event_hash,event_hash) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        event_id,
                        SCHEMA_VERSION,
                        stream,
                        event_type,
                        occurred_at,
                        observed_at,
                        ingested_at,
                        "LEGACY_EVIDENCE",
                        "humanos-runtime-0.1",
                        source_locator,
                        ingestion_id,
                        payload_id,
                        record.source_name,
                        record.source_key,
                        previous_hash,
                        event_hash,
                    ),
                )
                db.execute(
                    "INSERT INTO legacy_records(source_kind,source_name,source_key,row_hash,preserved,status,target_ref,"
                    "target_event_id,target_payload_id) VALUES(?,?,?,?,?,?,?,?,?)",
                    (
                        record.source_kind,
                        record.source_name,
                        record.source_key,
                        record.row_hash,
                        record.canonical_bytes,
                        "MIGRATED_EVIDENCE",
                        f"event:{event_id}",
                        event_id,
                        payload_id,
                    ),
                )
            previous_hash = event_hash
            migrated_now += 1

        source_count = len(records)
        mapped_count = db.execute("SELECT COUNT(*) FROM legacy_records").fetchone()[0]
        migrated_total = db.execute(
            "SELECT COUNT(*) FROM legacy_records WHERE status='MIGRATED_EVIDENCE'"
        ).fetchone()[0]
        retained_total = mapped_count - migrated_total
        event_count = db.execute("SELECT COUNT(*) FROM kernel_events").fetchone()[0]
        payload_count = db.execute("SELECT COUNT(*) FROM payload_objects").fetchone()[0]
        if mapped_count != source_count:
            raise MigrationConflict(
                f"Migration coverage mismatch: source={source_count} mapped={mapped_count}"
            )
        if event_count != payload_count or event_count != migrated_total:
            raise MigrationConflict("Candidate event/payload mapping is not one-to-one")

        return {
            "migration_version": MIGRATION_VERSION,
            "source_fingerprint": fingerprint,
            "source_records": source_count,
            "mapped_records": mapped_count,
            "migrated_evidence": migrated_total,
            "retained_records": retained_total,
            "kernel_events": event_count,
            "payload_objects": payload_count,
            "migrated_now": migrated_now,
            "retained_now": retained_now,
            "idempotent_replay": migrated_now == 0 and retained_now == 0,
        }
    finally:
        db.close()


def verify_candidate_chain(target_db: Path) -> bool:
    db = sqlite3.connect(str(target_db))
    db.row_factory = sqlite3.Row
    try:
        previous_hash = ZERO_HASH
        for row in db.execute("SELECT * FROM kernel_events ORDER BY seq"):
            payload = db.execute(
                "SELECT content_hash,payload FROM payload_objects WHERE payload_id=?", (row["payload_id"],)
            ).fetchone()
            if payload is None or hashlib.sha256(payload["payload"]).hexdigest() != payload["content_hash"]:
                raise MigrationConflict(f"Payload verification failed for {row['event_id']}")
            event_envelope = {
                "event_id": row["event_id"],
                "schema_version": row["schema_version"],
                "stream": row["stream"],
                "event_type": row["event_type"],
                "occurred_at": row["occurred_at"],
                "observed_at": row["observed_at"],
                "ingested_at": row["ingested_at"],
                "actor_type": row["actor_type"],
                "source_system": row["source_system"],
                "source_locator": row["source_locator"],
                "ingestion_id": row["ingestion_id"],
                "payload_id": row["payload_id"],
                "payload_hash": payload["content_hash"],
                "legacy_source_name": row["legacy_source_name"],
                "legacy_source_key": row["legacy_source_key"],
            }
            if row["prev_event_hash"] != previous_hash:
                raise MigrationConflict(f"Candidate chain predecessor mismatch at {row['event_id']}")
            expected = _event_hash(previous_hash, event_envelope)
            if row["event_hash"] != expected:
                raise MigrationConflict(f"Candidate chain hash mismatch at {row['event_id']}")
            previous_hash = row["event_hash"]
        return True
    finally:
        db.close()
