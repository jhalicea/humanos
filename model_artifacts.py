from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Callable, Mapping, Optional, Sequence

SCHEMA_VERSION = 1
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REVISION_RE = re.compile(r"^[0-9a-f]{40,64}$")
MODEL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
ALLOWED_KINDS = frozenset({"weights", "tokenizer", "config", "runtime"})
ALLOWED_STATUSES = frozenset({"candidate", "qualified", "approved", "blocked"})


class ModelArtifactError(Exception):
    """Base error for the isolated model artifact subsystem."""


class RegistryError(ModelArtifactError):
    pass


class ManifestError(ModelArtifactError):
    pass


class IntegrityError(ModelArtifactError):
    pass


class DownloadPolicyError(ModelArtifactError):
    pass


@dataclass(frozen=True)
class RegistryEntry:
    model_id: str
    status: str
    source_revision: str
    manifest_url: str
    manifest_size: int
    manifest_sha256: str
    allowed_hosts: tuple[str, ...]


@dataclass(frozen=True)
class ArtifactSpec:
    name: str
    kind: str
    url: str
    size: int
    sha256: str


@dataclass(frozen=True)
class ModelManifest:
    model_id: str
    source_revision: str
    runtime_family: str
    artifacts: tuple[ArtifactSpec, ...]


@dataclass(frozen=True)
class DownloadResult:
    model_id: str
    source_revision: str
    model_dir: Path
    reused_cache: bool
    artifact_count: int
    total_bytes: int


def _require_exact_keys(value: Mapping[str, object], required: set[str], where: str) -> None:
    actual = set(value)
    if actual != required:
        missing = sorted(required - actual)
        extra = sorted(actual - required)
        raise ValueError(f"{where} keys invalid; missing={missing}, extra={extra}")


def _require_int(value: object, where: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{where} must be an integer >= {minimum}")
    return value


def _require_str(value: object, where: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where} must be a non-empty string")
    return value


def _validate_model_id(value: object, where: str = "model_id") -> str:
    model_id = _require_str(value, where)
    if not MODEL_ID_RE.fullmatch(model_id):
        raise ValueError(f"{where} is invalid")
    return model_id


def _validate_revision(value: object, where: str = "source_revision") -> str:
    revision = _require_str(value, where)
    if not REVISION_RE.fullmatch(revision):
        raise ValueError(f"{where} must be a 40-64 character lowercase hexadecimal immutable revision")
    return revision


def _validate_sha256(value: object, where: str) -> str:
    digest = _require_str(value, where)
    if not SHA256_RE.fullmatch(digest):
        raise ValueError(f"{where} must be a lowercase SHA-256 hex digest")
    return digest


def _validate_host(host: object, where: str) -> str:
    value = _require_str(host, where).lower().rstrip(".")
    if any(ch.isspace() for ch in value) or "/" in value or ":" in value:
        raise ValueError(f"{where} is not a bare hostname")
    if "." not in value and value != "localhost":
        raise ValueError(f"{where} is not a valid hostname")
    return value


def _safe_artifact_name(value: object, where: str) -> str:
    name = _require_str(value, where)
    if "\x00" in name or "\\" in name:
        raise ValueError(f"{where} contains unsafe path characters")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"{where} must be a safe relative POSIX path")
    return path.as_posix()


def _validate_source_url(url: object, revision: str, allowed_hosts: Sequence[str], where: str) -> str:
    value = _require_str(url, where)
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https":
        raise DownloadPolicyError(f"{where} must use https")
    if parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise DownloadPolicyError(f"{where} may not contain credentials, a fragment, or a query string")
    host = (parsed.hostname or "").lower().rstrip(".")
    if host not in allowed_hosts:
        raise DownloadPolicyError(f"{where} host {host!r} is not allowlisted")
    if revision not in parsed.path:
        raise DownloadPolicyError(f"{where} must contain immutable revision {revision}")
    mutable_segments = {"main", "master", "latest", "head"}
    segments = {segment.lower() for segment in parsed.path.split("/") if segment}
    if segments & mutable_segments:
        raise DownloadPolicyError(f"{where} contains a mutable ref segment")
    return value


