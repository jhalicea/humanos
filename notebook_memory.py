"""Small deterministic semantic-memory layer over authoritative Life Notebook evidence.

The transcript is canonical. Semantic events are append-only history; current state is
a rebuildable projection. V1 intentionally promotes only explicit user preferences so
HumanOS can prove the complete usable memory loop before expanding the taxonomy.
"""

import hashlib
import json
import re
from datetime import datetime, timezone

SCHEMA_VERSION = 1
GENESIS = "GENESIS"
MAX_CONTEXT_PREFERENCES = 32


def _now():
    return datetime.now(timezone.utc).isoformat()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _event_id(idempotency_key):
    return "HOS-MEM-" + hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:24]


def ensure_memory_schema(book):
    book.db.executescript(
        """
        CREATE TABLE IF NOT EXISTS memory_meta(
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_events(
          seq INTEGER PRIMARY KEY AUTOINCREMENT,
          event_id TEXT UNIQUE NOT NULL,
          schema_version INTEGER NOT NULL,
          owner TEXT NOT NULL,
          event_type TEXT NOT NULL,
          subject TEXT NOT NULL,
          value TEXT NOT NULL,
          source_tx TEXT NOT NULL REFERENCES transactions(tx),
          source_seq INTEGER NOT NULL REFERENCES transcript(seq),
          source_role TEXT NOT NULL,
          created TEXT NOT NULL,
          supersedes TEXT,
          idempotency_key TEXT UNIQUE NOT NULL,
          previous_hash TEXT NOT NULL,
          event_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS memory_state(
          owner TEXT NOT NULL,
          subject TEXT NOT NULL,
          status TEXT NOT NULL CHECK(status IN ('ACTIVE','CONFLICTED')),
          event_id TEXT,
          value TEXT,
          updated TEXT NOT NULL,
          PRIMARY KEY(owner,subject)
        );
        CREATE TRIGGER IF NOT EXISTS memory_events_no_update
          BEFORE UPDATE ON memory_events
          BEGIN SELECT RAISE(ABORT, 'append-only memory event'); END;
        CREATE TRIGGER IF NOT EXISTS memory_events_no_delete
          BEFORE DELETE ON memory_events
          BEGIN SELECT RAISE(ABORT, 'append-only memory event'); END;
        """
    )
    row = book.db.execute("SELECT value FROM memory_meta WHERE key='schema_version'").fetchone()
    if row is None:
        with book.db:
            book.db.execute(
                "INSERT INTO memory_meta(key,value) VALUES('schema_version',?)",
                (str(SCHEMA_VERSION),),
            )
    elif row[0] != str(SCHEMA_VERSION):
        raise RuntimeError("Unsupported HumanOS memory schema version: " + str(row[0]))


def _source_for_tx(book, tx):
    row = book.db.execute(
        """
        SELECT t.tx,t.hcid,i.owner,i.page,s.seq,s.ordinal,s.role,s.text,s.created
        FROM transactions t
        JOIN identities i ON i.hcid=t.hcid
        JOIN transcript s ON s.tx=t.tx
        WHERE t.tx=? AND s.role='HUMAN'
        ORDER BY s.ordinal,s.seq
        LIMIT 1
        """,
        (tx,),
    ).fetchone()
    if row is None:
        raise ValueError("Memory extraction requires a persisted HUMAN transcript row")
    return row


def _clean_subject(value):
    return " ".join(value.strip().strip(" .!?,:;\"'").casefold().split())


def _clean_value(value):
    return " ".join(value.strip().strip(" .!?,:;\"'").split())


def _extract_preference(text):
    compact = " ".join(text.strip().split())
    declared = re.match(r"(?i)^i\s+prefer\s+([\w-]+)\s+(.+?)[.!?]*$", compact)
    if declared:
        value = _clean_value(declared.group(1))
        subject = _clean_subject(declared.group(2))
        if value and subject:
            return {"mode": "DECLARE", "subject": subject, "value": value}
    corrected = re.match(
        r"(?i)^(?:actually|instead|correction|i\s+changed\s+my\s+mind)[,\s:-]*"
        r"(?:please\s+)?(?:make|use|set)\s+(?:it|them|that|those)?\s*(?:to\s+)?(.+?)[.!?]*$",
        compact,
    )
    if corrected:
        value = _clean_value(corrected.group(1))
        if value:
            return {"mode": "CORRECT_RECENT", "value": value}
    return None


def _active_rows(book, owner):
    return list(
        book.db.execute(
            """SELECT owner,subject,status,event_id,value,updated
               FROM memory_state WHERE owner=? ORDER BY updated DESC,subject""",
            (owner,),
        )
    )


