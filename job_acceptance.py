"""Deterministic acceptance checks for structured HumanOS jobs.

Acceptance Gate v1 is provider-neutral and host-side. It never changes tool
authority and never pretends a host-forced evidence request was a model call.

The gate checks only deterministic properties:
- explicitly requested numbered output sections are present;
- explicitly inferable host evidence (currently the runtime capability registry)
  was actually verified by the HumanOS tool gateway before a final is accepted.

It does not claim to judge whether prose is true or high quality. Evidence status
is supplied by the host Agent, never reconstructed from model-authored text.
"""
from __future__ import annotations

import re
from typing import Iterable


JOB_RE = re.compile(r"^\s*HUMANOS\s+JOB\s+([A-Za-z0-9][A-Za-z0-9._:-]{0,127})\b", re.I)
OUTPUT_ANCHOR_RE = re.compile(r"\b(?:report exactly|required output|output only)\s*:\s*", re.I)
EVIDENCE_STATES = frozenset({"VERIFIED", "FAILED"})


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


def validate_evidence_state(evidence) -> dict:
    if evidence is None:
        return {}
    if not isinstance(evidence, dict):
        raise AcceptanceError("Structured job evidence state is invalid")
    clean = {}
    for name, status in evidence.items():
        if not isinstance(name, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise AcceptanceError("Structured job evidence contains an invalid tool name")
        if status not in EVIDENCE_STATES:
            raise AcceptanceError("Structured job evidence contains an invalid status")
        clean[name] = status
    return clean


def required_tool_request(contract, evidence=None):
    """Return the next required read tool, or raise when required evidence failed."""
    if not contract:
        return None
    evidence = validate_evidence_state(evidence)
    for name in contract.get("required_tools", []):
        status = evidence.get(name)
        if status == "VERIFIED":
            continue
        if status == "FAILED":
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


def validate_final(final: str, contract: dict, evidence=None) -> None:
    """Raise AcceptanceError when deterministic completion requirements are absent."""
    if not contract:
        return
    evidence = validate_evidence_state(evidence)
    missing_sections = _missing_sections(final, contract.get("required_sections", []))
    missing_tools = [name for name in contract.get("required_tools", [])
                     if evidence.get(name) != "VERIFIED"]
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
