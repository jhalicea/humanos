"""Trusted public Context Registry -> Context Graph projection bridge.

CTX-010 projects only validated *public* registry structure into an existing local
ContextGraph. It does not load private overlay entries into the graph, infer facts,
choose a live graph path, or grant any execution authority.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from context_graph import ContextGraph
from context_registry import ContextRegistry


SUPPORTED_REGISTRY_RELATIONS = frozenset({"EXTENDS", "RELATED_TO", "DEPENDS_ON"})


class RegistryGraphBridgeError(ValueError):
    pass


class RegistryGraphBoundaryError(PermissionError):
    pass


@dataclass(frozen=True)
class SkippedRegistryRelation:
    source_workstream_id: str
    relation_type: str
    target_workstream_id: str
    reason: str


@dataclass(frozen=True)
class RegistryGraphProjection:
    snapshot_sha256: str
    workspace_entities: tuple[tuple[str, str], ...]
    workstream_entities: tuple[tuple[str, str], ...]
    membership_edges: tuple[str, ...]
    relation_edges: tuple[str, ...]
    skipped_relations: tuple[SkippedRegistryRelation, ...]


def public_registry_snapshot_sha256(registry: ContextRegistry) -> str:
    """Digest the exact public snapshot consumed by this projection."""
    payload = json.dumps(
        registry.public_snapshot(),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _assertion_provenance_ref(kind: str, *parts: str) -> str:
    """Bind provenance to exactly the registry fields that define one graph assertion."""
    payload = json.dumps(
        {"kind": kind, "parts": parts},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return f"registry:assertion:{kind}:sha256:{digest}"


def _preflight(registry: ContextRegistry):
    public_workspace_ids = set(registry.public_workspace_ids)
    public_workstream_ids = set(registry.public_workstream_ids)

    workspaces = []
    for workspace_id in sorted(public_workspace_ids):
        workspace = registry.workspaces.get(workspace_id)
        if workspace is None:
            raise RegistryGraphBridgeError(
                f"public workspace {workspace_id} is missing from the loaded registry")
        workspaces.append(workspace)

    workstreams = []
    for workstream_id in sorted(public_workstream_ids):
        stream = registry.workstreams.get(workstream_id)
        if stream is None:
            raise RegistryGraphBridgeError(
                f"public workstream {workstream_id} is missing from the loaded registry")
        if stream.workspace_id not in public_workspace_ids:
            raise RegistryGraphBoundaryError(
                f"public workstream {workstream_id} belongs to a non-public workspace")
        workspace = registry.workspaces[stream.workspace_id]
        if stream.confidentiality != workspace.confidentiality:
            raise RegistryGraphBoundaryError(
                f"workstream {workstream_id} confidentiality does not match its workspace")
        workstreams.append(stream)

    supported_relations = []
    skipped_relations = []
    for stream in workstreams:
        for relation in sorted(
            stream.relations,
            key=lambda item: (item.relation, item.target_workstream_id),
        ):
            if relation.target_workstream_id not in public_workstream_ids:
                skipped_relations.append(SkippedRegistryRelation(
                    stream.workstream_id,
                    relation.relation,
                    relation.target_workstream_id,
                    "TARGET_NOT_PUBLIC",
                ))
                continue
            if relation.relation not in SUPPORTED_REGISTRY_RELATIONS:
                skipped_relations.append(SkippedRegistryRelation(
                    stream.workstream_id,
                    relation.relation,
                    relation.target_workstream_id,
                    "UNSUPPORTED_GRAPH_RELATION",
                ))
                continue

            target = registry.workstreams[relation.target_workstream_id]
            if target.workspace_id != stream.workspace_id:
                raise RegistryGraphBoundaryError(
                    f"supported relation {stream.workstream_id} {relation.relation} "
                    f"{target.workstream_id} crosses workspaces")
            if target.confidentiality != stream.confidentiality:
                raise RegistryGraphBoundaryError(
                    f"supported relation {stream.workstream_id} {relation.relation} "
                    f"{target.workstream_id} crosses confidentiality classes")
            supported_relations.append((stream, relation, target))

    return workspaces, workstreams, supported_relations, tuple(skipped_relations)


def project_public_registry(registry: ContextRegistry, graph: ContextGraph) -> RegistryGraphProjection:
    """Project one public-registry snapshot into an existing append-only graph.

    All workspace/security checks occur before the first graph mutation. Writes are
    deterministic and idempotent because CTX-009 uses stable IDs and append-only rows.

    The returned ID sets define this snapshot's projection. Raw graph rows are not a
    currentness signal: assertions from older snapshots can remain append-only after
    registry removal until a later active-projection/rebuild policy is introduced.
    """
    workspaces, workstreams, relations, skipped = _preflight(registry)
    digest = public_registry_snapshot_sha256(registry)

    workspace_entities = {}
    for workspace in workspaces:
        entity = graph.add_entity(
            workspace_id=workspace.workspace_id,
            entity_type="WORKSPACE",
            stable_key=workspace.workspace_id,
            label=workspace.workspace_id,
            confidentiality=workspace.confidentiality,
            provenance_kind="REGISTRY_EVIDENCE",
            provenance_ref=_assertion_provenance_ref(
                "workspace",
                workspace.workspace_id,
                workspace.confidentiality,
            ),
        )
        workspace_entities[workspace.workspace_id] = entity.entity_id

    workstream_entities = {}
    for stream in workstreams:
        entity = graph.add_entity(
            workspace_id=stream.workspace_id,
            entity_type="WORKSTREAM",
            stable_key=stream.workstream_id,
            label=stream.workstream_id,
            confidentiality=stream.confidentiality,
            provenance_kind="REGISTRY_EVIDENCE",
            provenance_ref=_assertion_provenance_ref(
                "workstream",
                stream.workstream_id,
                stream.workspace_id,
                stream.confidentiality,
            ),
        )
        workstream_entities[stream.workstream_id] = entity.entity_id

    membership_edges = []
    for stream in workstreams:
        edge = graph.add_edge(
            source_entity_id=workstream_entities[stream.workstream_id],
            relation_type="BELONGS_TO",
            target_entity_id=workspace_entities[stream.workspace_id],
            workspace_id=stream.workspace_id,
            provenance_kind="REGISTRY_EVIDENCE",
            provenance_ref=_assertion_provenance_ref(
                "membership",
                stream.workstream_id,
                stream.workspace_id,
                stream.confidentiality,
            ),
        )
        membership_edges.append(edge.edge_id)

    relation_edges = []
    for source, relation, target in relations:
        edge = graph.add_edge(
            source_entity_id=workstream_entities[source.workstream_id],
            relation_type=relation.relation,
            target_entity_id=workstream_entities[target.workstream_id],
            workspace_id=source.workspace_id,
            provenance_kind="REGISTRY_EVIDENCE",
            provenance_ref=_assertion_provenance_ref(
                "relation",
                source.workstream_id,
                relation.relation,
                target.workstream_id,
                source.workspace_id,
                source.confidentiality,
            ),
        )
        relation_edges.append(edge.edge_id)

    return RegistryGraphProjection(
        snapshot_sha256=digest,
        workspace_entities=tuple(sorted(workspace_entities.items())),
        workstream_entities=tuple(sorted(workstream_entities.items())),
        membership_edges=tuple(sorted(membership_edges)),
        relation_edges=tuple(sorted(relation_edges)),
        skipped_relations=skipped,
    )
