"""Code Mode-style token savings: heavy reading and filtering run in scripts, and only short answers enter the
conversation (job_context, fm_query, figma_outline, brief QA summary, contact sheet, image budget, capped reports)."""
import io, json, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.helpers import ROOT, SCRIPTS, run, temp_home

sys.path.insert(0, str(SCRIPTS))


def call(mod, argv):
    out = io.StringIO()
    old = sys.argv
    sys.argv = [mod.__name__ + ".py", *argv]
    try:
        with redirect_stdout(out):
            mod.main()
    finally:
        sys.argv = old
    return out.getvalue()


class JobContext(unittest.TestCase):
    def test_digest_keeps_set_rules_and_lists_unset_keys(self):
        import job_context as jc
        sop = ("# A\n> template guidance\n## 3. Workflow\n- Versioning: new V# frame (Jesse, 2026-10-14)\n- Frame naming: <not set>\n"
               "- Review flow: <not set>  (e.g. Internal Review)\n## 9. Hard rules\n- <not set>\n## 10. Rule log\n- <YYYY-MM-DD — rule — source>\n")
        d = jc.digest_sop(sop)
        self.assertIn("Versioning: new V# frame", d)
        self.assertIn("(not set: Frame naming, Review flow)", d)
        self.assertNotIn("template guidance", d); self.assertNotIn("Rule log", d); self.assertNotIn("Hard rules", d)

    def test_task_sop_keeps_only_this_projects_jobs(self):
        import job_context as jc
        sop = "## 4. Method\n- do x\n## 8. Jobs\n### Job 1: Alpha School\n- id 1\n### Job 2: Beta Co\n- id 2\n"
        d = jc.digest_sop(sop, project="beta-co")
        self.assertIn("id 2", d); self.assertNotIn("id 1", d); self.assertIn("Alpha School", d)

    def test_real_client_is_much_smaller_than_the_files(self):
        import importlib, job_context as jc, workdir
        td, home = temp_home()
        try:
            (home / "playbook.md").unlink(); (home / "playbook.md").symlink_to(ROOT / "knowledge" / "playbook.md")
            for m in (workdir, jc):
                m.FM = home
            jd = home / "job"
            text = call(jc, ["--agency", "Lasso up", "--for", "images", "--job-dir", str(jd)])
            raw = sum(len(p.read_text()) for p in (ROOT / "knowledge" / "playbook.md", ROOT / "knowledge" / "clients" / "_index.md",
                                                     ROOT / "knowledge" / "clients" / "lasso-up" / "client.md"))
            self.assertIn("Adobe Stock", text)
            self.assertLess(len(text), raw * 0.6)
            self.assertTrue((jd / "context.md").exists())
        finally:
            importlib.reload(workdir); importlib.reload(jc); td.cleanup()


