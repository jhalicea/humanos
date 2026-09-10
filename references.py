"""Verified conversational reference binding for HumanOS.

Reference resolution is host-side and can only bind to paths captured from a
successful prior workspace tool observation. The language model never expands
its own authority.
"""
import json
import re
from pathlib import PurePosixPath
from notebook import encode

_ACTION = re.compile(r"\b(read|open|inspect|show|view|cat)\b", re.I)
_REFERENCE = re.compile(
    r"\b(it|that(?:\s+(?:file|one))?|this(?:\s+(?:file|one))?|the\s+(?:file|one))\b",
    re.I,
)
_EXPLICIT_FILE = re.compile(r"(?:^|\s)[^\s/]+\.[A-Za-z0-9]{1,12}(?:\s|$)")
_ORDINALS = {
    "first": 0, "1st": 0,
    "second": 1, "2nd": 1,
    "third": 2, "3rd": 2,
    "fourth": 3, "4th": 3,
    "fifth": 4, "5th": 4,
}


def reference_requested(text):
    if not isinstance(text, str):
        return False
    return bool(_ACTION.search(text) and _REFERENCE.search(text) and not _EXPLICIT_FILE.search(text))


def simple_reference_read(text):
    if not reference_requested(text):
        return False
    cleaned = text.strip().rstrip("?!,.")
    return bool(re.fullmatch(
        r"(?:please\s+)?(?:read|open|inspect|show|view|cat)(?:\s+me)?\s+"
        r"(?:it|that(?:\s+(?:file|one))?|this(?:\s+(?:file|one))?|the\s+(?:file|one))",
        cleaned, re.I))


def _safe_path(value):
    if not isinstance(value, str) or not value or any(c in value for c in "\r\n\t\0"):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") or part.startswith(".") for part in path.parts):
        return None
    return path.as_posix()


def _join(base, name):
    base = "." if base in (None, "") else base
    value = name if base == "." else str(PurePosixPath(base) / name)
    return _safe_path(value)


def capture_reference_frame(tx, request, observation):
    if not isinstance(request, dict) or not isinstance(observation, dict) or not observation.get("ok"):
        return None
    name = request.get("name")
    paths = []

    if name == "list_files":
        base = request.get("path", ".")
        for line in observation.get("stdout", "").splitlines():
            path = _join(base, line)
            if path:
                paths.append(path)
    elif name == "read_file":
        path = _safe_path(request.get("path"))
        if path:
            paths.append(path)
    elif name in ("scan_files", "find_duplicates"):
        try:
            report = json.loads(observation.get("stdout", ""))
        except (TypeError, json.JSONDecodeError):
            report = {}
        if name == "scan_files":
            for item in report.get("entries", []):
                if isinstance(item, dict) and item.get("kind") == "file":
                    path = _safe_path(item.get("path"))
                    if path:
                        paths.append(path)
        else:
            for group in report.get("groups", []):
                if isinstance(group, dict):
                    for value in group.get("files", []):
                        path = _safe_path(value)
                        if path:
                            paths.append(path)

    paths = list(dict.fromkeys(paths))
    if not paths:
        return None
    return {"version": 1, "tx": tx, "tool": name, "paths": paths}


def reference_frame_event(book, frame):
    return {
        "reference_frame_version": frame["version"],
        "source_tool": frame["tool"],
        "path_count": len(frame["paths"]),
        "frame_digest": book.content_digest(encode(frame)),
    }


def _event_digest(book, tx):
    row = book.db.execute(
        "SELECT payload FROM events WHERE tx=? AND kind='REFERENCE_FRAME' ORDER BY seq DESC LIMIT 1",
        (tx,),
    ).fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0]).get("frame_digest")
    except (TypeError, json.JSONDecodeError):
        return None


