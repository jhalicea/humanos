
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook


class PrivacyHideUnhideTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.book = Notebook(Path(self.tmp.name))
        self.identity = self.book.bind("Jon", "privacy test")
        self.hcid = self.identity["hcid"]
        self.tx = "TX-privacy-test"
        self.book.start(self.hcid, self.tx, "private message")
        self.book.append(self.tx, 1, "ASSISTANT", "public reply")

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def test_hide_filters_projection(self):
        self.book.set_privacy(self.tx, 0, "HIDE", confirmation="HIDE")
        page = self.book.projections()["pages/" + self.identity["page"] + ".json"]
        self.assertNotIn("private message", page)
        self.assertIn("public reply", page)

    def test_unhide_restores_projection(self):
        self.book.set_privacy(self.tx, 0, "HIDE", confirmation="HIDE")
        self.book.set_privacy(self.tx, 0, "UNHIDE", confirmation="UNHIDE")
        page = self.book.projections()["pages/" + self.identity["page"] + ".json"]
        self.assertIn("private message", page)

    def test_non_human_authorization_rejected(self):
        with self.assertRaises(PermissionError):
            self.book.set_privacy(
                self.tx, 0, "HIDE",
                actor="model:qwen",
                confirmation="HIDE",
            )

    def test_receipt_is_append_only(self):
        self.book.set_privacy(self.tx, 0, "HIDE", confirmation="HIDE")
        with self.assertRaises(Exception):
            self.book.db.execute(
                "DELETE FROM privacy_receipts"
            )


if __name__ == "__main__":
    unittest.main()
