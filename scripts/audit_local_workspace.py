#!/usr/bin/env python3
"""Read-only inventory for HumanOS/BodyFixOS workspace cleanup.

This tool does not move, rename, delete, checkout, stash, commit, or push anything.
It records filesystem/Git evidence so cleanup decisions can be made safely.

The output directory is mandatory: the tool will not dump reports into the current
working directory or home-directory root by accident.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any


SKIP_DIR_NAMES = {
    ".git",
    ".Trash",
    "Library",
    "Applications",
    "Movies",
    "Music",
    "Pictures",
    "VirtualBox VMs",
    "node_modules",
    ".next",
    "dist",
    "build",
    ".venv",
    "venv",
    "__pycache__",
}

CLASSIFICATIONS = {
    "CANONICAL_REPO",
    "ACTIVE_WORKTREE",
    "PRIVATE_RUNTIME_STATE",
    "SOURCE_OF_TRUTH_DOCUMENT",
    "GENERATED_EVIDENCE_ARTIFACT",
    "IMPORT_MIGRATION",
    "BACKUP_ARCHIVE",
    "TEMP_CACHE",
    "LEGACY_CANDIDATE",
    "UNKNOWN",
}


def run_git(path: pathlib.Path, args: list[str]) -> tuple[int, str]:
    result = subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    text = result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
    return result.returncode, text


def git_metadata(path: pathlib.Path) -> dict[str, Any]:
    code, inside = run_git(path, ["rev-parse", "--is-inside-work-tree"])
    if code != 0 or inside != "true":
        return {"is_git": False}

    code, git_dir = run_git(path, ["rev-parse", "--git-dir"])
    code2, common_dir = run_git(path, ["rev-parse", "--git-common-dir"])
    is_worktree = code == 0 and code2 == 0 and pathlib.Path(git_dir).resolve() != pathlib.Path(common_dir).resolve()

    _, head = run_git(path, ["rev-parse", "HEAD"])
    _, branch = run_git(path, ["branch", "--show-current"])
    _, remote = run_git(path, ["remote", "get-url", "origin"])
    _, status = run_git(path, ["status", "--porcelain"])
    _, stash = run_git(path, ["stash", "list"])
    _, worktrees = run_git(path, ["worktree", "list", "--porcelain"])

    upstream_code, upstream = run_git(path, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    unpushed_count = None
    if upstream_code == 0 and upstream:
        count_code, count = run_git(path, ["rev-list", "--count", f"{upstream}..HEAD"])
        if count_code == 0 and count.isdigit():
            unpushed_count = int(count)

    ignored_code, ignored = run_git(path, ["status", "--porcelain", "--ignored"])
    ignored_count = 0
    if ignored_code == 0 and ignored:
        ignored_count = sum(1 for line in ignored.splitlines() if line.startswith("!!"))

    env_file_present = any(
        candidate.exists()
        for candidate in (
            path / ".env",
            path / ".env.local",
            path / ".env.development",
            path / ".env.production",
        )
    )

    return {
        "is_git": True,
        "is_worktree": is_worktree,
        "git_dir": git_dir,
        "git_common_dir": common_dir,
        "remote_origin": remote or None,
        "branch": branch or None,
        "head": head or None,
        "dirty": bool(status),
        "status_porcelain": status,
        "stash_count": len(stash.splitlines()) if stash else 0,
        "unpushed_commit_count": unpushed_count,
        "ignored_entry_count": ignored_count,
        "env_file_present": env_file_present,
        "worktree_list_porcelain": worktrees,
    }


def classify(path: pathlib.Path, git: dict[str, Any]) -> tuple[str, str, str | None]:
    name = path.name.lower()
    text = str(path).lower()

    if git.get("is_git"):
        if git.get("is_worktree"):
            return "ACTIVE_WORKTREE", "HIGH", "~/Developer/worktrees/<product>/<workstream>/"
        return "CANONICAL_REPO", "MEDIUM", "~/Developer/repos/<repository>/"

    if "/.humanos/" in text or text.endswith("/.humanos"):
        return "PRIVATE_RUNTIME_STATE", "HIGH", "~/.humanos/private/"
    if "backup" in name or "archive" in name:
        return "BACKUP_ARCHIVE", "MEDIUM", "~/Archives/<product>/"
    if "migration" in name or "import" in name:
        return "IMPORT_MIGRATION", "MEDIUM", "~/Developer/imports/<product>/"
    if "tmp" == name or name.startswith("tmp-") or name.endswith("-tmp"):
        return "TEMP_CACHE", "MEDIUM", None
    if any(token in name for token in ("audit", "snapshot", "results", "manifest", "evidence")):
        return "GENERATED_EVIDENCE_ARTIFACT", "MEDIUM", "~/Developer/artifacts/<product>/"

    return "UNKNOWN", "LOW", None


def iter_candidates(root: pathlib.Path, max_depth: int):
    root = root.expanduser().resolve()
    if not root.exists():
        return

    root_parts = len(root.parts)
    for current, dirs, files in os.walk(root):
        current_path = pathlib.Path(current)
        depth = len(current_path.parts) - root_parts
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_NAMES]
        if depth >= max_depth:
            dirs[:] = []

        if current_path == root:
            for file_name in files:
                yield current_path / file_name
            continue

        yield current_path
        if (current_path / ".git").exists():
            dirs[:] = []


def record_for(path: pathlib.Path) -> dict[str, Any]:
    try:
        stat = path.stat()
    except OSError as exc:
        return {
            "path": str(path),
            "error": str(exc),
            "classification": "UNKNOWN",
            "confidence": "LOW",
        }

    git = git_metadata(path) if path.is_dir() else {"is_git": False}
    classification, confidence, destination = classify(path, git)

    return {
        "path": str(path),
        "kind": "directory" if path.is_dir() else "file",
        "size_bytes": stat.st_size if path.is_file() else None,
        "modified_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        "classification": classification,
        "confidence": confidence,
        "proposed_destination": destination,
        **git,
    }


def write_csv(path: pathlib.Path, records: list[dict[str, Any]]) -> None:
    fieldnames = [
        "path",
        "kind",
        "classification",
        "confidence",
        "proposed_destination",
        "is_git",
        "is_worktree",
        "remote_origin",
        "branch",
        "head",
        "dirty",
        "stash_count",
        "unpushed_commit_count",
        "ignored_entry_count",
        "env_file_present",
        "size_bytes",
        "modified_utc",
        "error",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        action="append",
        dest="roots",
        help="Root to inventory. Repeat for multiple roots.",
    )
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Explicit directory for JSON/CSV reports. No implicit output path is allowed.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    roots = args.roots or [str(pathlib.Path.home()), str(pathlib.Path.home() / "Documents"), str(pathlib.Path.home() / "Developer")]
    output_dir = pathlib.Path(args.output_dir).expanduser().resolve()

    home = pathlib.Path.home().resolve()
    if output_dir == home or output_dir == pathlib.Path.cwd().resolve():
        print("Refusing ambiguous output directory. Choose a dedicated artifact subdirectory.", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)

    seen: set[pathlib.Path] = set()
    records: list[dict[str, Any]] = []
    for root_text in roots:
        root = pathlib.Path(root_text).expanduser()
        for candidate in iter_candidates(root, args.max_depth) or []:
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            records.append(record_for(resolved))

    records.sort(key=lambda record: record.get("path", ""))
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    json_path = output_dir / f"WORKSPACE_INVENTORY_{timestamp}.json"
    csv_path = output_dir / f"WORKSPACE_INVENTORY_{timestamp}.csv"

    json_path.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(csv_path, records)

    print(f"Read-only inventory complete: {len(records)} items")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print("No files were moved, renamed, deleted, committed, stashed, or pushed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