def _resolve_candidate(book, source, candidate):
    if candidate["mode"] == "DECLARE":
        return candidate["subject"], candidate["value"], None
    active = [row for row in _active_rows(book, source["owner"]) if row["status"] == "ACTIVE"]
    if len(active) != 1:
        return None
    return active[0]["subject"], candidate["value"], active[0]["event_id"]


def _event_payload(row):
    return {
        "event_id": row["event_id"],
        "schema_version": SCHEMA_VERSION,
        "owner": row["owner"],
        "event_type": "PREFERENCE",
        "subject": row["subject"],
        "value": row["value"],
        "source_tx": row["source_tx"],
        "source_seq": int(row["source_seq"]),
        "source_role": row["source_role"],
        "created": row["created"],
        "supersedes": row["supersedes"],
        "idempotency_key": row["idempotency_key"],
        "previous_hash": row["previous_hash"],
    }


def _derive_subject_state(book, owner, subject):
    rows = list(
        book.db.execute(
            """
            SELECT e.* FROM memory_events e
            WHERE e.owner=? AND e.subject=?
              AND NOT EXISTS (
                SELECT 1 FROM memory_events newer WHERE newer.supersedes=e.event_id
              )
            ORDER BY e.seq
            """,
            (owner, subject),
        )
    )
    if not rows:
        return None
    if len(rows) == 1:
        row = rows[0]
        return {
            "owner": owner,
            "subject": subject,
            "status": "ACTIVE",
            "event_id": row["event_id"],
            "value": row["value"],
            "updated": row["created"],
        }
    return {
        "owner": owner,
        "subject": subject,
        "status": "CONFLICTED",
        "event_id": None,
        "value": None,
        "updated": max(row["created"] for row in rows),
    }


def _write_derived_state(book, owner, subject):
    state = _derive_subject_state(book, owner, subject)
    book.db.execute("DELETE FROM memory_state WHERE owner=? AND subject=?", (owner, subject))
    if state:
        book.db.execute(
            """INSERT INTO memory_state(owner,subject,status,event_id,value,updated)
               VALUES(?,?,?,?,?,?)""",
            (
                state["owner"], state["subject"], state["status"],
                state["event_id"], state["value"], state["updated"],
            ),
        )
    return state


