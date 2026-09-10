"""Provider-neutral model-run evidence ledger for HumanOS.

Stores model interaction evidence outside the Life Notebook and outside Git.
The caller supplies provider metadata exactly as exposed by the provider/UI/API;
unknown fields remain unknown rather than being inferred.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


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
    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    run_dir = Path(root).expanduser() / f"{now:%Y/%m/%d}" / job_id / run_id

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
        "usage": None,
        "cost": None,
        "quota_observation": None,
        "finish_reason": None,
        "tool_summary": None,
    }
    if extra_metadata:
        metadata.update(dict(extra_metadata))

    _atomic_write(request_doc_path := run_dir / "request.json", json.dumps(request_doc, indent=2, sort_keys=True) + "\n")
    _atomic_write(run_dir / "metadata.json", json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return request_doc_path.parent


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
    """Persist raw response and measured provider metadata for a completed run."""
    run_path = Path(run_dir)
    metadata_path = run_path / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    response_sha = _sha256_text(response)
    _atomic_write(run_path / "response.txt", response)

    metadata.update(
        {
            "model_version": model_version or metadata.get("model_version") or "unknown",
            "ended_at_utc": _utc_now(),
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
    """Record verification separately from the model's own output."""
    allowed = {"PASS", "FAIL", "PARTIAL", "UNVERIFIED"}
    if status not in allowed:
        raise ValueError(f"status must be one of {sorted(allowed)}")
    review = {
        "status": status,
        "reviewer": reviewer,
        "reviewed_at_utc": _utc_now(),
        "notes": notes,
        "evidence": evidence or [],
    }
    _atomic_write(Path(run_dir) / "review.json", json.dumps(review, indent=2, sort_keys=True) + "\n")
