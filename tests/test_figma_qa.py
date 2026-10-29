"""figma_qa.py: the clone-aware layer diff, time helpers, and an end-to-end evidence run on fixtures."""
import copy, json, os, sys, unittest
from datetime import timezone

from tests.helpers import SCRIPTS, fixtures, run, temp_home

sys.path.insert(0, str(SCRIPTS))
import figma_qa as q  # noqa: E402

_ID = [100]


def node(t, name, children=(), x=0, y=0, w=100, h=20, **kw):
    _ID[0] += 1
    n = {"id": f"9:{_ID[0]}", "type": t, "name": name, "absoluteBoundingBox": {"x": x, "y": y, "width": w, "height": h}}
    if children:
        n["children"] = list(children)
    n.update(kw)
    return n


def frame():
    return node("FRAME", "Page - 23 Oct", [
        node("TEXT", "Heading", characters="Used in 3,000+ rooms", style={"fontFamily": "Inter", "fontSize": 22}, y=10),
        node("RECTANGLE", "image 37", fills=[{"type": "IMAGE", "imageRef": "aaaa1111"}], y=40, h=300),
        node("INSTANCE", "Card", [node("TEXT", "Card title", characters="Benches", style={"fontFamily": "Inter"})], componentId="5:1", y=400),
        node("FRAME", "Block A", [node("TEXT", "A1", characters="one")], y=500),
        node("FRAME", "Block B", [node("TEXT", "B1", characters="two")], y=600),
    ], w=1920, h=1000)


def renumber(n):
    n = copy.deepcopy(n)

    def walk(x):
        _ID[0] += 1
        x["id"] = f"7:{_ID[0]}"
        for c in x.get("children", []):
            walk(c)
    walk(n)
    return n


class Diff(unittest.TestCase):
    def setUp(self):
        self.src = frame()
        self.out = renumber(self.src)
        self.out["name"] = "Page - 27 Oct"

    def test_identical_copy_only_renamed(self):
        r = q.diff_pair(self.src, self.out)
        self.assertEqual([c["after"] for c in r["name"]], ["Page - 27 Oct"])
        for k in ("text", "fills", "annotations", "added", "removed", "reordered", "flags"):
            self.assertEqual(r[k], [], k)

    def test_text_fill_annotation(self):
        kids = self.out["children"]
        kids[0]["characters"] = "Used in 4,500+ rooms"
        kids[1]["fills"] = [{"type": "SOLID", "color": {"r": 0.85, "g": 0.85, "b": 0.85}}]
        kids[1]["annotations"] = [{"label": "render needed"}]
        r = q.diff_pair(self.src, self.out)
        self.assertEqual(r["text"][0]["after"], "Used in 4,500+ rooms")
        self.assertEqual((r["fills"][0]["before"], r["fills"][0]["after"]), ("image aaaa1111", "solid #D9D9D9"))
        self.assertEqual(r["annotations"][0]["after"], ["render needed"])

    def test_detached_instance_and_font_flagged(self):
        kids = self.out["children"]
        kids[2]["type"] = "FRAME"; kids[2].pop("componentId")
        kids[0]["style"] = {"fontFamily": "Arial", "fontSize": 22}
        flags = " | ".join(q.diff_pair(self.src, self.out)["flags"])
        self.assertIn("DETACHED", flags); self.assertIn("FONT FAMILY", flags)

    def test_new_hidden_layer_flagged(self):
        self.out["children"].append(node("TEXT", "Old copy", characters="x", visible=False))
        r = q.diff_pair(self.src, self.out)
        self.assertEqual(len(r["added"]), 1); self.assertTrue(any("hidden" in f for f in r["flags"]))

    def test_reordered_block_is_not_add_remove(self):
        kids = self.out["children"]
        kids[3], kids[4] = kids[4], kids[3]
        r = q.diff_pair(self.src, self.out)
        self.assertEqual(r["added"], []); self.assertEqual(r["removed"], [])
        self.assertEqual(len(r["reordered"]), 1)


class Helpers(unittest.TestCase):
    def test_parse_when(self):
        self.assertEqual(q.parse_when("2026-10-29 14:00 IST").isoformat(), "2026-10-29T08:30:00+00:00")
        self.assertEqual(q.parse_when("2026-10-29T08:30Z").isoformat(), "2026-10-29T08:30:00+00:00")
        self.assertEqual(q.parse_when("2026-10-29").tzinfo, timezone.utc)
        with self.assertRaises(SystemExit):
            q.parse_when("yesterday")

    def test_plan_approval(self):
        t = q.plan_approval("# Plan\nStatus: APPROVED 2026-10-27 23:57 IST by someone\n")
        self.assertEqual(t.isoformat(), "2026-10-27T18:27:00+00:00")
        self.assertIsNone(q.plan_approval("Status: PENDING APPROVAL"))


class EndToEnd(unittest.TestCase):
    def test_evidence_run_on_fixtures(self):
        td, home = temp_home()
        try:
            key = "FIXKEY1234567890abcdefG"
            src, out = frame(), None
            src["id"] = "1:1"
            out = renumber(src); out["id"] = "2:1"; out["name"] = "Page - 27 Oct"
            out["children"][0]["characters"] = "Used in 4,500+ rooms"
            meta = {"file": {"name": "Fixture file", "last_touched_at": "2026-10-29T08:00:00Z"}}
            versions = {"versions": [{"id": "v1", "created_at": "2026-10-29T07:59:00Z"}]}
            page = {"id": "0:1", "type": "CANVAS", "name": "Home", "children": [dict(src, children=[]), dict(out, children=[])]}
            fx = fixtures(home / "fx", {
                f"/files/{key}/meta": meta, f"/files/{key}/versions": versions,
                f"/files/{key}/nodes?ids=1:1,2:1": {"nodes": {"1:1": {"document": src}, "2:1": {"document": out}}},
                f"/files/{key}?depth=2": {"name": "Fixture file", "document": {"id": "0:0", "children": [page]}},
            })
            job = home / "work/test-person/acme/site/jobs/2026-10-29-hero"
            job.mkdir(parents=True)
            (job / "client-message.md").write_text(
                'Home - The count now reads "Used in 4,500+ rooms".\n'
                f"https://www.figma.com/proto/{key}/Fixture?page-id=0%3A1&node-id=2-1&starting-point-node-id=2-1\n\nThank you!\n")
            (job / "report.md").write_text("## Report\n- **Undo:** delete the new frame 2:1\n")
            stdout, err, rc = run("figma_qa.py", {}, home, args=["--file", key, "--pair", "1:1=2:1", "--job", str(job),
                                                                 "--out", str(job / "qa"), "--no-render"],
                                  env={"FIGMA_FIXTURES": str(fx)})
            self.assertEqual(rc, 0, err[-500:])
            self.assertIn("Used in 3,000+ rooms → Used in 4,500+ rooms", stdout)
            self.assertIn("points to an output frame", stdout)
            self.assertIn('quoted "Used in 4,500+ rooms": found in the output', stdout)
            self.assertIn("Undo line in the report: ✓", stdout)
            ev = json.loads((job / "qa" / "evidence.json").read_text())
            self.assertEqual(ev["pairs"][0]["output"], "2:1")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
