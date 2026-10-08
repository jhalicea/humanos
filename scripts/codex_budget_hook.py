"""HumanOS Codex budget lifecycle hooks: advisory action caps, not token caps."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import time
import tomllib

MAX_TURNS, MAX_TOOLS, MAX_SECONDS = 4, 24, 900
# Strict per-session ceilings: no automatic resets or escalation.
SCHEMA = "humanos.codex.hook-budget.v1"

def scoped(cwd, home=None):
    if not isinstance(cwd, str) or not cwd:
        return False
    home = (home or Path.home()).resolve()
    location = Path(cwd).resolve()
    repo = home / "Developer" / "10_Repos" / "humanos"
    work = home / "Developer" / "20_Worktrees" / "humanos"
    return location == repo or repo in location.parents or (
        location != work and work in location.parents)

def denied(kind, reason):
    reason = ("HUMANOS REPLAN_REQUIRED: " + reason +
              "; preserve verified findings; no automatic budget increase. "
              "A new authorized bounded work slice is required.")
    if kind == "PreToolUse":
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny", "permissionDecisionReason": reason}}
    if kind == "PreCompact":
        return {"continue": False, "stopReason": reason}
    return {"decision": "block", "reason": reason}

def low_configuration_problem(home):
    """Inspect persistent Codex defaults. Explicit session overrides remain unobservable."""
    config = home / ".codex" / "config.toml"
    if config.is_symlink() or not config.is_file():
        return "LOW_EFFORT_DEFAULTS_MISSING"
    try:
        with config.open("rb") as source:
            settings = tomllib.load(source)
        agents = settings.get("agents", {})
        if (settings.get("model_reasoning_effort") != "low" or
                settings.get("plan_mode_reasoning_effort") != "low" or
                not isinstance(agents, dict) or
                agents.get("default_subagent_reasoning_effort") != "low" or
                agents.get("default_subagent_model") != "gpt-6-luna" or
                agents.get("max_concurrent_threads_per_session") != 1):
            return "LOW_EFFORT_DEFAULTS_DRIFTED"
        root = home / ".codex" / "agents"
        if root.is_symlink():
            return "CUSTOM_AGENT_DIRECTORY_UNSAFE"
        if root.exists():
            for agent in root.glob("*.toml"):
                if agent.is_symlink() or not agent.is_file():
                    return "CUSTOM_AGENT_CONFIG_UNSAFE"
                with agent.open("rb") as source:
                    data = tomllib.load(source)
                effort = data.get("model_reasoning_effort")
                if effort is not None and effort != "low":
                    return "CUSTOM_AGENT_EFFORT_NOT_LOW"
    except (OSError, ValueError, TypeError):
        return "LOW_EFFORT_CONFIG_UNREADABLE"
    return None


def assess(event, state, now):
    kind = event.get("hook_event_name")
    if kind not in ("UserPromptSubmit", "PreToolUse", "PreCompact"):
        return {}, False
    if type(now) not in (int, float) or now < 0:
        return denied(kind, "INVALID_CLOCK"), False
    # Codex does not currently expose an authoritative effective effort field.
    # If one is present and contradicts LOW, fail closed.
    effective_effort = event.get("model_reasoning_effort")
    if effective_effort is not None and effective_effort != "low":
        return denied(kind, "EFFECTIVE_EFFORT_NOT_LOW"), False
    sid = event.get("session_id")
    if not isinstance(sid, str) or not 0 < len(sid) <= 250:
        return denied(kind, "session identifier missing"), False
    key = hashlib.sha256(sid.encode()).hexdigest()
    record = state["sessions"].get(key)
    if record is None:
        if kind != "UserPromptSubmit":
            return denied(kind, "no approved prompt"), False
        record = {"opened": now, "turns": [], "tools": []}
        state["sessions"][key] = record
    if not isinstance(record, dict) or not isinstance(record.get("opened"), (int, float)) or not isinstance(record.get("turns"), list) or not isinstance(record.get("tools"), list):
        return denied(kind, "invalid budget record"), False
    elapsed = now - record["opened"]
    if elapsed < -5 or elapsed >= MAX_SECONDS:
        return denied(kind, "session time allowance exhausted"), False
    if kind == "PreCompact":
        return {}, False
    identifier = event.get("turn_id" if kind == "UserPromptSubmit" else "tool_use_id")
    if not isinstance(identifier, str) or not 0 < len(identifier) <= 250:
        return denied(kind, "hook event identifier missing"), False
    item = "turns" if kind == "UserPromptSubmit" else "tools"
    limit = MAX_TURNS if item == "turns" else MAX_TOOLS
    identity = hashlib.sha256(identifier.encode()).hexdigest()
    if identity in record[item]:
        return {}, False
    if len(record[item]) >= limit:
        return denied(kind, item + " budget exhausted"), False
    record[item].append(identity)
    warning = 100 * len(record[item]) >= 80 * limit or elapsed >= 720
    return ({"systemMessage": "HumanOS budget warning: checkpoint and STOP -> REPLAN."} if warning else {}), True

def run(event, home=None, now=None):
    if not isinstance(event, dict):
        return denied("UserPromptSubmit", "invalid input")
    kind = event.get("hook_event_name")
    if kind not in ("UserPromptSubmit", "PreToolUse", "PreCompact") or not scoped(event.get("cwd"), home):
        return {}
    resolved_home = home or Path.home()
    problem = low_configuration_problem(resolved_home)
    if problem:
        return denied(kind, problem)
    directory = resolved_home / ".codex" / "humanos-budget"
    if directory.is_symlink():
        raise PermissionError("state symlink")
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    info = directory.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError("state not private")
    fd = os.open(directory / "state.lock", os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(fd, "rb") as lock:
        info = os.fstat(lock.fileno())
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("unsafe lock")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        path = directory / "state.json"
        if path.exists():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > 2000000:
                raise PermissionError("unsafe ledger")
            state = json.loads(path.read_text())
        else:
            state = {"schema": SCHEMA, "sessions": {}}
        if not isinstance(state, dict) or state.get("schema") != SCHEMA or not isinstance(state.get("sessions"), dict):
            raise ValueError("bad ledger")
        result, changed = assess(event, state, time.time() if now is None else now)
        if changed:
            fd2, temp = tempfile.mkstemp(prefix=".budget-", dir=directory)
            try:
                os.fchmod(fd2, 0o600)
                with os.fdopen(fd2, "w") as output:
                    json.dump(state, output)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        return result

if __name__ == "__main__":
    try:
        raw = sys.stdin.buffer.read(131073)
        if len(raw) > 131072:
            raise ValueError("large event")
        event = json.loads(raw)
        result = run(event)
    except (OSError, ValueError, TypeError, KeyError, PermissionError):
        kind = event.get("hook_event_name", "UserPromptSubmit") if "event" in locals() and isinstance(event, dict) else "UserPromptSubmit"
        result = denied(kind, "budget state inaccessible")
    print(json.dumps(result))
