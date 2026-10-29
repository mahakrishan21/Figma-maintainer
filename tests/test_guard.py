"""figma_guard.py: enforced Figma write rules, including the live-edit prompt."""
import json, unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import fixtures, run, temp_home, transcript

KEY = "TESTKEY1234567890abcdeF"
MAKER = "figma-maintainer:figma-maintainer"


def iso(dt):
    return dt.isoformat(timespec="seconds")


class Guard(unittest.TestCase):
    def setUp(self):
        self.td, self.home = temp_home()
        self.tp = transcript(self.home, [f"Use figma-maintainer: fix the hero on https://www.figma.com/design/{KEY}/x?node-id=1-2"])
        self.fx = fixtures(self.home / "fx", {})  # no network in tests; meta unknown unless a test adds it

    def tearDown(self):
        self.td.cleanup()

    def guard(self, code, agent=MAKER, key=KEY, tool="mcp__claude_ai_Figma__use_figma", tp=None, env=None):
        hook = {"tool_name": tool, "agent_type": agent, "agent_id": "a1", "transcript_path": str(tp or self.tp),
                "tool_input": {"fileKey": key, "code": code, "description": "test"}}
        out, err, rc = run("figma_guard.py", hook, self.home, env=dict({"FIGMA_FIXTURES": str(self.fx)}, **(env or {})))
        self.assertEqual(rc, 0, err)
        if not out.strip():
            return "allow", ""
        o = json.loads(out)["hookSpecificOutput"]
        return o["permissionDecision"], o["permissionDecisionReason"]

    def log(self):
        f = self.home / "figma-audit-log.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    def test_read_only_agents_denied(self):
        for a in ("figma-maintainer:qa-checker", "figma-maintainer:client-comments", "figma-maintainer:consistency-auditor"):
            self.assertEqual(self.guard("return 1", agent=a)[0], "deny", a)

    def test_file_not_linked_denied(self):
        d, why = self.guard("n.characters = 'x'", key="OTHERKEY123456789abcdeF")
        self.assertEqual(d, "deny"); self.assertIn("was not linked", why)

    def test_network_and_page_delete_denied(self):
        self.assertEqual(self.guard("await fetch('https://x')")[0], "deny")
        self.assertEqual(self.guard("figma.currentPage.remove()")[0], "deny")

    def test_risky_writes_ask(self):
        self.assertEqual(self.guard("figma.createPage()")[0], "ask")
        self.assertEqual(self.guard("nodes.forEach(n => { n.remove() })")[0], "ask")

    def test_skip_invisible_is_a_read(self):
        d, _ = self.guard("figma.skipInvisibleInstanceChildren = true; const n = await figma.getNodeByIdAsync('1:2'); return n.name;")
        self.assertEqual(d, "allow")
        self.assertEqual(self.log()[-1]["decision"], "read")

    def test_log_has_session_and_agent(self):
        self.guard("n.characters = 'x'")
        rec = self.log()[-1]
        self.assertEqual(rec["agent_id"], "a1"); self.assertEqual(rec["session"], "session-test")

    def _baseline(self, minutes_ago):
        with open(self.home / "figma-audit-log.jsonl", "a") as f:
            f.write(json.dumps({"ts": iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)), "tool": "use_figma",
                                "fileKey": KEY, "decision": "completed"}) + "\n")

    def _meta(self, minutes_ago):
        fixtures(self.fx, {f"/files/{KEY}/meta": {"file": {"name": "t", "last_touched_at":
                                                          iso(datetime.now(timezone.utc) - timedelta(minutes=minutes_ago))}}})

    def test_live_edit_asks_when_file_changed_after_last_write(self):
        self._baseline(10); self._meta(1)
        d, why = self.guard("n.characters = 'x'")
        self.assertEqual(d, "ask"); self.assertIn("the file changed", why)

    def test_live_edit_quiet_when_only_our_own_write(self):
        self._baseline(10); self._meta(9)  # within the save grace
        self.assertEqual(self.guard("n.characters = 'x'")[0], "allow")

    def test_live_edit_never_blocks_when_figma_unreachable(self):
        self._baseline(10)
        fixtures(self.fx, {f"/files/{KEY}/meta": {"status": 503}})
        self.assertEqual(self.guard("n.characters = 'x'")[0], "allow")
        self.assertTrue(any(r.get("decision") == "live-edit-check-skipped" for r in self.log()))

    def test_no_baseline_no_check(self):
        self._meta(1)
        self.assertEqual(self.guard("n.characters = 'x'")[0], "allow")


if __name__ == "__main__":
    unittest.main()
