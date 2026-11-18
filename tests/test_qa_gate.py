"""qa_gate.py: a figma-maintainer job that changed Figma can't end without QA (Stop hook), and 'skip QA' waives it."""
import json, unittest
from datetime import datetime, timedelta, timezone

from tests.helpers import context, run, temp_home, transcript

MAKER, QA = "figma-maintainer:figma-maintainer", "figma-maintainer:qa-checker"
KEY = "TESTKEY1234567890abcdeF"


class QAGate(unittest.TestCase):
    def setUp(self):
        self.td, self.home = temp_home()
        self.main = transcript(self.home, ["Use figma-maintainer: fix it"], fm_session=True, name="sess1")
        self.job = str(self.home / "work/test-person/acme/site/jobs/2026-10-29-hero-fix")
        self.sub = self.home / "sess1" / "subagents" / "agent-a1.jsonl"
        self.sub.parent.mkdir(parents=True)
        self.sub.write_text(json.dumps({"type": "user", "message": {"content": "Use figma-maintainer: fix the hero"}}) + "\n"
                            + json.dumps({"type": "assistant", "message": {"content": f"Job folder: {self.job}"}}) + "\n")

    def tearDown(self):
        self.td.cleanup()

    def write_log(self, agent_id="a1", decision="completed"):
        with open(self.home / "figma-audit-log.jsonl", "a") as f:
            f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "tool": "use_figma", "fileKey": KEY,
                                "agent": MAKER, "agent_id": agent_id, "decision": decision}) + "\n")

    def sub_stop(self, kind, agent_id="a1", sub=None):
        run("qa_gate.py", {"agent_type": kind, "agent_id": agent_id, "transcript_path": str(self.main),
                           "agent_transcript_path": str(sub or self.sub)}, self.home, args=["--subagent-stop"])

    def stop(self, active=False, tp=None):
        out, err, rc = run("qa_gate.py", {"transcript_path": str(tp or self.main), "session_id": "sess1", "stop_hook_active": active},
                           self.home, args=["--stop"])
        self.assertEqual(rc, 0, err)
        return json.loads(out) if out.strip() else {}

    def pending(self):
        f = self.home / "qa-pending.json"
        return json.loads(f.read_text()).get("sess1", []) if f.exists() else []

    def test_maker_with_writes_is_pending_and_blocks_once(self):
        self.write_log(); self.sub_stop(MAKER)
        p = self.pending()
        self.assertEqual(len(p), 1); self.assertEqual(p[0]["files"], [KEY]); self.assertEqual(p[0]["job"], self.job)
        o = self.stop()
        self.assertEqual(o.get("decision"), "block"); self.assertIn("qa-checker", o["reason"]); self.assertIn(self.job, o["reason"])
        o2 = self.stop(active=True)  # Claude is already continuing because of the gate: warn, never loop
        self.assertNotIn("decision", o2); self.assertIn("QA hasn't run", o2.get("systemMessage", ""))

    def test_maker_without_writes_is_not_pending(self):
        self.write_log(decision="read"); self.sub_stop(MAKER)
        self.assertEqual(self.pending(), [])
        self.assertEqual(self.stop(), {})

    def test_qa_run_clears_the_mark(self):
        self.write_log(); self.sub_stop(MAKER)
        qa = self.home / "sess1" / "subagents" / "agent-q1.jsonl"
        qa.write_text(json.dumps({"type": "user", "message": {"content": f"Job folder: {self.job}\nFile: {KEY}"}}) + "\n")
        self.sub_stop(QA, agent_id="q1", sub=qa)
        self.assertEqual(self.pending(), [])
        o = self.stop()  # no block; just the one-time "start a new conversation" reminder
        self.assertNotIn("decision", o); self.assertIn("new conversation", o.get("systemMessage", ""))
        self.assertEqual(self.stop(), {})

    def test_qa_for_another_job_doesnt_clear(self):
        self.write_log(); self.sub_stop(MAKER)
        qa = self.home / "sess1" / "subagents" / "agent-q2.jsonl"
        qa.write_text(json.dumps({"type": "user", "message": {"content": "Job folder: /x/work/p/a/b/jobs/2026-10-01-other\nFile: OTHER"}}) + "\n")
        self.sub_stop(QA, agent_id="q2", sub=qa)
        self.assertEqual(len(self.pending()), 1)

    def test_qa_launched_in_background_doesnt_block(self):
        self.write_log(); self.sub_stop(MAKER)
        later = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
        with open(self.main, "a") as f:
            f.write(json.dumps({"type": "assistant", "timestamp": later, "message": {"content": [
                {"type": "tool_use", "name": "Agent", "input": {"subagent_type": QA, "prompt": "Job folder: x"}}]}}) + "\n")
        self.assertEqual(self.stop(), {})

    def test_skip_qa_clears(self):
        self.write_log(); self.sub_stop(MAKER)
        out, err, rc = run("image_gate.py", {"prompt": "skip QA", "transcript_path": str(self.main), "session_id": "sess1"}, self.home)
        self.assertIn("skip the QA check", context(out))
        self.assertEqual(self.pending(), [])

    def test_other_sessions_unaffected(self):
        self.write_log(); self.sub_stop(MAKER)
        other = transcript(self.home, ["hello"], name="sess2")
        out, err, rc = run("qa_gate.py", {"transcript_path": str(other), "session_id": "sess2", "stop_hook_active": False},
                           self.home, args=["--stop"])
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