def capture_memory_from_turn(book, tx):
    """Promote semantics only after the exact human turn is already persisted."""
    ensure_memory_schema(book)
    source = _source_for_tx(book, tx)
    candidate = _extract_preference(source["text"])
    if candidate is None:
        return {"status": "NO_MEMORY_EVENT", "tx": tx}

    # Stable identity is content-free. Crucially, replay is checked BEFORE current
    # state resolution so later changes cannot alter the result of reprocessing an
    # already-observed source message.
    idempotency_key = f"PREFERENCE:{tx}:{source['seq']}"
    event_id = _event_id(idempotency_key)
    existing = book.db.execute(
        "SELECT event_id FROM memory_events WHERE idempotency_key=?", (idempotency_key,)
    ).fetchone()
    if existing is not None:
        return {"status": "ALREADY_CAPTURED", "event_id": existing["event_id"], "tx": tx}

    resolved = _resolve_candidate(book, source, candidate)
    if resolved is None:
        return {"status": "AMBIGUOUS_MEMORY_CORRECTION", "tx": tx}
    subject, value, supersedes = resolved

    previous = book.db.execute("SELECT event_hash FROM memory_events ORDER BY seq DESC LIMIT 1").fetchone()
    row = {
        "event_id": event_id,
        "owner": source["owner"],
        "subject": subject,
        "value": value,
        "source_tx": tx,
        "source_seq": source["seq"],
        "source_role": source["role"],
        "created": _now(),
        "supersedes": supersedes,
        "idempotency_key": idempotency_key,
        "previous_hash": previous["event_hash"] if previous else GENESIS,
    }
    event_hash = book.content_digest(row["previous_hash"] + "\n" + _canonical(_event_payload(row)))

    with book._immediate():
        book.db.execute(
            """
            INSERT INTO memory_events(
              event_id,schema_version,owner,event_type,subject,value,source_tx,source_seq,
              source_role,created,supersedes,idempotency_key,previous_hash,event_hash
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id, SCHEMA_VERSION, row["owner"], "PREFERENCE", subject, value,
                tx, row["source_seq"], row["source_role"], row["created"], supersedes,
                idempotency_key, row["previous_hash"], event_hash,
            ),
        )
        state = _write_derived_state(book, source["owner"], subject)
    return {
        "status": "CAPTURED",
        "event_id": event_id,
        "supersedes": supersedes,
        "state": state,
        "tx": tx,
    }


def rebuild_memory_state(book):
    ensure_memory_schema(book)
    pairs = list(book.db.execute("SELECT DISTINCT owner,subject FROM memory_events ORDER BY owner,subject"))
    with book._immediate():
        book.db.execute("DELETE FROM memory_state")
        for pair in pairs:
            _write_derived_state(book, pair["owner"], pair["subject"])
    return {"status": "REBUILT", "records": len(pairs)}


def active_preferences(book, owner, limit=MAX_CONTEXT_PREFERENCES):
    ensure_memory_schema(book)
    rows = list(
        book.db.execute(
            """
            SELECT ms.owner,ms.subject,ms.status,ms.event_id,ms.value,ms.updated,
                   me.source_tx,me.source_seq,i.page,i.hcid,
                   s.created AS source_created,s.text AS source_text
            FROM memory_state ms
            LEFT JOIN memory_events me ON me.event_id=ms.event_id
            LEFT JOIN transactions t ON t.tx=me.source_tx
            LEFT JOIN identities i ON i.hcid=t.hcid
            LEFT JOIN transcript s ON s.seq=me.source_seq
            WHERE ms.owner=?
            ORDER BY ms.updated DESC,ms.subject
            LIMIT ?
            """,
            (owner, int(limit)),
        )
    )
    return [dict(row) for row in rows]


def get_preference(book, owner, subject):
    normalized = _clean_subject(subject)
    rows = [row for row in active_preferences(book, owner) if row["subject"] == normalized]
    if not rows:
        return {"status": "NOT_FOUND", "subject": normalized}
    row = rows[0]
    if row["status"] != "ACTIVE":
        return {"status": row["status"], "subject": normalized}
    return {
        "status": "ACTIVE",
        "subject": row["subject"],
        "value": row["value"],
        "event_id": row["event_id"],
        "provenance": {
            "page": row["page"],
            "hcid": row["hcid"],
            "tx": row["source_tx"],
            "seq": row["source_seq"],
            "created": row["source_created"],
            "message": row["source_text"],
        },
    }


def memory_context(book, owner, limit=MAX_CONTEXT_PREFERENCES):
    preferences, conflicts = [], []
    for row in active_preferences(book, owner, limit=limit):
        if row["status"] == "ACTIVE":
            preferences.append(
                {
                    "subject": row["subject"],
                    "value": row["value"],
                    "event_id": row["event_id"],
                    "provenance": {
                        "page": row["page"],
                        "tx": row["source_tx"],
                        "seq": row["source_seq"],
                        "created": row["source_created"],
                    },
                }
            )
        else:
            conflicts.append({"subject": row["subject"], "status": row["status"]})
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "LOCAL_DERIVED_LIFE_NOTEBOOK_STATE",
        "preferences": preferences,
        "conflicts": conflicts,
    }


def verify_memory(book):
    ensure_memory_schema(book)
    previous_hash = GENESIS
    for row in book.db.execute("SELECT * FROM memory_events ORDER BY seq"):
        if row["previous_hash"] != previous_hash:
            raise RuntimeError("Memory event chain previous hash mismatch")
        source = book.db.execute(
            "SELECT tx,seq,role FROM transcript WHERE seq=?", (row["source_seq"],)
        ).fetchone()
        if source is None or source["tx"] != row["source_tx"] or source["role"] != row["source_role"]:
            raise RuntimeError("Memory event provenance mismatch")
        expected = book.content_digest(previous_hash + "\n" + _canonical(_event_payload(row)))
        if row["event_hash"] != expected:
            raise RuntimeError("Memory event hash mismatch")
        previous_hash = row["event_hash"]

    expected = {}
    for pair in book.db.execute("SELECT DISTINCT owner,subject FROM memory_events"):
        state = _derive_subject_state(book, pair["owner"], pair["subject"])
        if state:
            expected[(pair["owner"], pair["subject"])] = state
    actual = {
        (row["owner"], row["subject"]): dict(row)
        for row in book.db.execute(
            "SELECT owner,subject,status,event_id,value,updated FROM memory_state"
        )
    }
    if expected != actual:
        raise RuntimeError("Derived memory state does not match append-only event history")
    return {
        "status": "VERIFIED",
        "events": book.db.execute("SELECT COUNT(*) FROM memory_events").fetchone()[0],
        "state_records": len(actual),
    }
