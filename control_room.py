"""HumanOS Control Room persistence and policy boundary.

Transport-neutral deterministic state machine behind the HumanOS MCP bridge.
It does not call a model, execute work, or grant authority.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

DATA_CLASSES = frozenset({"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"})
SIZE_CLASSES = frozenset({"XS", "S", "M", "L"})
RISK_CLASSES = frozenset({"R0", "R1", "R2", "R3", "INCIDENT", "EXPERIMENT"})
WORK_ID_RE = re.compile(r"^HOS-[A-Z0-9][A-Z0-9-]{2,127}$")
REQUEST_ID_RE = re.compile(r"^HOS-REQ-[A-F0-9]{16}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_text(value: str) -> str:
    return _digest_bytes(value.encode("utf-8"))


def _encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _require_text(name: str, value: Any, *, limit: int = 100_000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be non-empty text")
    if len(value) > limit:
        raise ValueError(f"{name} exceeds {limit} characters")
    return value


class ControlRoomStore:
    """Append-oriented local store for HumanOS <-> external-model coordination."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        with self.db:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.executescript(
                """
                CREATE TABLE IF NOT EXISTS control_requests(
                    request_id TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    text TEXT NOT NULL,
                    text_digest TEXT NOT NULL,
                    data_class TEXT NOT NULL,
                    external_approved INTEGER NOT NULL CHECK(external_approved IN (0,1)),
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS control_responses(
                    request_id TEXT PRIMARY KEY REFERENCES control_requests(request_id),
                    request_digest TEXT NOT NULL,
                    responder TEXT NOT NULL,
                    text TEXT NOT NULL,
                    text_digest TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS control_work_orders(
                    work_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    baseline_commit TEXT NOT NULL,
                    initial_state TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS control_approvals(
                    work_id TEXT PRIMARY KEY REFERENCES control_work_orders(work_id),
                    payload_digest TEXT NOT NULL,
                    baseline_commit TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    approval_ref TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS control_requests_no_update
                  BEFORE UPDATE ON control_requests
                  BEGIN SELECT RAISE(ABORT, 'immutable control request'); END;
                CREATE TRIGGER IF NOT EXISTS control_requests_no_delete
                  BEFORE DELETE ON control_requests
                  BEGIN SELECT RAISE(ABORT, 'immutable control request'); END;
                CREATE TRIGGER IF NOT EXISTS control_responses_no_update
                  BEFORE UPDATE ON control_responses
                  BEGIN SELECT RAISE(ABORT, 'immutable control response'); END;
                CREATE TRIGGER IF NOT EXISTS control_responses_no_delete
                  BEFORE DELETE ON control_responses
                  BEGIN SELECT RAISE(ABORT, 'immutable control response'); END;
                CREATE TRIGGER IF NOT EXISTS control_work_orders_no_update
                  BEFORE UPDATE ON control_work_orders
                  BEGIN SELECT RAISE(ABORT, 'immutable control work order'); END;
                CREATE TRIGGER IF NOT EXISTS control_work_orders_no_delete
                  BEFORE DELETE ON control_work_orders
                  BEGIN SELECT RAISE(ABORT, 'immutable control work order'); END;
                CREATE TRIGGER IF NOT EXISTS control_approvals_no_update
                  BEFORE UPDATE ON control_approvals
                  BEGIN SELECT RAISE(ABORT, 'immutable control approval'); END;
                CREATE TRIGGER IF NOT EXISTS control_approvals_no_delete
                  BEFORE DELETE ON control_approvals
                  BEGIN SELECT RAISE(ABORT, 'immutable control approval'); END;
                """
            )

    def close(self) -> None:
        self.db.close()

    def queue_local_request(self, text: str, *, data_class: str = "INTERNAL", external_approved: bool = False, owner: str = "jon") -> dict[str, Any]:
        text = _require_text("text", text)
        owner = _require_text("owner", owner, limit=128)
        data_class = str(data_class).upper()
        if data_class not in DATA_CLASSES:
            raise ValueError("unsupported data_class")
        if data_class == "RESTRICTED" and external_approved:
            raise PermissionError("RESTRICTED requests cannot be approved for external MCP egress")
        stamp = _now()
        request_id = "HOS-REQ-" + secrets.token_hex(8).upper()
        text_digest = _digest_text(text)
        with self.db:
            self.db.execute(
                "INSERT INTO control_requests VALUES(?,?,?,?,?,?,?)",
                (request_id, owner, text, text_digest, data_class, 1 if external_approved else 0, stamp),
            )
        return {"request_id": request_id, "request_digest": text_digest, "data_class": data_class, "external_approved": bool(external_approved), "created_at": stamp}

    def next_external_request(self) -> dict[str, Any] | None:
        row = self.db.execute(
            """SELECT r.* FROM control_requests r
            LEFT JOIN control_responses s ON s.request_id=r.request_id
            WHERE r.external_approved=1 AND r.data_class!='RESTRICTED'
              AND s.request_id IS NULL
            ORDER BY r.created_at, r.request_id LIMIT 1"""
        ).fetchone()
        if not row:
            return None
        if _digest_text(row["text"]) != row["text_digest"]:
            raise RuntimeError("control request failed integrity validation")
        return {"request_id": row["request_id"], "request_digest": row["text_digest"], "data_class": row["data_class"], "text": row["text"], "created_at": row["created_at"]}

    def append_external_response(self, request_id: str, request_digest: str, text: str, *, responder: str = "chatgpt") -> dict[str, Any]:
        if not REQUEST_ID_RE.fullmatch(str(request_id)):
            raise ValueError("invalid request_id")
        text = _require_text("text", text)
        responder = _require_text("responder", responder, limit=128)
        row = self.db.execute("SELECT * FROM control_requests WHERE request_id=?", (request_id,)).fetchone()
        if not row:
            raise KeyError("unknown request_id")
        if row["text_digest"] != request_digest or _digest_text(row["text"]) != row["text_digest"]:
            raise PermissionError("request digest mismatch")
        if not row["external_approved"] or row["data_class"] == "RESTRICTED":
            raise PermissionError("request is not authorized for external response")
        text_digest = _digest_text(text)
        existing = self.db.execute("SELECT * FROM control_responses WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            if existing["request_digest"] == request_digest and existing["text_digest"] == text_digest and existing["text"] == text:
                return {"request_id": request_id, "response_digest": text_digest, "created_at": existing["created_at"], "state": "IDEMPOTENT"}
            raise RuntimeError("conflicting response already exists")
        stamp = _now()
        with self.db:
            self.db.execute("INSERT INTO control_responses VALUES(?,?,?,?,?,?)", (request_id, request_digest, responder, text, text_digest, stamp))
        return {"request_id": request_id, "response_digest": text_digest, "created_at": stamp, "state": "RECORDED"}

    def local_response(self, request_id: str) -> dict[str, Any] | None:
        row = self.db.execute("SELECT * FROM control_responses WHERE request_id=?", (request_id,)).fetchone()
        if not row:
            return None
        if _digest_text(row["text"]) != row["text_digest"]:
            raise RuntimeError("control response failed integrity validation")
        return dict(row)

    def _validate_work_order(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, Mapping):
            raise ValueError("work_order must be an object")
        order = dict(raw)
        required = {"work_id", "approval", "baseline_commit", "objective", "scope", "non_goals", "allowed_actions", "forbidden_actions", "acceptance_tests", "rollback", "done_condition", "data_class", "size_class", "risk_class"}
        missing = sorted(required - set(order))
        if missing:
            raise ValueError("work_order missing fields: " + ", ".join(missing))
        if set(order) - required - {"provenance_refs", "budget"}:
            raise ValueError("work_order contains unsupported fields")
        work_id = _require_text("work_id", order["work_id"], limit=128).upper()
        if not WORK_ID_RE.fullmatch(work_id):
            raise ValueError("invalid work_id")
        order["work_id"] = work_id
        baseline = _require_text("baseline_commit", order["baseline_commit"], limit=128)
        if not re.fullmatch(r"[0-9a-fA-F]{7,64}", baseline):
            raise ValueError("baseline_commit must be a git-style hex commit id")
        order["baseline_commit"] = baseline.lower()
        order["objective"] = _require_text("objective", order["objective"])
        order["rollback"] = _require_text("rollback", order["rollback"])
        order["done_condition"] = _require_text("done_condition", order["done_condition"])
        for field in ("scope", "non_goals", "allowed_actions", "forbidden_actions", "acceptance_tests"):
            value = order[field]
            if not isinstance(value, list) or any(not isinstance(x, str) or not x.strip() for x in value):
                raise ValueError(f"{field} must be a list of non-empty strings")
        order["data_class"] = str(order["data_class"]).upper()
        order["size_class"] = str(order["size_class"]).upper()
        order["risk_class"] = str(order["risk_class"]).upper()
        if order["data_class"] not in DATA_CLASSES:
            raise ValueError("unsupported data_class")
        if order["size_class"] not in SIZE_CLASSES:
            raise ValueError("unsupported size_class")
        if order["risk_class"] not in RISK_CLASSES:
            raise ValueError("unsupported risk_class")
        approval = order["approval"]
        if not isinstance(approval, Mapping) or set(approval) != {"approved_by", "decision", "approval_ref"}:
            raise ValueError("approval must contain approved_by, decision, approval_ref")
        if str(approval["approved_by"]).casefold() != "jon":
            raise PermissionError("only Jon approval is accepted")
        if approval["decision"] != "APPROVE":
            raise PermissionError("work order is not approved")
        _require_text("approval_ref", approval["approval_ref"], limit=512)
        if order["data_class"] == "RESTRICTED" and any(action.casefold().startswith(("external", "network", "friend", "hosted")) for action in order["allowed_actions"]):
            raise PermissionError("RESTRICTED work cannot authorize external egress")
        return order

    def submit_work_order(self, work_order: Mapping[str, Any], *, current_baseline: str | None) -> dict[str, Any]:
        order = self._validate_work_order(work_order)
        payload = _encode(order)
        digest = _digest_text(payload)
        baseline = order["baseline_commit"]
        state = "PENDING_LOCAL_APPROVAL"
        existing = self.db.execute("SELECT * FROM control_work_orders WHERE work_id=?", (order["work_id"],)).fetchone()
        if existing:
            if existing["payload_digest"] == digest and existing["payload"] == payload:
                return {"work_id": order["work_id"], "payload_digest": digest, "state": self.work_status(order["work_id"], current_baseline=current_baseline)["state"], "record_state": "IDEMPOTENT"}
            raise RuntimeError("conflicting work order already exists")
        stamp = _now()
        with self.db:
            self.db.execute("INSERT INTO control_work_orders VALUES(?,?,?,?,?,?)", (order["work_id"], payload, digest, baseline, state, stamp))
        return {"work_id": order["work_id"], "payload_digest": digest, "state": state, "record_state": "RECORDED"}

    def approve_work_order(
        self,
        work_id: str,
        payload_digest: str,
        *,
        approval_ref: str,
        current_baseline: str | None,
    ) -> dict[str, Any]:
        work_id = str(work_id).upper()
        approval_ref = _require_text("approval_ref", approval_ref, limit=512)
        row = self.db.execute(
            "SELECT * FROM control_work_orders WHERE work_id=?", (work_id,)
        ).fetchone()
        if not row:
            raise KeyError("unknown work_id")
        if _digest_text(row["payload"]) != row["payload_digest"]:
            raise RuntimeError("work order failed integrity validation")
        if payload_digest != row["payload_digest"]:
            raise PermissionError("work-order payload digest mismatch")
        if current_baseline is None:
            raise PermissionError("local baseline is unknown; approval cannot be bound")
        if row["baseline_commit"] != str(current_baseline).lower():
            raise PermissionError("work order is stale and cannot be approved")
        existing = self.db.execute(
            "SELECT * FROM control_approvals WHERE work_id=?", (work_id,)
        ).fetchone()
        if existing:
            if (existing["payload_digest"] == payload_digest and
                    existing["baseline_commit"] == row["baseline_commit"] and
                    existing["approval_ref"] == approval_ref):
                return {"work_id": work_id, "state": "READY", "record_state": "IDEMPOTENT",
                        "approved_at": existing["created_at"]}
            raise RuntimeError("conflicting local approval already exists")
        stamp = _now()
        with self.db:
            self.db.execute(
                "INSERT INTO control_approvals VALUES(?,?,?,?,?,?)",
                (work_id, payload_digest, row["baseline_commit"], "jon", approval_ref, stamp),
            )
        return {"work_id": work_id, "state": "READY", "record_state": "RECORDED",
                "approved_at": stamp}

    def work_status(self, work_id: str, *, current_baseline: str | None) -> dict[str, Any]:
        row = self.db.execute("SELECT * FROM control_work_orders WHERE work_id=?", (str(work_id).upper(),)).fetchone()
        if not row:
            raise KeyError("unknown work_id")
        if _digest_text(row["payload"]) != row["payload_digest"]:
            raise RuntimeError("work order failed integrity validation")
        approval = self.db.execute(
            "SELECT * FROM control_approvals WHERE work_id=?", (row["work_id"],)
        ).fetchone()
        if not approval:
            state = "PENDING_LOCAL_APPROVAL"
        elif approval["payload_digest"] != row["payload_digest"] or approval["baseline_commit"] != row["baseline_commit"]:
            raise RuntimeError("local approval binding failed integrity validation")
        elif current_baseline is None:
            state = "BASELINE_UNKNOWN"
        elif row["baseline_commit"] != str(current_baseline).lower():
            state = "STALE"
        else:
            state = "READY"
        return {"work_id": row["work_id"], "payload_digest": row["payload_digest"], "baseline_commit": row["baseline_commit"], "state": state, "created_at": row["created_at"], "locally_approved": bool(approval)}

    def pending_work_orders(self, *, current_baseline: str | None) -> list[dict[str, Any]]:
        rows = self.db.execute("SELECT work_id FROM control_work_orders ORDER BY created_at, work_id").fetchall()
        return [self.work_status(row["work_id"], current_baseline=current_baseline) for row in rows]
