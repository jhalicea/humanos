from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

SCHEMA_VERSION = 1
ID_RE = re.compile(r"^[A-Z][A-Z0-9._-]{1,63}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
TOKEN_RE = re.compile(r"[a-z0-9]+")

WORKSPACE_TYPES = frozenset({"HUMANOS_INTERNAL", "PERSONAL", "BUSINESS", "EMPLOYER", "CLIENT", "EXPERIMENT", "RESEARCH"})
CONFIDENTIALITY_CLASSES = frozenset({"PUBLIC", "INTERNAL", "PERSONAL_PRIVATE", "BUSINESS_PRIVATE", "EMPLOYER_PRIVATE", "CLIENT_PRIVATE", "RESEARCH_PRIVATE"})
WORKSTREAM_STATES = frozenset({"BACKLOG", "READY", "ACTIVE", "BLOCKED", "PAUSED", "REVIEW", "VERIFIED", "PROMOTION_PENDING", "PROMOTED", "DEFERRED", "UNKNOWN", "ARCHIVED", "SUPERSEDED"})
RELATION_TYPES = frozenset({"CONTINUES", "EXTENDS", "DEPENDS_ON", "RELATED_TO", "SUPERSEDES", "EXPERIMENT_FOR", "BLOCKED_BY", "INTEGRATES_WITH"})
CONCURRENT_STATES = frozenset({"ACTIVE", "REVIEW", "PROMOTION_PENDING"})
TERMINAL_STATES = frozenset({"VERIFIED", "PROMOTED", "ARCHIVED", "SUPERSEDED"})
EXPLICIT_CONTINUE_WORDS = frozenset({"continue", "resume", "finish", "fix", "debug"})
EXPLICIT_EXTEND_WORDS = frozenset({"extend", "enhance", "integrate", "add", "expand", "improve"})
EXPLICIT_SEPARATE_WORDS = frozenset({"separate", "new", "apart", "independent"})


class RegistryError(ValueError):
    pass


class ContextBoundaryError(PermissionError):
    pass


@dataclass(frozen=True)
class Workspace:
    workspace_id: str
    workspace_type: str
    public_alias: str
    confidentiality: str
    repository: Optional[str]
    topics: tuple[str, ...]
    cross_workspace_policy: str = "DENY"


@dataclass(frozen=True)
class Relation:
    relation: str
    target_workstream_id: str


@dataclass(frozen=True)
class Workstream:
    workstream_id: str
    workspace_id: str
    title: str
    project: str
    repository: Optional[str]
    branch: Optional[str]
    work_order: Optional[str]
    status: str
    confidentiality: str
    topics: tuple[str, ...]
    components: tuple[str, ...]
    relations: tuple[Relation, ...]
    last_verified_commit: Optional[str]
    resume_point: str
    next_action: str


@dataclass(frozen=True)
class RouteCandidate:
    workstream_id: str
    score: int
    status: str


@dataclass(frozen=True)
class RouteResult:
    decision: str
    workspace_id: Optional[str]
    workstream_id: Optional[str]
    candidates: tuple[RouteCandidate, ...]
    reason: str


@dataclass(frozen=True)
class ContextRegistry:
    workspaces: Mapping[str, Workspace]
    workstreams: Mapping[str, Workstream]
    private_metadata: Mapping[str, Mapping[str, object]]
    public_workspace_ids: frozenset[str]
    public_workstream_ids: frozenset[str]

    def workspace_workstreams(self, workspace_id: str) -> tuple[Workstream, ...]:
        return tuple(w for w in self.workstreams.values() if w.workspace_id == workspace_id)

    def public_snapshot(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "workspaces": [
                {
                    "workspace_id": w.workspace_id,
                    "workspace_type": w.workspace_type,
                    "public_alias": w.public_alias,
                    "confidentiality": w.confidentiality,
                    "repository": w.repository,
                    "topics": list(w.topics),
                    "cross_workspace_policy": w.cross_workspace_policy,
                }
                for w in self.workspaces.values()
                if w.workspace_id in self.public_workspace_ids
            ],
            "workstreams": [
                {
                    "workstream_id": s.workstream_id,
                    "workspace_id": s.workspace_id,
                    "title": s.title,
                    "project": s.project,
                    "repository": s.repository,
                    "branch": s.branch,
                    "work_order": s.work_order,
                    "status": s.status,
                    "confidentiality": s.confidentiality,
                    "topics": list(s.topics),
                    "components": list(s.components),
                    "relations": [
                        {"relation": r.relation, "target_workstream_id": r.target_workstream_id}
                        for r in s.relations
                    ],
                    "last_verified_commit": s.last_verified_commit,
                    "resume_point": s.resume_point,
                    "next_action": s.next_action,
                }
                for s in self.workstreams.values()
                if s.workstream_id in self.public_workstream_ids
            ],
        }


def _require_exact_keys(value: Mapping[str, object], keys: set[str], where: str) -> None:
    actual = set(value)
    if actual != keys:
        raise RegistryError(f"{where} keys invalid; missing={sorted(keys - actual)}, extra={sorted(actual - keys)}")


def _require_string(value: object, where: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty):
        raise RegistryError(f"{where} must be {'a string' if allow_empty else 'a non-empty string'}")
    return value


def _optional_string(value: object, where: str) -> Optional[str]:
    if value is None:
        return None
    return _require_string(value, where)


def _validate_id(value: object, where: str) -> str:
    result = _require_string(value, where)
    if not ID_RE.fullmatch(result):
        raise RegistryError(f"{where} must match {ID_RE.pattern}")
    return result


def _string_list(value: object, where: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise RegistryError(f"{where} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        text = _require_string(item, f"{where}[{index}]").strip()
        if text not in result:
            result.append(text)
    return tuple(result)


def _parse_workspace(item: object, where: str) -> Workspace:
    if not isinstance(item, dict):
        raise RegistryError(f"{where} must be an object")
    _require_exact_keys(item, {"workspace_id", "workspace_type", "public_alias", "confidentiality", "repository", "topics", "cross_workspace_policy"}, where)
    workspace_id = _validate_id(item["workspace_id"], f"{where}.workspace_id")
    workspace_type = _require_string(item["workspace_type"], f"{where}.workspace_type")
    if workspace_type not in WORKSPACE_TYPES:
        raise RegistryError(f"{where}.workspace_type is invalid")
    alias = _require_string(item["public_alias"], f"{where}.public_alias")
    confidentiality = _require_string(item["confidentiality"], f"{where}.confidentiality")
    if confidentiality not in CONFIDENTIALITY_CLASSES:
        raise RegistryError(f"{where}.confidentiality is invalid")
    repository = _optional_string(item["repository"], f"{where}.repository")
    topics = _string_list(item["topics"], f"{where}.topics")
    policy = _require_string(item["cross_workspace_policy"], f"{where}.cross_workspace_policy")
    if policy != "DENY":
        raise RegistryError(f"{where}.cross_workspace_policy must be DENY in schema v1")
    return Workspace(workspace_id, workspace_type, alias, confidentiality, repository, topics, policy)


def _parse_workstream(item: object, where: str) -> Workstream:
    if not isinstance(item, dict):
        raise RegistryError(f"{where} must be an object")
    _require_exact_keys(item, {"workstream_id", "workspace_id", "title", "project", "repository", "branch", "work_order", "status", "confidentiality", "topics", "components", "relations", "last_verified_commit", "resume_point", "next_action"}, where)
    workstream_id = _validate_id(item["workstream_id"], f"{where}.workstream_id")
    workspace_id = _validate_id(item["workspace_id"], f"{where}.workspace_id")
    title = _require_string(item["title"], f"{where}.title")
    project = _require_string(item["project"], f"{where}.project")
    repository = _optional_string(item["repository"], f"{where}.repository")
    branch = _optional_string(item["branch"], f"{where}.branch")
    work_order = _optional_string(item["work_order"], f"{where}.work_order")
    status = _require_string(item["status"], f"{where}.status")
    if status not in WORKSTREAM_STATES:
        raise RegistryError(f"{where}.status is invalid")
    confidentiality = _require_string(item["confidentiality"], f"{where}.confidentiality")
    if confidentiality not in CONFIDENTIALITY_CLASSES:
        raise RegistryError(f"{where}.confidentiality is invalid")
    topics = _string_list(item["topics"], f"{where}.topics")
    components = _string_list(item["components"], f"{where}.components")
    raw_relations = item["relations"]
    if not isinstance(raw_relations, list):
        raise RegistryError(f"{where}.relations must be a list")
    relations: list[Relation] = []
    for index, raw in enumerate(raw_relations):
        rel_where = f"{where}.relations[{index}]"
        if not isinstance(raw, dict):
            raise RegistryError(f"{rel_where} must be an object")
        _require_exact_keys(raw, {"relation", "target_workstream_id"}, rel_where)
        relation = _require_string(raw["relation"], f"{rel_where}.relation")
        if relation not in RELATION_TYPES:
            raise RegistryError(f"{rel_where}.relation is invalid")
        target = _validate_id(raw["target_workstream_id"], f"{rel_where}.target_workstream_id")
        relations.append(Relation(relation, target))
    last_verified = _optional_string(item["last_verified_commit"], f"{where}.last_verified_commit")
    if last_verified is not None and not COMMIT_RE.fullmatch(last_verified):
        raise RegistryError(f"{where}.last_verified_commit must be a 40-character lowercase git SHA")
    resume_point = _require_string(item["resume_point"], f"{where}.resume_point")
    next_action = _require_string(item["next_action"], f"{where}.next_action")
    return Workstream(workstream_id, workspace_id, title, project, repository, branch, work_order, status, confidentiality, topics, components, tuple(relations), last_verified, resume_point, next_action)


def _read_json(path: Path, where: str) -> object:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read {where}: {exc}") from exc


def _parse_registry_document(raw: object, where: str) -> tuple[dict[str, Workspace], dict[str, Workstream]]:
    if not isinstance(raw, dict):
        raise RegistryError(f"{where} must be an object")
    _require_exact_keys(raw, {"schema_version", "workspaces", "workstreams"}, where)
    if raw["schema_version"] != SCHEMA_VERSION:
        raise RegistryError(f"{where}.schema_version is unsupported")
    if not isinstance(raw["workspaces"], list) or not isinstance(raw["workstreams"], list):
        raise RegistryError(f"{where}.workspaces and workstreams must be lists")
    workspaces: dict[str, Workspace] = {}
    for index, item in enumerate(raw["workspaces"]):
        workspace = _parse_workspace(item, f"{where}.workspaces[{index}]")
        if workspace.workspace_id in workspaces:
            raise RegistryError(f"duplicate workspace_id {workspace.workspace_id}")
        workspaces[workspace.workspace_id] = workspace
    workstreams: dict[str, Workstream] = {}
    for index, item in enumerate(raw["workstreams"]):
        workstream = _parse_workstream(item, f"{where}.workstreams[{index}]")
        if workstream.workstream_id in workstreams:
            raise RegistryError(f"duplicate workstream_id {workstream.workstream_id}")
        workstreams[workstream.workstream_id] = workstream
    return workspaces, workstreams


def _validate_graph(workspaces: Mapping[str, Workspace], workstreams: Mapping[str, Workstream]) -> None:
    for workstream in workstreams.values():
        workspace = workspaces.get(workstream.workspace_id)
        if workspace is None:
            raise RegistryError(f"workstream {workstream.workstream_id} references unknown workspace {workstream.workspace_id}")
        if workspace.repository and workstream.repository and workspace.repository != workstream.repository:
            raise RegistryError(f"workstream {workstream.workstream_id} repository conflicts with workspace repository")
        for relation in workstream.relations:
            if relation.target_workstream_id == workstream.workstream_id:
                raise RegistryError(f"workstream {workstream.workstream_id} cannot relate to itself")
            if relation.target_workstream_id not in workstreams:
                raise RegistryError(f"workstream {workstream.workstream_id} references unknown relation target {relation.target_workstream_id}")


def _load_private_overlay(path: Path, workspaces: dict[str, Workspace], workstreams: dict[str, Workstream]) -> dict[str, Mapping[str, object]]:
    raw = _read_json(path, "private overlay")
    if not isinstance(raw, dict):
        raise RegistryError("private overlay must be an object")
    _require_exact_keys(raw, {"schema_version", "workspace_metadata", "workspaces", "workstreams"}, "private overlay")
    if raw["schema_version"] != SCHEMA_VERSION:
        raise RegistryError("private overlay schema_version is unsupported")
    overlay_ws, overlay_streams = _parse_registry_document({"schema_version": SCHEMA_VERSION, "workspaces": raw["workspaces"], "workstreams": raw["workstreams"]}, "private overlay.registry")
    overlap_ws = set(workspaces) & set(overlay_ws)
    overlap_streams = set(workstreams) & set(overlay_streams)
    if overlap_ws:
        raise RegistryError(f"private overlay may not redefine public workspaces: {sorted(overlap_ws)}")
    if overlap_streams:
        raise RegistryError(f"private overlay may not redefine public workstreams: {sorted(overlap_streams)}")
    workspaces.update(overlay_ws)
    workstreams.update(overlay_streams)
    metadata_raw = raw["workspace_metadata"]
    if not isinstance(metadata_raw, dict):
        raise RegistryError("private overlay.workspace_metadata must be an object")
    metadata: dict[str, Mapping[str, object]] = {}
    allowed_meta = {"display_name", "local_roots", "notes"}
    for workspace_id, item in metadata_raw.items():
        _validate_id(workspace_id, "private overlay.workspace_metadata key")
        if workspace_id not in workspaces:
            raise RegistryError(f"private metadata references unknown workspace {workspace_id}")
        if not isinstance(item, dict):
            raise RegistryError(f"private metadata for {workspace_id} must be an object")
        if not set(item).issubset(allowed_meta):
            raise RegistryError(f"private metadata for {workspace_id} contains disallowed keys {sorted(set(item) - allowed_meta)}")
        if "display_name" in item:
            _require_string(item["display_name"], f"private metadata {workspace_id}.display_name")
        if "notes" in item:
            _require_string(item["notes"], f"private metadata {workspace_id}.notes", allow_empty=True)
        if "local_roots" in item:
            _string_list(item["local_roots"], f"private metadata {workspace_id}.local_roots")
        metadata[workspace_id] = dict(item)
    return metadata


def load_registry(public_path: Path, private_overlay_path: Optional[Path] = None) -> ContextRegistry:
    raw = _read_json(public_path, "public registry")
    workspaces, workstreams = _parse_registry_document(raw, "public registry")
    public_workspace_ids = frozenset(workspaces)
    public_workstream_ids = frozenset(workstreams)
    private_metadata: dict[str, Mapping[str, object]] = {}
    if private_overlay_path is not None:
        private_metadata = _load_private_overlay(Path(private_overlay_path), workspaces, workstreams)
    _validate_graph(workspaces, workstreams)
    return ContextRegistry(workspaces, workstreams, private_metadata, public_workspace_ids, public_workstream_ids)


def load_default_registry(repo_root: Optional[Path] = None) -> ContextRegistry:
    root = Path(repo_root) if repo_root is not None else Path(__file__).resolve().parent
    public_path = root / "config" / "context_registry.public.json"
    overlay_value = os.environ.get("HUMANOS_CONTEXT_PRIVATE_REGISTRY")
    overlay_path = Path(overlay_value).expanduser() if overlay_value else None
    return load_registry(public_path, overlay_path)


def _tokens(value: str) -> set[str]:
    return set(TOKEN_RE.findall(value.lower()))


def _workstream_score(text_tokens: set[str], stream: Workstream) -> int:
    topics = _tokens(" ".join(stream.topics))
    identity = _tokens(" ".join(filter(None, [stream.title, stream.project, stream.branch or "", stream.work_order or ""])))
    components = _tokens(" ".join(stream.components))
    return 4 * len(text_tokens & topics) + 2 * len(text_tokens & identity) + len(text_tokens & components)


def _workspace_score(text_tokens: set[str], workspace: Workspace, streams: Sequence[Workstream]) -> int:
    own = 5 * len(text_tokens & _tokens(workspace.public_alias)) + 3 * len(text_tokens & _tokens(" ".join(workspace.topics)))
    stream_best = max((_workstream_score(text_tokens, stream) for stream in streams), default=0)
    return own + stream_best


def _resolve_workspace_hint(registry: ContextRegistry, hint: str) -> str:
    exact = registry.workspaces.get(hint)
    if exact:
        return exact.workspace_id
    matches = [w.workspace_id for w in registry.workspaces.values() if w.public_alias.casefold() == hint.casefold()]
    if len(matches) != 1:
        raise RegistryError(f"workspace hint {hint!r} does not uniquely resolve")
    return matches[0]


def route_request(registry: ContextRegistry, text: str, workspace_hint: Optional[str] = None) -> RouteResult:
    text = _require_string(text, "request text")
    text_tokens = _tokens(text)
    if not text_tokens:
        return RouteResult("AMBIGUOUS", None, None, (), "request contains no routable terms")

    if workspace_hint:
        workspace_id = _resolve_workspace_hint(registry, workspace_hint)
    else:
        scored_workspaces: list[tuple[int, str]] = []
        for workspace in registry.workspaces.values():
            streams = registry.workspace_workstreams(workspace.workspace_id)
            scored_workspaces.append((_workspace_score(text_tokens, workspace, streams), workspace.workspace_id))
        best = max((score for score, _ in scored_workspaces), default=0)
        winners = sorted(workspace_id for score, workspace_id in scored_workspaces if score == best and score > 0)
        if not winners:
            return RouteResult("AMBIGUOUS", None, None, (), "workspace could not be resolved safely")
        if len(winners) != 1:
            return RouteResult("AMBIGUOUS", None, None, (), f"multiple workspaces match equally: {winners}")
        workspace_id = winners[0]

    streams = registry.workspace_workstreams(workspace_id)
    scored = sorted((RouteCandidate(stream.workstream_id, _workstream_score(text_tokens, stream), stream.status) for stream in streams), key=lambda candidate: (-candidate.score, candidate.workstream_id))
    positive = tuple(candidate for candidate in scored if candidate.score > 0)
    if not positive:
        return RouteResult("CREATE_SEPARATE", workspace_id, None, (), "workspace resolved but no related workstream matched")

    best_score = positive[0].score
    best_candidates = tuple(candidate for candidate in positive if candidate.score == best_score)
    if len(best_candidates) > 1:
        return RouteResult("AMBIGUOUS", workspace_id, None, best_candidates, "multiple workstreams match equally; confirmation is required before implementation")

    candidate = best_candidates[0]
    stream = registry.workstreams[candidate.workstream_id]
    if text_tokens & EXPLICIT_SEPARATE_WORDS:
        decision = "CREATE_SEPARATE"
        reason = f"request explicitly asks for separate/new work; closest related stream is {stream.workstream_id}"
    elif text_tokens & EXPLICIT_CONTINUE_WORDS:
        decision = "CONTINUE"
        reason = f"request explicitly indicates continuation and best match is {stream.workstream_id}"
    elif text_tokens & EXPLICIT_EXTEND_WORDS:
        decision = "EXTEND"
        reason = f"request indicates extension/integration of {stream.workstream_id}"
    elif stream.status in TERMINAL_STATES:
        decision = "EXTEND"
        reason = f"best related workstream {stream.workstream_id} is terminal; new work should extend rather than mutate history"
    elif best_score >= 8:
        decision = "CONTINUE"
        reason = f"strong unique match to resumable workstream {stream.workstream_id}"
    else:
        decision = "EXTEND"
        reason = f"related work exists in {stream.workstream_id}, but match is not strong enough to assume continuation"

    return RouteResult(decision, workspace_id, stream.workstream_id, positive[:5], reason)


def assert_workspace_access(registry: ContextRegistry, source_workspace_id: str, target_workspace_id: str, *, explicit_authorization: bool = False) -> None:
    if source_workspace_id not in registry.workspaces or target_workspace_id not in registry.workspaces:
        raise RegistryError("workspace access check references unknown workspace")
    if source_workspace_id == target_workspace_id:
        return
    if not explicit_authorization:
        raise ContextBoundaryError(f"cross-workspace access denied: {source_workspace_id} -> {target_workspace_id}; explicit owner authorization is required")


def _component_overlap(left: str, right: str) -> bool:
    left = left.strip("/")
    right = right.strip("/")
    return left == right or left.startswith(right + "/") or right.startswith(left + "/")


def find_component_conflicts(registry: ContextRegistry, workstream_id: str, proposed_components: Iterable[str]) -> tuple[str, ...]:
    stream = registry.workstreams.get(workstream_id)
    if stream is None:
        raise RegistryError(f"unknown workstream {workstream_id}")
    proposed = tuple(_require_string(value, "proposed component").strip("/") for value in proposed_components)
    conflicts: list[str] = []
    for other in registry.workstreams.values():
        if other.workstream_id == stream.workstream_id:
            continue
        if stream.repository is None or other.repository != stream.repository:
            continue
        if other.status not in CONCURRENT_STATES:
            continue
        if any(_component_overlap(left, right) for left in proposed for right in other.components):
            conflicts.append(other.workstream_id)
    return tuple(sorted(conflicts))


def _route_to_dict(result: RouteResult) -> dict[str, object]:
    return {
        "decision": result.decision,
        "workspace_id": result.workspace_id,
        "workstream_id": result.workstream_id,
        "reason": result.reason,
        "candidates": [{"workstream_id": c.workstream_id, "score": c.score, "status": c.status} for c in result.candidates],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="HumanOS context/workstream registry")
    parser.add_argument("--registry", default=str(Path(__file__).resolve().parent / "config" / "context_registry.public.json"))
    parser.add_argument("--private-overlay", default=os.environ.get("HUMANOS_CONTEXT_PRIVATE_REGISTRY"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate")
    route = sub.add_parser("route")
    route.add_argument("text")
    route.add_argument("--workspace")
    args = parser.parse_args(argv)
    registry = load_registry(Path(args.registry), Path(args.private_overlay).expanduser() if args.private_overlay else None)
    if args.command == "validate":
        print(json.dumps({"ok": True, "workspaces": len(registry.workspaces), "workstreams": len(registry.workstreams)}))
        return 0
    result = route_request(registry, args.text, args.workspace)
    print(json.dumps(_route_to_dict(result), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
