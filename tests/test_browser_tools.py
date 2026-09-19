import json
from pathlib import Path
import tempfile
import unittest

from engine import Tools
from permissions import allows_read, task_scope
from runtime_info import format_observation, intent, request_for


class FakeBrowser:
    def __init__(self):
        self.approve = lambda _: False
        self.calls = []

    def execute(self, request):
        self.calls.append(request)
        if request["tool"] in ("navigate", "click", "type") and not self.approve(request):
            return {"ok": False, "error": "Human browser approval required"}
        if request["tool"] == "navigate":
            return {"ok": True, "observation": {"navigated": True, "url": request["arguments"]["url"], "title": "Search"}}
        if request["tool"] == "inspect":
            return {"ok": True, "observation": {
                "url": "https://duckduckgo.com/?q=humanos",
                "title": "humanos at DuckDuckGo",
                "text": "Result one\nResult two",
                "forms": [],
            }}
        return {"ok": True, "observation": {"accepted": request["tool"]}}


class BrowserPermissionTests(unittest.TestCase):
    def row(self, text):
        return {"tx": "tx", "hcid": "hcid", "input": text}

    def test_explicit_web_intent_enables_all_browser_tools(self):
        scope = task_scope(self.row("search the web for HumanOS"), "/tmp/workspace", version=7)
        self.assertTrue(scope["browser_enabled"])
        for name in ("browser_search", "browser_inspect", "browser_navigate", "browser_click", "browser_type"):
            request = {"name": name}
            self.assertTrue(allows_read(scope, request))

    def test_unrelated_conversation_does_not_enable_browser(self):
        scope = task_scope(self.row("tell me something interesting"), "/tmp/workspace")
        self.assertFalse(scope["browser_enabled"])
        self.assertFalse(allows_read(scope, {"name": "browser_inspect"}))


class BrowserToolTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.browser = FakeBrowser()
        self.tools = Tools(
            Path(self.tmp.name) / "workspace",
            browser=self.browser,
            browser_search_url="https://duckduckgo.com/?q={query}",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_browser_effect_is_authorized_exactly_once(self):
        approvals = []
        result = self.tools.execute(
            {"name": "browser_navigate", "tab_id": 0, "url": "https://example.com/"},
            lambda request: approvals.append(dict(request)) or True,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(approvals), 1)
        self.assertEqual(self.browser.calls[0]["tab_id"], 0)

    def test_browser_inspect_still_passes_task_policy(self):
        approvals = []
        result = self.tools.execute(
            {"name": "browser_inspect", "tab_id": 0},
            lambda request: approvals.append(dict(request)) or True,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(approvals), 1)
        self.assertEqual(self.browser.calls[0]["tool"], "inspect")

    def test_browser_search_navigates_then_inspects_with_one_authorization(self):
        approvals = []
        result = self.tools.execute(
            {"name": "browser_search", "tab_id": 0, "query": "HumanOS browser"},
            lambda request: approvals.append(dict(request)) or True,
        )
        self.assertTrue(result["ok"])
        self.assertEqual(len(approvals), 1)
        self.assertEqual([call["tool"] for call in self.browser.calls], ["navigate", "inspect"])
        payload = json.loads(result["stdout"])
        self.assertEqual(payload["observation"]["title"], "humanos at DuckDuckGo")
        self.assertIn("HumanOS+browser", payload["search_url"])

    def test_browser_failure_keeps_authorization_truth_separate(self):
        class Failing(FakeBrowser):
            def execute(self, request):
                self.calls.append(request)
                return {"ok": False, "error": "selected tab missing"}
        self.tools.browser = Failing()
        result = self.tools.execute(
            {"name": "browser_inspect", "tab_id": 0},
            lambda _: True,
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["authorization"], "ALLOWED")
        self.assertIn("selected tab missing", result["stderr"])

    def test_search_capability_requires_search_provider(self):
        tools = Tools(Path(self.tmp.name) / "other", browser=self.browser)
        state = tools.capability_states()["browser_search"]
        self.assertFalse(state["ready"])
        self.assertIn("search provider", state["reason"])


class BrowserIntentTests(unittest.TestCase):
    def test_capability_question_is_not_mistaken_for_search_action(self):
        self.assertEqual(intent("can you search the internet?"), "capabilities")

    def test_natural_search_action_becomes_browser_search(self):
        request = request_for("search the internet for HumanOS architecture", [])
        self.assertEqual(request, {
            "name": "browser_search",
            "tab_id": 0,
            "query": "HumanOS architecture",
        })

    def test_web_slash_command_preserves_query(self):
        request = request_for('/web "HumanOS Browser Bridge"', [])
        self.assertEqual(request["name"], "browser_search")
        self.assertEqual(request["query"], "HumanOS Browser Bridge")

    def test_search_observation_formats_as_human_readable_page(self):
        observation = {
            "ok": True,
            "stdout": json.dumps({
                "ok": True,
                "observation": {
                    "url": "https://duckduckgo.com/?q=humanos",
                    "title": "HumanOS Search",
                    "text": "First result",
                },
            }),
            "stderr": "",
            "authorization": "ALLOWED",
        }
        text = format_observation({"name": "browser_search"}, observation)
        self.assertIn("Web search results", text)
        self.assertIn("HumanOS Search", text)
        self.assertIn("First result", text)


if __name__ == "__main__":
    unittest.main()
