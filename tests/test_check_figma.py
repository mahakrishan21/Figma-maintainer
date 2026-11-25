"""/figma-maintainer:check-figma: the connected Figma account is shown and confirmed before any figma-maintainer work;
Figma calls are blocked in a conversation until the user confirms."""
import json, sys, unittest

from tests.helpers import ROOT, SCRIPTS, context, run, temp_home

sys.path.insert(0, str(SCRIPTS))

ON = {"FIGMA_MAINTAINER_ACCOUNT_CHECK": "on"}
LINK = "https://www.figma.com/design/jUau2sA38TBr0R2HjR75HE/x?node-id=1-2"


class CheckFigma(unittest.TestCase):
    def setUp(self):
        self.td, self.home = temp_home()
        self.tp = self.home / "sess-123.jsonl"
        self.tp.write_text(json.dumps({"type": "user", "message": {"role": "user", "content": f"Use figma-maintainer: fix the heading on {LINK}"}}) + "\n")

    def tearDown(self):
        self.td.cleanup()

    def confirm(self):
        out, err, rc = run("figma_account.py", {}, self.home, args=["--session", "sess-123", "--confirm", "--mcp", "Design Studio invision@e2m.example"])
        self.assertEqual(rc, 0, err)

    def prompt_ctx(self, prompt):
        return context(run("image_gate.py", {"prompt": prompt, "transcript_path": str(self.tp), "session_id": "sess-123"}, self.home, env=ON)[0])

    def guard(self):
        out, _, _ = run("figma_guard.py", {"tool_name": "mcp__claude_ai_Figma__use_figma", "agent_type": "figma-maintainer:figma-maintainer",
                                           "tool_input": {"fileKey": "jUau2sA38TBr0R2HjR75HE", "code": "return 1"},
                                           "transcript_path": str(self.tp)}, self.home, env=ON)
        return out

    def test_job_prompt_asks_for_the_account_check_until_confirmed(self):
        ctx = self.prompt_ctx(f"Use figma-maintainer: fix the heading on {LINK}, no new images")
        self.assertIn("FIGMA ACCOUNT CHECK FIRST", ctx); self.assertIn("check-figma.md", ctx); self.assertIn("sess-123", ctx)
        self.confirm()
        self.assertNotIn("FIGMA ACCOUNT CHECK", self.prompt_ctx(f"Use figma-maintainer: fix the heading on {LINK}, no new images"))

    def test_figma_calls_blocked_until_confirmed(self):
        self.assertIn("hasn't been confirmed", self.guard())
        self.confirm()
        self.assertNotIn("hasn't been confirmed", self.guard())

    def test_command_gets_the_session_id(self):
        self.assertIn("Session id for figma_account.py: sess-123", self.prompt_ctx("/figma-maintainer:check-figma"))

    def test_other_work_untouched(self):
        self.assertEqual(self.prompt_ctx("build the site for Acme with design-master"), "")

    def test_command_file(self):
        t = (ROOT / "commands" / "check-figma.md").read_text()
        for s in ("whoami", "figma_account.py", "AskUserQuestion", "--confirm", "Never run the `--confirm` step without my \"Yes\""):
            self.assertIn(s, t)


if __name__ == "__main__":
    unittest.main()
