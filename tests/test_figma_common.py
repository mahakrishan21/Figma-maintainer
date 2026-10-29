"""figma_common.get(): retries, clear errors, fixtures."""
import io, json, os, sys, unittest, urllib.error
from unittest import mock

from tests.helpers import SCRIPTS, fixtures, temp_home

sys.path.insert(0, str(SCRIPTS))
import figma_common as fc  # noqa: E402


class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def http_error(code, headers=None):
    return urllib.error.HTTPError("https://api.figma.com/v1/x", code, "err", headers or {}, io.BytesIO(b'{"err":"x"}'))


class Get(unittest.TestCase):
    def setUp(self):
        os.environ.pop("FIGMA_FIXTURES", None)
        self.sleeps = []
        self.p_sleep = mock.patch.object(fc.time, "sleep", lambda s: self.sleeps.append(s))
        self.p_sleep.start()

    def tearDown(self):
        self.p_sleep.stop()

    def test_retries_rate_limit_then_succeeds(self):
        calls = [http_error(429, {"Retry-After": "7"}), FakeResp(json.dumps({"ok": 1}).encode())]

        def fake(req, timeout=0):
            c = calls.pop(0)
            if isinstance(c, Exception):
                raise c
            return c
        with mock.patch.object(fc.urllib.request, "urlopen", fake):
            self.assertEqual(fc.get("/x", "t"), {"ok": 1})
        self.assertEqual(self.sleeps, [7])

    def test_server_errors_give_up_with_figma_error(self):
        def fake(req, timeout=0):
            raise http_error(500)
        with mock.patch.object(fc.urllib.request, "urlopen", fake):
            with self.assertRaises(fc.FigmaError) as cm:
                fc.get("/files/K/meta", "t")
        self.assertEqual(cm.exception.status, 500)
        self.assertEqual(len(self.sleeps), 4)  # 5 attempts
        self.assertIn("Figma server problem", str(cm.exception))

    def test_no_retry_on_403_and_plain_reason(self):
        def fake(req, timeout=0):
            raise http_error(403)
        with mock.patch.object(fc.urllib.request, "urlopen", fake):
            with self.assertRaises(SystemExit) as cm:  # FigmaError is a SystemExit: old callers keep working
                fc.get("/teams/1/projects", "t")
        self.assertEqual(self.sleeps, [])
        self.assertIn("lacks the scope", str(cm.exception))

    def test_network_error(self):
        def fake(req, timeout=0):
            raise urllib.error.URLError("no route")
        with mock.patch.object(fc.urllib.request, "urlopen", fake):
            with self.assertRaises(fc.FigmaError) as cm:
                fc.get("/x", "t", retries=1)
        self.assertEqual(cm.exception.status, 0)

    def test_fixture_mode(self):
        td, home = temp_home()
        try:
            fx = fixtures(home / "fx", {"/files/K/nodes?ids=1:2,3:4": {"nodes": {}}, "/files/K/meta": {"status": 404}})
            with mock.patch.dict(os.environ, {"FIGMA_FIXTURES": str(fx)}):
                self.assertEqual(fc.token(), "fixture-token")
                self.assertEqual(fc.get("/files/K/nodes?ids=1:2,3:4", "t"), {"nodes": {}})
                with self.assertRaises(fc.FigmaError) as cm:
                    fc.get("/files/K/meta", "t")
                self.assertEqual(cm.exception.status, 404)
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
