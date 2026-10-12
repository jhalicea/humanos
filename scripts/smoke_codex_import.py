#!/usr/bin/env python3
"""Synthetic acceptance rehearsal for the opt-in one-turn Codex importer.

This creates no source from, and does not discover, a real Codex session.  It
uses only a private temporary root and removes it on every exit path.
"""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


REPO = Path(__file__).resolve().parents[1]
HUMAN = "synthetic idless human \U0001f9ed\nsecond line"
ASSISTANT = "synthetic idless assistant answer"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_cli(*args, expected=0):
    result = subprocess.run(
        [sys.executable, str(REPO / "humanos.py"), *map(str, args)],
        cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        check=False,
    )
    require(result.returncode == expected,
            "CLI exit mismatch for %s: %s" % (args[0], result.stderr))
    return result


def read_notebook(vault, transaction):
    code = (
        "import json, sys; from notebook import Notebook; "
        "book = Notebook(sys.argv[1]); "
        "print(json.dumps({'transaction': book.get_transaction(sys.argv[2]), "
        "'task': book.task(sys.argv[2]), 'records': [dict(row) for row in "
        "book.db.execute(\"SELECT role,text FROM transcript ORDER BY seq\")], "
        "'transaction_count': book.db.execute(\"SELECT COUNT(*) FROM transactions\").fetchone()[0], "
        "'verified': book.verify()}, sort_keys=True)); book.close()"
    )
    result = subprocess.run([sys.executable, "-c", code, str(vault), transaction], cwd=REPO,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    require(result.returncode == 0, "fresh Notebook readback failed: " + result.stderr)
    return json.loads(result.stdout)


def main():
    root = Path(tempfile.mkdtemp(prefix="humanos-codex-import-smoke-"))
    try:
        os.chmod(root, 0o700)
        capture = root / "capture"
        notebook_parent = root / "notebook-parent"
        capture.mkdir(mode=0o700)
        notebook_parent.mkdir(mode=0o700)
        source = root / "synthetic-rollout.jsonl"
        ledger = capture / "ledger.jsonl"
        notebook = notebook_parent / "notebook"
        records = [
            {"type": "session_meta", "payload": {"id": "synthetic-idless-session"}},
            {"type": "response_item", "payload": {"type": "message", "role": "user",
             "content": [{"type": "input_text", "text": HUMAN}]}},
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "synthetic-turn"}},
            {"type": "response_item", "payload": {"type": "message", "role": "assistant",
             "content": [{"type": "output_text", "text": ASSISTANT}]}},
            {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "synthetic-turn"}},
        ]
        source.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n",
                          encoding="utf-8")
        os.chmod(source, 0o600)
        before_hash = hashlib.sha256(source.read_bytes()).hexdigest()

        inspected = run_cli("inspect-codex", "--source", source)
        inspected_output = inspected.stdout + inspected.stderr
        require("synthetic idless human" not in inspected_output
                and "synthetic idless assistant" not in inspected_output,
                "inspection exposed synthetic conversation content")
        require(not ledger.exists() and not notebook.exists(),
                "metadata inspection created a destination")
        report = json.loads(inspected.stdout)
        require(report["status"] == "UNVERIFIED_METADATA_ONLY", "unexpected inspect status")
        messages = report["messages"]
        require([(row["role"], row["source_id_origin"]) for row in messages] == [
            ("HUMAN", "LOCAL_DERIVED_RECORD_V1"),
            ("ASSISTANT", "LOCAL_DERIVED_RECORD_V1"),
        ], "idless provenance was not reported exactly")
        ids = [row["source_id"] for row in messages]
        require(len(set(ids)) == 2 and all(value.startswith("local-record-v1:") for value in ids),
                "inspect did not return two derived selectable references")

        command = ("import-codex", "--source", source, "--ledger", ledger,
                   "--notebook", notebook, "--confirm-observed",
                   "--human-source-id", ids[0], "--assistant-source-id", ids[1])
        first = json.loads(run_cli(*command).stdout)
        require(first == {"status": "CHECKPOINTED", "source": "codex-rollout", "turns": 1,
                          "ledger": {"rows": 2, "status": "CHECKPOINTED"},
                          "notebook": {"status": "CHECKPOINTED", "projected": 1,
                                       "skipped": 0, "pending": 0}},
                "first import result changed")
        rows = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]
        require([(row["source_id"], row["source_id_origin"], row["source_line"], row["text"])
                 for row in rows] == [
            (ids[0], "LOCAL_DERIVED_RECORD_V1", 2, HUMAN),
            (ids[1], "LOCAL_DERIVED_RECORD_V1", 4, ASSISTANT),
        ], "ledger did not preserve selected text and derived provenance")
        first_ledger = ledger.read_bytes()
        require(hashlib.sha256(source.read_bytes()).hexdigest() == before_hash,
                "import changed the selected source")
        readback = read_notebook(notebook, "CAPTURE-" + ids[1])
        require(readback["verified"] is True
                and readback["transaction"]["input"] == HUMAN
                and readback["task"] == {
                    "phase": "COMPLETE", "final": ASSISTANT, "final_ordinal": 1,
                    "model": "codex-rollout", "projection_version": 1,
                    "source": "codex-rollout", "conversation_id": "synthetic-idless-session",
                    "human_source_id": ids[0], "assistant_source_id": ids[1],
                }
                and readback["records"] == [
                    {"role": "HUMAN", "text": HUMAN}, {"role": "ASSISTANT", "text": ASSISTANT},
                ] and readback["transaction_count"] == 1,
                "fresh Notebook process did not read exact selected provenance")

        repeated = json.loads(run_cli(*command).stdout)
        require(repeated["notebook"] == {"status": "CHECKPOINTED", "projected": 0,
                                         "skipped": 1, "pending": 0},
                "restart did not report one idempotent skip")
        require(ledger.read_bytes() == first_ledger, "restart duplicated ledger evidence")
        require(hashlib.sha256(source.read_bytes()).hexdigest() == before_hash,
                "restart changed the selected source")
        require(read_notebook(notebook, "CAPTURE-" + ids[1]) == readback,
                "restart changed the Notebook transcript or provenance")
        print("synthetic Codex import smoke: PASS")
    finally:
        shutil.rmtree(root)
        require(not root.exists(), "synthetic temporary root was not removed")


if __name__ == "__main__":
    main()
