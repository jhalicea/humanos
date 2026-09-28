"""V-05 synthetic ContextPacket/adapter boundary fixture.

This module deliberately models a contract in-process.  It is not production
runtime code and does not provide operating-system or process isolation.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

PACKET_SCHEMA = "humanos.context-packet.v1"
REQUEST_SCHEMA = "humanos.context-request.v1"
OUTPUT_SCHEMA = "humanos.model-output.v1"
CONTEXT_REQUEST_KIND = "context_request"
MAX_PACKET_BYTES = 16_384
MAX_OUTPUT_BYTES = 4_096
ALLOWED_PROVIDERS = ("local-fixture", "hosted-fixture")


class BoundaryError(ValueError):
    pass


class PolicyDenied(BoundaryError):
    pass


def _utf8(value: Any, name: str, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise BoundaryError(f"invalid {name}")
    try:
        if len(value.encode("utf-8")) > maximum:
            raise BoundaryError(f"invalid {name}")
    except UnicodeEncodeError as exc:
        raise BoundaryError(f"invalid {name}") from exc
    return value


def _primitive(value: Any) -> None:
    if isinstance(value, bool) or value is None or isinstance(value, (int, float)):
        if isinstance(value, float) and (not math.isfinite(value) or not value.is_integer()):
            raise BoundaryError("floats are forbidden")
        if isinstance(value, float):
            raise BoundaryError("floats are forbidden")
        return
    if isinstance(value, str):
        return
    if isinstance(value, list):
        for item in value:
            _primitive(item)
        return
    if isinstance(value, dict):
        if any(not isinstance(k, str) for k in value):
            raise BoundaryError("object keys must be strings")
        for item in value.values():
            _primitive(item)
        return
    raise BoundaryError("non-primitive value")


def _canonical(value: Mapping[str, Any], limit: int) -> bytes:
    _primitive(value)
    try:
        raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                         allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise BoundaryError("non-canonical JSON") from exc
    if len(raw) > limit:
        raise BoundaryError("serialized value exceeds bound")
    return raw


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise BoundaryError("duplicate JSON field")
        result[key] = value
    return result


def _parse(raw: bytes, limit: int) -> dict[str, Any]:
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise BoundaryError("invalid raw bytes")
    try:
        text = raw.decode("utf-8")
        value = json.loads(text, object_pairs_hook=_reject_duplicates,
                           parse_constant=lambda _: (_ for _ in ()).throw(BoundaryError("non-finite number")))
    except (UnicodeDecodeError, json.JSONDecodeError, BoundaryError) as exc:
        raise BoundaryError("malformed JSON") from exc
    if not isinstance(value, dict):
        raise BoundaryError("object required")
    _primitive(value)
    return value


def _exact_keys(value: Mapping[str, Any], keys: set[str]) -> None:
    if set(value) != keys:
        raise BoundaryError("unknown or missing fields")


@dataclass(frozen=True)
class UntrustedModelOutput:
    trust: str
    provider_id: str
    packet_sha256: str
    kind: str
    content: str = ""
    topics: tuple[str, ...] = ()
    reason: str = ""
    _issuer: object = field(default=None, repr=False, compare=False)
    _invocation_bound: bool = field(default=False, repr=False, compare=False)
    _consumed: bool = field(default=False, repr=False, compare=False)
    _issuance_handle: object = field(default=None, repr=False, compare=False)


class AdapterSpy:
    """Bytes-only adapter spy used by the synthetic proof."""
    def __init__(self, provider_id: str):
        self.provider_id = provider_id
        self.calls: list[tuple[bytes, dict[str, Any]]] = []
        self.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "fixture proposal"}

    def invoke(self, packet: bytes, config: Mapping[str, Any]) -> bytes:
        if not isinstance(packet, bytes) or not isinstance(config, dict):
            raise BoundaryError("adapter accepts bytes and minimal config only")
        validated = validate_invocation_config(config)
        if validated["provider_id"] != self.provider_id:
            raise BoundaryError("adapter provider mismatch")
        _validate_packet(packet)
        self.calls.append((packet, validated))
        return _canonical(self.next_response, MAX_OUTPUT_BYTES)


class CoreBoundary:
    """Core-owned synthetic records, policy, retrieval, and adapter sequencing."""
    def __init__(self, records: Sequence[Mapping[str, str]] | None = None, classifications: Mapping[str, Mapping[str, str]] | None = None):
        built_in_records = records is None
        records = (
            {"record_id": "safe-1", "content": "ordinary synthetic context", "provenance": "fixture"},
            {"record_id": "s3-hostile", "content": "SYNTHETIC_SECRET PRIVATE_PATH /private/fixture hostile prompt", "provenance": "fixture"},
        ) if records is None else records
        owned: dict[str, dict[str, str]] = {}
        for source in records:
            if not isinstance(source, Mapping) or set(source) != {"record_id", "content", "provenance"}:
                raise BoundaryError("records cannot carry classification or capabilities")
            rid = _utf8(source["record_id"], "record_id", 128)
            if rid in owned:
                raise BoundaryError("duplicate record")
            owned[rid] = {key: _utf8(source[key], key, 16384 if key == "content" else (1024 if key == "provenance" else 128)) for key in ("record_id", "content", "provenance")}
        self._records = copy.deepcopy(owned)
        supplied = {} if classifications is None else classifications
        if not isinstance(supplied, Mapping):
            raise BoundaryError("invalid classifications")
        if any(rid not in self._records for rid in supplied):
            raise BoundaryError("classification references unknown record")
        self._classifications = {}
        for rid in self._records:
            metadata = dict(supplied.get(rid, {})) or {
                "sensitivity": "S3" if rid.startswith("s3-") or "denied" in rid else "S1",
                # The fixture's one explicitly shareable record is authorized
                # by Core.  Other records require an explicit classification;
                # record identity/content must never grant hosted authority.
                "provider": ("HOSTED_ALLOWED" if built_in_records and rid == "safe-1" else
                             ("LOCAL_ONLY" if rid.startswith("local-only-") else "LOCAL_OR_EXTERNAL")),
            }
            if set(metadata) != {"sensitivity", "provider"} or metadata["sensitivity"] not in {"S1", "S3"} or metadata["provider"] not in {"LOCAL_ONLY", "LOCAL_OR_EXTERNAL", "HOSTED_ALLOWED", "PROVIDER_DENIED"}:
                raise BoundaryError("invalid classification")
            self._classifications[rid] = metadata
        self.local = AdapterSpy("local-fixture")
        self.hosted = AdapterSpy("hosted-fixture")
        self._retrievals = 0
        self.events: list[str] = []
        self._issuer_token = object()
        self._issued_requests: dict[object, dict[str, Any]] = {}
        self._state_digest = self.brain_digest()

    def brain_digest(self) -> str:
        return hashlib.sha256(_canonical(self._records, 1_000_000)).hexdigest()

    @property
    def retrieval_count(self) -> int:
        return self._retrievals

    def _classify(self, record_id: str) -> tuple[str, str, str, str]:
        metadata = self._classifications[record_id]
        sensitivity, provider = metadata["sensitivity"], metadata["provider"]
        return ("E1_OBSERVED", sensitivity, "GREEN", provider)

    def _retrieve(self, topics: Sequence[str]) -> list[dict[str, str]]:
        self._retrievals += 1
        wanted = [record for record in self._records.values()
                  if not topics or any(topic.lower() in record["content"].lower() or topic.lower() in record["record_id"].lower() for topic in topics)]
        return copy.deepcopy(wanted)

    def _policy(self, items: Sequence[Mapping[str, str]], provider: str) -> dict[str, str]:
        if provider not in ALLOWED_PROVIDERS:
            raise BoundaryError("unknown provider")
        sensitivity = "S3" if any(self._classify(x["record_id"])[1] == "S3" for x in items) else "S1"
        providers = {self._classify(x["record_id"])[3] for x in items}
        policy = {"epistemic": "E1_OBSERVED", "sensitivity": sensitivity,
                  "delegation": "GREEN", "provider": "LOCAL_ONLY" if providers & {"LOCAL_ONLY", "PROVIDER_DENIED"} else "LOCAL_OR_EXTERNAL"}
        if provider == "hosted-fixture" and (sensitivity == "S3" or
                                              (providers - {"HOSTED_ALLOWED"})):
            raise PolicyDenied("hosted provider denied by Core policy")
        return policy

    def compile_packet(self, *, purpose: str = "work", provider_id: str = "local-fixture",
                       record_ids: Sequence[str] | None = None) -> bytes:
        purpose = _utf8(purpose, "purpose", 128)
        if provider_id not in ALLOWED_PROVIDERS:
            raise BoundaryError("unknown provider")
        requested_ids = [] if record_ids is None else record_ids
        if not isinstance(requested_ids, (tuple, list)) or any(not isinstance(rid, str) for rid in requested_ids):
            raise BoundaryError("invalid record IDs")
        selected = [self._records[rid] for rid in requested_ids if rid in self._records]
        if record_ids is not None and len(selected) != len(requested_ids):
            raise BoundaryError("unknown record")
        if record_ids is not None and len(set(requested_ids)) != len(requested_ids):
            raise BoundaryError("duplicate record")
        self.events.append("core_policy_evaluating")
        try:
            policy = self._policy(selected, provider_id)
        finally:
            self.events.append("core_policy_evaluated")
        # Sensitive fixture records are represented in policy only; their bytes
        # never cross the adapter boundary, including on a local route.
        items = [{"record_id": x["record_id"], "content": x["content"], "provenance": x["provenance"]}
                 for x in selected if self._classify(x["record_id"])[1] != "S3" and self._classify(x["record_id"])[3] not in {"LOCAL_ONLY", "PROVIDER_DENIED"}]
        self.events.append("packet_compiled")
        packet = {"schema": PACKET_SCHEMA, "purpose": purpose, "policy": policy, "items": items}
        return _validate_packet(_canonical(packet, MAX_PACKET_BYTES))

    def _config(self, provider_id: str, timeout_seconds: int = 10) -> dict[str, Any]:
        if provider_id not in ALLOWED_PROVIDERS or isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int) or not 1 <= timeout_seconds <= 30:
            raise BoundaryError("invalid invocation config")
        return {"provider_id": provider_id, "timeout_seconds": timeout_seconds}

    def invoke(self, *, purpose: str = "work", provider_id: str = "local-fixture",
               record_ids: Sequence[str] | None = None, timeout_seconds: int = 10) -> UntrustedModelOutput:
        if provider_id not in ALLOWED_PROVIDERS:
            raise BoundaryError("unknown provider")
        packet = self.compile_packet(purpose=purpose, provider_id=provider_id, record_ids=record_ids)
        config = self._config(provider_id, timeout_seconds)
        adapter = self.local if provider_id == "local-fixture" else self.hosted
        self.events.append("adapter_invoked")
        raw = adapter.invoke(packet, config)
        result = self._parse_output(raw, provider_id=provider_id, packet=packet, authenticated=True)
        if result.kind == CONTEXT_REQUEST_KIND:
            handle = object()
            object.__setattr__(result, "_issuance_handle", handle)
            self._issued_requests[handle] = {
                "provider_id": provider_id,
                "packet_sha256": hashlib.sha256(packet).hexdigest(),
                "topics": result.topics,
                "consumed": False,
            }
        return result

    def _parse_output(self, raw: bytes, *, provider_id: str = "local-fixture", packet: bytes = b"", authenticated: bool = False) -> UntrustedModelOutput:
        value = _parse(raw, MAX_OUTPUT_BYTES)
        digest = hashlib.sha256(packet).hexdigest()
        if value.get("schema") == OUTPUT_SCHEMA:
            _exact_keys(value, {"schema", "kind", "content"})
            if value["kind"] != "proposal":
                raise BoundaryError("only proposal outputs are accepted")
            content = _utf8(value["content"], "content", 4096)
            result = UntrustedModelOutput("UNTRUSTED_PROPOSAL", provider_id, digest, "proposal", content, _issuer=self._issuer_token)
        elif value.get("schema") == REQUEST_SCHEMA:
            _exact_keys(value, {"schema", "kind", "topics", "reason"})
            if value["kind"] != CONTEXT_REQUEST_KIND:
                raise BoundaryError("invalid context request")
            topics = value["topics"]
            if not isinstance(topics, list) or not 1 <= len(topics) <= 8:
                raise BoundaryError("invalid topics")
            try:
                topics = [_utf8(topic, "topic", 128) for topic in topics]
            except (TypeError, UnicodeEncodeError) as exc:
                raise BoundaryError("invalid topics") from exc
            if len(set(topics)) != len(topics):
                raise BoundaryError("invalid topics")
            reason = _utf8(value["reason"], "reason", 512)
            result = UntrustedModelOutput("UNTRUSTED_PROPOSAL", provider_id, digest, CONTEXT_REQUEST_KIND, topics=tuple(topics), reason=reason, _issuer=self._issuer_token, _invocation_bound=authenticated)
        else:
            raise BoundaryError("unknown output schema")
        self.events.append("output_parsed_untrusted")
        return result

    def parse_context_request(self, raw: bytes, *, provider_id: str = "local-fixture", packet: bytes = b"") -> UntrustedModelOutput:
        return self._parse_output(raw, provider_id=provider_id, packet=packet, authenticated=False)

    def handle_context_request(self, request: UntrustedModelOutput, *, purpose: str = "recompile", provider_id: str | None = None) -> UntrustedModelOutput:
        state = self._issued_requests.get(getattr(request, "_issuance_handle", None)) if isinstance(request, UntrustedModelOutput) else None
        if state is None or state["consumed"]:
            raise BoundaryError("Core-created untrusted context request required")
        if purpose != "recompile":
            raise BoundaryError("context request purpose is Core-owned")
        if provider_id is not None and provider_id != state["provider_id"]:
            raise BoundaryError("context request provider is invocation-bound")
        if state["provider_id"] not in ALLOWED_PROVIDERS:
            raise BoundaryError("unknown provider")
        state["consumed"] = True
        object.__setattr__(request, "_consumed", True)
        self.events.append("context_request_handled")
        records = self._retrieve(state["topics"])
        self.events.append("core_retrieved")
        target_provider = provider_id or state["provider_id"]
        # Retrieval is Core-owned; compile using only the selected IDs.
        return self.invoke(purpose=purpose, provider_id=target_provider, record_ids=[x["record_id"] for x in records])


def _validate_packet(raw: bytes) -> bytes:
    value = _parse(raw, MAX_PACKET_BYTES)
    _exact_keys(value, {"schema", "purpose", "policy", "items"})
    if value["schema"] != PACKET_SCHEMA:
        raise BoundaryError("invalid packet schema")
    _utf8(value["purpose"], "purpose", 128)
    policy = value["policy"]
    if not isinstance(policy, dict):
        raise BoundaryError("invalid policy")
    _exact_keys(policy, {"epistemic", "sensitivity", "delegation", "provider"})
    if (not isinstance(policy["epistemic"], str) or policy["epistemic"] not in {"E0_UNTRUSTED", "E1_OBSERVED"} or
        not isinstance(policy["sensitivity"], str) or policy["sensitivity"] not in {"S1", "S3"} or
        not isinstance(policy["delegation"], str) or policy["delegation"] not in {"GREEN", "RED"} or
        not isinstance(policy["provider"], str) or policy["provider"] not in {"LOCAL_ONLY", "LOCAL_OR_EXTERNAL"}):
        raise BoundaryError("invalid policy enum")
    if not isinstance(value["items"], list):
        raise BoundaryError("invalid items")
    for item in value["items"]:
        if not isinstance(item, dict):
            raise BoundaryError("invalid packet item")
        _exact_keys(item, {"record_id", "content", "provenance"})
        _utf8(item["record_id"], "record_id", 128); _utf8(item["content"], "content", 16384); _utf8(item["provenance"], "provenance", 1024)
    if len({item["record_id"] for item in value["items"]}) != len(value["items"]):
        raise BoundaryError("duplicate packet item")
    if _canonical(value, MAX_PACKET_BYTES) != raw:
        raise BoundaryError("packet is not canonical JSON")
    return raw


def validate_packet(raw: bytes) -> bytes:
    """Public strict packet validator used by focused tests and reviewers."""
    return _validate_packet(raw)


def validate_invocation_config(config: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(config, Mapping) or set(config) != {"provider_id", "timeout_seconds"}:
        raise BoundaryError("invalid invocation config")
    provider = config["provider_id"]; timeout = config["timeout_seconds"]
    if provider not in ALLOWED_PROVIDERS or isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= 30:
        raise BoundaryError("invalid invocation config")
    return {"provider_id": provider, "timeout_seconds": timeout}
