#!/usr/bin/env python3
"""Operator CLI for the private HumanOS model-run evidence ledger.

The CLI is intentionally provider-neutral and standard-library only. It preserves
exact prompt/response text, records only metadata supplied by the operator, and
keeps all run data beneath an explicitly selected private ledger root.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from pathlib import Path
from typing import Any, Sequence

import model_runs


DEFAULT_ROOT = Path.home() / "HumanOSData" / "model-runs"
REVIEW_STATUSES = ("PASS", "FAIL", "PARTIAL", "UNVERIFIED")
JOB_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _read_text(file_path: str | None, use_stdin: bool, label: str) -> str:
    if use_stdin:
        return sys.stdin.read()
    if not file_path:
        raise ValueError(f"{label}: provide --{label}-file or --{label}-stdin")
    path = Path(file_path).expanduser()
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"{label} file must be an ordinary existing file: {path}")
    return path.read_text(encoding="utf-8")


def _json_object(value: str | None, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def _json_string_list(value: str | None, label: str) -> list[str] | None:
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc}") from exc
    if not isinstance(parsed, list) or any(not isinstance(item, str) for item in parsed):
        raise ValueError(f"{label} must be a JSON array of strings")
    return parsed


def _json_print(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


def _private_root(value: str | Path) -> Path:
    root = Path(value).expanduser()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"ledger root is not a directory: {root}")
    os.chmod(root, 0o700)
    return root


def _reject_symlink_components(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"run directory escapes ledger root: {path}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink is not allowed in run path: {current}")


def _resolve_run_dir(root_value: str | Path, value: str) -> tuple[Path, Path]:
    root = _private_root(root_value)
    raw = Path(value).expanduser()
    candidate = raw if raw.is_absolute() else root / raw
    candidate = candidate.resolve(strict=False)
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"run directory must stay beneath ledger root {root}") from exc
    _reject_symlink_components(root, candidate)
    if not candidate.is_dir():
        raise ValueError(f"run directory does not exist: {candidate}")
    return root, candidate


def _harden_run_permissions(root: Path, run_dir: Path) -> None:
    """Make directories owner-only and known run files owner-read/write only."""
    relative = run_dir.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink is not allowed in run path: {current}")
        os.chmod(current, 0o700)
    for name in ("request.json", "metadata.json", "response.txt", "review.json"):
        path = run_dir / name
        if path.exists():
            if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"run artifact must be an ordinary file: {path}")
            os.chmod(path, 0o600)


def _assert_core_run_files(run_dir: Path) -> None:
    for name in ("request.json", "metadata.json"):
        path = run_dir / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"run is missing ordinary {name}: {run_dir}")


def cmd_start(args: argparse.Namespace) -> int:
    if not JOB_ID_RE.fullmatch(args.job_id):
        raise ValueError("job-id must be 1-128 characters: letters, digits, '.', '_' or '-', starting with a letter or digit")
    request = _read_text(args.request_file, args.request_stdin, "request")
    root = _private_root(args.root)
    run_dir = Path(model_runs.create_run(
        root,
        job_id=args.job_id,
        provider=args.provider,
        model=args.model,
        role=args.role,
        request=request,
        metadata_source=args.metadata_source,
        repository_ref=args.repository_ref,
        parent_run_id=args.parent_run_id,
    )).resolve()
    try:
        run_dir.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("model_runs.create_run returned a path outside the ledger root") from exc
    _harden_run_permissions(root, run_dir)
    payload = {
        "run_dir": str(run_dir),
        "request_path": str(run_dir / "request.json"),
        "metadata_path": str(run_dir / "metadata.json"),
    }
    _json_print(payload) if args.json else print(str(run_dir))
    return 0


def cmd_finish(args: argparse.Namespace) -> int:
    root, run_dir = _resolve_run_dir(args.root, args.run_dir)
    _assert_core_run_files(run_dir)
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    if (run_dir / "response.txt").exists() or metadata.get("ended_at_utc") is not None:
        raise ValueError("run already has completion evidence; inspect/reconcile instead of overwriting it")
    response = _read_text(args.response_file, args.response_stdin, "response")
    usage = _json_object(args.usage, "usage")
    cost = _json_object(args.cost, "cost")
    tool_summary = _json_object(args.tool_summary, "tool-summary")
    model_runs.finish_run(
        run_dir,
        response=response,
        model_version=args.model_version,
        usage=usage,
        cost=cost,
        quota_observation=args.quota_observation,
        finish_reason=args.finish_reason,
        tool_summary=tool_summary,
    )
    _harden_run_permissions(root, run_dir)
    payload = {
        "run_dir": str(run_dir),
        "response_path": str(run_dir / "response.txt"),
        "metadata_path": str(run_dir / "metadata.json"),
    }
    _json_print(payload) if args.json else print(str(run_dir / "response.txt"))
    return 0


def cmd_review(args: argparse.Namespace) -> int:
    root, run_dir = _resolve_run_dir(args.root, args.run_dir)
    _assert_core_run_files(run_dir)
    if (run_dir / "review.json").exists():
        raise ValueError("run already has review evidence; do not overwrite it")
    evidence = _json_string_list(args.evidence, "evidence")
    model_runs.record_review(
        run_dir,
        status=args.status,
        reviewer=args.reviewer,
        notes=args.notes,
        evidence=evidence,
    )
    _harden_run_permissions(root, run_dir)
    payload = {"run_dir": str(run_dir), "review_path": str(run_dir / "review.json")}
    _json_print(payload) if args.json else print(str(run_dir / "review.json"))
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    root, run_dir = _resolve_run_dir(args.root, args.run_dir)
    _assert_core_run_files(run_dir)
    _harden_run_permissions(root, run_dir)
    request_path = run_dir / "request.json"
    metadata_path = run_dir / "metadata.json"
    response_path = run_dir / "response.txt"
    review_path = run_dir / "review.json"
    payload: dict[str, Any] = {
        "run_dir": str(run_dir),
        "request": json.loads(request_path.read_text(encoding="utf-8")),
        "metadata": json.loads(metadata_path.read_text(encoding="utf-8")),
        "review": json.loads(review_path.read_text(encoding="utf-8")) if review_path.exists() else None,
        "response_present": response_path.exists(),
        "response_bytes": response_path.stat().st_size if response_path.exists() else None,
    }
    if args.include_response and response_path.exists():
        payload["response"] = response_path.read_text(encoding="utf-8")
    if args.json:
        _json_print(payload)
    else:
        print(f"run_dir: {run_dir}")
        print(f"request: {request_path}")
        print(f"metadata: {metadata_path}")
        print(f"response: {response_path}" + (f" ({payload['response_bytes']} bytes)" if response_path.exists() else " (missing)"))
        print(f"review: {review_path}" + ("" if review_path.exists() else " (missing)"))
        if args.include_response and response_path.exists():
            print("--- response ---")
            sys.stdout.write(payload["response"])
            if not payload["response"].endswith("\n"):
                print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="model_runs_cli", description="HumanOS private model-run ledger operator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("start", help="create a run and preserve the exact request")
    p.add_argument("--root", default=str(DEFAULT_ROOT))
    p.add_argument("--job-id", required=True)
    p.add_argument("--provider", required=True)
    p.add_argument("--model", required=True, help="use UNKNOWN when the service does not expose it")
    p.add_argument("--role", required=True)
    request = p.add_mutually_exclusive_group(required=True)
    request.add_argument("--request-file")
    request.add_argument("--request-stdin", action="store_true")
    p.add_argument("--metadata-source", default="unknown", choices=("api", "ui", "self_report", "config", "unknown"))
    p.add_argument("--repository-ref")
    p.add_argument("--parent-run-id")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("finish", help="record a completed model response without overwriting prior completion evidence")
    p.add_argument("--root", default=str(DEFAULT_ROOT))
    p.add_argument("--run-dir", required=True)
    response = p.add_mutually_exclusive_group(required=True)
    response.add_argument("--response-file")
    response.add_argument("--response-stdin", action="store_true")
    p.add_argument("--model-version")
    p.add_argument("--usage", help="JSON object containing measured provider usage")
    p.add_argument("--cost", help="JSON object containing measured provider cost")
    p.add_argument("--quota-observation")
    p.add_argument("--finish-reason")
    p.add_argument("--tool-summary", help="JSON object describing exposed tool usage")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_finish)

    p = sub.add_parser("review", help="record one immutable verification disposition")
    p.add_argument("--root", default=str(DEFAULT_ROOT))
    p.add_argument("--run-dir", required=True)
    p.add_argument("--status", required=True, choices=REVIEW_STATUSES)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--notes", default="")
    p.add_argument("--evidence", help="JSON array of evidence strings")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("inspect", help="inspect one run; raw response is hidden unless explicitly requested")
    p.add_argument("--root", default=str(DEFAULT_ROOT))
    p.add_argument("--run-dir", required=True)
    p.add_argument("--include-response", action="store_true")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_inspect)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
