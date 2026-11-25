"""qa_gate.py: a figma-maintainer job that changed Figma can't end without QA (Stop hook), and 'skip QA' waives it."""
import json, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


    # ---- the agents' final replies are saved by the hook (report.md / qa.md), so nobody re-types them
    def reply(self, text, name="agent-a1.jsonl", brief="Use figma-maintainer: fix the hero", handback=True):
        sub = self.home / "sess1" / "subagents" / name
        last = ({"type": "tool_use", "name": "SubagentHandback", "input": {"message": text}} if handback
                else {"type": "text", "text": text})
        sub.write_text(json.dumps({"type": "user", "message": {"content": brief}}) + "\n"
                       + json.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Working on it."}]}}) + "\n"
                       + json.dumps({"type": "assistant", "message": {"content": [last]}}) + "\n")
        return sub

    def test_maker_reply_is_saved_as_report_md(self):
        job = Path(self.job); job.mkdir(parents=True)
        earlier = job.parent / "2026-10-20-earlier-job"; earlier.mkdir()
        report = (f"All 3 comments are handled. Values match the earlier run in {earlier}.\n\n"
                  f"- **Job folder:** {job}\n" + "- changed 1:2 to the new copy\n" * 20)
        self.sub_stop(MAKER, sub=self.reply(report))
        self.assertEqual((job / "report.md").read_text().strip(), report.strip())
        self.assertFalse((earlier / "report.md").exists(), "the 'Job folder:' line wins over other job paths")

    def test_plain_final_text_is_saved_too(self):
        job = Path(self.job); job.mkdir(parents=True)
        report = f"Report for the job in {job}.\n" + "- changed 1:2 to the new copy\n" * 20
        sub = self.reply(report, handback=False)
        run("qa_gate.py", {"agent_type": MAKER, "agent_id": "a1", "transcript_path": str(self.main),
                           "agent_transcript_path": str(sub), "last_assistant_message": report}, self.home, args=["--subagent-stop"])
        self.assertEqual((job / "report.md").read_text().strip(), report.strip())

    def test_qa_reply_is_saved_as_qa_md_and_the_earlier_one_is_kept(self):
        job = Path(self.job); job.mkdir(parents=True)
        (job / "qa.md").write_text("# QA: the first run\n")
        qa = "# QA: acme › site, hero fix · Overall: PASS\n" + "| 1 | comment | expected | found | PASS |\n" * 8
        self.sub_stop(QA, agent_id="q1", sub=self.reply(qa, "agent-q1.jsonl", brief=f"Job folder: {job}\nFile: {KEY}"))
        self.assertEqual((job / "qa.md").read_text().strip(), qa.strip())
        kept = list(job.glob("qa-*.md"))
        self.assertEqual(len(kept), 1)
        self.assertIn("the first run", kept[0].read_text())
        self.sub_stop(QA, agent_id="q1", sub=self.home / "sess1" / "subagents" / "agent-q1.jsonl")
        self.assertEqual(len(list(job.glob("qa-*.md"))), 1, "the same reply again doesn't pile up copies")

    def test_reply_is_not_saved_outside_work_or_when_it_is_only_a_question(self):
        outside = self.home / "elsewhere" / "work" / "acme" / "jobs" / "2026-10-29-hero-fix"; outside.mkdir(parents=True)
        self.sub_stop(MAKER, sub=self.reply(f"Report.\n- **Job folder:** {outside}\n" + "- changed\n" * 60))
        self.assertFalse((outside / "report.md").exists())
        job = Path(self.job); job.mkdir(parents=True)
        self.sub_stop(MAKER, sub=self.reply(f"Font needed: Inter — Bold. Job folder: {job}"))
        self.assertFalse((job / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
