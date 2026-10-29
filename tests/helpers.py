"""Shared helpers for the figma-maintainer tests: a throw-away session folder and a runner for the hook scripts."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
FM_SESSION_MARKER = '"subagent_type":"figma-maintainer:figma-maintainer"'


def temp_home():
    """A temporary ~/.claude/figma-maintainer with links to the plugin's real SOPs. Returns (TemporaryDirectory, Path)."""
    td = tempfile.TemporaryDirectory()
    home = Path(td.name)
    (home / "clients").symlink_to(ROOT / "knowledge" / "clients")
    (home / "playbook.md").symlink_to(ROOT / "knowledge" / "playbook.md")
    (home / ".person").write_text("Test Person\n")
    return td, home


def transcript(home, messages=(), fm_session=False, name="session-test"):
    """A main-session transcript with these user messages (and the plugin's session marker when fm_session)."""
    p = home / f"{name}.jsonl"
    with open(p, "w") as f:
        for m in messages:
            f.write(json.dumps({"type": "user", "message": {"role": "user", "content": m}}) + "\n")
        if fm_session:
            f.write(json.dumps({"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Agent",
                                "input": {"subagent_type": "figma-maintainer:figma-maintainer"}}]}}).replace(" ", "") + "\n")
    return p


def run(script, payload, home, args=(), env=None):
    """Run a plugin script the way hooks do (python3 -I), with stdin JSON. Returns (stdout, stderr, returncode)."""
    e = dict(os.environ, FIGMA_MAINTAINER_HOME=str(home))
    e.pop("FIGMA_TOKEN", None)
    e.update(env or {})
    r = subprocess.run([sys.executable, "-I", str(SCRIPTS / script), *args], input=json.dumps(payload),
                       capture_output=True, text=True, env=e, timeout=120)
    return r.stdout, r.stderr, r.returncode


def context(stdout):
    """additionalContext of a UserPromptSubmit hook output ('' when silent)."""
    if not stdout.strip():
        return ""
    return json.loads(stdout).get("hookSpecificOutput", {}).get("additionalContext", "")


def fixtures(dirpath, responses):
    """Write a FIGMA_FIXTURES folder: {api path: json body or {"status": code}}."""
    d = Path(dirpath); d.mkdir(parents=True, exist_ok=True)
    idx = {}
    for i, (path, body) in enumerate(responses.items()):
        if isinstance(body, dict) and set(body) == {"status"}:
            idx[path] = body
            continue
        name = f"r{i}.json"
        (d / name).write_text(json.dumps(body))
        idx[path] = name
    (d / "index.json").write_text(json.dumps(idx, indent=1))
    return d
