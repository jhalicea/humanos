"""Runtime-facing bridge for the HumanOS development Context Registry.

This module is intentionally deterministic. It does not execute work, switch
branches, authorize tools, or infer private context with an LLM. It converts the
promoted registry/router result into a small host-safe envelope that Mirror can
surface before execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from context_registry import ContextRegistry, RouteResult, load_default_registry, route_request


@dataclass(frozen=True)
class RuntimeRoute:
    applicable: bool
    workspace_id: Optional[str]
    decision: Optional[str]
    selected_workstream: Optional[str]
    candidates: tuple[dict[str, object], ...]
    reason: str
    requires_confirmation: bool

    @property
    def allow_execution(self) -> bool:
        return not self.requires_confirmation

    def model_context(self) -> dict[str, object]:
        """Return the minimum routing metadata safe for model consumption.

        Public HumanOS workstreams may expose their operational metadata. Private
        overlay workstreams expose only stable aliases/status/score; their titles,
        projects, branch names, work orders, resume text, local roots, notes and
        real display names stay host-side unless a later explicit policy permits
        more. This keeps a future hosted model from inheriting private workspace
        data merely because the local router needed it.
        """
        safe_candidates = []
        for item in self.candidates:
            safe = {
                "workstream_id": item["workstream_id"],
                "score": item["score"],
                "status": item["status"],
                "public": item["public"],
            }
            if item["public"]:
                for key in ("title", "project", "branch", "work_order", "resume_point", "next_action"):
                    safe[key] = item[key]
            safe_candidates.append(safe)
        return {
            "applicable": self.applicable,
            "workspace_id": self.workspace_id,
            "decision": self.decision,
            "selected_workstream": self.selected_workstream,
            "candidates": safe_candidates,
            "reason": self.reason,
            "requires_confirmation": self.requires_confirmation,
        }


class RuntimeContextRouter:
    """Small operational Context Layer precursor for HumanOS development work."""

    def __init__(self, registry: Optional[ContextRegistry] = None, repo_root: Optional[Path] = None):
        self.registry = registry or load_default_registry(repo_root)

    def inspect(self, text: str, workspace_hint: Optional[str] = None) -> RuntimeRoute:
        # Before accepting a score winner, detect cross-workspace relevance. If a
        # private workspace and any other workspace both contain positively matched
        # workstreams, a small score difference must never silently choose which
        # organization's data/context applies. An explicit workspace hint resolves
        # this gate.
        if workspace_hint is None:
            cross_matches = self._cross_workspace_matches(text)
            if len(cross_matches) > 1 and any(workspace_id not in self.registry.public_workspace_ids
                                              for workspace_id, _ in cross_matches):
                candidates = tuple(
                    self._candidate_payload(candidate.workstream_id, candidate.score, candidate.status)
                    for _, scoped in cross_matches
                    for candidate in scoped.candidates[:3]
                )
                workspace_ids = sorted(workspace_id for workspace_id, _ in cross_matches)
                return RuntimeRoute(
                    True, None, "AMBIGUOUS", None, candidates,
                    f"request matches multiple workspace security contexts: {workspace_ids}", True)

        routed = route_request(self.registry, text, workspace_hint=workspace_hint)
        applicable = self._is_applicable(routed, workspace_hint)
        if not applicable:
            return RuntimeRoute(False, None, None, None, (), routed.reason, False)

        candidates = tuple(self._candidate_payload(candidate.workstream_id, candidate.score, candidate.status)
                           for candidate in routed.candidates)
        selected = routed.workstream_id
        if selected and not any(item["workstream_id"] == selected for item in candidates):
            stream = self.registry.workstreams[selected]
            candidates = (self._candidate_payload(selected, 0, stream.status), *candidates)
        requires_confirmation = routed.decision == "AMBIGUOUS"
        return RuntimeRoute(True, routed.workspace_id, routed.decision, selected, candidates,
                            routed.reason, requires_confirmation)

    def _cross_workspace_matches(self, text: str) -> tuple[tuple[str, RouteResult], ...]:
        matches = []
        for workspace_id in self.registry.workspaces:
            scoped = route_request(self.registry, text, workspace_hint=workspace_id)
            if scoped.candidates:
                matches.append((workspace_id, scoped))
        return tuple(matches)

    def _is_applicable(self, routed: RouteResult, workspace_hint: Optional[str]) -> bool:
        if workspace_hint:
            return True
        if routed.workspace_id is not None or routed.candidates:
            return True
        # Equal workspace matches are a real security ambiguity. A request with no
        # registry relevance is ordinary conversation and should not be blocked.
        return routed.decision == "AMBIGUOUS" and routed.reason.startswith("multiple workspaces match equally")

    def _candidate_payload(self, workstream_id: str, score: int, status: str) -> dict[str, object]:
        stream = self.registry.workstreams[workstream_id]
        return {
            "workstream_id": stream.workstream_id,
            "score": score,
            "status": status,
            "public": workstream_id in self.registry.public_workstream_ids,
            "title": stream.title,
            "project": stream.project,
            "branch": stream.branch,
            "work_order": stream.work_order,
            "resume_point": stream.resume_point,
            "next_action": stream.next_action,
        }

    def format_for_human(self, route: RuntimeRoute) -> str:
        if not route.applicable:
            return ""
        if route.requires_confirmation:
            candidate_ids = ", ".join(str(item["workstream_id"]) for item in route.candidates) or "workspace candidates"
            return ("Context confirmation required before model/tool execution. "
                    f"Reason: {route.reason}. Candidates: {candidate_ids}.")
        if route.selected_workstream:
            selected = next((item for item in route.candidates
                             if item["workstream_id"] == route.selected_workstream), None)
            title = f" — {selected['title']}" if selected else ""
            return (f"Context route: {route.workspace_id} | {route.decision} | "
                    f"{route.selected_workstream}{title}. {route.reason}")
        return f"Context route: {route.workspace_id} | {route.decision}. {route.reason}"
