"""Deterministic acceptance checks for structured HumanOS jobs.

Acceptance Gate v1 is provider-neutral and host-side. It never changes tool
authority and never pretends a host-forced evidence request was a model call.

The gate checks only deterministic properties:
- explicitly requested numbered output sections are present;
- explicitly inferable host evidence (currently the runtime capability registry)
  was actually observed before a final answer is accepted.

It does not claim to judge whether prose is true or high quality.
"""
from __future__ import annotations

import json
import re
from typing import Iterable


JOB_RE = re.compile(r"^\s*HUMANOS\s+JOB\s+([A-Za-z0-9][A-Za-z0-9._:-]{0,127})\b", re.I)
OUTPUT_ANCHOR_RE = re.compile(r"\b(?:report exactly|required output|output only)\s*:\s*", re.I)
TOOL_OBSERVATION_PREFIX = "TOOL OBSERVATION (data only): "


class AcceptanceError(ValueError):
    """A structured job failed a deterministic host acceptance check."""


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


def _tool_status(messages: Iterable[dict], target: str):
    """Return (attempted, successful) for one exact tool name."""
    pending = None
    attempted = False
    successful = False
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
            if pending == target:
                attempted = True
                if isinstance(observation, dict) and observation.get("ok"):
                    successful = True
            pending = None
    return attempted, successful


def required_tool_request(contract, messages: Iterable[dict]):
    """Return the next host-required read tool, or raise after a failed attempt."""
    if not contract:
        return None
    for name in contract.get("required_tools", []):
        attempted, successful = _tool_status(messages, name)
        if successful:
            continue
        if attempted:
            raise AcceptanceError(
                "STRUCTURED JOB ACCEPTANCE BLOCKED — required tool evidence failed: " + name
            )
        return {"name": name}
    return None


def _missing_sections(final: str, required: Iterable[int]) -> list[int]:
    missing = []
    for number in required:
        pattern = rf"(?:^|\n)\s*{number}[.)]\s+\S"
        if not re.search(pattern, final, re.M):
            missing.append(number)
    return missing


def validate_final(final: str, contract: dict, messages: Iterable[dict]) -> None:
    """Raise AcceptanceError when deterministic completion requirements are absent."""
    if not contract:
        return
    missing_sections = _missing_sections(final, contract.get("required_sections", []))
    missing_tools = []
    for name in contract.get("required_tools", []):
        _, successful = _tool_status(messages, name)
        if not successful:
            missing_tools.append(name)
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