def load_registry(path: Path) -> dict[str, RegistryEntry]:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"cannot read registry: {exc}") from exc
    try:
        if not isinstance(raw, dict):
            raise ValueError("registry must be an object")
        _require_exact_keys(raw, {"schema_version", "models"}, "registry")
        if raw["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported registry schema_version")
        models = raw["models"]
        if not isinstance(models, list):
            raise ValueError("registry.models must be a list")
        result: dict[str, RegistryEntry] = {}
        for index, item in enumerate(models):
            if not isinstance(item, dict):
                raise ValueError(f"registry.models[{index}] must be an object")
            _require_exact_keys(
                item,
                {"model_id", "status", "source_revision", "manifest_url", "manifest_size", "manifest_sha256", "allowed_hosts"},
                f"registry.models[{index}]",
            )
            model_id = _validate_model_id(item["model_id"], f"registry.models[{index}].model_id")
            status = _require_str(item["status"], f"registry.models[{index}].status")
            if status not in ALLOWED_STATUSES:
                raise ValueError(f"registry.models[{index}].status is invalid")
            revision = _validate_revision(item["source_revision"], f"registry.models[{index}].source_revision")
            hosts_raw = item["allowed_hosts"]
            if not isinstance(hosts_raw, list) or not hosts_raw:
                raise ValueError(f"registry.models[{index}].allowed_hosts must be a non-empty list")
            hosts = tuple(dict.fromkeys(_validate_host(v, f"registry.models[{index}].allowed_hosts") for v in hosts_raw))
            manifest_size = _require_int(item["manifest_size"], f"registry.models[{index}].manifest_size", minimum=2)
            if manifest_size > 1024 * 1024:
                raise ValueError("manifest_size exceeds 1 MiB policy limit")
            digest = _validate_sha256(item["manifest_sha256"], f"registry.models[{index}].manifest_sha256")
            url = _validate_source_url(item["manifest_url"], revision, hosts, f"registry.models[{index}].manifest_url")
            if model_id in result:
                raise ValueError(f"duplicate model_id {model_id!r}")
            result[model_id] = RegistryEntry(model_id, status, revision, url, manifest_size, digest, hosts)
        return result
    except (TypeError, ValueError, DownloadPolicyError) as exc:
        raise RegistryError(str(exc)) from exc


def parse_manifest(data: bytes, entry: RegistryEntry, *, max_artifacts: int, max_total_bytes: int) -> ModelManifest:
    try:
        raw = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"manifest is not valid UTF-8 JSON: {exc}") from exc
    try:
        if not isinstance(raw, dict):
            raise ValueError("manifest must be an object")
        _require_exact_keys(raw, {"schema_version", "model_id", "source_revision", "runtime_family", "artifacts"}, "manifest")
        if raw["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported manifest schema_version")
        model_id = _validate_model_id(raw["model_id"], "manifest.model_id")
        revision = _validate_revision(raw["source_revision"], "manifest.source_revision")
        if model_id != entry.model_id:
            raise ValueError("manifest model_id does not match registry")
        if revision != entry.source_revision:
            raise ValueError("manifest source_revision does not match registry")
        runtime_family = _require_str(raw["runtime_family"], "manifest.runtime_family")
        if len(runtime_family) > 128:
            raise ValueError("manifest.runtime_family is too long")
        items = raw["artifacts"]
        if not isinstance(items, list) or not items:
            raise ValueError("manifest.artifacts must be a non-empty list")
        if len(items) > max_artifacts:
            raise ValueError("manifest has too many artifacts")
        artifacts: list[ArtifactSpec] = []
        seen: set[str] = set()
        total = 0
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValueError(f"manifest.artifacts[{index}] must be an object")
            _require_exact_keys(item, {"name", "kind", "url", "size", "sha256"}, f"manifest.artifacts[{index}]")
            name = _safe_artifact_name(item["name"], f"manifest.artifacts[{index}].name")
            if name in seen:
                raise ValueError(f"duplicate artifact name {name!r}")
            seen.add(name)
            kind = _require_str(item["kind"], f"manifest.artifacts[{index}].kind")
            if kind not in ALLOWED_KINDS:
                raise ValueError(f"manifest.artifacts[{index}].kind is invalid")
            size = _require_int(item["size"], f"manifest.artifacts[{index}].size", minimum=1)
            total += size
            if total > max_total_bytes:
                raise ValueError("manifest total size exceeds policy limit")
            digest = _validate_sha256(item["sha256"], f"manifest.artifacts[{index}].sha256")
            url = _validate_source_url(item["url"], revision, entry.allowed_hosts, f"manifest.artifacts[{index}].url")
            artifacts.append(ArtifactSpec(name, kind, url, size, digest))
        return ModelManifest(model_id, revision, runtime_family, tuple(artifacts))
    except (TypeError, ValueError, DownloadPolicyError) as exc:
        raise ManifestError(str(exc)) from exc


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size


