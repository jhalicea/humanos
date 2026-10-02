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
MAX_CONTEXT_EVENTS = 128
MAX_MEMORY_SCAN_EVENTS = 20000


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
    """Raw rebuildable state; privacy is enforced separately on every read surface."""
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


def _semantic_rows(book, owner, event_ids=None):
    """Read semantic events with current transcript privacy and exact provenance."""
    ensure_memory_schema(book)
    params = [owner]
    where = "e.owner=?"
    if event_ids is not None:
        if not event_ids:
            return []
        marks = ",".join("?" for _ in event_ids)
        where += f" AND e.event_id IN ({marks})"
        params.extend(event_ids)
    rows = list(
        book.db.execute(
            f"""
            SELECT e.*,i.page,i.hcid,s.ordinal AS source_ordinal,
                   s.created AS source_created,s.text AS source_text,
                   COALESCE(p.state,'VISIBLE') AS privacy_state
            FROM memory_events e
            JOIN transactions t ON t.tx=e.source_tx
            JOIN identities i ON i.hcid=t.hcid
            JOIN transcript s ON s.seq=e.source_seq
            LEFT JOIN privacy_state p
              ON p.tx=s.tx AND p.ordinal=s.ordinal
            WHERE {where}
            ORDER BY e.seq
            LIMIT ?
            """,
            (*params, MAX_MEMORY_SCAN_EVENTS + 1),
        )
    )
    if len(rows) > MAX_MEMORY_SCAN_EVENTS:
        raise RuntimeError("Semantic memory scan exceeds the bounded event limit")
    return [dict(row) for row in rows]


def _visible_groups(book, owner):
    """Return privacy-safe surviving events grouped by subject.

    A correction depends on the event it supersedes because its subject may have been
    inferred from that earlier statement. Therefore a hidden ancestor makes the derived
    correction ineligible too. Hiding only the newer correction lets the prior visible
    state re-emerge; unhiding restores the newer state.
    """
    rows = _semantic_rows(book, owner)
    by_id = {row["event_id"]: row for row in rows}
    memo = {}
    visiting = set()

    def eligible(event_id):
        if event_id in memo:
            return memo[event_id]
        if event_id in visiting:
            raise RuntimeError("Semantic memory supersession cycle detected")
        row = by_id.get(event_id)
        if row is None:
            raise RuntimeError("Semantic memory supersession ancestry is missing")
        visiting.add(event_id)
        allowed = row["privacy_state"] != "HIDDEN"
        parent = row.get("supersedes")
        if allowed and parent:
            if parent not in by_id:
                raise RuntimeError("Semantic memory supersession ancestry is missing")
            allowed = eligible(parent)
        visiting.remove(event_id)
        memo[event_id] = allowed
        return allowed

    eligible_rows = [row for row in rows if eligible(row["event_id"])]
    superseded = {
        row["supersedes"] for row in eligible_rows if row.get("supersedes")
    }
    survivors = [row for row in eligible_rows if row["event_id"] not in superseded]
    groups = {}
    for row in survivors:
        groups.setdefault(row["subject"], []).append(row)
    return groups, by_id


def _visible_state_rows(book, owner, limit=MAX_CONTEXT_PREFERENCES):
    groups, _ = _visible_groups(book, owner)
    ordered = sorted(
        groups.items(),
        key=lambda item: (max(row["seq"] for row in item[1]), item[0]),
        reverse=True,
    )[: int(limit)]
    result = []
    for subject, rows in ordered:
        if len(rows) == 1:
            row = rows[0]
            result.append(
                {
                    "owner": owner,
                    "subject": subject,
                    "status": "ACTIVE",
                    "event_id": row["event_id"],
                    "value": row["value"],
                    "updated": row["created"],
                    "source_tx": row["source_tx"],
                    "source_seq": row["source_seq"],
                    "page": row["page"],
                    "hcid": row["hcid"],
                    "source_created": row["source_created"],
                    "source_text": row["source_text"],
                }
            )
        else:
            result.append(
                {
                    "owner": owner,
                    "subject": subject,
                    "status": "CONFLICTED",
                    "event_id": None,
                    "value": None,
                    "updated": max(row["created"] for row in rows),
                    "source_tx": None,
                    "source_seq": None,
                    "page": None,
                    "hcid": None,
                    "source_created": None,
                    "source_text": None,
                }
            )
    return result


def _resolve_candidate(book, source, candidate):
    if candidate["mode"] == "DECLARE":
        return candidate["subject"], candidate["value"], None
    active = [
        row for row in _visible_state_rows(book, source["owner"])
        if row["status"] == "ACTIVE"
    ]
    if len(active) != 1:
        return None
    return active[0]["subject"], candidate["value"], active[0]["event_id"]


def capture_memory_from_turn(book, tx):
    """Promote semantics only after the exact human turn is already persisted."""
    ensure_memory_schema(book)
    source = _source_for_tx(book, tx)
    candidate = _extract_preference(source["text"])
    if candidate is None:
        return {"status": "NO_MEMORY_EVENT", "tx": tx}

    # Stable identity is content-free. Replay is checked before current-state
    # resolution so later changes cannot alter reprocessing of observed evidence.
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
    """Privacy-aware current preference surface used by humans and model context."""
    ensure_memory_schema(book)
    return _visible_state_rows(book, owner, limit=limit)


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


