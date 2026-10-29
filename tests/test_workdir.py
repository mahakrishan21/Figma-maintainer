"""workdir.py: file key → agency › project, and per-job folders."""
import json, unittest

from tests.helpers import run, temp_home


class Workdir(unittest.TestCase):
    def setUp(self):
        self.td, self.home = temp_home()

    def tearDown(self):
        self.td.cleanup()

    def wd(self, *args):
        out, err, rc = run("workdir.py", {}, self.home, args=list(args) + ["--json"])
        self.assertEqual(rc, 0, err)
        return json.loads(out)

    def test_key_from_sops(self):
        r = self.wd("--file-key", "jUau2sA38TBr0R2HjR75HE")
        self.assertEqual((r["agency"], r["project"]), ("lions-share-digital", "khl"))

    def test_key_from_project_md(self):
        p = self.home / "work" / "test-person" / "acme" / "new-site"
        p.mkdir(parents=True)
        (p / "PROJECT.md").write_text("# acme › new-site\n- New site: fileKey `ZZZZ1234567890abcdefXY`\n")
        r = self.wd("--file-key", "ZZZZ1234567890abcdefXY")
        self.assertEqual((r["agency"], r["project"]), ("acme", "new-site"))

    def test_unknown_key_goes_to_unassigned(self):
        r = self.wd("--file-key", "QQQQ1234567890abcdefXY")
        self.assertEqual(r["agency"], "_unassigned")

    def test_second_job_same_day_gets_its_own_folder(self):
        a = self.wd("--file-key", "jUau2sA38TBr0R2HjR75HE", "--job", "hero fix")
        (self.home / a["job_path"].split(str(self.home) + "/", 1)[1] / "request.md").write_text("x")
        b = self.wd("--file-key", "jUau2sA38TBr0R2HjR75HE", "--job", "hero fix")
        self.assertNotEqual(a["job_path"], b["job_path"])
        self.assertTrue(b["job_path"].endswith("-hero-fix-2"))
        self.assertTrue((self.home / "work" / "test-person" / "lions-share-digital" / "khl" / "PROJECT.md").exists())


if __name__ == "__main__":
    unittest.main()
