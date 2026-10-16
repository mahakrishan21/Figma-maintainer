#!/usr/bin/env python3
"""SOP manager: package the plugin (with all SOPs in knowledge/) for co-workers.

Requires the .master file. Commits any pending changes (SOPs, scripts, agents), bumps the patch
version, tags it, updates the local install and writes ~/ClaudeAI/figma-maintainer-plugin.zip.
Session files (logs, audits, reports, contributions) live outside the plugin and are never shared.
"""
import json, subprocess, sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
FM = Path.home() / ".claude" / "figma-maintainer"
ZIP = PLUGIN.parent / "figma-maintainer-plugin.zip"


def run(*cmd):
    return subprocess.run(cmd, cwd=PLUGIN, capture_output=True, text=True)


def main():
    if not (FM / ".master").exists():
        sys.exit("Only the SOP manager shares the plugin. Co-workers: send proposals with /figma-maintainer:contribute.")
    changed = run("git", "status", "--porcelain").stdout.strip()
    pj = PLUGIN / ".claude-plugin" / "plugin.json"
    d = json.loads(pj.read_text())
    if changed:
        major, minor, patch = (int(x) for x in d["version"].split("."))
        d["version"] = f"{major}.{minor}.{patch + 1}"
        pj.write_text(json.dumps(d, indent=2))
        files = [l[3:] for l in changed.splitlines()]
        sops = sum(1 for f in files if f.startswith("knowledge/"))
        run("git", "add", "-A")
        run("git", "-c", "user.name=SOP manager", "-c", "user.email=sop@localhost", "commit", "-q", "-m",
            f"Share v{d['version']}: {sops} SOP/knowledge file(s), {len(files) - sops} other file(s) changed")
        run("git", "tag", f"v{d['version']}")
    subprocess.run(["claude", "plugin", "marketplace", "update", "e2m-figma"], capture_output=True)
    subprocess.run(["claude", "plugin", "update", "figma-maintainer@e2m-figma"], capture_output=True)
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-rq", str(ZIP), PLUGIN.name, "-x", "*.DS_Store", "-x", "*__pycache__*", "-x", f"{PLUGIN.name}/.git/*"],
                   cwd=PLUGIN.parent, check=True)
    n = sum(1 for _ in (PLUGIN / "knowledge" / "clients").rglob("*.md"))
    print(f"figma-maintainer v{d['version']} ready to share: {n} SOP files · {ZIP}"
          + ("" if changed else " (nothing changed since the last share)"))


if __name__ == "__main__":
    main()
