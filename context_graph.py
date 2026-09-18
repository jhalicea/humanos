"""Deterministic local entity/relationship substrate for the HumanOS Context Engine.

This module is derived context, not Life Notebook evidence and not execution authority.
It stores only explicitly sourced entities and relationships in a caller-selected local
SQLite database. No model output provenance is accepted in schema v1.
"""
from __future__ import annotations

import hashlib
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from context_registry import CONFIDENTIALITY_CLASSES, ID_RE


ENTITY_TYPES = frozenset({
    "PERSON",
    "SYSTEM",
    "WORKSPACE",
    "PROJECT",
    "WORKSTREAM",
    "WORK_ORDER",
    "ARTIFACT",
    "CONVERSATION",
    "ORGANIZATION",
    "GOAL",
})
RELATION_TYPES = frozenset({
    "OWNS",
    "CONTAINS",
    "BELONGS_TO",
    "EXTENDS",
    "PRODUCED_BY",
    "CONCERNS",
    "RELATED_TO",
    "DEPENDS_ON",
})
PROVENANCE_KINDS = frozenset({
    "OWNER_ASSERTION",
    "NOTEBOOK_EVIDENCE",
    "REPOSITORY_EVIDENCE",
    "REGISTRY_EVIDENCE",
    "TOOL_EVIDENCE",
})
ENTITY_ID_RE = re.compile(r"^ENT-[A-Z][A-Z0-9_]*-[0-9A-F]{24}$")
EDGE_ID_RE = re.compile(r"^EDGE-[0-9A-F]{24}$")
PROVENANCE_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/#@+\-]{0,511}$")
_DOMAIN_ENTITY = b"HumanOS context entity v1\x00"
_DOMAIN_EDGE = b"HumanOS context edge v1\x00"


class ContextGraphError(ValueError):
    pass


class ContextGraphConflict(ContextGraphError):
    pass


class ContextGraphBoundaryError(PermissionError):
    pass


@dataclass(frozen=True)
class ContextEntity:
    entity_id: str
    entity_type: str
    stable_key: str
    label: str
    workspace_id: str
    confidentiality: str
    created: str


@dataclass(frozen=True)
class ContextEdge:
    edge_id: str
    source_entity_id: str
    relation_type: str
    target_entity_id: str
    workspace_id: str
    confidentiality: str
    created: str


@dataclass(frozen=True)
class Provenance:
    provenance_kind: str
    provenance_ref: str
    created: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require_text(value: object, where: str, *, max_chars: int) -> str:
    if not isinstance(value, str) or not value or len(value) > max_chars:
        raise ContextGraphError(f"{where} must be a non-empty string up to {max_chars} characters")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise ContextGraphError(f"{where} contains control characters")
    return value


def _workspace_id(value: object) -> str:
    text = _require_text(value, "workspace_id", max_chars=64)
    if not ID_RE.fullmatch(text):
        raise ContextGraphError("workspace_id is invalid")
    return text


def _entity_type(value: object) -> str:
    text = _require_text(value, "entity_type", max_chars=64)
    if text not in ENTITY_TYPES:
        raise ContextGraphError("entity_type is invalid")
    return text


def _confidentiality(value: object) -> str:
    text = _require_text(value, "confidentiality", max_chars=64)
    if text not in CONFIDENTIALITY_CLASSES:
        raise ContextGraphError("confidentiality is invalid")
    return text


def _provenance(kind: object, ref: object) -> tuple[str, str]:
    kind_text = _require_text(kind, "provenance_kind", max_chars=64)
    if kind_text not in PROVENANCE_KINDS:
        raise ContextGraphError("provenance_kind is not trusted for canonical graph assertions")
    ref_text = _require_text(ref, "provenance_ref", max_chars=512)
    if not PROVENANCE_REF_RE.fullmatch(ref_text):
        raise ContextGraphError("provenance_ref must be a content-light stable reference")
    return kind_text, ref_text


def stable_entity_id(workspace_id: str, entity_type: str, stable_key: str) -> str:
    """Return a deterministic workspace-scoped entity ID.

    Workspace scope deliberately prevents an identity learned in one security context
    from silently becoming the same canonical entity in another workspace.
    """
    workspace = _workspace_id(workspace_id)
    kind = _entity_type(entity_type)
    key = _require_text(stable_key, "stable_key", max_chars=512)
    payload = "\x00".join((workspace, kind, key)).encode("utf-8")
    digest = hashlib.sha256(_DOMAIN_ENTITY + payload).hexdigest()[:24].upper()
    return f"ENT-{kind}-{digest}"


def stable_edge_id(workspace_id: str, source_entity_id: str,
                   relation_type: str, target_entity_id: str) -> str:
    workspace = _workspace_id(workspace_id)
    source = _require_text(source_entity_id, "source_entity_id", max_chars=128)
    target = _require_text(target_entity_id, "target_entity_id", max_chars=128)
    relation = _require_text(relation_type, "relation_type", max_chars=64)
    if not ENTITY_ID_RE.fullmatch(source) or not ENTITY_ID_RE.fullmatch(target):
        raise ContextGraphError("edge entity ID is invalid")
    if relation not in RELATION_TYPES:
        raise ContextGraphError("relation_type is invalid")
    payload = "\x00".join((workspace, source, relation, target)).encode("utf-8")
    digest = hashlib.sha256(_DOMAIN_EDGE + payload).hexdigest()[:24].upper()
    return f"EDGE-{digest}"


