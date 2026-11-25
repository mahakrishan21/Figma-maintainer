"""/figma-maintainer:make-inner-page: the command, the design skill, and the agent and QA hook-ups."""
import re, unittest

from tests.helpers import ROOT


class InnerPage(unittest.TestCase):
    def test_command(self):
        c = (ROOT / "commands" / "make-inner-page.md").read_text()
        self.assertIn("disable-model-invocation: true", c)
        for part in ("Inner page mode", "Copy source:", "Image/video source:", "inner-page-from-homepage.md", "workdir.py"):
            self.assertIn(part, c)

    def test_skill_is_the_design_standard(self):
        s = (ROOT / "skills" / "inner-page-from-homepage" / "SKILL.md").read_text()
        self.assertTrue(s.startswith("---\ndisable-model-invocation: true\nname: inner-page-from-homepage\n"))
        for part in ("style-map.md", "page-plan.md", "Off-system check", "Placeholder – ", "read-only", "task-inner-pages.md",
                     "Clone a matching homepage section", "Never detach the header or footer"):
            self.assertIn(part, s)

    def test_agent_and_qa_know_the_mode(self):
        agent = (ROOT / "agents" / "figma-maintainer.md").read_text()
        self.assertIn("## Inner page mode", agent)
        self.assertIn("guides/inner-page-from-homepage.md", agent)
        self.assertIn("Inner-page jobs", (ROOT / "agents" / "qa-checker.md").read_text())

    def test_documented(self):
        for f in ("README.md", "commands/prompts.md", "docs/figma-maintainer-guide.html"):
            self.assertIn("make-inner-page", (ROOT / f).read_text(), f)


if __name__ == "__main__":
    unittest.main()
