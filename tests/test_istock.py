"""iStock placeholders work on any team Mac: curl fallback, clear 'iStock setup needed' reasons, the cached check,
and the prompt hook asking the user to fix iStock before the job when it fails on this Mac. Offline (no network)."""
import io, json, ssl, sys, time, unittest
from contextlib import redirect_stdout
from unittest import mock

from tests.helpers import SCRIPTS, context, run, temp_home

sys.path.insert(0, str(SCRIPTS))
import istock_fetch as i  # noqa: E402

PROMPT = "Use figma-maintainer: update the hero image on https://www.figma.com/design/jUau2sA38TBr0R2HjR75HE/x?node-id=1-2, images: iStock"


class Fetch(unittest.TestCase):
    def setUp(self):
        i.STATE.clear(); i.STATE["via"] = "python"

    def test_python_tls_failure_falls_back_to_curl(self):
        with mock.patch("urllib.request.urlopen", side_effect=ssl.SSLError("CERTIFICATE_VERIFY_FAILED")), \
             mock.patch.object(i, "_curl", return_value=b"ok") as curl:
            self.assertEqual(i.get("https://www.istockphoto.com/x"), b"ok")
        curl.assert_called_once()
        self.assertEqual(i.STATE["via"], "curl")

    def test_blocked_network_is_explained(self):
        done = mock.Mock(returncode=0, stdout=b"<html>denied</html>\n403", stderr=b"")
        with mock.patch("subprocess.run", return_value=done), mock.patch("os.path.exists", return_value=True):
            with self.assertRaises(i.SetupNeeded) as e:
                i._curl("https://www.istockphoto.com/x")
        self.assertIn("HTTP 403", e.exception.reason); self.assertIn("VPN", e.exception.fix)

    def test_captcha_page_is_explained(self):
        with mock.patch.object(i, "get", return_value=b"<html>Please complete the captcha</html>"):
            with self.assertRaises(i.SetupNeeded) as e:
                i.search("office", None)
        self.assertIn("robot check", e.exception.reason)

    def test_check_prints_setup_needed_and_exits_3(self):
        fail = {"ok": False, "reason": "can't connect to istockphoto.com", "fix": "Check the internet connection"}
        out = io.StringIO()
        with mock.patch.object(i, "check", return_value=fail), mock.patch.object(sys, "argv", ["istock_fetch.py", "--check"]), \
             redirect_stdout(out), self.assertRaises(SystemExit) as e:
            i.main()
        self.assertEqual(e.exception.code, 3)
        self.assertIn("iStock setup needed: can't connect", out.getvalue()); self.assertIn("Fix: Check the internet", out.getvalue())


class Cache(unittest.TestCase):
    def setUp(self):
        self.td, self.home = temp_home()
        self.old = i.CACHE
        i.CACHE = self.home / "istock-check.json"

    def tearDown(self):
        i.CACHE = self.old
        self.td.cleanup()

    def write(self, ok, minutes_ago):
        at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(time.time() - minutes_ago * 60))
        i.CACHE.write_text(json.dumps({"ok": ok, "at": at, "reason": "" if ok else "blocked", "fix": ""}))

    def test_fresh_pass_and_recent_failure_are_reused(self):
        with mock.patch.object(i, "check") as chk:
            self.write(True, 60 * 5); self.assertTrue(i.cached_check()["ok"])
            self.write(False, 3); self.assertFalse(i.cached_check()["ok"])
        chk.assert_not_called()

    def test_old_results_are_checked_again(self):
        with mock.patch.object(i, "check", return_value={"ok": True}) as chk:
            self.write(False, 30); i.cached_check()
            self.write(True, 60 * 30); i.cached_check()
        self.assertEqual(chk.call_count, 2)


class PromptHook(unittest.TestCase):
    def _ctx(self, ok):
        td, home = temp_home()
        try:
            at = time.strftime("%Y-%m-%dT%H:%M:%S")
            (home / "istock-check.json").write_text(json.dumps({"ok": ok, "at": at, "reason": "iStock refused the request (HTTP 403)",
                                                                "fix": "Turn off VPN"}))
            return context(run("image_gate.py", {"prompt": PROMPT, "transcript_path": ""}, home)[0])
        finally:
            td.cleanup()

    def test_failing_istock_is_raised_before_the_job(self):
        ctx = self._ctx(False)
        self.assertIn("iStock CHECK FAILED on this Mac: iStock refused the request (HTTP 403)", ctx)
        self.assertIn("Fix it now (Recommended)", ctx)

    def test_working_istock_adds_nothing(self):
        ctx = self._ctx(True)
        self.assertIn("names the image/video source (iStock)", ctx)
        self.assertNotIn("CHECK FAILED", ctx)


class SessionStart(unittest.TestCase):
    def test_missing_python_is_announced(self):
        import os, subprocess, tempfile
        from tests.helpers import ROOT
        with tempfile.TemporaryDirectory() as h:
            def boot(path):
                env = {"HOME": h, "PATH": path, "CLAUDE_PLUGIN_ROOT": str(ROOT)}
                return subprocess.run(["/bin/bash", str(ROOT / "scripts" / "bootstrap.sh")], env=env, capture_output=True, text=True, timeout=60).stdout
            self.assertIn("xcode-select --install", boot("/bin:/usr/sbin"))  # no python3 on PATH
            self.assertNotIn("Python 3 isn't installed", boot(os.path.dirname(sys.executable) + ":/usr/bin:/bin:/usr/sbin"))


if __name__ == "__main__":
    unittest.main()
