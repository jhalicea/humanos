from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path, old, new):
    target = ROOT / path
    text = target.read_text()
    if text.count(old) != 1:
        raise SystemExit(f"{path}: patch anchor mismatch")
    target.write_text(text.replace(old, new, 1))


references = r'''"""Verified contextual reference binding for HumanOS.

Mirror resolves human references only against integrity-verified prior HumanOS
observations. Models may consume a resolved binding but can never manufacture
one or widen its authority.
"""
import json
import re
from pathlib import PurePosixPath
from notebook import encode

_FILE_ACTION = re.compile(r"\b(read|open|inspect|show|view|cat)\b", re.I)
_PLAN_ACTION = re.compile(r"\b(apply|do|use|execute|run|undo|revert)\b", re.I)
_REFERENCE = re.compile(r"\b(it|that(?:\s+(?:file|one|plan))?|this(?:\s+(?:file|one|plan))?|the\s+(?:file|one|plan))\b", re.I)
_EXPLICIT_FILE = re.compile(r"(?:^|\s)[^\s/]+\.[A-Za-z0-9]{1,12}(?:\s|$)")
_ORDINALS = {"first": 0, "1st": 0, "second": 1, "2nd": 1, "third": 2, "3rd": 2,
             "fourth": 3, "4th": 3, "fifth": 4, "5th": 4}


def reference_intent(text):
    if not isinstance(text, str):
        return None
    lowered = text.casefold().strip().rstrip("?!,.")
    if not lowered:
        return None
    if re.search(r"\b(plan|changes?|moves?)\b", lowered) and (_REFERENCE.search(lowered) or _PLAN_ACTION.search(lowered)):
        return "plan"
    if lowered in ("do it", "do that", "use it", "use that", "apply it", "apply that", "run it", "undo it", "revert it"):
        return "plan"
    if _FILE_ACTION.search(lowered) and _REFERENCE.search(lowered) and not _EXPLICIT_FILE.search(text):
        return "file"
    if any(re.search(r"\b" + re.escape(word) + r"\b", lowered) for word in _ORDINALS) and re.search(r"\b(file|one)\b", lowered):
        return "file"
    if re.search(r"\blast\b", lowered) and re.search(r"\b(file|one)\b", lowered):
        return "file"
    return None


def reference_requested(text):
    return reference_intent(text) is not None


def simple_reference_read(text):
    return reference_intent(text) == "file" and bool(_FILE_ACTION.search(text or ""))


def simple_plan_reference_action(text):
    return reference_intent(text) == "plan" and bool(_PLAN_ACTION.search(text or ""))


def _safe_path(value):
    if not isinstance(value, str) or not value or any(c in value for c in "\r\n\t\0"):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") or part.startswith(".") for part in path.parts):
        return None
    return path.as_posix()


def _join(base, name):
    base = "." if base in (None, "") else base
    return _safe_path(name if base == "." else str(PurePosixPath(base) / name))


def capture_reference_frame(tx, request, observation):
    if not isinstance(request, dict) or not isinstance(observation, dict) or not observation.get("ok"):
        return None
    name = request.get("name")
    kind, values = None, []
    if name == "list_files":
        kind = "file"
        base = request.get("path", ".")
        for line in observation.get("stdout", "").splitlines():
            value = _join(base, line)
            if value:
                values.append(value)
    elif name == "read_file":
        kind = "file"
        value = _safe_path(request.get("path"))
        if value:
            values.append(value)
    elif name in ("scan_files", "find_duplicates"):
        kind = "file"
        try:
            report = json.loads(observation.get("stdout", ""))
        except (TypeError, json.JSONDecodeError):
            report = {}
        if name == "scan_files":
            for item in report.get("entries", []):
                if isinstance(item, dict) and item.get("kind") == "file":
                    value = _safe_path(item.get("path"))
                    if value:
                        values.append(value)
        else:
            for group in report.get("groups", []):
                if isinstance(group, dict):
                    for item in group.get("files", []):
                        value = _safe_path(item)
                        if value:
                            values.append(value)
    elif name in ("plan_organization", "plan_contextual_organization", "plan_inbox_organization", "plan_move"):
        kind = "plan"
        try:
            report = json.loads(observation.get("stdout", ""))
        except (TypeError, json.JSONDecodeError):
            report = {}
        value = report.get("plan_id") or report.get("id")
        if isinstance(value, str) and value:
            values.append(value)
    values = list(dict.fromkeys(values))
    if not kind or not values:
        return None
    return {"version": 2, "tx": tx, "tool": name, "kind": kind, "paths": values}


def reference_frame_event(book, frame):
    return {"reference_frame_version": frame["version"], "source_tool": frame["tool"],
            "reference_kind": frame.get("kind", "file"), "path_count": len(frame["paths"]),
            "frame_digest": book.content_digest(encode(frame))}


def _event_digest(book, tx):
    row = book.db.execute("SELECT payload FROM events WHERE tx=? AND kind='REFERENCE_FRAME' ORDER BY seq DESC LIMIT 1", (tx,)).fetchone()
    if not row:
        return None
    try:
        return json.loads(row[0]).get("frame_digest")
    except (TypeError, json.JSONDecodeError):
        return None


def _frame_kind(frame):
    return "file" if frame.get("version") == 1 else frame.get("kind")


def _verified_frame(book, hcid, exclude_tx=None, kind=None):
    rows = book.db.execute("""SELECT tx FROM transactions WHERE hcid=? AND tx!=? AND status='CHECKPOINTED'
                            ORDER BY rowid DESC LIMIT 20""", (hcid, exclude_tx or "")).fetchall()
    for row in rows:
        tx = row["tx"] if hasattr(row, "keys") else row[0]
        state = book.task(tx) or {}
        frame = state.get("reference_frame")
        if not frame:
            continue
        if frame.get("tx") != tx or frame.get("version") not in (1, 2):
            raise PermissionError("Saved contextual reference frame is invalid")
        frame_kind = _frame_kind(frame)
        if frame_kind not in ("file", "plan"):
            raise PermissionError("Saved contextual reference kind is invalid")
        if kind and frame_kind != kind:
            continue
        digest = book.content_digest(encode(frame))
        if _event_digest(book, tx) != digest:
            raise PermissionError("Saved contextual reference frame failed integrity verification")
        return frame, digest
    return None, None


def _binding(frame, digest, value, mode):
    if frame.get("version") == 1:
        return {"version": 1, "source_tx": frame["tx"], "frame_digest": digest, "path": value, "mode": mode}
    return {"version": 2, "source_tx": frame["tx"], "frame_digest": digest,
            "path": value, "kind": _frame_kind(frame), "mode": mode}


def resolve_reference(book, hcid, exclude_tx, text, workspace=None):
    kind = reference_intent(text)
    if not kind:
        return {"status": "none", "candidates": []}
    frame, digest = _verified_frame(book, hcid, exclude_tx, kind)
    if not frame:
        # Short follow-ups such as "do it" keep their historical behavior when
        # there is no verified plan to bind.
        if text.casefold().strip().rstrip("?!,.") in ("do it", "do that", "use it", "use that", "run it"):
            return {"status": "none", "candidates": []}
        return {"status": "unresolved", "candidates": [], "kind": kind}
    candidates = frame["paths"]
    lowered, selected, mode = text.casefold(), None, "auto"
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
        return {"status": "resolved", "candidates": candidates,
                "binding": _binding(frame, digest, selected, mode), "kind": kind}
    return {"status": "ambiguous", "candidates": candidates, "source_tx": frame["tx"],
            "frame_digest": digest, "kind": kind,
            "prompt": "Which plan do you mean?" if kind == "plan" else "Which file do you mean?"}


def bind_choice(resolution, path):
    if resolution.get("status") != "ambiguous" or path not in resolution.get("candidates", []):
        raise ValueError("Reference choice must be one of the verified candidates")
    return {"version": 2, "source_tx": resolution["source_tx"], "frame_digest": resolution["frame_digest"],
            "path": path, "kind": resolution.get("kind", "file"), "mode": "human_menu"}


def validate_reference_binding(book, binding, hcid, text=None):
    if not isinstance(binding, dict) or binding.get("version") not in (1, 2):
        raise PermissionError("Contextual reference binding is malformed")
    expected = {"version", "source_tx", "frame_digest", "path", "mode"}
    if binding.get("version") == 2:
        expected.add("kind")
    if set(binding) != expected or binding.get("mode") not in ("auto", "ordinal", "human_menu"):
        raise PermissionError("Contextual reference binding is malformed")
    if text is not None and not reference_requested(text):
        raise PermissionError("Contextual reference binding does not match the human request")
    row = book.get_transaction(binding["source_tx"])
    if not row or row["hcid"] != hcid or row["status"] != "CHECKPOINTED":
        raise PermissionError("Contextual reference source is not a verified completed turn")
    state = book.task(binding["source_tx"]) or {}
    frame = state.get("reference_frame")
    if not frame or frame.get("tx") != binding["source_tx"]:
        raise PermissionError("Contextual reference source frame is missing")
    digest = book.content_digest(encode(frame))
    if digest != binding["frame_digest"] or _event_digest(book, binding["source_tx"]) != digest:
        raise PermissionError("Contextual reference source frame failed integrity verification")
    if binding["path"] not in frame.get("paths", []):
        raise PermissionError("Selected contextual reference was not in the verified source frame")
    if binding.get("version") == 2:
        if binding.get("kind") != _frame_kind(frame) or reference_intent(text) != binding.get("kind"):
            raise PermissionError("Contextual reference kind does not match the human request")
    return True


def clarification_text(resolution):
    candidates = resolution.get("candidates", [])
    kind = resolution.get("kind", "file")
    if not candidates:
        noun = "plan" if kind == "plan" else "file"
        return f"I understand that you mean a {noun} from the conversation, but I do not have a verified recent {noun} reference to bind safely. Name it explicitly or create/list it again."
    lines = [resolution.get("prompt") or ("Which plan do you mean?" if kind == "plan" else "Which file do you mean?")]
    lines.extend(f"  {index}. {value}" for index, value in enumerate(candidates[:20], 1))
    if len(candidates) > 20:
        lines.append(f"  … {len(candidates) - 20} more")
    lines.append("Choose it in the interactive terminal or name it explicitly.")
    return "\n".join(lines)
'''