class ArtifactStore:
    """Download and verify immutable model artifacts without executing them."""

    def __init__(self, root: Path, *, opener: Optional[Callable[..., BinaryIO]] = None,
                 timeout_seconds: int = 30, max_artifacts: int = 2048,
                 max_total_bytes: int = 32 * 1024 * 1024 * 1024, chunk_bytes: int = 1024 * 1024):
        self.root = Path(root)
        self.opener = opener or self._default_open
        self.timeout_seconds = _require_int(timeout_seconds, "timeout_seconds", minimum=1)
        self.max_artifacts = _require_int(max_artifacts, "max_artifacts", minimum=1)
        self.max_total_bytes = _require_int(max_total_bytes, "max_total_bytes", minimum=1)
        self.chunk_bytes = _require_int(chunk_bytes, "chunk_bytes", minimum=4096)
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise DownloadPolicyError("artifact store root may not be a symlink")
        (self.root / "models").mkdir(exist_ok=True)
        (self.root / "staging").mkdir(exist_ok=True)

    @staticmethod
    def _default_open(url: str, timeout: int):
        request = urllib.request.Request(url, headers={"User-Agent": "HumanOS-ModelArtifactStore/0.1"}, method="GET")
        return urllib.request.urlopen(request, timeout=timeout)

    def _ensure_no_symlink_chain(self, path: Path) -> None:
        try:
            relative = path.relative_to(self.root)
        except ValueError as exc:
            raise DownloadPolicyError("path escapes artifact store") from exc
        cursor = self.root
        for part in relative.parts:
            cursor = cursor / part
            if cursor.exists() and cursor.is_symlink():
                raise DownloadPolicyError(f"symlink not allowed in artifact store path: {cursor}")

    def _open_checked(self, url: str, allowed_hosts: Sequence[str]):
        response = self.opener(url, self.timeout_seconds)
        final_url = getattr(response, "geturl", lambda: url)()
        parsed = urllib.parse.urlsplit(final_url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme != "https" or host not in allowed_hosts:
            try:
                response.close()
            finally:
                raise DownloadPolicyError("redirect/final URL left the HTTPS host allowlist")
        return response

    def _download_bytes(self, url: str, expected_size: int, expected_sha256: str, allowed_hosts: Sequence[str]) -> bytes:
        digest = hashlib.sha256(); chunks: list[bytes] = []; total = 0
        try:
            with self._open_checked(url, allowed_hosts) as response:
                while True:
                    chunk = response.read(min(self.chunk_bytes, expected_size - total + 1))
                    if not chunk: break
                    total += len(chunk)
                    if total > expected_size: raise IntegrityError("download exceeded expected size")
                    digest.update(chunk); chunks.append(chunk)
        except ModelArtifactError:
            raise
        except Exception as exc:
            raise ModelArtifactError(f"download failed for {url}: {exc}") from exc
        if total != expected_size: raise IntegrityError(f"download size mismatch: expected {expected_size}, got {total}")
        if digest.hexdigest() != expected_sha256: raise IntegrityError("download SHA-256 mismatch")
        return b"".join(chunks)

    def _download_file(self, spec: ArtifactSpec, target: Path, allowed_hosts: Sequence[str]) -> None:
        self._ensure_no_symlink_chain(target.parent)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_no_symlink_chain(target.parent)
        if target.exists():
            if target.is_symlink(): raise DownloadPolicyError("artifact destination may not be a symlink")
            digest, size = _sha256_file(target)
            if digest != spec.sha256 or size != spec.size: raise IntegrityError(f"existing staged artifact is corrupt: {spec.name}")
            return
        partial = target.with_name(target.name + ".partial")
        if partial.exists():
            if partial.is_symlink(): raise DownloadPolicyError("partial artifact may not be a symlink")
            partial.unlink()
        digest = hashlib.sha256(); total = 0
        try:
            with self._open_checked(spec.url, allowed_hosts) as response, partial.open("xb") as out:
                while True:
                    chunk = response.read(min(self.chunk_bytes, spec.size - total + 1))
                    if not chunk: break
                    total += len(chunk)
                    if total > spec.size: raise IntegrityError(f"{spec.name} exceeded expected size")
                    digest.update(chunk); out.write(chunk)
                out.flush(); os.fsync(out.fileno())
            if total != spec.size: raise IntegrityError(f"{spec.name} size mismatch: expected {spec.size}, got {total}")
            if digest.hexdigest() != spec.sha256: raise IntegrityError(f"{spec.name} SHA-256 mismatch")
            os.replace(partial, target)
        except Exception:
            try: partial.unlink(missing_ok=True)
            except OSError: pass
            raise

    def _verify_complete_model(self, model_dir: Path, entry: RegistryEntry, manifest: ModelManifest) -> bool:
        receipt_path = model_dir / "VERIFIED.json"
        if not receipt_path.is_file() or receipt_path.is_symlink(): return False
        try: receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError): return False
        if (receipt.get("model_id") != entry.model_id or receipt.get("source_revision") != entry.source_revision
                or receipt.get("manifest_sha256") != entry.manifest_sha256): return False
        for spec in manifest.artifacts:
            path = model_dir.joinpath(*PurePosixPath(spec.name).parts)
            if not path.is_file() or path.is_symlink(): return False
            digest, size = _sha256_file(path)
            if digest != spec.sha256 or size != spec.size: return False
        return True

    def fetch_model(self, registry_path: Path, model_id: str) -> DownloadResult:
        registry = load_registry(registry_path)
        if model_id not in registry: raise RegistryError(f"unknown model_id {model_id!r}")
        entry = registry[model_id]
        manifest_bytes = self._download_bytes(entry.manifest_url, entry.manifest_size, entry.manifest_sha256, entry.allowed_hosts)
        manifest = parse_manifest(manifest_bytes, entry, max_artifacts=self.max_artifacts, max_total_bytes=self.max_total_bytes)
        model_dir = self.root / "models" / entry.model_id / entry.source_revision
        self._ensure_no_symlink_chain(model_dir.parent)
        if model_dir.exists():
            if model_dir.is_symlink(): raise DownloadPolicyError("model directory may not be a symlink")
            if not self._verify_complete_model(model_dir, entry, manifest):
                raise IntegrityError("existing model cache failed verification; refusing to overwrite")
            return DownloadResult(entry.model_id, entry.source_revision, model_dir, True, len(manifest.artifacts), sum(i.size for i in manifest.artifacts))
        staging = self.root / "staging" / entry.model_id / entry.source_revision
        self._ensure_no_symlink_chain(staging.parent)
        staging.mkdir(parents=True, exist_ok=True)
        self._ensure_no_symlink_chain(staging)
        for spec in manifest.artifacts:
            self._download_file(spec, staging.joinpath(*PurePosixPath(spec.name).parts), entry.allowed_hosts)
        receipt = {
            "schema_version": SCHEMA_VERSION,
            "model_id": entry.model_id,
            "source_revision": entry.source_revision,
            "manifest_sha256": entry.manifest_sha256,
            "runtime_family": manifest.runtime_family,
            "verified_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [{"name": i.name, "kind": i.kind, "size": i.size, "sha256": i.sha256} for i in manifest.artifacts],
        }
        receipt_path = staging / "VERIFIED.json"
        receipt_path.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        model_dir.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_no_symlink_chain(model_dir.parent)
        os.replace(staging, model_dir)
        return DownloadResult(entry.model_id, entry.source_revision, model_dir, False, len(manifest.artifacts), sum(i.size for i in manifest.artifacts))
