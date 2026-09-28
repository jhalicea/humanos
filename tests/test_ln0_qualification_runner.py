"""Adversarial checks for the deterministic LN-0 qualification runner."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tooling.ln0_baseline_qualification import verify_manifest_hash


class QualificationRunnerTests(unittest.TestCase):
    def test_current_manifest_matches_frozen_candidate_hash(self):
        from tooling.ln0_baseline_qualification import EXPECTED_MANIFEST_SHA256, MANIFEST
        self.assertTrue(EXPECTED_MANIFEST_SHA256)
        self.assertTrue(verify_manifest_hash(MANIFEST, EXPECTED_MANIFEST_SHA256)[0])

    def test_tampered_manifest_does_not_match_frozen_hash(self):
        with tempfile.TemporaryDirectory(prefix="ln0-manifest-tamper-") as root:
            manifest = Path(root) / "manifest.md"
            original = b"canonical qualification manifest\n"
            manifest.write_bytes(original)
            expected = hashlib.sha256(original).hexdigest()
            self.assertEqual(verify_manifest_hash(manifest, expected), (True, expected))
            manifest.write_bytes(b"tampered qualification manifest\n")
            matches, actual = verify_manifest_hash(manifest, expected)
            self.assertFalse(matches)
            self.assertNotEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
