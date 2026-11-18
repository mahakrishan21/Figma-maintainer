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


class CostReports(unittest.TestCase):
    def _home(self):
        td, home = temp_home()
        (home / "pricing.json").symlink_to(ROOT / "knowledge" / "pricing.json")
        return td, home

    def _transcript(self, home, n_main):
        main = home / "sessX.jsonl"
        rows = [{"type": "user", "cwd": "/tmp/work", "timestamp": "2026-11-18T10:00:00Z", "message": {"content": "Use figma-maintainer: x"}}]
        for i in range(n_main):
            rows.append({"type": "assistant", "timestamp": f"2026-11-18T10:0{i + 1}:00Z", "isSidechain": False,
                         "message": {"id": f"m{i}", "model": "claude-opus-5-5", "content": [],
                                     "usage": {"input_tokens": 1000, "output_tokens": 500, "cache_read_input_tokens": 10000}}})
        main.write_text("".join(json.dumps(r) + "\n" for r in rows))
        sub = home / "sessX" / "subagents"; sub.mkdir(parents=True, exist_ok=True)
        (sub / "agent-a1.jsonl").write_text(json.dumps({"type": "assistant", "timestamp": "2026-11-18T10:05:00Z", "isSidechain": True,
            "message": {"id": "s1", "model": "claude-sonnet-5-5", "content": [], "usage": {"input_tokens": 2000, "output_tokens": 800}}}) + "\n")
        (sub / "agent-a1.meta.json").write_text(json.dumps({"agentType": "figma-maintainer:qa-checker", "description": "QA test"}))
        return main

    def test_session_row_upsert(self):
        td, home = self._home()
        try:
            main = self._transcript(home, 2)
            hook = {"transcript_path": str(main), "agent_id": "a1", "agent_type": "figma-maintainer:qa-checker"}
            run("usage_report.py", hook, home, args=["--hook-subagent-stop"])
            rows = [json.loads(l) for l in (home / "usage-sessions.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 1); self.assertEqual(rows[0]["session"], "sessX"); self.assertEqual(rows[0]["tasks"], 1)
            first = rows[0]["main_usd"]
            self._transcript(home, 4)  # the conversation grew: same session, updated row
            run("usage_report.py", hook, home, args=["--hook-subagent-stop"])
            rows = [json.loads(l) for l in (home / "usage-sessions.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 1); self.assertGreater(rows[0]["main_usd"], first)
        finally:
            td.cleanup()

    def test_consolidated_report_sums_and_filters(self):
        td, home = self._home()
        try:
            (home / "usage-log.jsonl").write_text("".join(json.dumps(r) + "\n" for r in [
                {"date": "2026-11-10", "agent": "figma-maintainer:figma-maintainer", "client": "Acme › Site", "usd": 2.0, "new_tokens": 1, "cache_read": 1, "tool_calls": 10, "models": ["claude-opus-5-5"]},
                {"date": "2026-11-12", "agent": "figma-maintainer:qa-checker", "client": "Acme › Site", "usd": 1.0, "new_tokens": 1, "cache_read": 1, "tool_calls": 5, "models": ["claude-sonnet-5-5"]},
                {"date": "2026-11-12", "agent": "other-plugin:builder", "client": "", "usd": 50.0, "new_tokens": 1, "cache_read": 1, "tool_calls": 5, "models": []}]))
            (home / "usage-sessions.jsonl").write_text(json.dumps({"session": "s1", "first": "2026-11-10", "last": "2026-11-12", "main_usd": 4.0,
                                                                  "tasks": 2, "tasks_usd": 3.0, "clients": ["Acme › Site"]}) + "\n")
            out = run("usage_report.py", {}, home, args=["--all"])[0]
            self.assertIn("1 session(s), 2 plugin task(s)", out)
            self.assertIn("Total $7.00", out)  # 4 main + 3 tasks; the other plugin's $50 is left out
            out2 = run("usage_report.py", {}, home, args=["--all", "--since", "2026-11-11"])[0]
            self.assertIn("1 plugin task(s)", out2)
        finally:
            td.cleanup()

    def test_default_report_is_one_conversation_or_task(self):
        cmd = (ROOT / "commands" / "cost-report.md").read_text()
        self.assertNotIn("client <name>", cmd); self.assertNotIn("all-sessions", cmd)
        allc = (ROOT / "commands" / "cost-report-all.md").read_text()
        self.assertIn("disable-model-invocation: true", allc); self.assertIn("--all", allc)
        self.assertIn("Consolidated:", (ROOT / "agents" / "usage-reporter.md").read_text())


if __name__ == "__main__":
    unittest.main()
