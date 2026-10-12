"""Thin local command surface for the verified conversation kernel."""

import argparse
import json
import os
import stat
import sys
from pathlib import Path

from capture_current_conversation import capture_audit, capture_current, capture_status
from conversation_ledger import _messages, read_ledger
from local_kernel_capture import capture_turn
from ledger_notebook_projection import project_all_pairs
from conversation_ledger import verify_ledger

DEFAULT_LEDGER = Path(__file__).resolve().parent / "var" / "current-conversation.jsonl"


def import_selected_codex_turn(source, ledger, notebook):
    """Manual one-turn local import; never enumerate browser or Codex sessions.

    Explicit source/destinations are required, the provider conversation and
    exact turn must be unambiguous, and all data stays outside this repository.
    """
    source, ledger, notebook = (Path(value) for value in (source, ledger, notebook))
    paths = (source, ledger, notebook)
    if any(not path.is_absolute() for path in paths):
        raise ValueError("Source, ledger, and Notebook paths must be absolute")
    source, ledger, notebook = (path.resolve() for path in paths)
    repo = Path(__file__).resolve().parent
    if any(path == repo or repo in path.parents for path in (source, ledger, notebook)):
        raise ValueError("Import files must remain outside the HumanOS repository")
    if source == ledger or source == notebook or ledger == notebook:
        raise ValueError("Import source and destinations must be distinct")
    if notebook in source.parents or notebook in ledger.parents:
        raise ValueError("Source and ledger may not be inside the Notebook vault")
    if not source.is_file() or source.suffix != ".jsonl" or paths[0].is_symlink():
        raise ValueError("Explicit source must be a regular rollout JSONL file")
    if source.stat().st_size > 1024 * 1024:
        raise ValueError("Selected rollout exceeds the one-turn import size limit")
    if paths[1].is_symlink() or paths[2].is_symlink():
        raise ValueError("Ledger and Notebook destinations may not be symbolic links")
    # Receipts and ledger plaintext require an owner-only parent directory;
    # a predictable path in shared /tmp (or a public home directory) is unsafe.
    for parent in (ledger.parent, notebook.parent):
        if (not parent.is_dir() or parent.stat().st_uid != os.getuid()
                or stat.S_IMODE(parent.stat().st_mode) & 0o077):
            raise ValueError("Ledger and Notebook parent directories must be owner-only")

    # The existing importer silently ignores unsupported records. This
    # stricter opt-in route must not call a partial parse 'complete'.
    raw = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines()
           if line.strip()]
    if any(not isinstance(record, dict) for record in raw):
        raise ValueError("Selected rollout contains invalid records")
    meta = [record.get("payload", {}) for record in raw
            if record.get("type") == "session_meta"]
    if len(meta) != 1 or not isinstance(meta[0], dict):
        raise ValueError("A single explicit Codex session is required")
    session = meta[0].get("session_id") or meta[0].get("id")
    if not isinstance(session, str) or not session:
        raise ValueError("Selected session is missing a stable ID")
    expected_roles = ["user", "assistant"]
    relevant = [record for record in raw
                if record.get("type") == "response_item"
                and isinstance(record.get("payload"), dict)
                and record["payload"].get("role") in ("user", "assistant")]
    if [record["payload"]["role"] for record in relevant] != expected_roles:
        raise ValueError("Exactly one ordered HUMAN/ASSISTANT turn is required")
    observed = list(_messages(source))
    if (len(observed) != 2 or [row["role"] for row in observed] != ["HUMAN", "ASSISTANT"]
            or any(row["conversation_id"] != session for row in observed)
            or observed[0]["source_id"] == observed[1]["source_id"]):
        raise ValueError("Incomplete or ambiguous selected source turn")

    if ledger.exists():
        verify_ledger(ledger)
        previous = read_ledger(ledger)
        permitted = {row["source_id"] for row in observed}
        if any(row.get("event_type") or row.get("source") != "codex-rollout"
               or row.get("conversation_id") != session
               or row.get("source_id") not in permitted for row in previous):
            raise ValueError("Ledger contains evidence outside the selected source turn")

    # The existing explicit capture path supplies append-only receipts. A
    # projection failure never rewrites the ledger or claims Notebook success.
    captured = capture_current(ledger, source)
    projected = project_all_pairs(ledger, notebook)
    if projected["pending"] or projected["projected"] + projected["skipped"] != 1:
        raise RuntimeError("Selected source turn did not yield one verified Notebook projection")
    return {
        "status": "CHECKPOINTED",
        "source": "codex-rollout",
        "turns": 1,
        "ledger": captured["verification"],
        "notebook": projected,
    }


