import os
import unittest

from experiments.ln0_sqlcipher_python_driver import run_python_driver_spike


@unittest.skipUnless(
    os.environ.get("HUMANOS_LN0_SQLCIPHER_PYTHON") == "1",
    "LN-0 Python SQLCipher qualification runs only in its dedicated job",
)
class LN0PythonSQLCipherDriverTests(unittest.TestCase):
    def test_candidate_driver_meets_minimum_notebook_contract(self):
        result = run_python_driver_spike()
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["candidate_package"], "sqlcipher3")
        self.assertTrue(result["dbapi_surface"])
        self.assertTrue(result["wal"])
        self.assertTrue(result["parameter_binding"])
        self.assertTrue(result["commit_reopen_readback"])
        self.assertTrue(result["wrong_key_rejected"])
        self.assertTrue(result["stdlib_sqlite_rejected"])
        self.assertTrue(result["plaintext_marker_absent"])
        self.assertTrue(result["plaintext_header_absent"])
        self.assertFalse(result["runtime_dependency_promoted"])


if __name__ == "__main__":
    unittest.main()
