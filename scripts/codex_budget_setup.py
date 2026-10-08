"""Install HumanOS Codex budget hooks without modifying repositories/worktrees."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import stat
import subprocess
import sys
import tempfile
import tomllib

EVENTS = ("UserPromptSubmit", "PreToolUse", "PreCompact")

def check(path):
    if path.is_symlink():
        raise PermissionError("unsafe symlink: " + str(path))
    if path.exists():
        st = path.stat()
        if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
            raise PermissionError("unsafe file: " + str(path))

def merge(original, command):
    doc = json.loads(original) if original.strip() else {"hooks": {}}
    if not isinstance(doc, dict) or not isinstance(doc.get("hooks"), dict):
        raise ValueError("existing hooks.json invalid")
    for event in EVENTS:
        entries = doc["hooks"].setdefault(event, [])
        if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get("hooks"), list) for e in entries):
            raise ValueError("invalid existing hook group")
        if any(h.get("command") == command for e in entries for h in e["hooks"] if isinstance(h, dict)):
            continue
        group = {"hooks": [{"type": "command", "command": command, "timeout": 5}]}
        if event == "PreToolUse":
            group["matcher"] = ".*"
        entries.append(group)
    return json.dumps(doc, indent=2) + "\n"

def write(path, value):
    check(path)
    path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if path.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = path.with_name(path.name + ".backup-" + stamp)
        with backup.open("xb") as stream:
            stream.write(path.read_bytes())
        os.chmod(backup, 0o600)
    fd, temp = tempfile.mkstemp(prefix=".humanos-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as out:
            out.write(value)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def prepare(repo, sha, home):
    if not (repo / ".git").exists() or len(sha) != 40 or any(c not in "0123456789abcdef" for c in sha):
        raise ValueError("canonical repo or immutable commit invalid")
    source = subprocess.run(
        ["git", "-C", str(repo), "show", sha + ":scripts/codex_budget_hook.py"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True).stdout
    if "humanos.codex.hook-budget.v1" not in source:
        raise ValueError("unknown hook source")
    codex = home / ".codex"
    if codex.is_symlink() or (codex / "hooks").is_symlink():
        raise PermissionError("Codex configuration path has an unsafe symlink")
    config_toml = codex / "config.toml"
    if config_toml.is_file():
        with config_toml.open("rb") as stream:
            settings = tomllib.load(stream)
        if settings.get("features", {}).get("hooks") is False:
            raise ValueError("Codex hooks are explicitly disabled; no installation")
    script = home / ".codex" / "hooks" / "humanos_budget_hook.py"
    hooks = home / ".codex" / "hooks.json"
    for path in (script, hooks):
        check(path)
    if script.exists() and script.read_text() != source:
        raise ValueError("existing customized budget hook; manual reconciliation needed")
    original = hooks.read_text() if hooks.exists() else ""
    command = shlex.quote(sys.executable) + " " + shlex.quote(str(script))
    return script, source, hooks, merge(original, command)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        script, source, hooks, config = prepare(args.repo, args.commit, args.home)
        change_script = not script.exists()
        change_config = not hooks.exists() or hooks.read_text() != config
        if not args.dry_run:
            if change_script:
                write(script, source)
            if change_config:
                write(hooks, config)
        print(("WOULD INSTALL" if args.dry_run else "INSTALLED") + ": HumanOS Codex budget hooks")
        print("Hook:", script, "change:", change_script)
        print("Config:", hooks, "change:", change_config)
        print("4 turns / 24 local tool calls / 15 minutes per session.")
        print("Not a hard token cap. Restart Codex and trust/verify hooks.")
    except (OSError, ValueError, subprocess.CalledProcessError, PermissionError) as exc:
        parser.exit(2, "STOP: " + str(exc) + "\n")

if __name__ == "__main__":
    main()
