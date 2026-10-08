"""HumanOS HOS-MR-001: bounded OpenAI Responses transport using existing BudgetGovernor.

Only calls made through THIS opt-in transport are controlled. This module
does not intercept Codex Desktop/ChatGPT-plan traffic and does not set a
universal account billing limit. No auto-retry, tools, streaming, or background
inference. The API key is never persisted.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib import error, request

from budget_governor import BudgetGovernor, BudgetLimits

SCHEMA = "humanos.responses.budget.v1"
API_ROOT = "https://api.openai.com/v1"
MODEL_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}$")


class ReplanRequired(RuntimeError):
    """A budget/authority failure that must not be automatically retried."""


class ResponsesTransport:
    """Minimal stdlib API client. No implicit SDK retries or alternate endpoints."""

    def __init__(self, api_key: str, timeout: float = 90):
        if not isinstance(api_key, str) or not api_key.strip():
            raise ValueError("OPENAI_API_KEY required for live calls")
        self.key = api_key
        self.timeout = timeout
        # Avoid leaking bearer credentials through ambient HTTP proxies.
        self.opener = request.build_opener(request.ProxyHandler({}))

    def post(self, path: str, payload: dict) -> dict:
        if path not in ("/responses/input_tokens", "/responses"):
            raise ValueError("unapproved endpoint")
        body = json.dumps(payload, separators=(",", ":")).encode()
        req = request.Request(API_ROOT + path, body, {
            "Authorization": "Bearer " + self.key,
            "Content-Type": "application/json",
        }, method="POST")
        try:
            with self.opener.open(req, timeout=self.timeout) as response:
                raw = response.read(4_000_001)
                if len(raw) > 4_000_000:
                    raise ReplanRequired("PROVIDER_RESPONSE_TOO_LARGE")
                result = json.loads(raw)
        except error.HTTPError as exc:
            # Do not expose response bodies, credentials or private input.
            raise ReplanRequired("PROVIDER_HTTP_" + str(exc.code)) from None
        except (error.URLError, TimeoutError, OSError, ValueError):
            raise ReplanRequired("PROVIDER_RESULT_UNCERTAIN") from None
        if not isinstance(result, dict):
            raise ReplanRequired("PROVIDER_JSON_INVALID")
        return result


def _validate_inputs(model, prompt, instructions, output_cap, limits):
    if not isinstance(model, str) or not MODEL_PATTERN.fullmatch(model):
        raise ValueError("model ID invalid; use an explicit Responses API model ID")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise ValueError("bounded nonempty text prompt required (<=100k characters)")
    if not isinstance(instructions, str) or len(instructions) > 20_000:
        raise ValueError("bounded text instructions required (<=20k characters)")
    if type(output_cap) is not int or not 16 <= output_cap <= limits.max_output_tokens:
        raise ValueError("output cap must be between 16 and max_output_tokens")
    if not isinstance(limits, BudgetLimits):
        raise ValueError("BudgetLimits required")


def _validate_private_path(path: Path) -> None:
    if not path.is_absolute():
        raise PermissionError("ledger path must be absolute")
    if path.name in ("", ".", "..") or path.suffix != ".json":
        raise PermissionError("ledger must be an explicit JSON filename")
    # Canonical private state stays outside public repositories/worktrees.
    private = Path.home() / ".humanos" / "private"
    if private not in path.parents:
        raise PermissionError("ledger must reside under ~/.humanos/private")
    cursor = path.parent
    while cursor != Path.home() and cursor != cursor.parent:
        if cursor.is_symlink():
            raise PermissionError("ledger parent is a symlink")
        cursor = cursor.parent
    if path.is_symlink():
        raise PermissionError("ledger is a symlink")
    if path.exists():
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.getuid():
            raise PermissionError("unsafe existing ledger")


def _private_directory(path: Path) -> None:
    # Create only the approved private state tree, never folders in repo or Documents.
    private = Path.home() / ".humanos" / "private"
    elements = [Path.home() / ".humanos", private]
    current = private
    for name in path.relative_to(private).parts:
        current = current / name
        elements.append(current)
    for item in elements:
        if item.is_symlink():
            raise PermissionError("private state path contains symlink")
        item.mkdir(mode=0o700, exist_ok=True)
        info = item.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("state directory is not owner-private")


@contextmanager
def _locked_ledger(path: Path):
    _validate_private_path(path)
    parent = path.parent
    _private_directory(parent)
    lockfile = path.with_name(path.name + ".lock")
    if lockfile.is_symlink():
        raise PermissionError("unsafe lock symlink")
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(lockfile, flags, 0o600)
    with os.fdopen(fd, "rb") as lock:
        info = os.fstat(lock.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise PermissionError("unsafe budget lock")
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        if path.exists():
            info = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                    or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > 200_000):
                raise PermissionError("unsafe budget ledger")
            state = json.loads(path.read_text())
        else:
            state = None
        yield state


def _write_ledger(path: Path, state: dict):
    fd, tmp = tempfile.mkstemp(prefix=".humanos-budget-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(state, stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        # Keep the budget checkpoint durable before any paid dispatch.
        parent_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _load_or_create(saved, model, limits):
    if saved is None:
        gov = BudgetGovernor(limits)
        return {"schema": SCHEMA, "model": model,
                "limits": asdict(limits), "checkpoint": gov.checkpoint(),
                "calls": []}, gov
    if not isinstance(saved, dict) or set(saved) != {
            "schema", "model", "limits", "checkpoint", "calls"}:
        raise ReplanRequired("BUDGET_LEDGER_INVALID")
    if (saved["schema"] != SCHEMA or saved["model"] != model
            or saved["limits"] != asdict(limits)
            or not isinstance(saved["calls"], list)):
        raise ReplanRequired("BUDGET_POLICY_CHANGED_OR_INVALID")
    try:
        gov = BudgetGovernor.restore(saved["checkpoint"], limits)
    except (ValueError, TypeError, KeyError):
        raise ReplanRequired("BUDGET_CHECKPOINT_INVALID") from None
    if len(saved["calls"]) > gov.calls:
        raise ReplanRequired("BUDGET_USAGE_LEDGER_INVALID")
    return saved, gov


def _get_output(response):
    parts = []
    for item in response.get("output", []):
        if isinstance(item, dict) and item.get("type") == "message":
            for block in item.get("content", []):
                if isinstance(block, dict) and block.get("type") == "output_text":
                    if isinstance(block.get("text"), str):
                        parts.append(block["text"])
    return "\n".join(parts)


def execute(*, ledger_path: Path, model: str, prompt: str, instructions: str,
            output_cap: int, limits: BudgetLimits, transport) -> dict:
    """Require explicit caller consent outside this function for API billing.

    Acquires a per-task lock, asks provider for exact text input count, reserves
    count+provider output cap, DURABLY saves checkpoint, then makes one request.
    Unknown result/usage never triggers an automatic replay.
    """
    _validate_inputs(model, prompt, instructions, output_cap, limits)
    ledger_path = Path(ledger_path)
    with _locked_ledger(ledger_path) as old:
        state, gov = _load_or_create(old, model, limits)
        if gov.halted_reason:
            raise ReplanRequired(gov.halted_reason)
        if gov.pending:
            raise ReplanRequired("UNCERTAIN_INFLIGHT_CALL_ON_RESTART")
        count_body = {"model": model, "input": prompt}
        if instructions:
            count_body["instructions"] = instructions
        counted = transport.post("/responses/input_tokens", count_body)
        n = counted.get("input_tokens")
        if (type(n) is not int or n < 0 or
                counted.get("object") != "response.input_tokens"):
            raise ReplanRequired("INPUT_TOKEN_COUNT_UNVERIFIED")
        decision = gov.reserve(effort="low", input_token_bound=n,
                               output_token_cap=output_cap,
                               provider_enforces_low=True,
                               provider_enforces_output_cap=True)
        state["checkpoint"] = gov.checkpoint()
        if not decision["dispatch_allowed_by_budget"]:
            _write_ledger(ledger_path, state)
            raise ReplanRequired(decision["reason"])
        # A crash after this checkpoint NEVER silently replays a possibly billed
        # response. Do not record prompt or key in the ledger.
        _write_ledger(ledger_path, state)
        request_body = dict(count_body)
        request_body.update({"reasoning": {"effort": "low"},
                             "max_output_tokens": output_cap, "store": False,
                             "tools": [], "tool_choice": "none",
                             "parallel_tool_calls": False,
                             "truncation": "disabled"})
        # Text-only, single response, no delegated tools or background work.
        try:
            response = transport.post("/responses", request_body)
        except Exception:
            raise ReplanRequired("PROVIDER_RESULT_UNCERTAIN_NO_RETRY") from None
        usage = response.get("usage")
        if not isinstance(usage, dict):
            gov.complete(input_tokens=None, output_tokens=None)
            state["checkpoint"] = gov.checkpoint()
            _write_ledger(ledger_path, state)
            raise ReplanRequired("PROVIDER_USAGE_UNVERIFIED")
        input_used, output_used = usage.get("input_tokens"), usage.get("output_tokens")
        total = usage.get("total_tokens")
        if (type(total) is not int or type(input_used) is not int or
                type(output_used) is not int or total != input_used + output_used):
            gov.complete(input_tokens=None, output_tokens=None)
            state["checkpoint"] = gov.checkpoint()
            _write_ledger(ledger_path, state)
            raise ReplanRequired("PROVIDER_USAGE_INVALID")
        result = gov.complete(input_tokens=input_used, output_tokens=output_used)
        state["checkpoint"] = gov.checkpoint()
        state["calls"].append({"model": model, "input_tokens": input_used,
               "output_tokens": output_used, "reserved_input_tokens": n,
               "max_output_tokens": output_cap,
               "response_status": response.get("status"),
               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
        _write_ledger(ledger_path, state)
        if result["status"] == "REPLAN_REQUIRED":
            raise ReplanRequired(result["reason"])
        if response.get("status") not in ("completed", "incomplete"):
            raise ReplanRequired("PROVIDER_RESPONSE_UNEXPECTED_STATUS")
        if response.get("status") not in ("completed", "incomplete"):
            gov._stop("PROVIDER_RESPONSE_UNEXPECTED_STATUS")
            state["checkpoint"] = gov.checkpoint()
            _write_ledger(ledger_path, state)
            raise ReplanRequired("PROVIDER_RESPONSE_UNEXPECTED_STATUS")
        text = _get_output(response)
        return {"status": response["status"], "text": text, "usage": usage,
                "reserved_total_tokens": gov.reserved_tokens,
                "remaining_reservation_tokens": limits.max_total_tokens - gov.reserved_tokens,
                "budget_status": result["status"],
                "incomplete_reason": (response.get("incomplete_details") or {}).get("reason")}