def main(argv=None):
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    if raw_args and raw_args[0] == "academy":
        from learning.academy_cli import main as academy_main
        return academy_main(raw_args[1:])

    parser = argparse.ArgumentParser(prog="humanos")
    parser.add_argument("command", choices=("capture", "turn", "project", "verify", "status", "audit", "import-codex"))
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--conversation-id")
    parser.add_argument("--turn-id")
    parser.add_argument("--human")
    parser.add_argument("--assistant")
    parser.add_argument("--notebook", type=Path)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--confirm-observed", action="store_true",
                        help="Explicit owner confirmation for the selected one-turn Codex import")
    args = parser.parse_args(raw_args)
    if args.command == "import-codex":
        if not args.confirm_observed or any(value is None for value in
                                            (args.source, args.ledger, args.notebook)):
            parser.error("import-codex requires --source, --ledger, --notebook and --confirm-observed")
        try:
            result = import_selected_codex_turn(args.source, args.ledger, args.notebook)
        except (OSError, ValueError, RuntimeError, UnicodeError):
            # Avoid printing exception details that might contain private paths.
            parser.error("Selected Codex import failed validation or projection")
    elif args.command == "capture":
        result = capture_current(args.ledger, args.source)
    elif args.command == "turn":
        required = (args.conversation_id, args.turn_id, args.human, args.assistant)
        if any(value is None for value in required):
            parser.error("turn requires --conversation-id, --turn-id, --human, and --assistant")
        result = capture_turn(args.ledger or DEFAULT_LEDGER, args.conversation_id, args.turn_id,
                              args.human, args.assistant)
    elif args.command == "project":
        if args.notebook is None:
            parser.error("project requires --notebook")
        result = project_all_pairs(args.ledger or DEFAULT_LEDGER, args.notebook)
    elif args.command == "verify":
        ledger = args.ledger or DEFAULT_LEDGER
        if not ledger.exists():
            # Missing evidence is PENDING, even when an orphan runtime receipt
            # exists. Verification must not create a Notebook from no ledger.
            result = {"ledger": {"status": "PENDING", "rows": 0},
                      "capture": capture_status(ledger),
                      "runtime_capture": "PENDING",
                      "reason": "local ledger has not been created yet"}
        else:
            runtime_receipt = ledger.parent / "runtime-capture-receipts.jsonl"
            runtime_status = "CHECKPOINTED" if runtime_receipt.exists() else "PENDING"
            result = {"ledger": verify_ledger(ledger), "capture": capture_status(ledger),
                      "runtime_capture": runtime_status}
            if args.notebook is not None:
                result["notebook"] = project_all_pairs(ledger, args.notebook)
    elif args.command == "status":
        result = capture_status(args.ledger)
    else:
        result = capture_audit(args.ledger)
    if args.pretty and args.command == "verify":
        print("HumanOS verification")
        print("  Ledger:  " + result["ledger"]["status"] + f" ({result['ledger'].get('rows', 0)} rows)")
        print("  Capture: " + result["capture"]["status"])
        if "runtime_capture" in result:
            print("  Runtime capture: " + result["runtime_capture"])
        if "notebook" in result:
            notebook = result["notebook"]
            print("  Notebook: " + notebook["status"] +
                  f" (projected={notebook.get('projected', 0)}, skipped={notebook.get('skipped', 0)})")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
