import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ledger_notebook_projection import project_all_pairs, project_one_pair


class LedgerNotebookProjectionTests(unittest.TestCase):
    def test_projects_pair_and_is_idempotent_after_reopen(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "ledger.jsonl"
            rows = []
            for source_id, role, text in (("u1", "HUMAN", "hello"), ("a1", "ASSISTANT", "world")):
                rows.append({"source": "codex-rollout", "source_id": source_id, "conversation_id": "c1",
                             "role": role, "text": text,
                             "content_digest": hashlib.sha256(text.encode()).hexdigest()})
            ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            notebook = root / "notebook"
            first = project_one_pair(ledger, notebook)
            second = project_one_pair(ledger, notebook)
            self.assertEqual(first["status"], "CHECKPOINTED")
            self.assertEqual(second["status"], "ALREADY_PROJECTED")

    def test_projects_all_pairs_and_skips_them_on_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "ledger.jsonl"
            rows = []
            for i, (role, text) in enumerate((("HUMAN", "one"), ("ASSISTANT", "uno"),
                                               ("HUMAN", "two"), ("ASSISTANT", "dos"))):
                rows.append({"source": "codex-rollout", "source_id": role[0].lower() + str(i),
                             "conversation_id": "c1", "role": role, "text": text,
                             "content_digest": hashlib.sha256(text.encode()).hexdigest()})
            ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            notebook = root / "notebook"
            self.assertEqual(project_all_pairs(ledger, notebook), {"status": "CHECKPOINTED", "projected": 2, "skipped": 0, "pending": 0})
            self.assertEqual(project_all_pairs(ledger, notebook), {"status": "CHECKPOINTED", "projected": 0, "skipped": 2, "pending": 0})


    def test_round_trip_reopens_with_exact_transcript(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "ledger.jsonl"
            rows = []
            for source_id, role, text in (("u1", "HUMAN", "exact human"), ("a1", "ASSISTANT", "exact assistant")):
                rows.append({"source": "codex-rollout", "source_id": source_id, "conversation_id": "c1",
                             "role": role, "text": text,
                             "content_digest": hashlib.sha256(text.encode()).hexdigest()})
            ledger.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
            notebook = root / "notebook"
            result = project_one_pair(ledger, notebook)
            from notebook import Notebook
            book = Notebook(notebook)
            try:
                self.assertEqual(book.message_count(result["tx"]), 2)
                transcript = book.db.execute(
                    "SELECT role, text FROM transcript WHERE tx=? ORDER BY ordinal",
                    (result["tx"],),
                ).fetchall()
                self.assertEqual(
                    [(row["role"], row["text"]) for row in transcript],
                    [("HUMAN", "exact human"), ("ASSISTANT", "exact assistant")],
                )
            finally:
                book.close()


    def test_verify_missing_ledger_is_pending_and_does_not_create_notebook(self):
        # An empty Memory First source must remain PENDING: no fabricated
        # checkpoint and no unwanted Notebook side effect.
        import contextlib
        import io
        from humanos import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger = root / "missing-ledger.jsonl"
            notebook = root / "notebook"
            argv = ["verify", "--ledger", str(ledger), "--notebook", str(notebook)]

            def verify():
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    main(argv)
                return json.loads(output.getvalue())

            first = verify()
            self.assertEqual(first["ledger"], {"status": "PENDING", "rows": 0})
            self.assertEqual(first["runtime_capture"], "PENDING")
            self.assertNotIn("notebook", first)
            self.assertFalse(ledger.exists())
            self.assertFalse(notebook.exists())

            # Orphan receipts without a source ledger cannot establish capture.
            (root / "runtime-capture-receipts.jsonl").write_text("{}\\n", encoding="utf-8")
            second = verify()
            self.assertEqual(second["ledger"]["status"], "PENDING")
            self.assertEqual(second["runtime_capture"], "PENDING")
            self.assertNotIn("notebook", second)
            self.assertFalse(notebook.exists())


if __name__ == "__main__":
    unittest.main()
