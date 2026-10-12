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


    def test_explicit_synthetic_observed_turn_survives_restart(self):
        # A host may supply a turn only after it was explicitly observed and
        # authorized upstream. This test does not scrape a browser or capture
        # personal data: it exercises the existing provider-aware sink and
        # Notebook projector end-to-end with original synthetic evidence.
        from conversation_ledger import read_ledger, verify_ledger
        from ledger_capture_adapter import capture_observed_turn
        from notebook import Notebook

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, vault = root / "observed.jsonl", root / "notebook"
            human = "  Original synthetic human message 🧭\\nline 2  "
            assistant = "Original synthetic assistant response.\\n"
            args = (ledger, "synthetic-host", "conversation-1", "turn-1", human, assistant)

            first = capture_observed_turn(*args)
            self.assertEqual(first["added"], 2)
            self.assertEqual(first["verification"], {"rows": 2, "status": "CHECKPOINTED"})
            first_bytes = ledger.read_bytes()
            repeated = capture_observed_turn(*args)
            self.assertEqual(repeated["added"], 0)
            self.assertEqual(ledger.read_bytes(), first_bytes)

            original_rows = read_ledger(ledger)
            self.assertEqual([(row["source"], row["role"], row["text"]) for row in original_rows], [
                ("synthetic-host", "HUMAN", human), ("synthetic-host", "ASSISTANT", assistant)
            ])
            self.assertEqual(verify_ledger(ledger)["status"], "CHECKPOINTED")

            first_projection = project_all_pairs(ledger, vault)
            self.assertEqual(first_projection["projected"], 1)
            self.assertEqual(first_projection["pending"], 0)
            self.assertEqual(project_all_pairs(ledger, vault)["skipped"], 1)

            # Simulate process restart with a new Notebook connection. Exact
            # original messages remain intact and source ledger is unmodified.
            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                tx = "CAPTURE-turn-1:ASSISTANT"
                self.assertEqual(book.get_transaction(tx)["status"], "CHECKPOINTED")
                rows = book.db.execute(
                    "SELECT role, text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,)
                ).fetchall()
                self.assertEqual(
                    [(row["role"], row["text"]) for row in rows],
                    [("HUMAN", human), ("ASSISTANT", assistant)]
                )
            finally:
                book.close()
            self.assertEqual(ledger.read_bytes(), first_bytes)


    @staticmethod
    def _write_synthetic_rows(ledger, specs):
        rows = []
        for source, conversation, role, source_id, text in specs:
            rows.append({
                "source": source, "conversation_id": conversation,
                "role": role, "source_id": source_id, "text": text,
                "content_digest": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            })
        ledger.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )

    def test_projection_does_not_cross_source_or_conversation(self):
        for (source, conversation) in (("provider-b", "c1"), ("provider-a", "c2")):
            with self.subTest(source=source, conversation=conversation):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    ledger = root / "ledger.jsonl"
                    vault = root / "vault"
                    self._write_synthetic_rows(ledger, [
                        ("provider-a", "c1", "HUMAN", "t1:HUMAN", "original A"),
                        (source, conversation, "ASSISTANT", "t1:ASSISTANT", "original B"),
                    ])
                    for projector in (project_one_pair, project_all_pairs):
                        with self.assertRaisesRegex(ValueError, "source or conversation"):
                            projector(ledger, vault)
                        self.assertFalse(vault.exists())

    def test_projection_requires_observed_turn_key(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, vault = root / "ledger.jsonl", root / "vault"
            self._write_synthetic_rows(ledger, [
                ("provider-a", "c1", "HUMAN", "t1:HUMAN", "human t1"),
                ("provider-a", "c1", "ASSISTANT", "t2:ASSISTANT", "reply t2"),
            ])
            with self.assertRaisesRegex(ValueError, "matching source turn key"):
                project_all_pairs(ledger, vault)
            self.assertFalse(vault.exists())

    def test_reused_assistant_message_id_fails_closed_before_any_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, vault = root / "ledger.jsonl", root / "vault"
            self._write_synthetic_rows(ledger, [
                ("provider-a", "c1", "HUMAN", "same:HUMAN", "human A"),
                ("provider-a", "c1", "ASSISTANT", "same:ASSISTANT", "assistant A"),
                ("provider-b", "c2", "HUMAN", "same:HUMAN", "human B"),
                ("provider-b", "c2", "ASSISTANT", "same:ASSISTANT", "assistant B"),
            ])
            for projector in (project_one_pair, project_all_pairs):
                with self.assertRaisesRegex(ValueError, "Ambiguous projection transaction ID"):
                    projector(ledger, vault)
                self.assertFalse(vault.exists())

    def test_existing_transaction_must_match_verified_provenance(self):
        from notebook import Notebook
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, other, vault = root / "first.jsonl", root / "other.jsonl", root / "vault"
            first = [
                ("provider-a", "c1", "HUMAN", "t1:HUMAN", "original human"),
                ("provider-a", "c1", "ASSISTANT", "t1:ASSISTANT", "original assistant"),
            ]
            self._write_synthetic_rows(ledger, first)
            self.assertEqual(project_all_pairs(ledger, vault)["projected"], 1)

            def snapshot():
                book = Notebook(vault)
                try:
                    self.assertTrue(book.verify())
                    tx = "CAPTURE-t1:ASSISTANT"
                    state = book.task(tx)
                    self.assertEqual(state["source"], "provider-a")
                    self.assertEqual(state["conversation_id"], "c1")
                    self.assertEqual(state["human_source_id"], "t1:HUMAN")
                    self.assertEqual(state["assistant_source_id"], "t1:ASSISTANT")
                    counts = tuple(book.db.execute(
                        "SELECT COUNT(*) FROM " + name
                    ).fetchone()[0] for name in ("identities", "transactions", "events", "recovery"))
                    transcript = [(x["role"], x["text"]) for x in book.db.execute(
                        "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,)
                    )]
                    return counts, transcript, state
                finally:
                    book.close()

            before = snapshot()
            self.assertEqual(project_all_pairs(ledger, vault)["skipped"], 1)
            self.assertEqual(snapshot(), before)

            # Same assistant ID in a different source/conversation must not
            # silently count as a retry, even when original content matches.
            self._write_synthetic_rows(other, [
                ("provider-b", "c2", "HUMAN", "t1:HUMAN", "original human"),
                ("provider-b", "c2", "ASSISTANT", "t1:ASSISTANT", "original assistant"),
            ])
            with self.assertRaisesRegex(ValueError, "matching verified source evidence"):
                project_all_pairs(other, vault)
            self.assertEqual(snapshot(), before)

            # Same identity but conflicting text also fails without mutation.
            self._write_synthetic_rows(other, [
                ("provider-a", "c1", "HUMAN", "t1:HUMAN", "different human"),
                ("provider-a", "c1", "ASSISTANT", "t1:ASSISTANT", "original assistant"),
            ])
            with self.assertRaisesRegex(ValueError, "matching verified source evidence"):
                project_all_pairs(other, vault)
            self.assertEqual(snapshot(), before)

    def test_legacy_unattributed_projection_requires_reconciliation(self):
        from notebook import Notebook
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, vault = root / "ledger.jsonl", root / "vault"
            self._write_synthetic_rows(ledger, [
                ("provider-a", "c1", "HUMAN", "t1:HUMAN", "original human"),
                ("provider-a", "c1", "ASSISTANT", "t1:ASSISTANT", "original assistant"),
            ])
            book = Notebook(vault)
            try:
                identity = book.bind("Jon", "original human")
                tx = "CAPTURE-t1:ASSISTANT"
                book.start(identity["hcid"], tx, "original human")
                book.append(tx, 1, "ASSISTANT", "original assistant")
                book.save_task(tx, {"phase": "COMPLETE", "final": "original assistant",
                                    "final_ordinal": 1, "model": "codex-rollout"})
                book.checkpoint(tx)
                before = (
                    book.db.execute("SELECT COUNT(*) FROM identities").fetchone()[0],
                    book.db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
                )
            finally:
                book.close()
            with self.assertRaisesRegex(ValueError, "matching verified source evidence"):
                project_all_pairs(ledger, vault)
            check = Notebook(vault)
            try:
                self.assertTrue(check.verify())
                self.assertEqual(before, (
                    check.db.execute("SELECT COUNT(*) FROM identities").fetchone()[0],
                    check.db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
                ))
                self.assertEqual(check.task(tx)["model"], "codex-rollout")
            finally:
                check.close()

    def test_distinct_provider_turns_project_without_cross_pairing(self):
        from notebook import Notebook
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ledger, vault = root / "ledger.jsonl", root / "vault"
            self._write_synthetic_rows(ledger, [
                ("provider-a", "c1", "HUMAN", "a1:HUMAN", "human A"),
                ("provider-a", "c1", "ASSISTANT", "a1:ASSISTANT", "assistant A"),
                ("provider-b", "c2", "HUMAN", "b1:HUMAN", "human B"),
                ("provider-b", "c2", "ASSISTANT", "b1:ASSISTANT", "assistant B"),
            ])
            self.assertEqual(project_all_pairs(ledger, vault),
                             {"status": "CHECKPOINTED", "projected": 2, "skipped": 0, "pending": 0})
            self.assertEqual(project_all_pairs(ledger, vault)["skipped"], 2)
            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                for tx, source, original in (
                    ("CAPTURE-a1:ASSISTANT", "provider-a", "human A"),
                    ("CAPTURE-b1:ASSISTANT", "provider-b", "human B"),
                ):
                    self.assertEqual(book.task(tx)["source"], source)
                    self.assertEqual(book.get_transaction(tx)["input"], original)
            finally:
                book.close()


if __name__ == "__main__":
    unittest.main()
