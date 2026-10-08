"""Regression tests for cautious Developer-root inventory (no local-Mac access)."""

import contextlib
import io
import json
import stat
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts.audit_local_workspace import classify, main


ROOT = Path("/sample/Developer")
MOCK_REMOTE = "https://example.test/owner/humanos.git"


class DeveloperWorkspaceLayoutTests(unittest.TestCase):
    def test_canonical_location_requires_expected_parent_and_git_remote(self):
        self.assertEqual(
            classify(ROOT / "10_Repos/humanos", {
                "is_git": True, "is_worktree": False, "remote_origin": MOCK_REMOTE
            }, ROOT),
            ("CANONICAL_REPO", "MEDIUM", "~/Developer/10_Repos/<repository>/"),
        )

    def test_git_clone_outside_canonical_root_is_not_called_canonical(self):
        self.assertEqual(
            classify(Path("/sample/Downloads/humanos"), {
                "is_git": True, "is_worktree": False, "remote_origin": MOCK_REMOTE
            }, ROOT),
            ("LEGACY_CANDIDATE", "LOW", "~/Developer/10_Repos/<repository>/"),
        )

    def test_git_checkout_without_verified_remote_is_not_called_canonical(self):
        self.assertEqual(
            classify(ROOT / "10_Repos/humanos", {
                "is_git": True, "is_worktree": False, "remote_origin": None
            }, ROOT),
            ("LEGACY_CANDIDATE", "LOW", "~/Developer/10_Repos/<repository>/"),
        )

    def test_registered_worktree_requires_expected_folder(self):
        self.assertEqual(
            classify(ROOT / "20_Worktrees/humanos/feature", {
                "is_git": True, "is_worktree": True
            }, ROOT),
            ("ACTIVE_WORKTREE", "MEDIUM", "~/Developer/20_Worktrees/<product>/<workstream>/"),
        )
        self.assertEqual(
            classify(Path("/sample/Desktop/feature"), {
                "is_git": True, "is_worktree": True
            }, ROOT),
            ("LEGACY_CANDIDATE", "LOW", "~/Developer/20_Worktrees/<product>/<workstream>/"),
        )

    def test_imports_and_evidence_use_numbered_destinations(self):
        self.assertEqual(
            classify(Path("/sample/incoming-import"), {"is_git": False}, ROOT),
            ("IMPORT_MIGRATION", "MEDIUM", "~/Developer/50_Imports/<product>/"),
        )
        self.assertEqual(
            classify(Path("/sample/audit-results"), {"is_git": False}, ROOT),
            ("GENERATED_EVIDENCE_ARTIFACT", "MEDIUM", "~/Developer/40_Artifacts/<product>/"),
        )

    def test_private_runtime_keeps_external_boundary(self):
        self.assertEqual(
            classify(Path("/sample/.humanos"), {"is_git": False}, ROOT),
            ("PRIVATE_RUNTIME_STATE", "HIGH", "~/.humanos/private/"),
        )

    def test_archive_is_not_called_disaster_backup(self):
        self.assertEqual(
            classify(Path("/sample/archive"), {"is_git": False}, ROOT),
            ("LEGACY_CANDIDATE", "MEDIUM", "~/Developer/90_Archive/<product>/"),
        )
        self.assertEqual(
            classify(Path("/sample/backup"), {"is_git": False}, ROOT),
            ("BACKUP_ARCHIVE", "MEDIUM", None),
        )

    def test_unknown_stays_unknown(self):
        self.assertEqual(
            classify(Path("/sample/other"), {"is_git": False}, ROOT),
            ("UNKNOWN", "LOW", None),
        )

    def _run_with_args(self, args):
        with patch.object(sys, "argv", ["workspace-audit", *args]):
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return main()

    def test_default_scope_only_scans_developer_root(self):
        with tempfile.TemporaryDirectory() as temp:
            top = Path(temp)
            root = top / "Developer"
            (root / "10_Repos").mkdir(parents=True)
            (root / "00_Map.md").write_text("Local-only placeholder")
            # Content outside Developer should not be found without --root.
            outside = top / "Documents"
            outside.mkdir()
            (outside / "private_note.txt").write_text("Never put in inventory")
            # Even an in-root symlink must not broaden the default scope.
            (root / "outside-link").symlink_to(outside / "private_note.txt")
            out = root / "40_Artifacts" / "humanos" / "workspace-audit"
            self.assertEqual(self._run_with_args(["--developer-root", str(root), "--output-dir", str(out)]), 0)
            manifests = list(out.glob("WORKSPACE_INVENTORY_*.json"))
            csv_reports = list(out.glob("WORKSPACE_INVENTORY_*.csv"))
            self.assertEqual(len(manifests), 1)
            self.assertEqual(len(csv_reports), 1)
            self.assertEqual(stat.S_IMODE(out.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(manifests[0].stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(csv_reports[0].stat().st_mode), 0o600)
            records = json.loads(manifests[0].read_text())
            self.assertTrue(records)
            self.assertTrue(all(Path(record["path"]).resolve().is_relative_to(root.resolve()) for record in records))
            self.assertFalse(any("private_note" in record["path"] for record in records))

    def test_repo_output_directory_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Developer"
            (root / "10_Repos" / "humanos").mkdir(parents=True)
            bad = root / "10_Repos" / "humanos" / "audit-output"
            self.assertEqual(self._run_with_args(["--developer-root", str(root), "--output-dir", str(bad)]), 2)
            self.assertFalse(bad.exists())

    def test_group_readable_existing_report_folder_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "Developer"
            (root / "10_Repos").mkdir(parents=True)
            out = root / "40_Artifacts" / "humanos" / "audit"
            out.mkdir(parents=True)
            out.chmod(0o755)
            self.assertEqual(self._run_with_args(["--developer-root", str(root), "--output-dir", str(out)]), 2)
            self.assertEqual(list(out.glob("WORKSPACE_INVENTORY_*")), [])

    def test_missing_developer_root_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "no-such-developer-root"
            out = root / "40_Artifacts" / "audit"
            self.assertEqual(self._run_with_args(["--developer-root", str(root), "--output-dir", str(out)]), 2)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
