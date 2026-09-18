"""Runtime-facing bridge for the HumanOS development Context Registry.

This module is intentionally deterministic. It does not execute work, switch
branches, authorize tools, or infer private context with an LLM. It converts the
promoted registry/router result into a small host-safe envelope that Mirror can
surface before execution.

HOS-CTX-003 adds a bounded session-continuity primitive: a short follow-up such
as "do it" may inherit the immediately preceding verified workstream route in
the same HumanOS session. This is a precursor to the future HumanOS Context
Engine, not a competing memory system.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from context_registry import ContextRegistry, RouteResult, load_default_registry, route_request


_CONTINUATION_PATTERNS = (
    re.compile(r"^(?:please\s+)?(?:continue|resume|proceed|keep going|carry on|go ahead)$", re.I),
    re.compile(r"^(?:please\s+)?(?:continue|resume|do|use|run|finish)\s+(?:it|that|this)$", re.I),
    re.compile(r"^(?:let(?:'|’)s|lets)\s+(?:continue|keep going|do it|do that|go ahead|proceed)$", re.I),
    re.compile(r"^(?:yes|yeah|yep)[,\s]+(?:continue|go ahead|do it|keep going|proceed)$", re.I),
)
_TERMINAL_WORKSTREAM_STATES = {"ARCHIVED", "SUPERSEDED"}
_HISTORY_PATTERNS = (
    re.compile(r"\b(?:continue|resume|return to|go back to|pick up|finish)\b", re.I),
    re.compile(r"\b(?:what we were doing|where we left off|that .* thing|previous work|earlier work)\b", re.I),
)
_HISTORY_CUES = re.compile(r"\b(?:yesterday|earlier|before|previous|last|old|where we left off|what we were doing|go back)\b", re.I)


@dataclass(frozen=True)
class RuntimeRoute:
    applicable: bool
    workspace_id: Optional[str]
    decision: Optional[str]
    selected_workstream: Optional[str]
    candidates: tuple[dict[str, object], ...]
    reason: str
    requires_confirmation: bool
    origin: str = "REQUEST"
    source_tx: Optional[str] = None

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

        ``source_tx`` is deliberately host-only. The model may know that context
        came from verified session continuity, but not the Notebook transaction ID
        that proved it.
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
            "origin": self.origin,
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

    def inspect_session(self, book, hcid: str, text: str, current_tx: Optional[str] = None,
                        workspace_hint: Optional[str] = None, allow_inherit: bool = True) -> RuntimeRoute:
        """Resolve the current request, then apply narrow verified session continuity.

        Fresh request evidence always wins. Session inheritance is considered only
        when the current request has no registry relevance and is a short explicit
        continuation phrase. The immediately preceding HumanOS transaction in the
        same HCID must be checkpointed and must contain a deterministic,
        non-ambiguous ``CONTEXT_ROUTE`` event.

        This is intentionally not broad conversational memory. It is the smallest
        safe primitive for future Context Engine evolution.
        """
        routed = self.inspect(text, workspace_hint=workspace_hint)
        if routed.applicable or not allow_inherit or workspace_hint is not None:
            return routed
        if not self._continuation_candidate(text):
            return routed

        binding = self._immediate_verified_session_binding(book, hcid, current_tx)
        if not binding:
            return routed

        workstream_id = binding["workstream_id"]
        workspace_id = binding["workspace_id"]
        stream = self.registry.workstreams.get(workstream_id)
        if (stream is None or stream.workspace_id != workspace_id or
                stream.status in _TERMINAL_WORKSTREAM_STATES):
            return routed

        candidate = self._candidate_payload(workstream_id, 0, stream.status)
        return RuntimeRoute(
            True,
            workspace_id,
            "CONTINUE",
            workstream_id,
            (candidate,),
            "short follow-up inherited the immediately preceding verified workstream context",
            False,
            origin="SESSION_CONTINUITY",
            source_tx=binding["source_tx"],
        )

    def inspect_history(self, book, text: str, current_tx: Optional[str] = None,
                        workspace_hint: Optional[str] = None) -> RuntimeRoute:
        """Resolve explicit historical-continuation language from verified Notebook evidence.

        This is deliberately deterministic and content-light. It uses checkpointed
        CONTEXT_ROUTE events as the authority, never raw model recollection. Raw
        TX/HCID identifiers remain host-side. If more than one workstream remains
        plausible, Mirror asks about human-readable topics instead of guessing.
        """
        fresh = self.inspect(text, workspace_hint=workspace_hint)
        if not self._history_candidate(text):
            return fresh

        try:
            book.verify()
        except Exception:
            return RuntimeRoute(
                True, workspace_hint, "AMBIGUOUS", None, (),
                "Notebook evidence failed integrity verification; historical context cannot be trusted",
                True, origin="NOTEBOOK_RECOVERY")

        records = self._verified_history_records(book, current_tx=current_tx)
        if workspace_hint:
            records = [item for item in records if item["workspace_id"] == workspace_hint]

        # Subject words may narrow historical evidence. Generic recovery words
        # ("continue", "earlier", "what we were doing") must not accidentally
        # select the Context Layer merely because those words are registry topics.
        subject_tokens = self._history_subject_tokens(text)
        if subject_tokens:
            subject_ids = set()
            for workstream_id, stream in self.registry.workstreams.items():
                haystack = " ".join((stream.title, stream.project, *stream.topics)).casefold()
                if any(token in set(re.findall(r"[a-z0-9]+", haystack)) for token in subject_tokens):
                    subject_ids.add(workstream_id)
            narrowed = [item for item in records if item["workstream_id"] in subject_ids]
            if narrowed:
                records = narrowed

        if re.search(r"\byesterday\b", text, re.I):
            today = datetime.now(timezone.utc).date()
            target = today - timedelta(days=1)
            records = [item for item in records if item["created_date"] == target.isoformat()]

        unique = []
        seen = set()
        for item in records:
            workstream_id = item["workstream_id"]
            if workstream_id in seen:
                continue
            stream = self.registry.workstreams.get(workstream_id)
            if (stream is None or stream.workspace_id != item["workspace_id"] or
                    stream.status in _TERMINAL_WORKSTREAM_STATES):
                continue
            seen.add(workstream_id)
            unique.append(item)

        if not unique:
            # Historical language is explicit intent. Do not silently send it to
            # the model when verified Notebook evidence cannot bind it.
            return RuntimeRoute(
                True, workspace_hint, "AMBIGUOUS", None, (),
                "no verified historical workstream matches this continuation request",
                True, origin="NOTEBOOK_RECOVERY")

        if len(unique) > 1:
            candidates = tuple(
                self._candidate_payload(item["workstream_id"], 0,
                                        self.registry.workstreams[item["workstream_id"]].status)
                for item in unique[:5]
            )
            workspace_ids = {item["workspace_id"] for item in unique}
            workspace_id = next(iter(workspace_ids)) if len(workspace_ids) == 1 else None
            return RuntimeRoute(
                True, workspace_id, "AMBIGUOUS", None, candidates,
                "multiple verified historical workstreams match; choose the topic to continue",
                True, origin="NOTEBOOK_RECOVERY")

        item = unique[0]
        stream = self.registry.workstreams[item["workstream_id"]]
        return RuntimeRoute(
            True, item["workspace_id"], "CONTINUE", item["workstream_id"],
            (self._candidate_payload(item["workstream_id"], 0, stream.status),),
            "resolved from verified historical Notebook context",
            False, origin="NOTEBOOK_RECOVERY", source_tx=item["source_tx"])

    def _history_candidate(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        stripped = text.strip()
        if not stripped or len(stripped) > 240 or len([x for x in stripped.splitlines() if x.strip()]) > 3:
            return False
        return bool(any(pattern.search(stripped) for pattern in _HISTORY_PATTERNS)
                    and _HISTORY_CUES.search(stripped))

    def _history_subject_tokens(self, text: str) -> set[str]:
        stop = {
            "continue", "resume", "return", "go", "back", "pick", "up", "finish",
            "what", "we", "were", "doing", "where", "left", "off", "that", "this",
            "thing", "work", "earlier", "before", "previous", "last", "old",
            "yesterday", "from", "to", "the", "a", "an", "it", "please",
        }
        return {token for token in re.findall(r"[a-z0-9]+", text.casefold())
                if token not in stop and len(token) > 2}

    def _verified_history_records(self, book, current_tx: Optional[str] = None) -> list[dict[str, str]]:
        rows = book.db.execute(
            """SELECT t.tx,t.created,e.payload
               FROM transactions t
               JOIN events e ON e.tx=t.tx AND e.kind='CONTEXT_ROUTE'
               WHERE t.status='CHECKPOINTED' AND t.tx!=?
               ORDER BY t.rowid DESC,e.seq DESC LIMIT 100""",
            (current_tx or "",),
        ).fetchall()
        records = []
        seen_tx = set()
        for row in rows:
            if row["tx"] in seen_tx:
                continue
            seen_tx.add(row["tx"])
            try:
                payload = json.loads(row["payload"])
            except (TypeError, json.JSONDecodeError):
                continue
            if payload.get("requires_confirmation") or payload.get("decision") == "AMBIGUOUS":
                continue
            workstream_id = payload.get("selected_workstream")
            workspace_id = payload.get("workspace_id")
            if not isinstance(workstream_id, str) or not isinstance(workspace_id, str):
                continue
            try:
                created_date = datetime.fromisoformat(row["created"]).astimezone(timezone.utc).date().isoformat()
            except (TypeError, ValueError):
                continue
            records.append({"source_tx": row["tx"], "workspace_id": workspace_id,
                            "workstream_id": workstream_id, "created_date": created_date})
        return records

    def _immediate_verified_session_binding(self, book, hcid: str,
                                            current_tx: Optional[str]) -> Optional[dict[str, str]]:
        # Use the immediately preceding transaction, not merely the most recent
        # routed transaction. An intervening ordinary/unfinished turn breaks
        # implicit inheritance and prevents stale-topic capture.
        if not hcid:
            return None
        row = book.db.execute(
            """SELECT tx,status FROM transactions
               WHERE hcid=? AND tx!=?
               ORDER BY rowid DESC LIMIT 1""",
            (hcid, current_tx or ""),
        ).fetchone()
        if not row or row["status"] != "CHECKPOINTED":
            return None

        event = book.db.execute(
            """SELECT payload FROM events
               WHERE tx=? AND kind='CONTEXT_ROUTE'
               ORDER BY seq DESC LIMIT 1""",
            (row["tx"],),
        ).fetchone()
        if not event:
            return None
        try:
            payload = json.loads(event["payload"])
        except (TypeError, json.JSONDecodeError):
            return None

        if payload.get("requires_confirmation"):
            return None
        workstream_id = payload.get("selected_workstream")
        workspace_id = payload.get("workspace_id")
        if not isinstance(workstream_id, str) or not isinstance(workspace_id, str):
            return None
        if payload.get("decision") == "AMBIGUOUS":
            return None
        return {
            "source_tx": row["tx"],
            "workspace_id": workspace_id,
            "workstream_id": workstream_id,
        }

    def _continuation_candidate(self, text: str) -> bool:
        if not isinstance(text, str):
            return False
        stripped = text.strip()
        if not stripped or len(stripped) > 120:
            return False
        if len([line for line in stripped.splitlines() if line.strip()]) > 2:
            return False
        normalized = stripped.rstrip("?!,. ").strip()
        return any(pattern.fullmatch(normalized) for pattern in _CONTINUATION_PATTERNS)

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
            labels = []
            for item in route.candidates:
                title = item.get("title") if item.get("public") else None
                labels.append(str(title or item.get("workstream_id") or "private workspace"))
            candidate_labels = "; ".join(labels) or "no trusted match"
            return ("Context confirmation required before model/tool execution. "
                    f"Reason: {route.reason}. Topics: {candidate_labels}.")
        if route.selected_workstream:
            selected = next((item for item in route.candidates
                             if item["workstream_id"] == route.selected_workstream), None)
            title = f" — {selected['title']}" if selected else ""
            if route.origin == "SESSION_CONTINUITY":
                label = "Context continuity"
            elif route.origin == "NOTEBOOK_RECOVERY":
                label = "Notebook context"
            else:
                label = "Context route"
            return (f"{label}: {route.workspace_id} | {route.decision} | "
                    f"{route.selected_workstream}{title}. {route.reason}")
        return f"Context route: {route.workspace_id} | {route.decision}. {route.reason}"
