"""The prompt hook (image_gate.py) routes real prompts correctly, including every misfire seen in use."""
import json, unittest

from tests.helpers import ROOT, context, run, temp_home, transcript

CASES = json.loads((ROOT / "tests" / "prompts.json").read_text())


def check(expect, out, ctx):
    if expect == "silent":
        return out.strip() == ""
    neg = expect.startswith("not:")
    name = expect[4:] if neg else expect
    if ":" in name:
        name, arg = name.split(":", 1)
    else:
        arg = None
    hit = {
        "route": "client comment:" in ctx,
        "gate": "image gate" in ctx,
        "gate-ask": "image gate" in ctx and "doesn't say where images" in ctx,
        "gate-source": "names the image/video source" in ctx,
        "client": arg and f"Client detected: {arg}" in ctx,
        "suggest": "Closest matches" in ctx and arg and f"clients/{arg}/" in ctx,
        "noclient": "doesn't name a client" in ctx,
        "audit": "the user asked for" in ctx,
        "slack": "Slack message" in ctx,
        "skipqa": "skip the QA check" in ctx,
        "qa-note": "qa-checker" in ctx,
        "sop-image": arg and f"image preference: {arg}" in ctx,
    }.get(name)
    if hit is None:
        raise ValueError(f"unknown expectation {expect}")
    return (not hit) if neg else bool(hit)


class PromptRouting(unittest.TestCase):
    def test_cases(self):
        td, home = temp_home()
        try:
            for i, c in enumerate(CASES):
                tp = transcript(home, fm_session=True, name=f"s{i}") if c.get("session") else ""
                out, err, code = run("image_gate.py", {"prompt": c["prompt"], "transcript_path": str(tp), "session_id": f"s{i}"}, home)
                self.assertEqual(code, 0, f"hook crashed on {c['prompt'][:60]!r}: {err[-300:]}")
                ctx = context(out)
                for e in c["expect"]:
                    with self.subTest(prompt=c["prompt"][:70], expect=e):
                        self.assertTrue(check(e, out, ctx), f"expected {e}; got: {ctx[:300] or '(silent)'}")
        finally:
            td.cleanup()


if __name__ == "__main__":
    unittest.main()
