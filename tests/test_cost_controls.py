"""Cost controls: pinned agent models, short descriptions, lean agent core, the after-job reminder, the Fable warning, budget flags."""
import json, os, re, sys, unittest
from unittest import mock

from tests.helpers import ROOT, SCRIPTS, run, temp_home, transcript

sys.path.insert(0, str(SCRIPTS))

EXPECTED_MODELS = {"figma-maintainer": "opus", "client-comments": "sonnet", "qa-checker": "sonnet", "consistency-auditor": "sonnet",
                   "content-auditor": "sonnet", "accessibility-auditor": "sonnet", "usage-reporter": "haiku"}


def frontmatter(p):
    m = re.match(r"---\n(.*?)\n---", p.read_text(), re.S)
    return dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l and not l.startswith(" "))


class Agents(unittest.TestCase):
    def test_every_agent_has_a_pinned_model(self):
        for name, model in EXPECTED_MODELS.items():
            fm = frontmatter(ROOT / "agents" / f"{name}.md")
            self.assertEqual(fm.get("model", "").strip(), model, f"{name} must run on {model}, not inherit the session's model")

    def test_descriptions_stay_short(self):  # sent in every session where the plugin is enabled
        total = 0
        for p in (ROOT / "agents").glob("*.md"):
            d = frontmatter(p).get("description", "").strip()
            total += len(d)
            self.assertLessEqual(len(d), 800, f"{p.name} description is {len(d)} chars")
        self.assertLessEqual(total, 4000)

    def test_maker_core_is_lean_and_guides_exist(self):
        core = (ROOT / "agents" / "figma-maintainer.md").read_text()
        self.assertLess(len(core) // 4, 7000, "figma-maintainer.md core grew back: move task-specific parts into guides/")
        for g in re.findall(r"guides/(maintainer-[a-z-]+\.md)", core):
            self.assertTrue((ROOT / "guides" / g).exists(), g)

    def test_light_qa_is_wired(self):
        self.assertIn("Level: light", (ROOT / "agents" / "qa-checker.md").read_text())
        self.assertIn("Level: light", (ROOT / "commands" / "client-comment.md").read_text())
        self.assertIn("context.json", (ROOT / "agents" / "client-comments.md").read_text())


class Reminder(unittest.TestCase):
    def test_reminder_once_after_qa_clears_the_last_job(self):
        td, home = temp_home()
        try:
            main = transcript(home, ["Use figma-maintainer: fix it"], fm_session=True, name="s1")
            (home / "qa-pending.json").write_text(json.dumps({"s1": [{"agent_id": "a1", "files": ["K"], "job": "/x/work/p/a/b/jobs/2026-11-18-fix",
                                                                      "at": "2099-01-01T00:00:00+00:00"}]}))
            qa = home / "s1" / "subagents" / "agent-q.jsonl"; qa.parent.mkdir(parents=True)
            qa.write_text(json.dumps({"type": "user", "message": {"content": "Job folder: /x/work/p/a/b/jobs/2026-11-18-fix\nFile: K"}}) + "\n")
            run("qa_gate.py", {"agent_type": "figma-maintainer:qa-checker", "agent_id": "q", "transcript_path": str(main),
                               "agent_transcript_path": str(qa)}, home, args=["--subagent-stop"])
            stop = lambda: run("qa_gate.py", {"transcript_path": str(main), "stop_hook_active": False}, home, args=["--stop"])[0]
            first = json.loads(stop())
            self.assertIn("start a new conversation", first.get("systemMessage", ""))
            self.assertNotIn("decision", first)
            self.assertEqual(stop().strip(), "", "the reminder shows only once")
        finally:
            td.cleanup()


class Doctor(unittest.TestCase):
    def test_default_model_detection(self):
        import doctor
        with mock.patch.dict(os.environ, {"ANTHROPIC_MODEL": "claude-fable-5-2"}):
            m, where = doctor.default_model()
        self.assertEqual((m, where), ("claude-fable-5-2", "ANTHROPIC_MODEL"))
        self.assertTrue(doctor.expensive_model(m))
        self.assertFalse(doctor.expensive_model("claude-opus-5-5"))
        td, home = temp_home()
        try:
            (home / "settings.json").write_text(json.dumps({"model": "sonnet"}))
            env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_MODEL"}
            env["CLAUDE_CONFIG_DIR"] = str(home)
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(doctor.default_model(), ("sonnet", "settings.json"))
        finally:
            td.cleanup()


class Budget(unittest.TestCase):
    def test_budget_flags(self):
        import usage_report as u
        base = {"agent": "figma-maintainer:qa-checker", "models": ["claude-sonnet-5-5"], "tool_calls": 30, "cache_read": 1_000_000, "usd": 0.9}
        self.assertEqual(u.budget_flag(base), "")
        self.assertIn("over budget", u.budget_flag(dict(base, usd=2.4)))
        self.assertIn("Fable", u.budget_flag(dict(base, models=["claude-fable-5-2"])))
        self.assertEqual(u.budget_flag(dict(base, agent="figma-maintainer:figma-maintainer", usd=2.9)), "")
        self.assertEqual(u.budget_flag(dict(base, agent="figma-maintainer:usage-reporter", usd=9)), "")


if __name__ == "__main__":
    unittest.main()
