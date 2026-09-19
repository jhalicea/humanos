"""Deterministic outbound privacy firewall for HumanOS FRIEND packets.

The firewall is intentionally narrow:
- it does not dispatch work;
- it does not grant authority;
- it does not infer identity with an LLM;
- it either rejects external disclosure or returns a sanitized copy plus findings.

FRIEND packets remain DATA_ONLY and PROPOSAL_UNVERIFIED under execution_contracts.
"""
from __future__ import annotations

import copy
import re
from dataclasses import dataclass

from execution_contracts import ContractError, validate_friend_packet


EXTERNAL_ALLOWED_PRIVACY = frozenset({"PUBLIC", "INTERNAL"})
EXTERNAL_BLOCKED_PRIVACY = frozenset({"CONFIDENTIAL", "RESTRICTED", "LOCAL_ONLY"})

_TEXT_FIELDS = (
    "worker_role",
    "task",
    "expected_output",
)
_LIST_FIELDS = (
    "known_evidence",
    "constraints",
    "unknown_do_not_assume",
    "allowed_scope",
    "prohibited_actions",
    "acceptance_criteria",
    "verification_required",
)

_REDACTIONS = (
    (
        "PRIVATE_KEY",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----", re.I | re.S),
        "[PRIVATE_KEY_REDACTED]",
    ),
    (
        "KNOWN_TOKEN",
        re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{12,}|AKIA[0-9A-Z]{16})\b"),
        "[SECRET_REDACTED]",
    ),
    (
        "LABELED_SECRET",
        re.compile(
            r"(?i)\b(api[_ -]?key|access[_ -]?token|auth[_ -]?token|password|passwd|secret)\b"
            r"(\s*[:=]\s*)([^\s,;]{6,})"
        ),
        None,
    ),
    (
        "EMAIL",
        re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9.-])"),
        "[EMAIL_REDACTED]",
    ),
    (
        "SSN",
        re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
        "[SSN_REDACTED]",
    ),
    (
        "PHONE",
        re.compile(r"(?<!\d)(?:\+?1[ .-]?)?\(?\d{3}\)?[ .-]\d{3}[ .-]\d{4}(?!\d)"),
        "[PHONE_REDACTED]",
    ),
    (
        "MAC_HOME_PATH",
        re.compile(r"(?<![A-Za-z0-9_])/(?:Users|home)/[^/\s]+(?:/[^\s,;]*)?"),
        "[LOCAL_PATH_REDACTED]",
    ),
    (
        "WINDOWS_HOME_PATH",
        re.compile(r"(?i)(?<![A-Za-z0-9_])[A-Z]:\\Users\\[^\\\s]+(?:\\[^\s,;]*)?"),
        "[LOCAL_PATH_REDACTED]",
    ),
)

_AUTHORITY_LANGUAGE = re.compile(
    r"(?i)\b(?:ignore|override|disregard|replace|bypass)\b.{0,40}"
    r"\b(?:system|developer|policy|constitution|instructions?|authority|approval|guardrail|safety)\b"
)


class PrivacyFirewallError(ContractError):
    """Base class for FRIEND export privacy failures."""


class ExternalDisclosureBlocked(PrivacyFirewallError):
    """Raised when packet classification forbids external disclosure."""


class ResidualSensitiveDataError(PrivacyFirewallError):
    """Raised when a sanitized packet still appears to contain blocked data."""


@dataclass(frozen=True)
class Finding:
    category: str
    field: str
    count: int
    action: str


@dataclass(frozen=True)
class SanitizedFriendPacket:
    packet: dict
    findings: tuple[Finding, ...]
    destination: str
    changed: bool


def _redact_labeled_secret(match):
    label = match.group(1)
    separator = match.group(2)
    return f"{label}{separator}[SECRET_REDACTED]"


def _sanitize_text(text, field):
    findings = []
    result = text
    for category, pattern, replacement in _REDACTIONS:
        if category == "LABELED_SECRET":
            result, count = pattern.subn(_redact_labeled_secret, result)
        else:
            result, count = pattern.subn(replacement, result)
        if count:
            findings.append(Finding(category, field, count, "REDACTED"))

    authority_count = len(_AUTHORITY_LANGUAGE.findall(result))
    if authority_count:
        # Preserve the text as evidence, but make the trust boundary explicit in
        # the audit result. execution_contracts separately enforces DATA_ONLY.
        findings.append(Finding(
            "AUTHORITY_LANGUAGE",
            field,
            authority_count,
            "PRESERVED_AS_DATA_ONLY",
        ))
    return result, findings


