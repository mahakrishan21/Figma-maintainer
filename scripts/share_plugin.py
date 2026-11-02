#!/usr/bin/env python3
"""SOP manager: release the plugin (with all SOPs in knowledge/) for co-workers.

  share_plugin.py [--version X.Y.Z | --bump patch|minor] [--message "what changed"]

1. Runs scripts/release_check.sh (compile, offline tests, manifests) and stops if it fails.
2. If anything changed (or --version is given): bumps the version (patch by default), commits everything
   with your git name, and makes an annotated tag vX.Y.Z.
3. Builds ~/ClaudeAI/Figma-maintainer.zip from exactly that tagged commit (git archive): no session files,
   no untracked or ignored files, no .git.
It never pushes, and never changes your Claude Code plugin install: yours reads this folder, so
/reload-plugins picks up changes. Publish with: git push origin main --tags
Session files (work folders, logs, audits, contributions) live outside the plugin and are never shared.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
ZIP = PLUGIN.parent / "Figma-maintainer.zip"


def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=PLUGIN, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", help="exact new version, e.g. 1.32.0")
    ap.add_argument("--bump", choices=["patch", "minor"], default="patch")
    ap.add_argument("--message", help="commit and tag message")
    a = ap.parse_args()
    if not (FM / ".master").exists():
        sys.exit("Only the SOP manager shares the plugin. Co-workers: send proposals with /figma-maintainer:contribute.")

    print("Release check …")
    rc = subprocess.run(["bash", str(PLUGIN / "scripts" / "release_check.sh")], cwd=PLUGIN, capture_output=True, text=True)
    if rc.returncode != 0:
        print(rc.stdout[-3000:] + rc.stderr[-1000:])
        sys.exit("Release check FAILED: nothing was committed or packaged. Fix the items above and share again.")
    print("  passed")

    pj = PLUGIN / ".claude-plugin" / "plugin.json"
    d = json.loads(pj.read_text())
    changed = git("status", "--porcelain")
    if changed or a.version:
        if a.version:
            new = a.version
        else:
            major, minor, patch = (int(x) for x in d["version"].split("."))
            new = f"{major}.{minor + 1}.0" if a.bump == "minor" else f"{major}.{minor}.{patch + 1}"
        if git("tag", "-l", f"v{new}"):
            sys.exit(f"Tag v{new} already exists: choose another --version.")
        d["version"] = new
        pj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
        files = [l[3:] for l in git("status", "--porcelain").splitlines()]
        sops = sum(1 for f in files if f.startswith("knowledge/"))
        msg = a.message or f"v{new}: share with the team ({sops} SOP/knowledge file(s), {len(files) - sops} other file(s))"
        git("add", "-A")
        git("commit", "-q", "-m", msg)
        git("tag", "-a", f"v{new}", "-m", msg.splitlines()[0])
    else:
        new = d["version"]
        if not git("tag", "-l", f"v{new}"):
            git("tag", "-a", f"v{new}", "-m", f"v{new}")
    if ZIP.exists():
        ZIP.unlink()
    git("archive", "--format=zip", f"--prefix={PLUGIN.name}/", "-o", str(ZIP), f"v{new}")
    tracked = git("ls-tree", "-r", "--name-only", f"v{new}").splitlines()
    sop_files = sum(1 for f in tracked if f.startswith("knowledge/clients/") and f.endswith(".md"))
    ahead = git("rev-list", "--count", "origin/main..HEAD", check=False) or "?"
    print(f"\nfigma-maintainer v{new} ready to share: {len(tracked)} files, {sop_files} SOP files · {ZIP} "
          f"({ZIP.stat().st_size // 1024} KB)" + ("" if changed or a.version else "  (nothing changed since the last share)"))
    print(f"Not pushed ({ahead} commit(s) ahead of GitHub). Publish with: git push origin main --tags")
    print("Co-workers: unzip over their plugin folder (first time: ~/ClaudeAI/Figma-maintainer), run "
          "/plugin marketplace update e2m-figma (first time: /plugin marketplace add … and /plugin install figma-maintainer@e2m-figma), "
          "restart Claude Code, then /figma-maintainer:doctor.")


if __name__ == "__main__":
    main()
