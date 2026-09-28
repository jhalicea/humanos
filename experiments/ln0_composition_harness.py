"""TEST-ONLY REFERENCE COMPOSITION HARNESS.

This is synthetic qualification code, not LN-1 or production runtime code. It
reproduces the already accepted V-01/V-03/V-04/V-05 contract boundaries in one
shared SQLite KernelStore because those frozen fixtures have no common API. This is
contract reuse, not code reuse. V-02 encryption is separately exercised against a
serialized snapshot using the accepted SQLCipher CLI/configuration helpers.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from experiments.ln0_migration_spike import SourceRecord, _deterministic_id, _event_payload
from experiments.ln0_sqlcipher_spike_v2 import _run_sqlcipher


class CompositionDenied(PermissionError):
    pass


class StalePacket(CompositionDenied):
    pass


class IngestionConflict(ValueError):
    pass


class RecoveryRequired(RuntimeError):
    pass


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class LegacyEvent:
    event_id: str
    payload_object_id: str
    payload: bytes
    provenance: str
    # Source/migration claim only. import_legacy deliberately ignores it.
    provider: str = "HOSTED_ALLOWED"


def migrated_legacy_event(source_key: str, payload_text: str) -> LegacyEvent:
    """Apply the accepted V-01 deterministic event/object identity mapping."""
    canonical_row = _canonical({"role": "HUMAN", "text": payload_text, "source_key": source_key})
    record = SourceRecord("DB_ROW", "transcript", source_key, canonical_row,
                          {"role": "HUMAN", "text": payload_text})
    payload, _mime = _event_payload(record)
    return LegacyEvent(
        event_id=_deterministic_id("event", record),
        payload_object_id=_deterministic_id("payload", record),
        payload=payload,
        provenance=f"legacy:transcript:{source_key}:{record.row_hash}",
    )


@dataclass(frozen=True)
class CompiledPacket:
    packet_id: str
    payload: bytes
    provider_id: str
    lease: object
    issuer: object


@dataclass(frozen=True)
class ContextRequest:
    handle: object
    provider_id: str
    record_ids: tuple[str, ...]


@dataclass(frozen=True)
class ErasureCheckpoint:
    deletion_id: str
    event_id: str
    payload_object_id: str
    match_length: int
    erasure_tag: str


class KernelCheckpointBoundary:
    """Synthetic out-of-store V-04 checkpoint boundary; contains no plaintext."""

    def __init__(self, secret: bytes | None = None, checkpoints: Iterable[ErasureCheckpoint] = ()):
        self._secret = secret or secrets.token_bytes(32)
        if len(self._secret) < 16:
            raise ValueError("checkpoint secret must be at least 128 bits")
        self._checkpoints = {item.deletion_id: item for item in checkpoints}

    def register(self, deletion_id: str, event_id: str, payload_object_id: str, payload: bytes) -> ErasureCheckpoint:
        tag = hmac.new(self._secret, b"LN0 composition erase\0" + deletion_id.encode() + b"\0" + payload, hashlib.sha256).hexdigest()
        item = ErasureCheckpoint(deletion_id, event_id, payload_object_id, len(payload), tag)
        prior = self._checkpoints.get(deletion_id)
        if prior is not None and prior != item:
            raise RecoveryRequired("deletion checkpoint identity conflict")
        self._checkpoints[deletion_id] = item
        return item

    def get(self, deletion_id: str) -> ErasureCheckpoint | None:
        return self._checkpoints.get(deletion_id)

    def checkpoints(self) -> tuple[ErasureCheckpoint, ...]:
        return tuple(self._checkpoints[key] for key in sorted(self._checkpoints))

    def matches_window(self, item: ErasureCheckpoint, candidate: bytes) -> bool:
        n = item.match_length
        if not n or len(candidate) < n:
            return False
        for offset in range(len(candidate) - n + 1):
            tag = hmac.new(self._secret, b"LN0 composition erase\0" + item.deletion_id.encode() + b"\0" + candidate[offset:offset + n], hashlib.sha256).hexdigest()
            if hmac.compare_digest(item.erasure_tag, tag):
                return True
        return False


class CorePolicyAuthority:
    """Out-of-store Core authority for synthetic disclosure and exemption grants."""

    def __init__(self):
        self.capability = object()
        self._independent_sources: dict[tuple[str, str], str] = {}

    def name_independent_source(self, event_id: str, payload_object_id: str) -> str:
        authorization_id = secrets.token_hex(32)
        self._independent_sources[(event_id, payload_object_id)] = authorization_id
        return authorization_id

    def validates_independent_source(self, event_id: str, payload_object_id: str,
                                    authorization_id: str) -> bool:
        expected = self._independent_sources.get((event_id, payload_object_id), "")
        return bool(expected and hmac.compare_digest(expected, authorization_id))


class KernelStore:
    """One synthetic governed store, including event, payload, derivative and erase state."""

    # Schema-owned content-bearing fields. Every one is scanned with V-04 window
    # semantics. All other fields are controlled identifiers, enums, chronology,
    # or deletion/integrity metadata and are structural by this test-only contract.
    _CONTENT_SCAN_FIELDS = {
        "events": ("payload", "provenance", "ingestion_id"),
        "derivatives": ("body",),
        "auxiliary_content": ("store_key", "content"),
    }
    _DERIVATIVE_KINDS = {
        "context_packet", "cache-embedded", "multi-source", "local-cache",
        "transformed-sole", "transformed-multi", "unlineaged-leak",
    }

    _SOURCE_POLICIES = {
        "connector-token": ("connector", "OBSERVED_EVIDENCE"),
        "migration-token": ("migration", "LEGACY_EVIDENCE"),
        "owner-token": ("owner", "OWNER_SUBMITTED"),
    }

    def __init__(self, path: Path, *, checkpoint: KernelCheckpointBoundary | None = None,
                 core_authority: CorePolicyAuthority | None = None,
                 restoring: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint = checkpoint or KernelCheckpointBoundary()
        self.core_authority = core_authority or CorePolicyAuthority()
        self._lock = threading.RLock()
        self._init()
        self._restoring = restoring
        if not restoring:
            self._set_meta("restore_state", "LIVE")
        self.migration_capability = object()
        self._policy_capability = self.core_authority.capability

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=30, isolation_level="DEFERRED", factory=_ClosingConnection)
        db.execute("PRAGMA busy_timeout=30000")
        return db

    def _init(self) -> None:
        with self._connect() as db:
            db.executescript("""
            PRAGMA journal_mode=DELETE;
            PRAGMA secure_delete=ON;
            CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(
              event_id TEXT PRIMARY KEY, payload_object_id TEXT UNIQUE NOT NULL,
              source_id TEXT NOT NULL, ingestion_id TEXT NOT NULL,
              source_authority TEXT NOT NULL, provenance TEXT NOT NULL, payload BLOB,
              content_hash TEXT, submission_fingerprint TEXT, sequence INTEGER UNIQUE NOT NULL,
              previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL UNIQUE,
              deletion_state TEXT NOT NULL DEFAULT 'LIVE', UNIQUE(source_id, ingestion_id));
            CREATE TABLE IF NOT EXISTS policy_state(
              event_id TEXT PRIMARY KEY, provider TEXT NOT NULL, privacy TEXT NOT NULL,
              policy_version INTEGER NOT NULL DEFAULT 1,
              FOREIGN KEY(event_id) REFERENCES events(event_id));
            CREATE TABLE IF NOT EXISTS derivatives(
              derivative_id TEXT PRIMARY KEY, kind TEXT NOT NULL, lineage TEXT NOT NULL,
              body BLOB, state TEXT NOT NULL DEFAULT 'LIVE');
            CREATE TABLE IF NOT EXISTS tombstones(
              deletion_id TEXT PRIMARY KEY, event_id TEXT NOT NULL,
              payload_object_id TEXT NOT NULL, state TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS deletion_receipts(
              deletion_id TEXT PRIMARY KEY, event_id TEXT NOT NULL,
              payload_object_id TEXT NOT NULL, state TEXT NOT NULL,
              previous_receipt_hash TEXT NOT NULL, receipt_hash TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS independent_source_authorizations(
              event_id TEXT PRIMARY KEY, payload_object_id TEXT NOT NULL,
              authorization_id TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS auxiliary_content(
              store_key TEXT PRIMARY KEY, content BLOB NOT NULL);
            """)
        if self._get_meta("sequence") is None:
            self._set_meta("sequence", "0")
            self._set_meta("generation", "0")
            self._set_meta("restore_state", "LIVE")

    def _get_meta(self, key: str) -> str | None:
        with self._connect() as db:
            row = db.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def _set_meta(self, key: str, value: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO meta VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))

    @property
    def generation(self) -> int:
        return int(self._get_meta("generation") or 0)

    @staticmethod
    def _bump_generation(db: sqlite3.Connection) -> None:
        row = db.execute("SELECT value FROM meta WHERE key='generation'").fetchone()
        db.execute("UPDATE meta SET value=? WHERE key='generation'", (str(int(row[0]) + 1),))

    def _require_live(self) -> None:
        if self._restoring or self._get_meta("restore_state") != "LIVE":
            raise RecoveryRequired("RESTORE_NOT_READY")

    def _commit(self, *, event_id: str, payload_object_id: str, source_id: str,
                ingestion_id: str, authority: str, provenance: str,
                payload: bytes, fingerprint: str) -> tuple[str, str]:
        with self._lock, self._connect() as db:
            self._require_live()
            existing = db.execute("SELECT event_id,submission_fingerprint FROM events WHERE source_id=? AND ingestion_id=?", (source_id, ingestion_id)).fetchone()
            if existing:
                if existing[1] != fingerprint:
                    raise IngestionConflict("ingestion identity reused with conflicting content/claims")
                return existing[0], db.execute("SELECT payload_object_id FROM events WHERE event_id=?", (existing[0],)).fetchone()[0]
            seq = int(db.execute("SELECT value FROM meta WHERE key='sequence'").fetchone()[0]) + 1
            prev = db.execute("SELECT event_hash FROM events ORDER BY sequence DESC LIMIT 1").fetchone()
            previous_hash = prev[0] if prev else "GENESIS"
            # Test-only deletion-safe integrity representation: event integrity covers
            # identity and chronology, never a plaintext-derived digest.
            envelope = {"event_id": event_id, "payload_object_id": payload_object_id,
                        "source_id": source_id, "ingestion_id": ingestion_id,
                        "authority": authority, "provenance": provenance,
                        "sequence": seq, "previous_hash": previous_hash}
            event_hash = _sha(_canonical(envelope))
            db.execute("INSERT INTO events VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'LIVE')",
                       (event_id, payload_object_id, source_id, ingestion_id, authority,
                        provenance, payload, _sha(payload), fingerprint,
                        seq, previous_hash, event_hash))
            # New/imported records receive no disclosure authority from their source.
            db.execute("INSERT INTO policy_state(event_id,provider,privacy) VALUES(?,?,?)",
                       (event_id, "PROVIDER_DENIED", "UNCLASSIFIED"))
            db.execute("UPDATE meta SET value=? WHERE key='sequence'", (str(seq),))
            self._bump_generation(db)
            return event_id, payload_object_id

    def import_legacy(self, legacy: LegacyEvent, *, capability: object) -> tuple[str, str]:
        if capability is not self.migration_capability:
            raise CompositionDenied("controlled migration capability required")
        if not legacy.event_id or not legacy.payload_object_id:
            raise ValueError("migration must preserve stable identities")
        fp = _sha(_canonical({"legacy_event_id": legacy.event_id,
                              "payload_object_id": legacy.payload_object_id,
                              "payload": legacy.payload.hex(), "provenance": legacy.provenance}))
        return self._commit(event_id=legacy.event_id, payload_object_id=legacy.payload_object_id,
                            source_id="migration", ingestion_id=legacy.event_id,
                            authority="LEGACY_EVIDENCE", provenance=legacy.provenance,
                            payload=legacy.payload,
                            fingerprint=fp)

    def ingest(self, token: str, ingestion_id: str, payload: bytes, *, claims: dict[str, Any],
               provenance: str) -> tuple[str, str]:
        resolved = self._SOURCE_POLICIES.get(token)
        if resolved is None or token == "migration-token":
            raise CompositionDenied("authenticated source required")
        source_id, authority = resolved
        # Source claims never set authority; Core resolves it from the authenticated token.
        fingerprint = _sha(_canonical({"ingestion_id": ingestion_id, "payload": payload.hex(),
                                       "claims": claims, "provenance": provenance}))
        event_id = "evt-" + _sha((source_id + "\0" + ingestion_id).encode())
        payload_object_id = "po-" + _sha(("payload\0" + event_id).encode())
        return self._commit(event_id=event_id, payload_object_id=payload_object_id,
                            source_id=source_id, ingestion_id=ingestion_id,
                            authority=authority, provenance=provenance,
                            payload=payload, fingerprint=fingerprint)

    def add_derivative(self, kind: str, lineage: Sequence[str], body: bytes) -> str:
        with self._lock, self._connect() as db:
            self._require_live()
            if kind not in self._DERIVATIVE_KINDS:
                raise ValueError("derivative kind must be a schema-owned enum")
            if not lineage or len(set(lineage)) != len(lineage):
                raise ValueError("derivative requires unique source lineage")
            for event_id in lineage:
                if not db.execute("SELECT 1 FROM events WHERE event_id=?", (event_id,)).fetchone():
                    raise ValueError("unknown lineage event")
            derivative_id = "d-" + uuid.uuid4().hex
            db.execute("INSERT INTO derivatives VALUES(?,?,?,?,'LIVE')",
                       (derivative_id, kind, json.dumps(list(lineage)), body))
            self._bump_generation(db)
            return derivative_id

    def update_authorization(self, event_id: str, provider: str, *, capability: object) -> None:
        if capability is not self._policy_capability:
            raise CompositionDenied("Core policy capability required")
        if provider not in {"HOSTED_ALLOWED", "LOCAL_ONLY", "PROVIDER_DENIED"}:
            raise ValueError("unknown provider authorization")
        with self._lock, self._connect() as db:
            self._require_live()
            db.execute("UPDATE policy_state SET provider=?,policy_version=policy_version+1 WHERE event_id=?", (provider, event_id))
            self._bump_generation(db)

    def update_privacy(self, event_id: str, privacy: str, *, capability: object) -> None:
        if capability is not self._policy_capability:
            raise CompositionDenied("Core policy capability required")
        if privacy not in {"UNCLASSIFIED", "STANDARD", "PRIVATE", "ERASE_REQUESTED"}:
            raise ValueError("unknown privacy class")
        with self._lock, self._connect() as db:
            self._require_live()
            db.execute("UPDATE policy_state SET privacy=?,policy_version=policy_version+1 WHERE event_id=?", (privacy, event_id))
            self._bump_generation(db)

    def read_event(self, event_id: str) -> tuple[Any, ...] | None:
        self._require_live()
        with self._connect() as db:
            return db.execute("SELECT event_id,payload_object_id,source_authority,provenance,deletion_state,event_hash FROM events WHERE event_id=?", (event_id,)).fetchone()

    def read_payload(self, event_id: str) -> bytes:
        self._require_live()
        with self._connect() as db:
            row = db.execute("SELECT payload,deletion_state FROM events WHERE event_id=?", (event_id,)).fetchone()
        if not row or row[0] is None or row[1] != "LIVE":
            raise CompositionDenied("payload missing or erased")
        return bytes(row[0])

    def authorized_retrieval(self, event_ids: Sequence[str], provider_id: str) -> list[dict[str, Any]]:
        self._require_live()
        if provider_id not in {"hosted-fixture", "local-fixture"}:
            raise CompositionDenied("unknown provider")
        items: list[dict[str, Any]] = []
        with self._connect() as db:
            for event_id in event_ids:
                row = db.execute("SELECT e.event_id,e.payload_object_id,e.payload,p.provider,p.privacy,e.deletion_state,e.provenance FROM events e JOIN policy_state p USING(event_id) WHERE e.event_id=?", (event_id,)).fetchone()
                if not row or row[2] is None or row[5] != "LIVE":
                    raise CompositionDenied("governed source absent, erasing, or erased")
                if provider_id == "hosted-fixture" and (row[3] != "HOSTED_ALLOWED" or row[4] != "STANDARD"):
                    raise CompositionDenied("Core policy denies hosted disclosure")
                items.append({"event_id": row[0], "payload_object_id": row[1],
                              "content": bytes(row[2]).decode("utf-8"), "provenance": row[6]})
        return items

    def request_erase(self, event_id: str, *, token: str, interrupt_after_tombstone: bool = False) -> bool:
        if token != "owner-token":
            raise CompositionDenied("authorized owner erase required")
        with self._lock, self._connect() as db:
            self._require_live()
            row = db.execute("SELECT payload_object_id,payload,deletion_state FROM events WHERE event_id=?", (event_id,)).fetchone()
            if not row or row[1] is None:
                raise CompositionDenied("live payload required")
            deletion_id = "del-" + _sha(event_id.encode())[:24]
            checkpoint = self.checkpoint.register(deletion_id, event_id, row[0], bytes(row[1]))
            db.execute("INSERT INTO tombstones VALUES(?,?,?,'RECOVERY_REQUIRED') ON CONFLICT(deletion_id) DO NOTHING", (deletion_id, event_id, row[0]))
            db.execute("UPDATE events SET deletion_state='ERASING' WHERE event_id=?", (event_id,))
            self._bump_generation(db)
        if interrupt_after_tombstone:
            return False
        self.replay_or_recover()
        return True

    def _reconcile_checkpoint_rows(self, db: sqlite3.Connection,
                                   item: ErasureCheckpoint) -> str | None:
        event = db.execute(
            "SELECT payload_object_id FROM events WHERE event_id=?", (item.event_id,)
        ).fetchone()
        if not event or event[0] != item.payload_object_id:
            raise RecoveryRequired("restore event identity does not match deletion checkpoint")
        tombstone = db.execute(
            "SELECT event_id,payload_object_id FROM tombstones WHERE deletion_id=?",
            (item.deletion_id,)).fetchone()
        if tombstone and tombstone != (item.event_id, item.payload_object_id):
            raise RecoveryRequired("tombstone identity does not match deletion checkpoint")
        receipt = db.execute(
            "SELECT event_id,payload_object_id,state,previous_receipt_hash,receipt_hash "
            "FROM deletion_receipts WHERE deletion_id=?", (item.deletion_id,)).fetchone()
        if receipt:
            if receipt[:3] != (item.event_id, item.payload_object_id, "ERASED"):
                raise RecoveryRequired("receipt identity/state does not match deletion checkpoint")
            expected = {"deletion_id": item.deletion_id, "event_id": item.event_id,
                        "payload_object_id": item.payload_object_id, "state": "ERASED",
                        "previous_receipt_hash": receipt[3]}
            if receipt[4] != _sha(_canonical(expected)):
                raise RecoveryRequired("deletion receipt integrity mismatch")
            return str(receipt[3])
        return None

    def _is_authorized_independent_cell(self, db: sqlite3.Connection,
                                        event_id: str, payload_object_id: str,
                                        item: ErasureCheckpoint, payload: bytes) -> bool:
        if len(payload) != item.match_length or not self.checkpoint.matches_window(item, payload):
            return False
        authorization = db.execute(
            "SELECT payload_object_id,authorization_id "
            "FROM independent_source_authorizations WHERE event_id=?", (event_id,)
        ).fetchone()
        return bool(authorization and event_id != item.event_id
                    and payload_object_id != item.payload_object_id
                    and authorization[0] == payload_object_id
                    and self.core_authority.validates_independent_source(
                        event_id, payload_object_id, authorization[1]))

    def _verify_all_store_erasure(self, db: sqlite3.Connection,
                                  item: ErasureCheckpoint) -> None:
        # This schema-owned boundary enumerates every content-capable field. Tables
        # omitted here contain only constrained structural identifiers/enums,
        # chronology, hashes, and deletion metadata by this synthetic contract.
        for table, columns in self._CONTENT_SCAN_FIELDS.items():
            for column in columns:
                if table == "events" and column == "payload":
                    rows = db.execute(
                        "SELECT event_id,payload_object_id,payload FROM events WHERE payload IS NOT NULL"
                    ).fetchall()
                else:
                    rows = [(None, None, row[0]) for row in db.execute(
                        f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL").fetchall()]
                for event_id, payload_object_id, value in rows:
                    if value is None:
                        continue
                    candidate = bytes(value) if isinstance(value, (bytes, bytearray, memoryview)) else str(value).encode("utf-8")
                    if not self.checkpoint.matches_window(item, candidate):
                        continue
                    if (table == "events" and column == "payload"
                            and self._is_authorized_independent_cell(
                                db, event_id, payload_object_id, item, candidate)):
                        continue
                    raise RecoveryRequired(
                        f"erased bytes remain in governed persistent field {table}.{column}")
        digests = db.execute(
            "SELECT content_hash,submission_fingerprint FROM events WHERE event_id=?",
            (item.event_id,)).fetchone()
        if digests != (None, None):
            raise RecoveryRequired("erased event retains a content-derived digest/fingerprint")

    def _apply_checkpoint(self, item: ErasureCheckpoint) -> None:
        with self._lock, self._connect() as db:
            prior_receipt_hash = self._reconcile_checkpoint_rows(db, item)
            db.execute("INSERT OR IGNORE INTO tombstones VALUES(?,?,?,'RECOVERY_REQUIRED')", (item.deletion_id, item.event_id, item.payload_object_id))
            db.execute("UPDATE events SET deletion_state='ERASING' WHERE event_id=?", (item.event_id,))
            for derivative_id, lineage_raw, body, state in db.execute("SELECT derivative_id,lineage,body,state FROM derivatives WHERE state='LIVE'").fetchall():
                lineage = json.loads(lineage_raw)
                if item.event_id in lineage:
                    remaining = [source for source in lineage if source != item.event_id]
                    if remaining:
                        replacement = b" ".join(self._payload_from(db, source) for source in remaining)
                        db.execute("UPDATE derivatives SET lineage=?,body=? WHERE derivative_id=?", (json.dumps(remaining), replacement, derivative_id))
                    else:
                        db.execute("UPDATE derivatives SET body=NULL,state='INVALIDATED' WHERE derivative_id=?", (derivative_id,))
                elif body is not None and self.checkpoint.matches_window(item, bytes(body)):
                    raise RecoveryRequired("unlineaged erased bytes found in derivative")
            db.execute("UPDATE events SET payload=NULL,content_hash=NULL,submission_fingerprint=NULL,deletion_state='ERASED' WHERE event_id=?", (item.event_id,))
            self._verify_all_store_erasure(db, item)
            db.execute("UPDATE tombstones SET state='ERASED' WHERE deletion_id=?", (item.deletion_id,))
            previous = db.execute("SELECT receipt_hash FROM deletion_receipts WHERE deletion_id<>? ORDER BY rowid DESC LIMIT 1", (item.deletion_id,)).fetchone()
            prev_hash = prior_receipt_hash or (previous[0] if previous else "GENESIS")
            receipt = {"deletion_id": item.deletion_id, "event_id": item.event_id,
                       "payload_object_id": item.payload_object_id, "state": "ERASED",
                       "previous_receipt_hash": prev_hash}
            db.execute("INSERT INTO deletion_receipts VALUES(?,?,?,?,?,?) ON CONFLICT(deletion_id) DO UPDATE SET event_id=excluded.event_id,payload_object_id=excluded.payload_object_id,state=excluded.state,previous_receipt_hash=excluded.previous_receipt_hash,receipt_hash=excluded.receipt_hash",
                       (item.deletion_id, item.event_id, item.payload_object_id, "ERASED", prev_hash, _sha(_canonical(receipt))))
            self._bump_generation(db)

    def core_policy_change(self, event_id: str, *, provider: str | None = None,
                           privacy: str | None = None, capability: object) -> None:
        if capability is not self._policy_capability:
            raise CompositionDenied("Core policy capability required")
        if provider is not None:
            self.update_authorization(event_id, provider, capability=capability)
        if privacy is not None:
            self.update_privacy(event_id, privacy, capability=capability)

    def _authorize_independent_source(self, event_id: str, *, capability: object) -> str:
        if capability is not self._policy_capability:
            raise CompositionDenied("Core policy capability required")
        with self._lock, self._connect() as db:
            row = db.execute(
                "SELECT payload_object_id,deletion_state FROM events WHERE event_id=?",
                (event_id,)).fetchone()
            if not row or row[1] != "LIVE":
                raise CompositionDenied("live governed source required")
            authorization_id = self.core_authority.name_independent_source(event_id, row[0])
            db.execute("INSERT INTO independent_source_authorizations VALUES(?,?,?)",
                       (event_id, row[0], authorization_id))
            self._bump_generation(db)
            return authorization_id

    def put_auxiliary_content(self, store_key: str, content: bytes) -> None:
        """Synthetic second persistent content store, included in the scan boundary."""
        with self._lock, self._connect() as db:
            self._require_live()
            db.execute("INSERT INTO auxiliary_content VALUES(?,?) ON CONFLICT(store_key) DO UPDATE SET content=excluded.content",
                       (store_key, sqlite3.Binary(content)))
            self._bump_generation(db)

    def remove_auxiliary_content_during_recovery(self, store_key: str) -> None:
        """Test-only sanitization operation available while restore remains quarantined."""
        with self._lock, self._connect() as db:
            if not self._restoring or self._get_meta("restore_state") != "RESTORING":
                raise RecoveryRequired("sanitization requires quarantined restore")
            db.execute("DELETE FROM auxiliary_content WHERE store_key=?", (store_key,))

    def _payload_from(self, db: sqlite3.Connection, event_id: str) -> bytes:
        row = db.execute("SELECT payload FROM events WHERE event_id=? AND deletion_state='LIVE'", (event_id,)).fetchone()
        if not row or row[0] is None:
            raise RecoveryRequired("cannot recompute derivative from unavailable source")
        return bytes(row[0])

    def replay_or_recover(self) -> None:
        self._require_restore_or_live()
        for item in self.checkpoint.checkpoints():
            # Checkpoint authority always causes identity reconciliation, idempotent
            # fan-out, and all-store content verification. An ERASED receipt is only
            # evidence to validate, never permission to skip revalidation.
            self._apply_checkpoint(item)
        if self.unresolved_count() != 0:
            raise RecoveryRequired("unresolved deletion/recovery state remains")
        self._vacuum()
        if self._restoring:
            with self._connect() as db:
                db.execute("UPDATE meta SET value='LIVE' WHERE key='restore_state'")
            self._restoring = False

    def unresolved_count(self) -> int:
        checkpoint_ids = {item.deletion_id for item in self.checkpoint.checkpoints()}
        with self._connect() as db:
            erasing = db.execute("SELECT COUNT(*) FROM events WHERE deletion_state!='LIVE' AND deletion_state!='ERASED'").fetchone()[0]
            unfinished_tombstones = db.execute("SELECT COUNT(*) FROM tombstones WHERE state!='ERASED'").fetchone()[0]
            unanchored_tombstones = db.execute("SELECT COUNT(*) FROM tombstones").fetchone()[0] - len(checkpoint_ids)
            unanchored_receipts = db.execute("SELECT COUNT(*) FROM deletion_receipts").fetchone()[0] - len(checkpoint_ids)
        return int(erasing + unfinished_tombstones + max(0, unanchored_tombstones) + max(0, unanchored_receipts))

    def _require_restore_or_live(self) -> None:
        if self._restoring and self._get_meta("restore_state") != "RESTORING":
            raise RecoveryRequired("restore state inconsistent")

    def backup_to(self, target: Path) -> None:
        self._require_live()
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as source, sqlite3.connect(target) as backup:
            source.backup(backup)

    @classmethod
    def restore_from(cls, backup: Path, target: Path, checkpoint: KernelCheckpointBoundary,
                     core_authority: CorePolicyAuthority | None = None) -> "KernelStore":
        shutil.copy2(backup, target)
        store = cls(target, checkpoint=checkpoint, core_authority=core_authority,
                    restoring=True)
        store._set_meta("restore_state", "RESTORING")
        store._restoring = True
        return store

    def _vacuum(self) -> None:
        with self._connect() as db:
            db.execute("PRAGMA secure_delete=ON")
            db.execute("VACUUM")

    def serialized_state(self) -> bytes:
        with self._connect() as db:
            return db.serialize()

    def scan_bytes(self, needles: Iterable[bytes]) -> bool:
        with self._connect() as db:
            serialized = db.serialize()
            return any(needle and needle in serialized for needle in needles)

    def verify_chain(self) -> bool:
        with self._connect() as db:
            rows = db.execute("SELECT event_id,payload_object_id,source_id,ingestion_id,source_authority,provenance,sequence,previous_hash,event_hash FROM events ORDER BY sequence").fetchall()
        previous = "GENESIS"
        for expected_seq, row in enumerate(rows, 1):
            event_id, payload_id, source_id, ingestion_id, authority, provenance, seq, prior, event_hash = row
            expected = _sha(_canonical({"event_id": event_id, "payload_object_id": payload_id,
                                        "source_id": source_id, "ingestion_id": ingestion_id,
                                        "authority": authority, "provenance": provenance,
                                        "sequence": seq, "previous_hash": prior}))
            if seq != expected_seq or prior != previous or event_hash != expected:
                raise AssertionError("event chronology/integrity invalid")
            previous = event_hash
        return True

    def erase_state(self, event_id: str) -> str:
        with self._connect() as db:
            row = db.execute("SELECT deletion_state FROM events WHERE event_id=?", (event_id,)).fetchone()
        return row[0] if row else "MISSING"

    def list_events(self) -> list[dict[str, Any]]:
        self._require_live()
        with self._connect() as db:
            rows = db.execute("SELECT e.event_id,e.payload_object_id,e.source_authority,e.provenance,p.provider,p.privacy,e.payload,e.deletion_state,e.content_hash FROM events e JOIN policy_state p USING(event_id) ORDER BY e.sequence").fetchall()
        return [{"event_id": r[0], "payload_object_id": r[1], "authority": r[2],
                 "provenance": r[3], "provider": r[4], "privacy": r[5],
                 "payload": bytes(r[6]) if r[6] is not None else None,
                 "deletion_state": r[7], "content_hash": r[8]} for r in rows]


class HostedAdapterSpy:
    def __init__(self):
        self.calls: list[tuple[bytes, dict[str, Any]]] = []

    def invoke(self, packet: bytes, config: dict[str, Any]) -> None:
        self.calls.append((packet, dict(config)))


class ContextCore:
    """Core-controlled compiler, lease gate, retrieval and adapter dispatch."""

    def __init__(self, store: KernelStore, *, lease_seconds: float = 120.0):
        self.store = store
        self.policy_authority = store.core_authority
        self.adapter = HostedAdapterSpy()
        self._issuer = object()
        self._policy_capability = store._policy_capability
        self._leases: dict[object, dict[str, Any]] = {}
        self._requests: dict[object, dict[str, Any]] = {}
        self._lease_seconds = lease_seconds

    def authorize_hosted(self, event_id: str) -> None:
        """Synthetic Core-owned disclosure grant; source claims cannot call it."""
        self.store.core_policy_change(event_id, provider="HOSTED_ALLOWED",
                                      privacy="STANDARD", capability=self._policy_capability)

    def authorize_independent_source_exemption(self, event_id: str) -> str:
        """Core explicitly names one governed identity for the narrow V-04 exemption."""
        return self.store._authorize_independent_source(
            event_id, capability=self._policy_capability)

    def set_provider_permission(self, event_id: str, provider: str) -> None:
        self.store.core_policy_change(event_id, provider=provider,
                                      capability=self._policy_capability)

    def set_privacy_classification(self, event_id: str, privacy: str) -> None:
        self.store.core_policy_change(event_id, privacy=privacy,
                                      capability=self._policy_capability)

    def compile_packet(self, event_ids: Sequence[str], provider_id: str = "hosted-fixture") -> CompiledPacket:
        with self.store._lock:
            items = self.store.authorized_retrieval(event_ids, provider_id)
            body = _canonical({"schema": "LN0_COMPOSITION_CONTEXT_V1", "provider_id": provider_id, "items": items})
            packet_id = self.store.add_derivative("context_packet", event_ids, body)
            lease = object()
            self._leases[lease] = {"packet_id": packet_id, "digest": _sha(body),
                                   "provider_id": provider_id, "event_ids": tuple(event_ids),
                                   "generation": self.store.generation,
                                   "expires": time.monotonic() + self._lease_seconds,
                                   "consumed": False, "revoked": False}
            return CompiledPacket(packet_id, body, provider_id, lease, self._issuer)

    def _revoke_and_purge(self, lease_state: dict[str, Any]) -> None:
        lease_state["revoked"] = True
        with self.store._lock, self.store._connect() as db:
            db.execute("UPDATE derivatives SET body=NULL,state='REVOKED' WHERE derivative_id=?", (lease_state["packet_id"],))

    def dispatch(self, packet: CompiledPacket, provider_id: str) -> None:
        # Reality + Authority Revalidation Gate and adapter call share one lock in
        # this test-only single-process model. This is not production atomicity.
        with self.store._lock:
            state = self._leases.get(getattr(packet, "lease", None))
            if packet.issuer is not self._issuer or state is None:
                raise CompositionDenied("packet was not issued by Core")
            if provider_id != state["provider_id"] or packet.provider_id != provider_id:
                self._revoke_and_purge(state)
                raise StalePacket("provider binding changed")
            if state["consumed"] or state["revoked"] or time.monotonic() >= state["expires"]:
                self._revoke_and_purge(state)
                raise StalePacket("packet lease consumed, expired, or revoked")
            if state["generation"] != self.store.generation or state["digest"] != _sha(packet.payload):
                self._revoke_and_purge(state)
                raise StalePacket("governed reality changed after compilation")
            current = self.store.authorized_retrieval(state["event_ids"], provider_id)
            expected = _canonical({"schema": "LN0_COMPOSITION_CONTEXT_V1", "provider_id": provider_id, "items": current})
            if expected != packet.payload:
                self._revoke_and_purge(state)
                raise StalePacket("packet sources or authorization no longer match current Core state")
            with self.store._connect() as db:
                row = db.execute("SELECT body,state FROM derivatives WHERE derivative_id=?", (state["packet_id"],)).fetchone()
            if not row or row[0] != packet.payload or row[1] != "LIVE":
                self._revoke_and_purge(state)
                raise StalePacket("packet derivative revoked or purged")
            state["consumed"] = True
            # One-shot send authority is consumed immediately before invocation.
            self.adapter.invoke(packet.payload, {"provider_id": provider_id})

    def issue_context_request(self, provider_id: str, event_ids: Sequence[str]) -> ContextRequest:
        handle = object()
        self._requests[handle] = {"provider_id": provider_id, "event_ids": tuple(event_ids), "consumed": False}
        return ContextRequest(handle, provider_id, tuple(event_ids))

    def handle_context_request(self, request: ContextRequest, provider_id: str | None = None) -> None:
        state = self._requests.get(getattr(request, "handle", None)) if isinstance(request, ContextRequest) else None
        if state is None or state["consumed"]:
            raise CompositionDenied("Core-issued, single-use ContextRequest required")
        target_provider = provider_id or state["provider_id"]
        if target_provider != state["provider_id"] or request.provider_id != state["provider_id"]:
            state["consumed"] = True
            raise CompositionDenied("ContextRequest is provider-bound")
        state["consumed"] = True
        packet = self.compile_packet(state["event_ids"], target_provider)
        self.dispatch(packet, target_provider)


def sqlcipher_seal_snapshot(serialized: bytes, target: Path, *, executable: str | None = None) -> dict[str, Any]:
    """Encrypt/read back a serialized KernelStore snapshot with the V-02 CLI helper.

    This is a separate CLI snapshot proof, not an in-process encrypted KernelStore.
    Keys are ephemeral and never returned or logged.
    """
    from experiments.ln0_sqlcipher_spike_v2 import _require_ok

    exe = executable or shutil.which("sqlcipher")
    if not exe:
        raise RuntimeError("SQLCipher CLI unavailable")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    home = target.parent / "sqlcipher-home"
    home.mkdir(mode=0o700, exist_ok=True)
    key = secrets.token_bytes(32)
    blob_literal = "X'" + serialized.hex() + "'"
    create = _run_sqlcipher(exe, target, key,
        ["PRAGMA journal_mode=WAL;", "CREATE TABLE kernel_snapshot(state BLOB NOT NULL);",
         f"INSERT INTO kernel_snapshot(state) VALUES({blob_literal});",
         "SELECT length(state) FROM kernel_snapshot;"], home)
    lines = _require_ok(create, "encrypted snapshot creation")
    readback = _run_sqlcipher(exe, target, key,
        ["SELECT hex(state) FROM kernel_snapshot;"], home)
    readback_lines = _require_ok(readback, "encrypted snapshot readback")
    if not readback_lines or bytes.fromhex(readback_lines[-1]) != serialized:
        raise RuntimeError("encrypted snapshot readback mismatch")
    wrong_key = _run_sqlcipher(exe, target, secrets.token_bytes(32),
        ["SELECT count(*) FROM kernel_snapshot;"], home)
    if wrong_key.returncode == 0:
        raise RuntimeError("wrong-key snapshot access unexpectedly succeeded")
    no_key = _run_sqlcipher(exe, target, None,
        ["SELECT count(*) FROM kernel_snapshot;"], home)
    if no_key.returncode == 0:
        raise RuntimeError("no-key snapshot access unexpectedly succeeded")
    try:
        with sqlite3.connect(target) as standard:
            standard.execute("SELECT count(*) FROM kernel_snapshot").fetchone()
    except sqlite3.DatabaseError:
        standard_sqlite_rejected = True
    else:
        standard_sqlite_rejected = False
    if not standard_sqlite_rejected:
        raise RuntimeError("standard SQLite unexpectedly read encrypted snapshot")
    # Do not include the ephemeral key in returned evidence.
    return {"create_readback": True, "wrong_key_rejected": True,
            "no_key_rejected": True, "standard_sqlite_rejected": True,
            "serialized_bytes": len(serialized), "encrypted_db_path": str(target),
            "command_output": lines}