(ROOT / "references.py").write_text(references)

replace_once("runtime_info.py",
             "from references import simple_reference_read",
             "from references import simple_plan_reference_action, simple_reference_read")
replace_once("runtime_info.py",
             "    if reference_binding and simple_reference_read(text):\n        return {'name': 'read_file', 'path': reference_binding['path']}\n",
             "    if reference_binding and reference_binding.get('kind', 'file') == 'file' and simple_reference_read(text):\n        return {'name': 'read_file', 'path': reference_binding['path']}\n    if reference_binding and reference_binding.get('kind') == 'plan' and simple_plan_reference_action(text):\n        lowered = text.casefold()\n        name = 'undo_plan' if re.search(r'\\b(undo|revert)\\b', lowered) else 'apply_plan'\n        return {'name': name, 'plan_id': reference_binding['path']}\n")

replace_once("permissions.py",
             "    if version >= 5 and reference_binding:\n        paths.append(reference_binding['path'])\n",
             "    if version >= 5 and reference_binding and reference_binding.get('kind', 'file') == 'file':\n        paths.append(reference_binding['path'])\n")

replace_once("server.py",
             "                    choice = choose_reference(resolution['candidates'])\n",
             "                    choice = choose_reference(resolution['candidates'], prompt=resolution.get('prompt', 'Which item do you mean?'))\n")

