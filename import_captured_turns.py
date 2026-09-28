#!/usr/bin/env python3
"""Materialize pending ChatGPT capture evidence into the canonical Life Notebook."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from capture_ledger import CaptureLedger
from notebook import Notebook


def _now():
    return datetime.now(timezone.utc).isoformat()


def import_pending(vault, capture_path, owner="chatgpt"):
    """Append pending turns; returns counts. Capture rows remain untouched."""
    captures = CaptureLedger(capture_path)
    book = Notebook(vault)
    imported = blocked = 0
    try:
        # Projections are derived files; repair them from authoritative SQLite before
        # start() performs its fail-closed readback check. Transcript rows are untouched.
        book.project()
        captures.db.executescript("""
          CREATE TABLE IF NOT EXISTS capture_materializations(
            message_id TEXT PRIMARY KEY, tx TEXT NOT NULL, hcid TEXT NOT NULL,
            text_sha256 TEXT NOT NULL, imported_at TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS capture_materializations_no_update
            BEFORE UPDATE ON capture_materializations BEGIN
              SELECT RAISE(ABORT, 'append-only materialization receipt'); END;
          CREATE TRIGGER IF NOT EXISTS capture_materializations_no_delete
            BEFORE DELETE ON capture_materializations BEGIN
              SELECT RAISE(ABORT, 'append-only materialization receipt'); END;
        """)
        rows = captures.db.execute("""
          SELECT p.* FROM pending_turns p
          LEFT JOIN capture_materializations m ON m.message_id=p.message_id
          WHERE m.message_id IS NULL
          ORDER BY p.rowid
        """).fetchall()
        active = {}
        for row in rows:
            chat = row["chat_id"]
            ident = book.db.execute(
                "SELECT * FROM identities WHERE owner=? ORDER BY created LIMIT 1",
                (owner + ":" + chat,)).fetchone()
            if not ident:
                ident = book.bind(owner + ":" + chat,
                                  "Imported ChatGPT chat " + row["chat_title"])
            hcid = ident["hcid"]
            txrow = book.db.execute("""
              SELECT tx FROM transactions WHERE hcid=? AND status!='CHECKPOINTED'
              ORDER BY created DESC LIMIT 1
            """, (hcid,)).fetchone()
            tx = txrow["tx"] if txrow else None
            if row["role"] == "USER":
                tx = "CAP-" + row["message_id"]
                try:
                    book.start(hcid, tx, row["text"])
                except RuntimeError as error:
                    if "Notebook readback mismatch" not in str(error):
                        raise
                    # A projection may have changed while the identity was created;
                    # repair once, then require the normal fail-closed start check.
                    book.project()
                    book.verify()
                    book.start(hcid, tx, row["text"])
                active[chat] = tx
            elif tx is None:
                blocked += 1
                continue
            else:
                active[chat] = tx
                ordinal = book.message_count(tx)
                book.append(tx, ordinal, "ASSISTANT", row["text"])
            with captures.db:
                captures.db.execute(
                    "INSERT INTO capture_materializations VALUES(?,?,?,?,?)",
                    (row["message_id"], tx, hcid, row["text_sha256"], _now()))
            imported += 1
        return {"imported": imported, "blocked": blocked, "remaining": captures.db.execute(
            "SELECT COUNT(*) FROM pending_turns p LEFT JOIN capture_materializations m "
            "ON m.message_id=p.message_id WHERE m.message_id IS NULL").fetchone()[0]}
    finally:
        book.close()
        captures.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import pending ChatGPT turns into HumanOS")
    parser.add_argument("--vault", default="HumanOS_Vault")
    parser.add_argument("--capture-ledger", default="HumanOS_Vault/runtime/capture-ledger.sqlite3")
    parser.add_argument("--owner", default="chatgpt")
    args = parser.parse_args(argv)
    print(json.dumps(import_pending(args.vault, args.capture_ledger, args.owner),
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
