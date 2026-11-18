#!/usr/bin/env python3
"""SOP manager: release the plugin (with all SOPs in knowledge/) for co-workers.

  share_plugin.py [--version X.Y.Z | --bump patch|minor] [--message "what changed"]

1. Runs scripts/release_check.sh (compile, offline tests, manifests) and stops if it fails.
2. If anything changed (or --version is given): bumps the version (patch by default), commits everything
   with your git name, and makes an annotated tag vX.Y.Z.
3. Builds ~/ClaudeAI/Figma-maintainer.zip from exactly that tagged commit (git archive): no session files,
   no untracked or ignored files, no .git. The plugin's files sit at the ROOT of the zip (.claude-plugin/plugin.json
   at the top), which plugin uploads require; double-clicking it on a Mac still gives a "Figma-maintainer" folder.
4. Refreshes the team marketplace repo (the "marketplace: <folder>" line in ~/.claude/figma-maintainer/.master):
   replaces plugins/figma-maintainer/ with the same tagged build, copies the version and description into its
   marketplace.json, validates it, commits and tags vX.Y.Z there.
Paths marked export-ignore in .gitattributes (tests, release tools, the management briefing) are left out of both.
It never pushes, and never changes your Claude Code plugin install: yours reads this folder, so
/reload-plugins picks up changes. Publish with: git push origin main --tags (both repos)
Session files (work folders, logs, audits, contributions) live outside the plugin and are never shared.
"""
import argparse, io, json, os, re, shutil, subprocess, sys, tarfile, zipfile
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
ZIP = PLUGIN.parent / "Figma-maintainer.zip"


def git(*args, check=True, cwd=PLUGIN):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        sys.exit(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def marketplace_dir():
    m = re.search(r"^marketplace:\s*(.+)$", (FM / ".master").read_text(), re.M)
    return Path(m.group(1).strip()).expanduser() if m else None


def refresh_marketplace(market, version, plugin_json):
    """Put the tagged build into the team marketplace repo, commit and tag it there. Never pushes."""
    if not (market / ".git").exists() or not (market / ".claude-plugin" / "marketplace.json").exists():
        sys.exit(f"Marketplace folder {market} is not set up (no .git or .claude-plugin/marketplace.json).")
    dest = market / "plugins" / plugin_json["name"]
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "archive", "--format=tar", f"v{version}"], cwd=PLUGIN, capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:  # tar keeps the scripts' executable bits (a zip extract doesn't)
        t.extractall(dest)
    (dest / ".claude-plugin" / "marketplace.json").unlink(missing_ok=True)  # the dev marketplace; the repo root has the real one
    mj = market / ".claude-plugin" / "marketplace.json"
    cat = json.loads(mj.read_text())
    for e in cat.get("plugins", []):
        if e.get("name") == plugin_json["name"]:
            e["version"], e["description"] = version, plugin_json["description"]
    mj.write_text(json.dumps(cat, indent=2, ensure_ascii=False) + "\n")
    if shutil.which("claude"):
        v = subprocess.run(["claude", "plugin", "validate", str(market)], capture_output=True, text=True, timeout=120)
        if v.returncode != 0:
            sys.exit(f"claude plugin validate failed for {market}:\n{v.stdout[-2000:]}{v.stderr[-1000:]}")
    git("add", "-A", cwd=market)
    if git("status", "--porcelain", cwd=market):
        git("commit", "-q", "-m", f"figma-maintainer v{version}", cwd=market)
    if not git("tag", "-l", f"v{version}", cwd=market):
        git("tag", "-a", f"v{version}", "-m", f"figma-maintainer v{version}", cwd=market)
    files = sum(1 for _ in dest.rglob("*") if _.is_file())
    print(f"Marketplace {market}: figma-maintainer v{version} ({files} files), committed and tagged. "
          f"Publish with: git -C {market} push origin main --tags")


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
    git("archive", "--format=zip", "-o", str(ZIP), f"v{new}")
    with zipfile.ZipFile(ZIP) as z:  # what plugin uploads check: manifest at the root, description within limits
        names = set(z.namelist())
        if ".claude-plugin/plugin.json" not in names:
            sys.exit("The zip has no .claude-plugin/plugin.json at its root: not shareable.")
        desc = json.loads(z.read(".claude-plugin/plugin.json")).get("description", "")
        if len(desc) > 500:
            sys.exit(f"plugin.json description is {len(desc)} characters (max 500): shorten it and share again.")
    tracked = git("ls-tree", "-r", "--name-only", f"v{new}").splitlines()
    sop_files = sum(1 for f in tracked if f.startswith("knowledge/clients/") and f.endswith(".md"))
    ahead = git("rev-list", "--count", "origin/main..HEAD", check=False) or "?"
    print(f"\nfigma-maintainer v{new} ready to share: {len(tracked)} files, {sop_files} SOP files · {ZIP} "
          f"({ZIP.stat().st_size // 1024} KB)" + ("" if changed or a.version else "  (nothing changed since the last share)"))
    print(f"Not pushed ({ahead} commit(s) ahead of GitHub). Publish with: git push origin main --tags")
    market = marketplace_dir()
    if market:
        refresh_marketplace(market, new, json.loads(git("show", f"v{new}:.claude-plugin/plugin.json")))
        print("Co-workers (after both pushes): /plugin marketplace update e2m-figma, then /reload-plugins. "
              "First time: /plugin marketplace add mahakrishan21/e2m-figma-marketplace and /plugin install figma-maintainer@e2m-figma.")
    else:
        print("No team marketplace set up (no 'marketplace:' line in .master): only the zip was built.")


if __name__ == "__main__":
    main()
