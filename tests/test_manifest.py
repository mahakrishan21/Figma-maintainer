"""Plugin manifest limits that plugin uploads enforce (claude plugin validate doesn't check them all)."""
import json, re, subprocess, tarfile, io, unittest

from pathlib import Path

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


def excluded():
    return [l.split()[0] for l in (ROOT / ".gitattributes").read_text().splitlines() if l.strip().endswith("export-ignore")]


class TeamBuild(unittest.TestCase):
    """What co-workers receive (zip and marketplace): no tests, release tools or the management briefing."""
    def test_exclude_list(self):
        ex = excluded()
        for path in ("tests/", "scripts/share_plugin.py", "scripts/release_check.sh", "docs/figma-maintainer-briefing.html"):
            self.assertIn(path, ex)

    def test_shipped_files_dont_need_excluded_ones(self):
        names = [Path(e.rstrip("/")).name for e in excluded() if not e.startswith((".", "tests"))]
        for p in [*(ROOT / "agents").glob("*.md"), *(ROOT / "guides").glob("*.md"), *(ROOT / "skills").rglob("*.md"),
                  ROOT / "hooks" / "hooks.json", *(ROOT / "scripts").glob("*")]:
            if any(str(p).endswith(e.rstrip("/")) for e in excluded()) or not p.is_file():
                continue
            text = p.read_text(errors="ignore")
            for n in names:
                self.assertNotIn(n, text, f"{p.relative_to(ROOT)} refers to {n}, which co-workers don't get")
        for p in (ROOT / "commands").glob("*.md"):
            if f"commands/{p.name}" in excluded():
                continue
            for n in ("share_plugin.py", "release_check.sh", "briefing.html"):  # SOP-manager mentions of the commands are fine
                self.assertNotIn(n, p.read_text(), f"commands/{p.name} refers to {n}, which co-workers don't get")

    def test_archive_is_clean(self):
        r = subprocess.run(["git", "-C", str(ROOT), "archive", "--worktree-attributes", "--format=tar", "HEAD"], capture_output=True)
        if r.returncode != 0:
            self.skipTest("not a git checkout")
        names = tarfile.open(fileobj=io.BytesIO(r.stdout)).getnames()
        self.assertIn(".claude-plugin/plugin.json", names)
        for e in excluded():
            self.assertFalse([n for n in names if n == e.rstrip("/") or n.startswith(e)], f"{e} is in the team build")


if __name__ == "__main__":
    unittest.main()
