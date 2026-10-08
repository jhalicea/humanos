#!/usr/bin/env python3
"""Apply LOW-effort user defaults to local Codex without destroying other settings.

Run once on the Mac where Codex Desktop/CLI actually runs. Does not manage hosted
ChatGPT/Work workers, enforce token limits, or defeat explicit session overrides.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
import tomllib
from datetime import datetime, timezone

KEYS = {
    "": {
        "model_reasoning_effort": '"low"',
        "plan_mode_reasoning_effort": '"low"',
    },
    "agents": {
        "default_subagent_model": '"gpt-6-luna"',
        "default_subagent_reasoning_effort": '"low"',
        "max_concurrent_threads_per_session": "1",
    },
}
HEADER = re.compile(r"^\s*\[\[?[^\[\]\r\n]+\]\]?\s*(?:#.*)?$")
KEY = re.compile(r"^\s*([A-Za-z_][\w-]*)\s*=")


def section_name(line: str) -> str | None:
    if not line.lstrip().startswith("["):
        return None
    if not HEADER.fullmatch(line.rstrip("\r\n")):
        raise ValueError("complex TOML table header; refusing an unsafe text edit")
    return line.split("#", 1)[0].strip().strip("[]").strip()


def render(text: str) -> str:
    """Conservatively edit only known simple keys; leave unrelated TOML intact."""
    parsed = tomllib.loads(text)
    if "agents" in parsed and not isinstance(parsed["agents"], dict):
        raise ValueError("existing agents setting is not a TOML table")
    lines = text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"

    for section, replacements in KEYS.items():
        headers = [(i, section_name(line)) for i, line in enumerate(lines)
                   if line.lstrip().startswith("[")]
        start = 0 if not section else next(
            (i + 1 for i, name in headers if name == section), None)
        if start is None:
            lines.extend(["\n" if lines and lines[-1].strip() else "",
                          f"[{section}]\n"])
            start = len(lines)
        end = next((i for i, name in headers if i >= start), len(lines))
        found = set()
        for index in range(start, end):
            match = KEY.match(lines[index])
            if match and match.group(1) in replacements:
                name = match.group(1)
                lines[index] = f"{name} = {replacements[name]}\n"
                found.add(name)
        missing = [f"{key} = {value}\n" for key, value in replacements.items()
                   if key not in found]
        lines[end:end] = missing

    rendered = "".join(lines)
    settings = tomllib.loads(rendered)
    assert settings["model_reasoning_effort"] == "low"
    assert settings["plan_mode_reasoning_effort"] == "low"
    assert settings["agents"]["default_subagent_model"] == "gpt-6-luna"
    assert settings["agents"]["default_subagent_reasoning_effort"] == "low"
    assert settings["agents"]["max_concurrent_threads_per_session"] == 1
    return rendered


def report_overrides(root: Path, config: dict) -> list[str]:
    warnings = []
    value = config.get("models", {}).get("new_thread", {})
    if isinstance(value, dict) and value.get("model_reasoning_effort") not in (None, "low"):
        warnings.append("[models.new_thread] sets a different effort; check new-thread settings")
    directory = root / "agents"
    if directory.is_dir():
        for path in sorted(directory.glob("*.toml")):
            try:
                if path.is_symlink():
                    warnings.append(f"{path.name}: symlink; not inspected")
                    continue
                agent = tomllib.loads(path.read_text())
                effort = agent.get("model_reasoning_effort")
                if effort is not None and effort != "low":
                    warnings.append(f"{path.name}: custom agent effort is {effort!r}")
            except (OSError, ValueError):
                warnings.append(f"{path.name}: custom agent not readable/parseable")
    return warnings


def install(path: Path, *, dry_run: bool = False) -> dict:
    parent = path.parent
    if parent.is_symlink() or path.is_symlink():
        raise PermissionError("Codex config must not be a symlink")
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise PermissionError("unsafe Codex configuration file")
        original = path.read_text(encoding="utf-8")
    else:
        original = ""
    replacement = render(original)
    changed = replacement != original
    if changed and not dry_run:
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        if path.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup = path.with_name(path.name + ".backup-" + stamp)
            # Preserve existing configuration, including unrelated tables.
            with open(backup, "xb") as dest:
                dest.write(path.read_bytes())
            os.chmod(backup, 0o600)
        fd, temporary = tempfile.mkstemp(prefix=".humanos-codex-", dir=parent)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(replacement)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    warnings = report_overrides(parent, tomllib.loads(replacement))
    return {"changed": changed, "applied": changed and not dry_run,
            "path": str(path), "warnings": warnings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--path", type=Path, default=Path(
        os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml")
    args = parser.parse_args()
    try:
        result = install(args.path.expanduser(), dry_run=args.dry_run)
    except (OSError, ValueError, PermissionError) as exc:
        parser.exit(2, f"STOP: no changes applied: {exc}\n")
    print(("WOULD UPDATE" if args.dry_run else "UPDATED" if result["applied"] else "ALREADY SET")
          + " " + result["path"])
    for message in result["warnings"]:
        print("OVERRIDE WARNING: " + message)
    print("Defaults are not hard limits: CLI/session/spawn overrides and live "
          "Codex worker usage require separate checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
