import os
import unittest

from experiments.ln0_sqlcipher_spike_v2 import run_sqlcipher_spike


@unittest.skipUnless(
    os.environ.get("HUMANOS_LN0_SQLCIPHER_SPIKE_V2") == "1",
    "LN-0 SQLCipher V2 spike runs only in its dedicated verification job",
)
class LN0SQLCipherSpikeV2Tests(unittest.TestCase):
    def test_v02_sqlcipher_storage_crash_export_and_recovery(self):
        result = run_sqlcipher_spike()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["revision"], 2)
        self.assertTrue(result["correct_key_readback"])
        self.assertTrue(result["wrong_key_rejected"])
        self.assertTrue(result["standard_sqlite_rejected"])
        self.assertTrue(result["wal_observed"])
        self.assertFalse(any(result["plaintext_scan"].values()))
        self.assertTrue(result["committed_crash_recovery"])
        self.assertTrue(result["uncommitted_crash_rollback"])
        self.assertTrue(result["encrypted_export_restore"])
        self.assertTrue(result["encrypted_backup_wrong_key_rejected"])
        self.assertTrue(result["independent_recovery_wrapper_proof"])
        self.assertTrue(result["plaintext_to_new_encrypted_export"])
        self.assertTrue(result["schema_trigger_exported"])
        self.assertFalse(result["keys_logged"])


if __name__ == "__main__":
    unittest.main()
