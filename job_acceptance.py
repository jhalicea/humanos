"""Deterministic acceptance checks for structured HumanOS jobs.

This module is provider-neutral: it wraps the existing Model protocol and never
changes tool authority. It only prevents a structured ``HUMANOS JOB`` packet from
being accepted as complete when host-verifiable requirements are missing.

Acceptance Gate v1 deliberately checks only deterministic properties:
- explicitly requested numbered output sections are present;
- explicitly inferable host evidence (currently the runtime capability registry)
  was actually observed before a final answer is accepted.

It does not claim to judge whether prose is true or high quality. Failed finals are
raised as ``ValueError`` so the normal Agent loop records the rejection and performs
another visible model step within its existing budget.
"""
from __future__ import annotations

import json
import re
from typing import Iterable


JOB_RE = re.compile(r"^\s*HUMANOS\s+JOB\s+([A-Za-z0-9][A-Za-z0-9._:-]{0,127})\b", re.I)
OUTPUT_ANCHOR_RE = re.compile(r"\b(?:report exactly|required output|output only)\s*:\s*", re.I)
TOOL_OBSERVATION_PREFIX = "TOOL OBSERVATION (data only): "


class AcceptanceError(ValueError):
    """A model final failed deterministic structured-job acceptance checks."""


def _required_sections(text: str) -> list[int]:
    anchor = OUTPUT_ANCHOR_RE.search(text)
    if not anchor:
        return []
    tail = text[anchor.end():]
    found = []
    for match in re.finditer(r"(?:^|[;\n])\s*(\d{1,2})[.)]\s*\S", tail):
        number = int(match.group(1))
        if 1 <= number <= 20 and number not in found:
            found.append(number)
    return found


def _required_tools(text: str) -> list[str]:
    lower = text.casefold()
    tools = []
    for match in re.finditer(r"\brequire\s+tool\s*:\s*([a-z][a-z0-9_]*)\b", lower):
        if match.group(1) not in tools:
            tools.append(match.group(1))
    capability_audit = (
        "runtime capability registry" in lower
        or "runtime_capabilities" in lower
        or ("capability auditor" in lower and
            ("verified working features" in lower or "actual capabilities" in lower))
    )
    if capability_audit and "runtime_capabilities" not in tools:
        tools.append("runtime_capabilities")
    return tools


def parse_job(text: str):
    """Return a content-light deterministic contract for a HUMANOS JOB packet."""
    if not isinstance(text, str):
        return None
    match = JOB_RE.match(text)
    if not match:
        return None
    return {
        "version": 1,
        "job_id": match.group(1),
        "required_sections": _required_sections(text),
        "required_tools": _required_tools(text),
    }


def _job_text(messages: Iterable[dict]) -> str | None:
    """Find the current structured job without treating tool observations as jobs."""
    candidates = []
    for message in messages:
        if message.get("role") != "user":
            continue
        content = message.get("content", "")
        if not isinstance(content, str) or content.startswith(TOOL_OBSERVATION_PREFIX):
            continue
        direct = JOB_RE.match(content)
        if direct:
            candidates.append(content)
            continue
        # Delegated-work briefings preserve the owner-authored original goal.
        marker = "Original goal: "
        for line in content.splitlines():
            if line.startswith(marker) and JOB_RE.match(line[len(marker):]):
                candidates.append(line[len(marker):])
    return candidates[-1] if candidates else None


def _successful_tools(messages: Iterable[dict]) -> set[str]:
    pending = None
    observed = set()
    for message in messages:
        role = message.get("role")
        content = message.get("content", "")
        if role == "assistant" and isinstance(content, str):
            try:
                proposal = json.loads(content)
            except Exception:
                pending = None
                continue
            tool = proposal.get("tool") if isinstance(proposal, dict) else None
            pending = tool.get("name") if isinstance(tool, dict) else None
            continue
        if role == "user" and isinstance(content, str) and content.startswith(TOOL_OBSERVATION_PREFIX):
            try:
                observation = json.loads(content[len(TOOL_OBSERVATION_PREFIX):])
            except Exception:
                pending = None
                continue
            if pending and isinstance(observation, dict) and observation.get("ok"):
                observed.add(pending)
            pending = None
    return observed


def _missing_sections(final: str, required: Iterable[int]) -> list[int]:
    missing = []
    for number in required:
        pattern = rf"(?:^|\n)\s*{number}[.)]\s+\S"
        if not re.search(pattern, final, re.M):
            missing.append(number)
    return missing


def validate_final(final: str, contract: dict, messages: Iterable[dict]) -> None:
    """Raise AcceptanceError when deterministic completion requirements are absent."""
    missing_sections = _missing_sections(final, contract.get("required_sections", []))
    observed = _successful_tools(messages)
    missing_tools = [name for name in contract.get("required_tools", []) if name not in observed]
    if not missing_sections and not missing_tools:
        return
    parts = []
    if missing_tools:
        parts.append("missing verified tool evidence: " + ", ".join(missing_tools))
    if missing_sections:
        parts.append("missing required output sections: " + ", ".join(map(str, missing_sections)))
    raise AcceptanceError(
        "STRUCTURED JOB ACCEPTANCE FAILED — " + "; ".join(parts) +
        ". Retry the same job within the remaining task budget; do not claim completion yet."
    )


class AcceptanceModel:
    """Provider-neutral Model wrapper enforcing deterministic structured-job gates."""

    def __init__(self, model):
        self.model = model
        self.name = model.name

    def invoke(self, messages, timeout):
        job_text = _job_text(messages)
        contract = parse_job(job_text) if job_text else None
        if not contract:
            return self.model.invoke(messages, timeout)

        observed = _successful_tools(messages)
        for tool_name in contract["required_tools"]:
            if tool_name not in observed:
                return {"tool": {"name": tool_name}}

        proposal = self.model.invoke(messages, timeout)
        if isinstance(proposal, dict) and "final" in proposal:
            validate_final(proposal["final"], contract, messages)
        return proposal