class Query(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory(); self.d = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def test_evidence_overview_and_kind(self):
        import fm_query
        ev = {"pairs": [{"source": "1:1", "output": "2:2", "output_name": "Home V2", "text": [{"src": "1:5", "out": "2:5", "type": "TEXT", "name": "H1",
              "before": "Old", "after": "New"}], "moved": [{"src": f"1:{i}", "out": f"2:{i}", "type": "FRAME", "name": "x"} for i in range(500)]}],
              "pages": [], "flags": ["protected frame changed"], "records": {"plan.md": True}}
        (self.d / "evidence.json").write_text(json.dumps(ev))
        o = call(fm_query, ["evidence", str(self.d)])
        self.assertIn("text 1, moved 500", o); self.assertIn("FLAGS: protected frame changed", o); self.assertLess(len(o), 800)
        o = call(fm_query, ["evidence", str(self.d), "--kind", "text"])
        self.assertIn("2:5 TEXT 'H1': Old ⇒ New", o)
        o = call(fm_query, ["evidence", str(self.d), "--kind", "moved", "--max", "500"])
        self.assertLess(len(o), 700); self.assertIn("more line(s) not shown", o)

    def test_nodes_in_a_rest_dump(self):
        import fm_query
        doc = {"id": "1:1", "type": "FRAME", "name": "Page", "absoluteBoundingBox": {"x": 100, "y": 100, "width": 1440, "height": 900},
               "children": [{"id": "1:2", "type": "TEXT", "name": "t", "characters": "Book a call", "style": {"fontFamily": "Inter", "fontSize": 16},
                             "absoluteBoundingBox": {"x": 110, "y": 120, "width": 80, "height": 20}}]}
        (self.d / "dump.json").write_text(json.dumps({"nodes": {"1:1": {"document": doc}}}))
        o = call(fm_query, ["nodes", str(self.d / "dump.json"), "--root", "1:1", "--text", "book"])
        self.assertIn('1:2 TEXT \'t\' [10,20 80×20] Inter 16 "Book a call"', o); self.assertNotIn("Page", o)

    def test_inbox(self):
        import fm_query
        (self.d / "inbox.json").write_text(json.dumps({"file_name": "F", "threads": [
            {"comment_id": "9", "author": "Bre", "created_at": "2026-10-26T13:32", "message": "Fix the hover", "new": True, "frame_id": "4:1", "frame": "Home"},
            {"comment_id": "8", "author": "Kim", "created_at": "2026-10-25T13:32", "message": "Old one", "new": False, "frame_id": "4:1", "frame": "Home"}]}))
        o = call(fm_query, ["inbox", str(self.d / "inbox.json"), "--new"])
        self.assertIn("Fix the hover", o); self.assertNotIn("Old one", o)


class Outputs(unittest.TestCase):
    def test_brief_qa_summary(self):
        import figma_qa
        lines = ["# QA", "- Fills / images: 40"] + [f"  - 1:{i} 'x' fills: a → b" for i in range(40)] + [f"- ⚠ new hidden layer 1:{i} 'v'" for i in range(9)]
        b = figma_qa.brief(lines, "QA")
        self.assertIn("(… 37 more: fm_query.py evidence QA --kind fills)", "\n".join(b))
        self.assertIn("6 more 'new' warning(s)", "\n".join(b))
        self.assertLess(len("\n".join(b)), len("\n".join(lines)) / 3)

    def test_contact_sheet(self):
        import figma_qa
        Image, _ = figma_qa.pil()
        if not Image:
            self.skipTest("PIL not installed")
        with tempfile.TemporaryDirectory() as t:
            fs = []
            for i in range(3):
                p = Path(t) / f"c{i}.png"; Image.new("RGB", (1600, 900), "white").save(p); fs.append(str(p))
            s = figma_qa.contact_sheet(Image, fs, Path(t) / "sheet.png")
            w, h = Image.open(s).size
            self.assertLessEqual(w, 1000); self.assertLessEqual(h, 2400)
            self.assertIsNone(figma_qa.contact_sheet(Image, fs[:1], Path(t) / "one.png"))

    def test_print_capped(self):
        import figma_common
        out = io.StringIO()
        with redirect_stdout(out):
            figma_common.print_capped([f"- finding {i} " + "x" * 80 for i in range(400)], "audit.md", cap=2000)
        self.assertLess(len(out.getvalue()), 2300); self.assertIn("more line(s) in audit.md", out.getvalue())


class ImageBudget(unittest.TestCase):
    def transcript(self, d, agent, images):
        tp = d / "s" / "subagents" / "agent-x.jsonl"
        tp.parent.mkdir(parents=True)
        tp.with_suffix(".meta.json").write_text(json.dumps({"agentType": agent}))
        rows = [{"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": str(i),
                 "content": [{"type": "image", "source": {}}]}]}} for i in range(images)]
        tp.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return tp

    def ask(self, agent, images, tool="Read", path="/x/crop.png"):
        td, home = temp_home()
        try:
            tp = self.transcript(home, agent, images)
            out, _, _ = run("image_budget.py", {"tool_name": tool, "tool_input": {"file_path": path}, "transcript_path": str(tp)}, home)
            return out
        finally:
            td.cleanup()

    def test_budget(self):
        self.assertEqual(self.ask("figma-maintainer:qa-checker", 3), "")
        self.assertIn('"ask"', self.ask("figma-maintainer:qa-checker", 5))
        self.assertEqual(self.ask("figma-maintainer:qa-checker", 6), "")       # asks again only every 4
        self.assertIn('"ask"', self.ask("figma-maintainer:qa-checker", 9))
        self.assertEqual(self.ask("design-master:html-builder", 40), "")         # other plugins untouched
        self.assertEqual(self.ask("figma-maintainer:qa-checker", 40, path="/x/notes.md"), "")
        self.assertIn('"ask"', self.ask("figma-maintainer:figma-maintainer", 8, tool="mcp__claude_ai_Figma__get_screenshot"))

    def test_hook_registered(self):
        hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"]
        self.assertTrue(any("image_budget.py" in h["hooks"][0]["command"] for h in hooks))


