"""Plugin manifest limits that plugin uploads enforce (claude plugin validate doesn't check them all)."""
import json, re, unittest

from tests.helpers import ROOT


class Manifest(unittest.TestCase):
    def test_plugin_json(self):
        d = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
        self.assertRegex(d["name"], r"^[a-z0-9-]+$")
        self.assertRegex(d["version"], r"^\d+\.\d+\.\d+$")
        self.assertLessEqual(len(d["description"]), 500, "uploads reject plugin descriptions over 500 characters")

    def test_skill_frontmatter(self):
        for p in (ROOT / "skills").glob("*/SKILL.md"):
            m = re.match(r"---\n(.*?)\n---", p.read_text(), re.S)
            self.assertIsNotNone(m, f"{p} has no frontmatter")
            fm = dict(l.split(":", 1) for l in m.group(1).splitlines() if ":" in l and not l.startswith(" "))
            self.assertLessEqual(len(fm.get("name", "").strip()), 64, p)
            self.assertLessEqual(len(fm.get("description", "").strip()), 1024, p)


if __name__ == "__main__":
    unittest.main()