def _ancestor_ids(event_id, by_id):
    ancestors = []
    seen = set()
    current = by_id[event_id].get("supersedes")
    while current:
        if current in seen:
            raise RuntimeError("Semantic memory supersession cycle detected")
        seen.add(current)
        row = by_id.get(current)
        if row is None:
            raise RuntimeError("Semantic memory supersession ancestry is missing")
        ancestors.append(current)
        current = row.get("supersedes")
    return ancestors


def memory_binding(book, owner, limit=MAX_CONTEXT_PREFERENCES):
    """Bind privacy-safe current memory using only immutable content-free event IDs."""
    ensure_memory_schema(book)
    groups, by_id = _visible_groups(book, owner)
    ordered = sorted(
        groups.items(),
        key=lambda item: (max(row["seq"] for row in item[1]), item[0]),
        reverse=True,
    )[: int(limit)]
    direct = []
    dependencies = []
    for _, rows in ordered:
        for row in rows:
            direct.append(row["event_id"])
            dependencies.extend(_ancestor_ids(row["event_id"], by_id))
    dependency_set = set(dependencies) - set(direct)
    all_ids = set(direct) | dependency_set
    if len(all_ids) > MAX_CONTEXT_EVENTS:
        raise RuntimeError("Current semantic memory exceeds the bounded context-event limit")
    sequence = {event_id: by_id[event_id]["seq"] for event_id in all_ids}
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "READY",
        "event_ids": sorted(set(direct), key=lambda event_id: sequence[event_id]),
        "dependency_event_ids": sorted(dependency_set, key=lambda event_id: sequence[event_id]),
    }


def _validate_id_list(value, label):
    if not isinstance(value, list) or len(value) > MAX_CONTEXT_EVENTS or len(value) != len(set(value)):
        raise RuntimeError(f"Invalid memory context {label} binding")
    if any(not isinstance(item, str) or not item.startswith("HOS-MEM-") for item in value):
        raise RuntimeError(f"Invalid memory context {label} identity")
    return value


def memory_context_from_binding(book, owner, binding):
    """Reconstruct exactly the immutable, privacy-authorized snapshot bound to a task."""
    ensure_memory_schema(book)
    if not isinstance(binding, dict) or binding.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeError("Invalid memory context binding")
    if binding.get("status") == "UNAVAILABLE":
        return {
            "schema_version": SCHEMA_VERSION,
            "source": "LOCAL_DERIVED_LIFE_NOTEBOOK_STATE",
            "status": "UNAVAILABLE",
            "error_type": binding.get("error_type", "MemoryUnavailable"),
            "preferences": [],
            "conflicts": [],
        }
    if binding.get("status") != "READY":
        raise RuntimeError("Unknown memory context binding status")
    ids = _validate_id_list(binding.get("event_ids"), "event")
    dependencies = _validate_id_list(binding.get("dependency_event_ids", []), "dependency")
    if set(ids) & set(dependencies):
        raise RuntimeError("Memory context direct and dependency identities overlap")
    all_ids = ids + dependencies
    if len(all_ids) > MAX_CONTEXT_EVENTS:
        raise RuntimeError("Bound semantic memory exceeds the context-event limit")
    if not all_ids:
        return {
            "schema_version": SCHEMA_VERSION,
            "source": "LOCAL_DERIVED_LIFE_NOTEBOOK_STATE",
            "preferences": [],
            "conflicts": [],
        }

    rows = _semantic_rows(book, owner, event_ids=all_ids)
    if len(rows) != len(all_ids) or {row["event_id"] for row in rows} != set(all_ids):
        raise RuntimeError("Bound semantic memory evidence is missing or belongs to another owner")
    if any(row["privacy_state"] == "HIDDEN" for row in rows):
        raise PermissionError("Bound semantic memory source is hidden by the human")
    by_id = {row["event_id"]: row for row in rows}
    dependency_set = set(dependencies)
    direct_set = set(ids)
    for event_id in ids:
        row = by_id[event_id]
        parent = row.get("supersedes")
        seen = set()
        while parent:
            if parent in seen:
                raise RuntimeError("Semantic memory supersession cycle detected")
            seen.add(parent)
            if parent in direct_set:
                raise RuntimeError("Bound semantic memory includes a superseded event as current")
            if parent not in dependency_set or parent not in by_id:
                raise RuntimeError("Bound semantic memory ancestry is incomplete")
            parent = by_id[parent].get("supersedes")

    groups = {}
    for event_id in ids:
        row = by_id[event_id]
        groups.setdefault(row["subject"], []).append(row)
    preferences, conflicts = [], []
    for subject, rows_for_subject in groups.items():
        if len(rows_for_subject) == 1:
            row = rows_for_subject[0]
            preferences.append(
                {
                    "subject": subject,
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
            conflicts.append({"subject": subject, "status": "CONFLICTED"})
    preferences.sort(key=lambda item: item["subject"])
    conflicts.sort(key=lambda item: item["subject"])
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "LOCAL_DERIVED_LIFE_NOTEBOOK_STATE",
        "preferences": preferences,
        "conflicts": conflicts,
    }


def memory_context(book, owner, limit=MAX_CONTEXT_PREFERENCES):
    return memory_context_from_binding(book, owner, memory_binding(book, owner, limit=limit))


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
