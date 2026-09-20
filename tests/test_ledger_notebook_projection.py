import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ledger_notebook_projection import project_one_pair


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


if __name__ == "__main__":
    unittest.main()