def _sanitize_packet_copy(packet):
    clean = copy.deepcopy(packet)
    findings = []

    for field in _TEXT_FIELDS:
        clean[field], observed = _sanitize_text(clean[field], field)
        findings.extend(observed)

    for field in _LIST_FIELDS:
        values = []
        for index, value in enumerate(clean[field]):
            sanitized, observed = _sanitize_text(value, f"{field}[{index}]")
            values.append(sanitized)
            findings.extend(observed)
        clean[field] = values

    paths = []
    for index, value in enumerate(clean["ownership"]["paths"]):
        sanitized, observed = _sanitize_text(value, f"ownership.paths[{index}]")
        paths.append(sanitized)
        findings.extend(observed)
    clean["ownership"]["paths"] = paths

    return clean, findings


def _blocked_residuals(packet):
    """Return residual hard-secret categories after sanitization."""
    residual = []
    values = []
    for field in _TEXT_FIELDS:
        values.append((field, packet[field]))
    for field in _LIST_FIELDS:
        values.extend((f"{field}[{index}]", value) for index, value in enumerate(packet[field]))
    values.extend(
        (f"ownership.paths[{index}]", value)
        for index, value in enumerate(packet["ownership"]["paths"])
    )

    hard_categories = {"PRIVATE_KEY", "KNOWN_TOKEN", "LABELED_SECRET"}
    for field, value in values:
        for category, pattern, _replacement in _REDACTIONS:
            if category not in hard_categories:
                continue
            if category == "LABELED_SECRET":
                # A successful redaction intentionally preserves the label and
                # separator (for useful context) while replacing only the value.
                # Do not mistake our own sentinel for a surviving credential.
                for match in pattern.finditer(value):
                    if match.group(3) != "[SECRET_REDACTED]":
                        residual.append((field, category))
                        break
                continue
            if pattern.search(value):
                residual.append((field, category))
    return residual


def sanitize_friend_packet(packet, destination="EXTERNAL", work_order=None):
    """Return a validated sanitized FRIEND packet or fail closed.

    LOCAL destination validates the contract but does not alter packet content.
    EXTERNAL destination permits only PUBLIC/INTERNAL packets and applies
    deterministic redaction to user-controlled text. CONFIDENTIAL, RESTRICTED,
    and LOCAL_ONLY packets are rejected rather than downgraded silently.
    """
    validate_friend_packet(packet, work_order)
    destination = destination.upper()
    if destination not in {"LOCAL", "EXTERNAL"}:
        raise PrivacyFirewallError("destination must be LOCAL or EXTERNAL")

    if destination == "LOCAL":
        return SanitizedFriendPacket(
            packet=copy.deepcopy(packet),
            findings=(),
            destination="LOCAL",
            changed=False,
        )

    privacy = packet["privacy_classification"]
    if privacy in EXTERNAL_BLOCKED_PRIVACY:
        raise ExternalDisclosureBlocked(
            f"FRIEND packet privacy class {privacy} is not eligible for external disclosure")
    if privacy not in EXTERNAL_ALLOWED_PRIVACY:
        raise ExternalDisclosureBlocked(
            f"FRIEND packet privacy class {privacy} has no external disclosure policy")

    clean, findings = _sanitize_packet_copy(packet)
    clean["content_authority"] = "DATA_ONLY"
    clean["output_trust"] = "PROPOSAL_UNVERIFIED"
    validate_friend_packet(clean, work_order)

    residual = _blocked_residuals(clean)
    if residual:
        detail = ", ".join(f"{field}:{category}" for field, category in residual)
        raise ResidualSensitiveDataError(
            "sanitization left residual sensitive data; external disclosure blocked: " + detail)

    return SanitizedFriendPacket(
        packet=clean,
        findings=tuple(findings),
        destination="EXTERNAL",
        changed=clean != packet,
    )


def external_export_ready(packet, work_order=None):
    """Fail-closed convenience check for future dispatchers."""
    return sanitize_friend_packet(packet, destination="EXTERNAL", work_order=work_order)