class ContextGraph:
    """Local deterministic graph store with fail-closed workspace boundaries."""

    def __init__(self, db_path):
        requested = Path(db_path).expanduser()
        if requested.exists() and requested.is_symlink():
            raise ContextGraphError("context graph database may not be a symlink")
        self.path = requested.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          PRAGMA foreign_keys=ON;
          PRAGMA trusted_schema=OFF;
          PRAGMA busy_timeout=5000;
          CREATE TABLE IF NOT EXISTS context_entities(
            entity_id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            stable_key TEXT NOT NULL,
            label TEXT NOT NULL,
            workspace_id TEXT NOT NULL,
            confidentiality TEXT NOT NULL,
            created TEXT NOT NULL,
            UNIQUE(workspace_id, entity_type, stable_key)
          );
          CREATE TABLE IF NOT EXISTS context_entity_provenance(
            entity_id TEXT NOT NULL REFERENCES context_entities(entity_id),
            provenance_kind TEXT NOT NULL,
            provenance_ref TEXT NOT NULL,
            created TEXT NOT NULL,
            PRIMARY KEY(entity_id, provenance_kind, provenance_ref)
          );
          CREATE TABLE IF NOT EXISTS context_edges(
            edge_id TEXT PRIMARY KEY,
            source_entity_id TEXT NOT NULL REFERENCES context_entities(entity_id),
            relation_type TEXT NOT NULL,
            target_entity_id TEXT NOT NULL REFERENCES context_entities(entity_id),
            workspace_id TEXT NOT NULL,
            confidentiality TEXT NOT NULL,
            created TEXT NOT NULL,
            UNIQUE(workspace_id, source_entity_id, relation_type, target_entity_id)
          );
          CREATE TABLE IF NOT EXISTS context_edge_provenance(
            edge_id TEXT NOT NULL REFERENCES context_edges(edge_id),
            provenance_kind TEXT NOT NULL,
            provenance_ref TEXT NOT NULL,
            created TEXT NOT NULL,
            PRIMARY KEY(edge_id, provenance_kind, provenance_ref)
          );
        """)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def add_entity(self, *, workspace_id: str, entity_type: str, stable_key: str,
                   label: str, confidentiality: str,
                   provenance_kind: str, provenance_ref: str) -> ContextEntity:
        workspace = _workspace_id(workspace_id)
        kind = _entity_type(entity_type)
        key = _require_text(stable_key, "stable_key", max_chars=512)
        display = _require_text(label, "label", max_chars=256)
        secrecy = _confidentiality(confidentiality)
        prov_kind, prov_ref = _provenance(provenance_kind, provenance_ref)
        entity_id = stable_entity_id(workspace, kind, key)
        created = _now()

        existing = self.db.execute(
            "SELECT * FROM context_entities WHERE entity_id=?", (entity_id,)
        ).fetchone()
        if existing is not None:
            expected = (kind, key, display, workspace, secrecy)
            actual = (
                existing["entity_type"], existing["stable_key"], existing["label"],
                existing["workspace_id"], existing["confidentiality"],
            )
            if actual != expected:
                raise ContextGraphConflict("stable entity ID already exists with different canonical fields")
        else:
            with self.db:
                self.db.execute(
                    """INSERT INTO context_entities
                       (entity_id,entity_type,stable_key,label,workspace_id,confidentiality,created)
                       VALUES (?,?,?,?,?,?,?)""",
                    (entity_id, kind, key, display, workspace, secrecy, created),
                )

        with self.db:
            self.db.execute(
                """INSERT OR IGNORE INTO context_entity_provenance
                   (entity_id,provenance_kind,provenance_ref,created)
                   VALUES (?,?,?,?)""",
                (entity_id, prov_kind, prov_ref, created),
            )
        return self.get_entity(entity_id, workspace)

    def get_entity(self, entity_id: str, workspace_id: str) -> Optional[ContextEntity]:
        workspace = _workspace_id(workspace_id)
        ident = _require_text(entity_id, "entity_id", max_chars=128)
        if not ENTITY_ID_RE.fullmatch(ident):
            raise ContextGraphError("entity_id is invalid")
        row = self.db.execute(
            "SELECT * FROM context_entities WHERE entity_id=?", (ident,)
        ).fetchone()
        if row is None:
            return None
        if row["workspace_id"] != workspace:
            raise ContextGraphBoundaryError("entity belongs to a different workspace")
        return self._entity(row)

    def entity_provenance(self, entity_id: str, workspace_id: str) -> tuple[Provenance, ...]:
        self.get_entity(entity_id, workspace_id)
        rows = self.db.execute(
            """SELECT provenance_kind,provenance_ref,created
               FROM context_entity_provenance WHERE entity_id=?
               ORDER BY provenance_kind,provenance_ref""",
            (entity_id,),
        ).fetchall()
        return tuple(Provenance(row["provenance_kind"], row["provenance_ref"], row["created"])
                     for row in rows)

    def add_edge(self, *, source_entity_id: str, relation_type: str,
                 target_entity_id: str, workspace_id: str,
                 provenance_kind: str, provenance_ref: str) -> ContextEdge:
        workspace = _workspace_id(workspace_id)
        relation = _require_text(relation_type, "relation_type", max_chars=64)
        if relation not in RELATION_TYPES:
            raise ContextGraphError("relation_type is invalid")
        prov_kind, prov_ref = _provenance(provenance_kind, provenance_ref)
        source = self.get_entity(source_entity_id, workspace)
        target = self.get_entity(target_entity_id, workspace)
        if source is None or target is None:
            raise ContextGraphError("both edge entities must already exist")
        if source.entity_id == target.entity_id:
            raise ContextGraphError("self relationships are not allowed in graph schema v1")
        if source.confidentiality != target.confidentiality:
            raise ContextGraphBoundaryError(
                "schema v1 does not relate entities across confidentiality classes")
        edge_id = stable_edge_id(workspace, source.entity_id, relation, target.entity_id)
        created = _now()
        existing = self.db.execute(
            "SELECT * FROM context_edges WHERE edge_id=?", (edge_id,)
        ).fetchone()
        if existing is None:
            with self.db:
                self.db.execute(
                    """INSERT INTO context_edges
                       (edge_id,source_entity_id,relation_type,target_entity_id,
                        workspace_id,confidentiality,created)
                       VALUES (?,?,?,?,?,?,?)""",
                    (edge_id, source.entity_id, relation, target.entity_id,
                     workspace, source.confidentiality, created),
                )
        else:
            expected = (
                source.entity_id, relation, target.entity_id, workspace, source.confidentiality)
            actual = (
                existing["source_entity_id"], existing["relation_type"],
                existing["target_entity_id"], existing["workspace_id"],
                existing["confidentiality"],
            )
            if actual != expected:
                raise ContextGraphConflict("stable edge ID already exists with different canonical fields")

        with self.db:
            self.db.execute(
                """INSERT OR IGNORE INTO context_edge_provenance
                   (edge_id,provenance_kind,provenance_ref,created)
                   VALUES (?,?,?,?)""",
                (edge_id, prov_kind, prov_ref, created),
            )
        return self.get_edge(edge_id, workspace)

    def get_edge(self, edge_id: str, workspace_id: str) -> Optional[ContextEdge]:
        workspace = _workspace_id(workspace_id)
        ident = _require_text(edge_id, "edge_id", max_chars=64)
        if not EDGE_ID_RE.fullmatch(ident):
            raise ContextGraphError("edge_id is invalid")
        row = self.db.execute(
            "SELECT * FROM context_edges WHERE edge_id=?", (ident,)
        ).fetchone()
        if row is None:
            return None
        if row["workspace_id"] != workspace:
            raise ContextGraphBoundaryError("edge belongs to a different workspace")
        return self._edge(row)

    def edge_provenance(self, edge_id: str, workspace_id: str) -> tuple[Provenance, ...]:
        self.get_edge(edge_id, workspace_id)
        rows = self.db.execute(
            """SELECT provenance_kind,provenance_ref,created
               FROM context_edge_provenance WHERE edge_id=?
               ORDER BY provenance_kind,provenance_ref""",
            (edge_id,),
        ).fetchall()
        return tuple(Provenance(row["provenance_kind"], row["provenance_ref"], row["created"])
                     for row in rows)

    def relationships(self, entity_id: str, workspace_id: str, *,
                      direction: str = "outgoing") -> tuple[ContextEdge, ...]:
        workspace = _workspace_id(workspace_id)
        entity = self.get_entity(entity_id, workspace)
        if entity is None:
            raise ContextGraphError("entity does not exist")
        if direction == "outgoing":
            clause, args = "source_entity_id=?", (entity.entity_id,)
        elif direction == "incoming":
            clause, args = "target_entity_id=?", (entity.entity_id,)
        elif direction == "both":
            clause, args = "(source_entity_id=? OR target_entity_id=?)", (
                entity.entity_id, entity.entity_id)
        else:
            raise ContextGraphError("direction must be outgoing, incoming, or both")
        rows = self.db.execute(
            f"""SELECT * FROM context_edges
                WHERE workspace_id=? AND {clause}
                ORDER BY edge_id""",
            (workspace, *args),
        ).fetchall()
        return tuple(self._edge(row) for row in rows)

    @staticmethod
    def _entity(row) -> ContextEntity:
        return ContextEntity(
            row["entity_id"], row["entity_type"], row["stable_key"], row["label"],
            row["workspace_id"], row["confidentiality"], row["created"])

    @staticmethod
    def _edge(row) -> ContextEdge:
        return ContextEdge(
            row["edge_id"], row["source_entity_id"], row["relation_type"],
            row["target_entity_id"], row["workspace_id"], row["confidentiality"],
            row["created"])