class Wiring(unittest.TestCase):
    def test_agents_use_the_query_tools(self):
        a = {n: (ROOT / "agents" / f"{n}.md").read_text() for n in ("figma-maintainer", "client-comments", "qa-checker")}
        self.assertIn("job_context.py", a["figma-maintainer"]); self.assertIn("figma_outline.py", a["figma-maintainer"])
        self.assertIn("fm_query.py", a["figma-maintainer"])
        self.assertIn("job_context.py", a["client-comments"]); self.assertIn("fm_query.py inbox", a["client-comments"])
        self.assertIn("fm_query.py evidence", a["qa-checker"]); self.assertIn("contact sheet", a["qa-checker"])
        for n in ("figma-maintainer", "qa-checker"):
            self.assertIn("never read the plugin's script source", a[n].replace("Never", "never"))

    def test_big_use_figma_result_gets_a_note(self):
        td, home = temp_home()
        try:
            out, _, _ = run("figma_guard.py", {"tool_name": "mcp__claude_ai_Figma__use_figma", "agent_type": "figma-maintainer:figma-maintainer",
                                               "tool_input": {"code": "return figma.currentPage.children.map(n=>n.id)", "fileKey": "k"},
                                               "tool_response": "x" * 5000, "transcript_path": ""}, home, args=["--post"])
            self.assertIn("use_figma result was", out)
        finally:
            td.cleanup()


class ToolDefinitions(unittest.TestCase):
    def test_agents_drop_unused_tool_definitions(self):
        """Inherited built-in tool definitions cost ~25k tokens on every turn (measured 35k → 10k base context)."""
        for p in (ROOT / "agents").glob("*.md"):
            head = p.read_text().split("\n---\n", 1)[0]
            if "\ntools:" in head:
                continue
            dis = (head.split("disallowedTools:", 1) + [""])[1].split("\n", 1)[0]
            for t in ("Artifact", "Workflow", "Agent", "Skill", "AskUserQuestion"):
                self.assertIn(t, [x.strip() for x in dis.split(",")], f"{p.name} should disallow {t}")
            self.assertNotIn("Read", [x.strip() for x in dis.split(",")])


class Bench(unittest.TestCase):
    def test_token_bench_counts_kinds(self):
        import token_bench as tb
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "agent-a.jsonl"
            rows = [{"type": "assistant", "message": {"id": "m1", "usage": {"input_tokens": 10, "cache_read_input_tokens": 1000, "output_tokens": 5},
                     "content": [{"type": "tool_use", "id": "u1", "name": "Read", "input": {"file_path": "/a/playbook.md"}},
                                 {"type": "tool_use", "id": "u2", "name": "Read", "input": {"file_path": "/a/crop.png"}}]}},
                    {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "u1", "content": "y" * 300},
                                                             {"type": "tool_result", "tool_use_id": "u2", "content": [{"type": "image"}]}]}}]
            p.write_text("\n".join(json.dumps(r) for r in rows))
            b = tb.bench(p)
            self.assertEqual(b["total_input"], 1010); self.assertEqual(b["images"], 1); self.assertEqual(b["chars"]["read:md"], 300)


if __name__ == "__main__":
    unittest.main()
