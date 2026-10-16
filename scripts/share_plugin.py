#!/usr/bin/env python3
"""Package the plugin for co-workers WITH the current team notes (master machine only).

  1. copies your notes (clients/ SOPs, playbook, prices, cost settings, job log) into seed/
  2. writes seed/notes-manifest.json: every earlier version's hash per file, so co-workers'
     untouched copies can be updated safely and their own edits are never overwritten
  3. bumps the patch version, commits and tags in git
  4. updates your own install and writes ~/ClaudeAI/figma-maintainer-plugin.zip
Personal files (usage log, Figma audit log, sync state) are never shared.
"""
import hashlib, json, os, shutil, subprocess, sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
NOTES = Path.home() / ".claude" / "figma-maintainer"
SHARED = ["playbook.md", "pricing.json", "cost-config.json", "job-log.md"]
ZIP = PLUGIN.parent / "figma-maintainer-plugin.zip"


def run(*cmd, **kw):
    return subprocess.run(cmd, cwd=PLUGIN, capture_output=True, text=True, **kw)


def sha_bytes(b):
    return hashlib.sha1(b).hexdigest()


def main():
    if not (NOTES / ".master").exists():
        sys.exit("This machine isn't the notes master (no .master file in ~/.claude/figma-maintainer). "
                 "Send your new SOPs to the master with the notes zip instead (see /figma-maintainer:import-notes).")
    seed = PLUGIN / "seed"
    # 1. mirror notes -> seed
    if (seed / "clients").exists():
        shutil.rmtree(seed / "clients")
    shutil.copytree(NOTES / "clients", seed / "clients",
                    ignore=shutil.ignore_patterns(".DS_Store", "*.from-plugin", "*.incoming", "__pycache__"))
    for f in SHARED:
        if (NOTES / f).exists():
            shutil.copy2(NOTES / f, seed / f)
    # 2. manifest with history hashes
    files = {}
    for p in sorted(seed.rglob("*")):
        if not p.is_file() or p.name in ("notes-manifest.json", ".DS_Store"):
            continue
        rel = str(p.relative_to(seed))
        hist = set()
        commits = run("git", "log", "--format=%H", "--", f"seed/{rel}").stdout.split()
        for c in commits:
            r = subprocess.run(["git", "show", f"{c}:seed/{rel}"], cwd=PLUGIN, capture_output=True)
            if r.returncode == 0:
                hist.add(sha_bytes(r.stdout))
        cur = sha_bytes(p.read_bytes())
        hist.add(cur)
        files[rel] = {"current": cur, "history": sorted(hist)}
    (seed / "notes-manifest.json").write_text(json.dumps({"files": files}, indent=0))
    # 3. version bump + commit
    pj = PLUGIN / ".claude-plugin" / "plugin.json"
    d = json.loads(pj.read_text())
    major, minor, patch = (int(x) for x in d["version"].split("."))
    changed = run("git", "status", "--porcelain").stdout.strip()
    if changed:
        d["version"] = f"{major}.{minor}.{patch + 1}"
        pj.write_text(json.dumps(d, indent=2))
        run("git", "add", "-A")
        n_clients = sum(1 for x in (seed / "clients").iterdir() if x.is_dir() and not x.name.startswith("_"))
        run("git", "-c", "user.name=figma-maintainer share", "-c", "user.email=share@localhost", "commit", "-q", "-m",
            f"Share v{d['version']}: team notes synced ({n_clients} agencies)")
        run("git", "tag", f"v{d['version']}")
    # 4. local install + zip
    subprocess.run(["claude", "plugin", "marketplace", "update", "e2m-figma"], capture_output=True)
    subprocess.run(["claude", "plugin", "update", "figma-maintainer@e2m-figma"], capture_output=True)
    if ZIP.exists():
        ZIP.unlink()
    subprocess.run(["zip", "-rq", str(ZIP), PLUGIN.name, "-x", "*.DS_Store", "-x", "*__pycache__*", "-x", f"{PLUGIN.name}/.git/*"],
                   cwd=PLUGIN.parent, check=True)
    n_sop = sum(1 for _ in (seed / "clients").rglob("*.md"))
    print(f"Shared figma-maintainer v{d['version']}: {n_sop} SOP/notes files, zip → {ZIP}"
          + ("" if changed else " (no notes changes since the last share)"))


if __name__ == "__main__":
    main()
