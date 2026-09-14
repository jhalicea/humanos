"""Provider-neutral model-run evidence ledger for HumanOS.

Stores model interaction evidence outside the Life Notebook and outside Git.
The caller supplies provider metadata exactly as exposed by the provider/UI/API;
unknown fields remain unknown rather than being inferred.

Core invariants are enforced here rather than delegated to a CLI wrapper:
- run paths stay beneath a private ledger root;
- job IDs cannot become path components with traversal semantics;
- files/directories are owner-only;
- atomic replacements are followed by parent-directory fsync;
- trusted metadata cannot be overwritten by caller-supplied extras;
- response/review writes are serialized and never silently overwrite evidence;
- reviews bind to the exact response digest they evaluated.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Mapping


JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
KNOWN_FILES = ("request.json", "metadata.json", "response.txt", "review.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_private_dir(path: Path) -> None:
    """Create one directory durably, then force owner-only permissions."""
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise ValueError(f"ledger path component is not an ordinary directory: {path}")
        os.chmod(path, 0o700)
        return
    parent = path.parent
    if not parent.is_dir():
        raise ValueError(f"ledger parent directory does not exist: {parent}")
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)
    _fsync_dir(parent)


def _private_root(root: str | Path) -> Path:
    raw = Path(root).expanduser()
    raw.mkdir(parents=True, exist_ok=True, mode=0o700)
    root_path = raw.resolve()
    if not root_path.is_dir():
        raise ValueError(f"ledger root is not a directory: {root_path}")
    os.chmod(root_path, 0o700)
    return root_path


def _run_directory(root: str | Path, now: datetime, job_id: str, run_id: str) -> tuple[Path, Path]:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("job_id must be 1-128 characters: letters, digits, '.', '_' or '-', starting with a letter or digit")
    root_path = _private_root(root)
    current = root_path
    for component in (f"{now:%Y}", f"{now:%m}", f"{now:%d}", job_id, run_id):
        candidate = current / component
        if candidate.exists() and candidate.is_symlink():
            raise ValueError(f"symlink is not allowed in ledger path: {candidate}")
        _ensure_private_dir(candidate)
        resolved = candidate.resolve()
        try:
            resolved.relative_to(root_path)
        except ValueError as exc:
            raise ValueError(f"ledger path escaped root: {candidate}") from exc
        current = resolved
    return root_path, current


def _assert_private_run_dir(run_dir: str | Path) -> Path:
    path = Path(run_dir).expanduser()
    if path.is_symlink() or not path.is_dir():
        raise ValueError(f"run directory is not an ordinary directory: {path}")
    path = path.resolve()
    os.chmod(path, 0o700)
    for name in KNOWN_FILES:
        artifact = path / name
        if artifact.exists():
            if artifact.is_symlink() or not stat.S_ISREG(artifact.stat().st_mode):
                raise ValueError(f"run artifact is not an ordinary file: {artifact}")
            os.chmod(artifact, 0o600)
    return path


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise ValueError(f"atomic-write parent is not an ordinary directory: {path.parent}")
    os.chmod(path.parent, 0o700)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(tmp, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            fd = -1
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        os.chmod(path, 0o600)
        _fsync_dir(path.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        if tmp.exists():
            tmp.unlink()


@contextmanager
def _run_lock(run_path: Path) -> Iterator[None]:
    """Serialize evidence transitions without trusting model/provider callers."""
    lock_path = run_path / ".ledger.lock"
    fd = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        os.fchmod(fd, 0o600)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"ledger artifact must contain a JSON object: {path}")
    return value


def create_run(
    root: str | Path,
    *,
    job_id: str,
    provider: str,
    model: str | None,
    role: str,
    request: str,
    metadata_source: str = "unknown",
    repository_ref: str | None = None,
    parent_run_id: str | None = None,
    extra_metadata: Mapping[str, Any] | None = None,
) -> Path:
    """Create a private run directory and persist request + initial metadata."""
    if not isinstance(request, str):
        raise TypeError("request must be exact text")
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    _, run_dir = _run_directory(root, now, job_id, run_id)

    request_doc = {
        "run_id": run_id,
        "job_id": job_id,
        "request": request,
        "request_sha256": _sha256_text(request),
    }
    metadata = {
        "run_id": run_id,
        "job_id": job_id,
        "parent_run_id": parent_run_id,
        "provider": provider,
        "model": model or "unknown",
        "model_version": "unknown",
        "metadata_source": metadata_source,
        "role": role,
        "started_at_utc": _utc_now(),
        "ended_at_utc": None,
        "repository_ref": repository_ref,
        "state": "CREATED",
        "usage": None,
        "cost": None,
        "quota_observation": None,
        "finish_reason": None,
        "tool_summary": None,
        "response_sha256": None,
        "extra": dict(extra_metadata) if extra_metadata else {},
    }

    # Request first, then metadata as the authoritative stage marker. A crash
    # between these writes is detectable as CAPTURE_INCOMPLETE by inspect_run().
    _atomic_write(run_dir / "request.json", json.dumps(request_doc, indent=2, sort_keys=True) + "\n")
    _atomic_write(run_dir / "metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return run_dir


def finish_run(
    run_dir: str | Path,
    *,
    response: str,
    model_version: str | None = None,
    usage: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    quota_observation: Any = None,
    finish_reason: str | None = None,
    tool_summary: Any = None,
) -> None:
    """Persist one raw response and measured provider metadata without overwrite."""
    if not isinstance(response, str):
        raise TypeError("response must be exact text")
    run_path = _assert_private_run_dir(run_dir)
    metadata_path = run_path / "metadata.json"
    response_path = run_path / "response.txt"

    with _run_lock(run_path):
        metadata = _load_json_object(metadata_path)
        if response_path.exists() or metadata.get("state") not in (None, "CREATED") or metadata.get("ended_at_utc") is not None:
            raise ValueError("run already contains completion evidence; inspect/reconcile instead of overwriting it")
        if (run_path / "review.json").exists():
            raise ValueError("run already contains review evidence; completion cannot be appended afterward")

        response_sha = _sha256_text(response)
        _atomic_write(response_path, response)
        metadata.update(
            {
                "model_version": model_version or metadata.get("model_version") or "unknown",
                "ended_at_utc": _utc_now(),
                "state": "RESPONDED",
                "usage": dict(usage) if usage is not None else None,
                "cost": dict(cost) if cost is not None else None,
                "quota_observation": quota_observation,
                "finish_reason": finish_reason,
                "tool_summary": tool_summary,
                "response_sha256": response_sha,
            }
        )
        _atomic_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def record_review(
    run_dir: str | Path,
    *,
    status: str,
    reviewer: str,
    notes: str = "",
    evidence: list[str] | None = None,
) -> None:
    """Record one immutable review bound to the exact response when present."""
    allowed = {"PASS", "FAIL", "PARTIAL", "UNVERIFIED"}
    if status not in allowed:
        raise ValueError(f"status must be one of {sorted(allowed)}")
    run_path = _assert_private_run_dir(run_dir)
    metadata_path = run_path / "metadata.json"
    review_path = run_path / "review.json"
    response_path = run_path / "response.txt"

    with _run_lock(run_path):
        if review_path.exists():
            raise ValueError("run already contains review evidence; do not overwrite it")
        metadata = _load_json_object(metadata_path)
        bound_response_sha = None
        if response_path.exists():
            bound_response_sha = _sha256_text(response_path.read_text(encoding="utf-8"))
            recorded_sha = metadata.get("response_sha256")
            if not recorded_sha:
                raise ValueError("response exists but metadata completion is incomplete; reconcile before review")
            if recorded_sha != bound_response_sha:
                raise ValueError("response digest does not match metadata; refuse to review altered evidence")
        elif status != "UNVERIFIED":
            raise ValueError("PASS/FAIL/PARTIAL review requires completed response evidence")

        review = {
            "run_id": metadata.get("run_id"),
            "status": status,
            "reviewer": reviewer,
            "reviewed_at_utc": _utc_now(),
            "notes": notes,
            "evidence": evidence or [],
            "bound_response_sha256": bound_response_sha,
        }
        _atomic_write(review_path, json.dumps(review, indent=2, sort_keys=True) + "\n")
        metadata["state"] = "REVIEWED" if bound_response_sha else "REVIEWED_INCOMPLETE"
        metadata["reviewed_at_utc"] = review["reviewed_at_utc"]
        _atomic_write(metadata_path, json.dumps(metadata, indent=2, sort_keys=True) + "\n")


def inspect_run(run_dir: str | Path) -> dict[str, Any]:
    """Classify partial/crashed states and verify response/review integrity."""
    run_path = _assert_private_run_dir(run_dir)
    request_path = run_path / "request.json"
    metadata_path = run_path / "metadata.json"
    response_path = run_path / "response.txt"
    review_path = run_path / "review.json"

    result: dict[str, Any] = {
        "run_dir": str(run_path),
        "state": "EMPTY",
        "integrity": "UNVERIFIED",
        "request_present": request_path.is_file(),
        "metadata_present": metadata_path.is_file(),
        "response_present": response_path.is_file(),
        "review_present": review_path.is_file(),
    }
    if not request_path.exists() and not metadata_path.exists():
        return result
    if request_path.exists() and not metadata_path.exists():
        result["state"] = "CAPTURE_INCOMPLETE"
        return result
    if not request_path.exists() and metadata_path.exists():
        result["state"] = "CORRUPT_MISSING_REQUEST"
        return result

    request = _load_json_object(request_path)
    metadata = _load_json_object(metadata_path)
    result["run_id"] = metadata.get("run_id")
    if request.get("run_id") != metadata.get("run_id") or request.get("job_id") != metadata.get("job_id"):
        result.update(state="INTEGRITY_ERROR", integrity="FAIL", error="request/metadata identity mismatch")
        return result
    if _sha256_text(request.get("request", "")) != request.get("request_sha256"):
        result.update(state="INTEGRITY_ERROR", integrity="FAIL", error="request digest mismatch")
        return result

    if response_path.exists():
        actual_response_sha = _sha256_text(response_path.read_text(encoding="utf-8"))
        recorded_response_sha = metadata.get("response_sha256")
        if not recorded_response_sha:
            result.update(state="RESPONSE_PENDING_METADATA", integrity="UNVERIFIED")
            return result
        if actual_response_sha != recorded_response_sha:
            result.update(state="INTEGRITY_ERROR", integrity="FAIL", error="response digest mismatch")
            return result
        result["response_sha256"] = actual_response_sha
    elif metadata.get("response_sha256"):
        result.update(state="CORRUPT_MISSING_RESPONSE", integrity="FAIL")
        return result

    if review_path.exists():
        review = _load_json_object(review_path)
        bound = review.get("bound_response_sha256")
        if bound is not None and bound != result.get("response_sha256"):
            result.update(state="INTEGRITY_ERROR", integrity="FAIL", error="review is not bound to current response")
            return result
        if metadata.get("state") not in ("REVIEWED", "REVIEWED_INCOMPLETE"):
            result.update(state="REVIEW_PENDING_METADATA", integrity="PASS")
            return result

    result["state"] = metadata.get("state") or ("RESPONDED" if response_path.exists() else "CREATED")
    result["integrity"] = "PASS"
    return result
