"""comment_inbox.py: matching a Mac notification to the exact comment, and the round / handled logic."""
import importlib, os, sys, unittest
from unittest import mock

from tests.helpers import SCRIPTS, temp_home

sys.path.insert(0, str(SCRIPTS))


def c(cid, author, at, msg, parent=None, resolved=False):
    return {"id": cid, "user": {"handle": author}, "created_at": at, "message": msg, "parent_id": parent or "",
            "resolved_at": "2026-10-28T00:00:00Z" if resolved else None, "client_meta": None}


class Inbox(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td, home = temp_home()
        with mock.patch.dict(os.environ, {"FIGMA_MAINTAINER_HOME": str(home)}):
            import workdir
            importlib.reload(workdir)
            import comment_inbox
            cls.ci = importlib.reload(comment_inbox)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_text_match(self):
        tm = self.ci.text_match
        self.assertEqual(tm("4,500", "4,500"), 1.0)
        self.assertGreaterEqual(tm("~ Remove this sign and mention From in all", "~ Remove this sign and mention From in all pricing cards"), 0.9)
        self.assertLess(tm("Tracked bench rendering", "View all case studies"), 0.75)
        self.assertEqual(tm("", "x"), 0.0)

    def test_match_notification_author_text_time(self):
        comments = [c("1", "Karly Anderson", "2026-10-26T14:16:29Z", "4,500"),
                    c("2", "Karly Anderson", "2026-10-26T14:16:53Z", "Tracked bench rendering"),
                    c("3", "Bre Swarts", "2026-10-26T14:16:50Z", "Tracked bench rendering")]
        n = {"author": "Karly Anderson", "body": "Tracked bench rendering", "delivered_at": "2026-10-26T14:16:56Z"}
        self.assertEqual(self.ci.match_notification(n, comments)[1]["id"], "2")
        n2 = {"author": "Someone Else", "body": "4,500", "delivered_at": "2026-10-26T14:16:56Z"}
        self.assertIsNone(self.ci.match_notification(n2, comments))

    def test_round_window_and_handled(self):
        comments = [c("old", "A", "2026-10-01T10:00:00Z", "old one"),
                    c("r1", "A", "2026-10-26T10:00:00Z", "new one"),
                    c("r2", "B", "2026-10-26T12:00:00Z", "another"),
                    c("res", "B", "2026-10-26T12:30:00Z", "resolved", resolved=True),
                    c("rep", "C", "2026-10-26T13:00:00Z", "a reply", parent="r1")]
        threads, older, cutoff = self.ci.threads_for("K", comments, "t", set(), {}, 2)
        ids = [t["comment_id"] for t in threads]
        self.assertEqual(ids, ["r1", "r2"]); self.assertEqual(older, 1)
        self.assertEqual(threads[0]["replies"][0]["comment_id"], "rep")
        # r2 handled earlier: it stays out unless the client replies after that
        st = {"handled": {"r2": {"at": "2026-10-27T00:00:00Z"}}}
        threads, _, _ = self.ci.threads_for("K", comments, "t", set(), st, 2)
        self.assertEqual([t["comment_id"] for t in threads], ["r1"])
        comments.append(c("rep2", "B", "2026-10-28T09:00:00Z", "one more thing", parent="r2"))
        threads, _, _ = self.ci.threads_for("K", comments, "t", set(), st, 2)
        self.assertIn("r2", [t["comment_id"] for t in threads])


if __name__ == "__main__":
    unittest.main()