def _verified_frame(book, hcid, exclude_tx=None):
    rows = book.db.execute(
        """SELECT tx FROM transactions
           WHERE hcid=? AND tx!=? AND status='CHECKPOINTED'
           ORDER BY rowid DESC LIMIT 12""",
        (hcid, exclude_tx or ""),
    ).fetchall()
    for row in rows:
        tx = row["tx"] if hasattr(row, "keys") else row[0]
        state = book.task(tx) or {}
        frame = state.get("reference_frame")
        if not frame:
            continue
        if frame.get("tx") != tx or frame.get("version") != 1:
            raise PermissionError("Saved conversational reference frame is invalid")
        digest = book.content_digest(encode(frame))
        if _event_digest(book, tx) != digest:
            raise PermissionError("Saved conversational reference frame failed integrity verification")
        return frame, digest
    return None, None


def _binding(frame, digest, path, mode):
    return {
        "version": 1,
        "source_tx": frame["tx"],
        "frame_digest": digest,
        "path": path,
        "mode": mode,
    }


def resolve_reference(book, hcid, exclude_tx, text, workspace=None):
    if not reference_requested(text):
        return {"status": "none", "candidates": []}
    frame, digest = _verified_frame(book, hcid, exclude_tx)
    if not frame:
        return {"status": "unresolved", "candidates": []}
    candidates = frame["paths"]

    lowered = text.casefold()
    selected = None
    mode = "auto"
    for word, index in _ORDINALS.items():
        if re.search(r"\b" + re.escape(word) + r"\b", lowered):
            if index < len(candidates):
                selected, mode = candidates[index], "ordinal"
            break
    if selected is None and re.search(r"\blast\b", lowered) and candidates:
        selected, mode = candidates[-1], "ordinal"
    if selected is None and len(candidates) == 1:
        selected = candidates[0]

    if selected is not None:
        return {
            "status": "resolved",
            "candidates": candidates,
            "binding": _binding(frame, digest, selected, mode),
        }
    return {
        "status": "ambiguous",
        "candidates": candidates,
        "source_tx": frame["tx"],
        "frame_digest": digest,
    }


def bind_choice(resolution, path):
    if resolution.get("status") != "ambiguous" or path not in resolution.get("candidates", []):
        raise ValueError("Reference choice must be one of the verified candidates")
    return {
        "version": 1,
        "source_tx": resolution["source_tx"],
        "frame_digest": resolution["frame_digest"],
        "path": path,
        "mode": "human_menu",
    }


def validate_reference_binding(book, binding, hcid, text=None):
    expected_keys = {"version", "source_tx", "frame_digest", "path", "mode"}
    if not isinstance(binding, dict) or set(binding) != expected_keys or binding.get("version") != 1:
        raise PermissionError("Conversational reference binding is malformed")
    if binding.get("mode") not in ("auto", "ordinal", "human_menu"):
        raise PermissionError("Conversational reference binding mode is invalid")
    if text is not None and not reference_requested(text):
        raise PermissionError("Conversational reference binding does not match the human request")
    row = book.get_transaction(binding["source_tx"])
    if not row or row["hcid"] != hcid or row["status"] != "CHECKPOINTED":
        raise PermissionError("Conversational reference source is not a verified completed turn")
    state = book.task(binding["source_tx"]) or {}
    frame = state.get("reference_frame")
    if not frame or frame.get("tx") != binding["source_tx"]:
        raise PermissionError("Conversational reference source frame is missing")
    digest = book.content_digest(encode(frame))
    if digest != binding["frame_digest"] or _event_digest(book, binding["source_tx"]) != digest:
        raise PermissionError("Conversational reference source frame failed integrity verification")
    if binding["path"] not in frame.get("paths", []):
        raise PermissionError("Selected conversational reference was not in the verified source frame")
    return True


def clarification_text(resolution):
    candidates = resolution.get("candidates", [])
    if not candidates:
        return (
            "I understand that you mean a file from the conversation, but I do not have a verified "
            "recent file reference to bind safely. List the files again or name the file."
        )
    lines = ["Which file do you mean?"]
    lines.extend(f"  {index}. {path}" for index, path in enumerate(candidates[:20], 1))
    if len(candidates) > 20:
        lines.append(f"  … {len(candidates) - 20} more")
    lines.append("Reply with the filename or choose it in the interactive terminal.")
    return "\n".join(lines)
