import json
import os
from pathlib import Path
import stat
import tempfile
import unittest

from browser_setup import (
    EXTENSION_ID,
    browser_status,
    config_path,
    control_root,
    extension_id_from_key,
    load_local_browser_config,
    native_manifest_path,
    remove_browser_setup,
    setup_browser,
)


class BrowserSetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        (self.repo / "browser_native_host.py").write_text("# host fixture\n", encoding="utf-8")
        self.home = self.root / "home"
        self.home.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def setup(self, **kwargs):
        return setup_browser(
            self.repo,
            target=kwargs.pop("target", "brave"),
            home=self.home,
            platform="darwin",
            python_executable="/usr/bin/python3",
            **kwargs,
        )

    def test_pinned_manifest_key_derives_expected_extension_id(self):
        self.assertEqual(extension_id_from_key(), EXTENSION_ID)
        self.assertRegex(EXTENSION_ID, r"^[a-p]{32}$")

    def test_setup_creates_private_local_pairing_outside_repo(self):
        report = self.setup(hosts=["github.com"], search_provider="duckduckgo")
        root = control_root(self.home)
        secret = root / "secret.bin"
        launcher = root / "native-host"
        runtime = config_path(self.home)
        manifest = native_manifest_path("brave", self.home, "darwin")

        self.assertTrue(report["configured"])
        self.assertTrue(secret.is_file())
        self.assertEqual(len(secret.read_bytes()), 32)
        self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((root / "state").stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(secret.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(runtime.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(launcher.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(manifest.stat().st_mode), 0o600)
        self.assertFalse(root.is_relative_to(self.repo))

        local = json.loads(runtime.read_text(encoding="utf-8"))
        self.assertEqual(local["extension_id"], EXTENSION_ID)
        self.assertEqual(local["hosts"], ["duckduckgo.com", "github.com"])
        self.assertNotIn(secret.read_bytes().hex(), runtime.read_text(encoding="utf-8"))

        native = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(native["name"], "com.humanos.browser_bridge")
        self.assertEqual(native["path"], str(launcher))
        self.assertEqual(native["allowed_origins"], ["chrome-extension://" + EXTENSION_ID + "/"])

        script = launcher.read_text(encoding="utf-8")
        self.assertIn(str(self.repo / "browser_native_host.py"), script)
        self.assertIn("--socket", script)
        self.assertIn(str(root / "bridge.sock"), script)
        self.assertIn("--secret", script)
        self.assertIn(str(secret), script)

    def test_runtime_config_builds_short_lived_host_envelope(self):
        self.setup(hosts=["github.com"], search_provider="google")
        runtime = load_local_browser_config(self.home, clock=lambda: 1000)
        self.assertEqual(runtime["envelope"]["expires"], 29800)
        self.assertEqual(runtime["envelope"]["hosts"], ["github.com", "google.com"])
        self.assertEqual(runtime["envelope"]["capabilities"], ["inspect", "navigate", "click", "type"])
        self.assertEqual(runtime["search_url"], "https://www.google.com/search?q={query}")
        self.assertNotIn("secret_bytes", runtime)

    def test_setup_is_idempotent_and_preserves_secret(self):
        self.setup(hosts=["github.com"])
        first = (control_root(self.home) / "secret.bin").read_bytes()
        self.setup(hosts=["developer.chrome.com"])
        second = (control_root(self.home) / "secret.bin").read_bytes()
        self.assertEqual(first, second)
        local = json.loads(config_path(self.home).read_text(encoding="utf-8"))
        self.assertEqual(local["hosts"], ["developer.chrome.com", "duckduckgo.com"])

    def test_invalid_host_and_target_fail_closed(self):
        with self.assertRaises(ValueError):
            self.setup(hosts=["https://example.com"])
        with self.assertRaises(ValueError):
            setup_browser(
                self.repo, target="safari", home=self.home, platform="darwin",
                python_executable="/usr/bin/python3",
            )

    def test_control_state_cannot_be_inside_repository(self):
        home = self.repo / "owner-home"
        home.mkdir()
        with self.assertRaises(PermissionError):
            setup_browser(
                self.repo, target="brave", home=home, platform="darwin",
                python_executable="/usr/bin/python3",
            )

    def test_status_without_setup_is_non_mutating(self):
        report = browser_status(self.repo, home=self.home, platform="darwin")
        self.assertFalse(report["configured"])
        self.assertFalse(config_path(self.home).exists())

    def test_uninstall_removes_only_humanos_pairing(self):
        self.setup(hosts=["github.com"])
        manifest = native_manifest_path("brave", self.home, "darwin")
        unrelated = manifest.parent / "other.host.json"
        unrelated.write_text("{}\n", encoding="utf-8")
        result = remove_browser_setup(self.repo, home=self.home, platform="darwin")
        self.assertTrue(result["removed"])
        self.assertFalse(control_root(self.home).exists())
        self.assertFalse(manifest.exists())
        self.assertTrue(unrelated.exists())


class BrowserExtensionStaticTests(unittest.TestCase):
    def test_extension_declares_native_messaging_and_pinned_key(self):
        root = Path(__file__).resolve().parents[1]
        manifest = json.loads((root / "browser-extension" / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("nativeMessaging", manifest["permissions"])
        self.assertEqual(extension_id_from_key(manifest["key"]), EXTENSION_ID)

    def test_selected_tab_zero_is_explicit_sentinel(self):
        root = Path(__file__).resolve().parents[1]
        worker = (root / "browser-extension" / "service-worker.js").read_text(encoding="utf-8")
        self.assertIn("command.tab_id !== 0", worker)
        self.assertIn("No tab is selected in HumanOS extension", worker)
        self.assertIn("waitForTabComplete", worker)


if __name__ == "__main__":
    unittest.main()
