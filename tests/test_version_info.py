"""/figma-maintainer:about and the session update check: version, build date, what's new, and asking to update
only when a newer version is live. Offline (the live check is mocked)."""
import io, json, sys, unittest
from contextlib import redirect_stdout
from unittest import mock

from tests.helpers import ROOT, SCRIPTS, temp_home

sys.path.insert(0, str(SCRIPTS))
import version_info as v  # noqa: E402


class About(unittest.TestCase):
    def test_changelog_has_the_installed_version(self):
        local = v.installed()
        self.assertIn(local, [x[0] for x in v.changelog()], "CHANGELOG.md needs an entry for the current version")

    def run_main(self, args, live, source="marketplace"):
        out = io.StringIO()
        with mock.patch.object(v, "latest", return_value=live), mock.patch.object(v, "cached_latest", return_value=live), \
             mock.patch.object(v, "source", return_value=source), mock.patch.object(sys, "argv", ["version_info.py", *args]), \
             redirect_stdout(out):
            try:
                v.main(); code = 0
            except SystemExit as e:
                code = e.code
        return out.getvalue(), code

    def test_update_available(self):
        out, code = self.run_main([], "99.0.0")
        self.assertEqual(code, 2)
        self.assertIn("UPDATE AVAILABLE", out); self.assertIn("claude plugin update figma-maintainer@e2m-figma", out)
        self.assertIn("What it can do", out); self.assertIn("What's new", out)

    def test_up_to_date(self):
        out, code = self.run_main([], v.installed())
        self.assertEqual(code, 0); self.assertIn("Up to date", out)

    def test_session_asks_only_when_newer(self):
        out, _ = self.run_main(["--session"], "99.0.0")
        self.assertIn("update available", out); self.assertIn("AskUserQuestion", out)
        self.assertEqual(self.run_main(["--session"], v.installed())[0], "")
        self.assertEqual(self.run_main(["--session"], None)[0], "")          # offline: silent
        self.assertEqual(self.run_main(["--session"], "99.0.0", "master")[0], "")  # SOP manager's Mac: silent

    def test_cache(self):
        td, home = temp_home()
        old = v.CACHE
        try:
            v.CACHE = home / "version-check.json"
            with mock.patch.object(v, "latest", return_value="1.2.3") as live:
                self.assertEqual(v.cached_latest(), "1.2.3"); self.assertEqual(v.cached_latest(), "1.2.3")
            live.assert_called_once()
        finally:
            v.CACHE = old; td.cleanup()


class Commands(unittest.TestCase):
    def test_removed_commands_are_gone(self):
        for n in ("sop", "contribute", "share", "review-contributions"):
            self.assertFalse((ROOT / "commands" / f"{n}.md").exists(), n)

    def test_about_command(self):
        t = (ROOT / "commands" / "about.md").read_text()
        self.assertIn("version_info.py", t); self.assertIn("UPDATE AVAILABLE", t); self.assertIn("AskUserQuestion", t)

    def test_session_start_runs_the_check(self):
        self.assertIn("version_info.py\" --session", (ROOT / "scripts" / "bootstrap.sh").read_text())


if __name__ == "__main__":
    unittest.main()
