"""Regression checks for the public-safe, read-only Mac workspace inventory destinations."""

from pathlib import Path
import unittest

from scripts.audit_local_workspace import classify


class DeveloperWorkspaceLayoutTests(unittest.TestCase):
    def test_canonical_repository_has_numbered_destination(self):
        self.assertEqual(
            classify(Path("/sample/humanos"), {"is_git": True, "is_worktree": False}),
            ("CANONICAL_REPO", "MEDIUM", "~/Developer/10_Repos/<repository>/"),
        )

    def test_registered_worktree_has_numbered_destination(self):
        self.assertEqual(
            classify(Path("/sample/humanos-ln0"), {"is_git": True, "is_worktree": True}),
            ("ACTIVE_WORKTREE", "HIGH", "~/Developer/20_Worktrees/<product>/<workstream>/"),
        )

    def test_imports_and_evidence_use_numbered_destinations(self):
        self.assertEqual(
            classify(Path("/sample/incoming-import"), {"is_git": False}),
            ("IMPORT_MIGRATION", "MEDIUM", "~/Developer/50_Imports/<product>/"),
        )
        self.assertEqual(
            classify(Path("/sample/audit-results"), {"is_git": False}),
            ("GENERATED_EVIDENCE_ARTIFACT", "MEDIUM", "~/Developer/40_Artifacts/<product>/"),
        )

    def test_private_runtime_is_not_migrated_to_source(self):
        self.assertEqual(
            classify(Path("/sample/.humanos"), {"is_git": False}),
            ("PRIVATE_RUNTIME_STATE", "HIGH", "~/.humanos/private/"),
        )

    def test_archive_is_not_called_a_backup(self):
        self.assertEqual(
            classify(Path("/sample/archive"), {"is_git": False}),
            ("LEGACY_CANDIDATE", "MEDIUM", "~/Developer/90_Archive/<product>/"),
        )
        self.assertEqual(
            classify(Path("/sample/backup"), {"is_git": False}),
            ("BACKUP_ARCHIVE", "MEDIUM", None),
        )

    def test_unknown_item_requires_classification(self):
        self.assertEqual(
            classify(Path("/sample/other"), {"is_git": False}),
            ("UNKNOWN", "LOW", None),
        )


if __name__ == "__main__":
    unittest.main()
