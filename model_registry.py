"""HumanOS model registry.

Separates an intelligence/model identity from the runtime profile used to invoke
it. Qualification evidence attaches to both identities so aliases and modified
Ollama profiles are not mistaken for independent intelligences.

The registry is descriptive only: it does not authorize, naturalize, route,
or promote a model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class ModelIdentity:
    model_id: str
    provider: str
    family: str
    architecture: str | None = None
    parameter_count: str | None = None
    quantization: str | None = None
    weights_digest: str | None = None
    license: str | None = None
    capabilities: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RuntimeProfile:
    profile_id: str
    model_id: str
    runtime: str
    configured_name: str
    endpoint: str | None = None
    context_window: int | None = None
    temperature: float | None = None
    max_output_tokens: int | None = None
    system_prompt_digest: str | None = None
    parser: str | None = None
    renderer: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class QualificationRef:
    qualification_id: str
    model_id: str
    profile_id: str
    framework: str
    framework_version: str
    status: str
    evidence_path: str | None = None
    evidence_digest: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """Fail-closed descriptive registry for models, profiles and evidence."""

    def __init__(self) -> None:
        self.models: dict[str, ModelIdentity] = {}
        self.profiles: dict[str, RuntimeProfile] = {}
        self.qualifications: dict[str, QualificationRef] = {}

    def register_model(self, model: ModelIdentity) -> None:
        existing = self.models.get(model.model_id)
        if existing is not None and existing != model:
            raise ValueError(f"model identity collision: {model.model_id}")
        self.models[model.model_id] = model

    def register_profile(self, profile: RuntimeProfile) -> None:
        if profile.model_id not in self.models:
            raise KeyError(f"unknown model: {profile.model_id}")
        existing = self.profiles.get(profile.profile_id)
        if existing is not None and existing != profile:
            raise ValueError(f"profile identity collision: {profile.profile_id}")
        self.profiles[profile.profile_id] = profile

    def attach_qualification(self, qualification: QualificationRef) -> None:
        if qualification.model_id not in self.models:
            raise KeyError(f"unknown model: {qualification.model_id}")
        profile = self.profiles.get(qualification.profile_id)
        if profile is None:
            raise KeyError(f"unknown profile: {qualification.profile_id}")
        if profile.model_id != qualification.model_id:
            raise ValueError("qualification model/profile mismatch")
        existing = self.qualifications.get(qualification.qualification_id)
        if existing is not None and existing != qualification:
            raise ValueError(f"qualification identity collision: {qualification.qualification_id}")
        self.qualifications[qualification.qualification_id] = qualification

    def profiles_for_model(self, model_id: str) -> list[RuntimeProfile]:
        return [p for p in self.profiles.values() if p.model_id == model_id]

    def qualifications_for_profile(self, profile_id: str) -> list[QualificationRef]:
        return [q for q in self.qualifications.values() if q.profile_id == profile_id]

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "humanos.model_registry.v1",
            "models": [asdict(x) for x in self.models.values()],
            "profiles": [asdict(x) for x in self.profiles.values()],
            "qualifications": [asdict(x) for x in self.qualifications.values()],
            "policy": {
                "descriptive_only": True,
                "automatic_naturalization": False,
                "automatic_routing": False,
                "human_promotion_required": True,
            },
        }


def model_id_from_ollama(*, family: str, weights_digest: str | None, quantization: str | None) -> str:
    """Stable-enough local identity: aliases sharing weights map to one model."""
    digest = (weights_digest or "unknown").replace("sha256:", "")[:16]
    quant = (quantization or "unknown").lower()
    return f"ollama:{family.lower()}:{digest}:{quant}"


def profile_id_from_name(configured_name: str) -> str:
    return "ollama-profile:" + configured_name.strip().lower()
