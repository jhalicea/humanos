"""HINE provider-neutral screening facade (candidate, NOT model admission).

Reuses the existing HINE cases and conservative grade() function. This
module adds NO hosted transport, secrets handling, tool permission, or
automatic registry promotion. An owner-authorized caller must supply a
bounded adapter, or enter independently collected ChatGPT responses.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from naturalization import CASES, HINE_VERSION, grade

SCHEMA = "humanos.hine.provider_screen.v0.1"
TRANSPORTS = ("OLLAMA_LOCAL", "CHATGPT_INTERACTIVE", "REMOTE_API")
MODALITIES = ("TEXT_CHAT", "VISION", "EMBEDDING", "CLASSIFIER")
EVIDENCE_LEVELS = ("PROVIDER_METADATA", "OWNER_RECORDED", "MODEL_SELF_REPORT", "UNKNOWN")
CONTEXTS = ("HARNESS_CONTROLLED", "CHAT_UNCONTROLLED", "UNKNOWN")
RESPONSE_PROVENANCE = ("CALLBACK_OBSERVED", "MANUAL_TRANSCRIPT")
SHA_SIZE = 64


class HINEContractError(ValueError):
    """Invalid evaluation data, not proof of model misbehavior."""


def _text(value, label, length=160):
    if not isinstance(value, str) or not value.strip() or len(value) > length:
        raise HINEContractError(label + " requires bounded nonempty text")
    return value


def _sha256(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"))


def validate_candidate(candidate):
    """Require exact source/profile identity without treating it as attestation."""
    required = {
        "provider", "transport", "model_label", "profile_id",
        "modality", "identity_evidence", "identity_source_ref",
        "context_control",
    }
    if not isinstance(candidate, dict) or set(candidate) != required:
        raise HINEContractError("candidate has missing or unknown identity keys")
    for name in ("provider", "model_label", "profile_id", "identity_source_ref"):
        _text(candidate[name], name)
    for key, allowed in (
        ("transport", TRANSPORTS), ("modality", MODALITIES),
        ("identity_evidence", EVIDENCE_LEVELS), ("context_control", CONTEXTS),
    ):
        if candidate[key] not in allowed:
            raise HINEContractError(key + " is unsupported")
    if candidate["transport"] == "CHATGPT_INTERACTIVE":
        if candidate["context_control"] != "CHAT_UNCONTROLLED":
            raise HINEContractError("ordinary ChatGPT sessions are not controlled harnesses")
        if candidate["identity_evidence"] == "PROVIDER_METADATA":
            raise HINEContractError("interactive ChatGPT model labels are not attested provider metadata")
    return candidate


def case_packets():
    """Public, immutable HINE question pack for *text* models only."""
    return [
        {"case_id": case.case_id, "critical": case.critical,
         "section": case.section, "prompt": case.prompt,
         "prompt_sha256": _sha256(case.prompt)}
        for case in CASES
    ]


def evaluate_provider_responses(candidate, responses, *,
                                provenance, source_ref,
                                completed_at=None):
    """Grade observed results conservatively; never auto-naturalize/admit.

    responses: case_id -> text. Only digests, not response plaintext, are
    included in the portable summary. Keep raw transcripts privately.
    """
    validate_candidate(candidate)
    if candidate["modality"] != "TEXT_CHAT":
        raise HINEContractError("text HINE is not valid for other modalities")
    if provenance not in RESPONSE_PROVENANCE:
        raise HINEContractError("unsupported response provenance")
    if candidate["transport"] == "CHATGPT_INTERACTIVE" and provenance != "MANUAL_TRANSCRIPT":
        raise HINEContractError("interactive evidence requires declared manual provenance")
    _text(source_ref, "source_ref", 240)
    if not isinstance(responses, dict):
        raise HINEContractError("responses must be a case-id mapping")
    known = {case.case_id for case in CASES}
    if not set(responses).issubset(known):
        raise HINEContractError("unexpected HINE case IDs")
    if completed_at is None:
        completed_at = datetime.now(timezone.utc).isoformat()
    else:
        _text(completed_at, "completed_at", 60)
    rows, passed, review, failed, critical_failed = [], 0, 0, 0, False
    for case in CASES:
        response = responses.get(case.case_id)
        if response is None:
            rows.append({"case_id": case.case_id, "status": "NOT_RUN",
                         "critical": case.critical,
                         "prompt_sha256": _sha256(case.prompt),
                         "response_sha256": None,
                         "reason": "No observed response"})
            continue
        _text(response, "response", 20000)
        status, reason = grade(case, response)
        passed += int(status == "PASS")
        review += int(status == "REVIEW")
        failed += int(status == "FAIL")
        critical_failed |= bool(case.critical and status == "FAIL")
        rows.append({"case_id": case.case_id, "status": status,
                     "critical": case.critical,
                     "prompt_sha256": _sha256(case.prompt),
                     "response_sha256": _sha256(response),
                     "reason": reason})
    missing = len(CASES) - (passed + review + failed)
    if critical_failed:
        screening = "QUARANTINE"
    elif missing:
        screening = "INCOMPLETE"
    else:
        screening = "HUMAN_REVIEW_REQUIRED"
    if candidate["context_control"] != "HARNESS_CONTROLLED" and screening == "HUMAN_REVIEW_REQUIRED":
        screening = "UNCONTROLLED_CONTEXT_REVIEW_REQUIRED"
    record = {
        "schema": SCHEMA, "hine_version": HINE_VERSION,
        "completed_at": completed_at, "candidate": dict(candidate),
        "provenance": provenance, "source_ref": source_ref,
        "case_results": rows,
        "summary": {
            "pass": passed, "review": review, "fail": failed,
            "not_run": missing, "critical_failed": critical_failed,
            "screening": screening,
            "qualification": "NOT_ADMITTED",
            "naturalized": False,
            "automatic_model_routing": False,
            "authority_granted": False,
            "requires_human_review": True,
            "role_competency_not_tested": True,
        },
        "limitations": [
            "Deterministic keyword-based screening is not robust adversarial proof",
            "Model identity claims may not be independently verifiable",
            "Plaintext model responses are not included; review private source evidence",
            "No tool, approval, write, release or data access authority granted",
        ],
    }
    record["record_sha256"] = _sha256(_canonical(record))
    return record


def run_provider_hine(candidate, ask, *, source_ref, timeout=45,
                      budget_calls=9):
    """Bounded adapter-injection entrypoint. No network/API client included.

    The caller supplies ask(prompt, timeout=<seconds>) returning a string.
    No caller may claim ChatGPT has a clean isolated session via this path.
    """
    validate_candidate(candidate)
    if candidate["transport"] == "CHATGPT_INTERACTIVE":
        raise HINEContractError("interactive ChatGPT uses manual, attributed response evidence")
    if candidate["modality"] != "TEXT_CHAT":
        raise HINEContractError("this battery only exercises text-chat models")
    if type(timeout) is not int or timeout < 1 or timeout > 120:
        raise HINEContractError("per-case timeout outside allowed bounds")
    if type(budget_calls) is not int or budget_calls < 1 or budget_calls > len(CASES):
        raise HINEContractError("HINE model-call budget outside allowed bounds")
    if not callable(ask):
        raise HINEContractError("caller must supply an authorized model adapter")
    observed = {}
    for case in CASES[:budget_calls]:
        try:
            reply = ask(case.prompt, timeout=timeout)
        except Exception:
            # Provider errors must not be mistaken for safe/qualified answers.
            break
        if not isinstance(reply, str) or not reply.strip():
            break
        observed[case.case_id] = reply
    return evaluate_provider_responses(
        candidate, observed, provenance="CALLBACK_OBSERVED",
        source_ref=source_ref,
    )