with (ROOT / "tests" / "test_references.py").open("a") as f:
    f.write(r'''

class ContextReferencePlanTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn

    def _plan(self):
        (self.workspace / "a.txt").write_text("a")
        agent = self.agent(
            {"tool": {"name": "plan_move", "source": "a.txt", "destination": "Archive/a.txt"}},
            {"final": "Plan ready."},
        )
        self.turn(agent, "/move a.txt Archive/a.txt", tx="plan-tx")
        frame = self.book.task("plan-tx").get("reference_frame")
        self.assertEqual(frame["kind"], "plan")
        self.assertEqual(len(frame["paths"]), 1)
        return frame["paths"][0]

    def test_do_it_binds_recent_verified_plan(self):
        plan_id = self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        self.assertEqual(resolution["status"], "resolved")
        self.assertEqual(resolution["binding"]["kind"], "plan")
        self.assertEqual(resolution["binding"]["path"], plan_id)

    def test_do_it_becomes_exact_apply_plan_request(self):
        plan_id = self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        from runtime_info import request_for
        request = request_for("do it", [], reference_binding=resolution["binding"])
        self.assertEqual(request, {"name": "apply_plan", "plan_id": plan_id})

    def test_plan_binding_cannot_be_retyped_as_file_authority(self):
        self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        binding = dict(resolution["binding"])
        binding["kind"] = "file"
        from references import validate_reference_binding
        with self.assertRaisesRegex(PermissionError, "kind"):
            validate_reference_binding(self.book, binding, self.binding["hcid"], "read that file")
''')
