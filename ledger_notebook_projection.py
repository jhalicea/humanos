"""Project one verified ledger turn into the existing Life Notebook."""

from pathlib import Path

from conversation_ledger import read_ledger, verify_ledger
from notebook import Notebook


def project_one_pair(ledger, notebook_root):
    rows = [row for row in read_ledger(ledger) if row.get("event_type") != "METADATA_CORRECTION"]
    verify_ledger(ledger)
    if len(rows) < 2 or rows[0]["role"] != "HUMAN" or rows[1]["role"] != "ASSISTANT":
        raise ValueError("ledger must begin with one HUMAN/ASSISTANT pair")
    human, assistant = rows[0], rows[1]
    tx = "CAPTURE-" + assistant["source_id"]
    owned = book is None
    book = book or Notebook(Path(notebook_root))
    try:
        if book.get_transaction(tx) is not None:
            return {"status": "ALREADY_PROJECTED", "tx": tx}
        identity = book.bind("Jon", human["text"])
        book.start(identity["hcid"], tx, human["text"])
        book.append(tx, 1, "ASSISTANT", assistant["text"])
        book.save_task(tx, {"phase": "FINAL", "final": assistant["text"],
                            "final_ordinal": 1, "model": "codex-rollout"})
        book.save_task(tx, {"phase": "COMPLETE", "final": assistant["text"],
                            "final_ordinal": 1, "model": "codex-rollout"})
        book.checkpoint(tx)
        return {"status": "CHECKPOINTED", "tx": tx, "page": identity["page"]}
    finally:
        book.close()


def project_all_pairs(ledger, notebook_root=None, book=None):
    rows = [row for row in read_ledger(ledger) if row.get("event_type") != "METADATA_CORRECTION"]
    verify_ledger(ledger)
    pairs = []
    pending = 0
    human = None
    for row in rows:
        if row["role"] == "HUMAN":
            if human is not None:
                pending += 1
            human = row
        elif row["role"] == "ASSISTANT" and human is not None:
            pairs.append((human, row))
            human = None
        else:
            pending += 1
    if human is not None:
        pending += 1
    projected = 0
    skipped = 0
    owned = book is None
    book = book or Notebook(Path(notebook_root))
    try:
        for human, assistant in pairs:
            tx = "CAPTURE-" + assistant["source_id"]
            if book.get_transaction(tx) is not None:
                skipped += 1
                continue
            identity = book.bind("Jon", human["text"])
            book.start(identity["hcid"], tx, human["text"])
            book.append(tx, 1, "ASSISTANT", assistant["text"])
            book.save_task(tx, {"phase": "COMPLETE", "final": assistant["text"],
                                "final_ordinal": 1, "model": "codex-rollout"})
            book.checkpoint(tx)
            projected += 1
        return {"status": "CHECKPOINTED" if not pending else "PENDING",
                "projected": projected, "skipped": skipped, "pending": pending}
    finally:
        if owned:
            book.close()
