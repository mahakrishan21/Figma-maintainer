#!/usr/bin/env python3
"""Bring the team notes shipped in the plugin (seed/) into this person's notes folder.

Runs at every session start (from bootstrap.sh). Silent unless something needs attention.
  - new SOP files              -> copied in
  - SOP updated in the plugin  -> replaces the local copy, IF the local copy is an untouched
                                  earlier plugin version (checked against seed/notes-manifest.json)
  - local copy edited by you   -> kept; the plugin's version is saved beside it as
                                  <file>.from-plugin and listed in sync-conflicts.md
  - files are never deleted; personal logs (usage, audit log) are never touched
Skipped entirely on the master machine (a `.master` file in the notes folder), where the
notes are the source the plugin is built from.
"""
import argparse, hashlib, json, os, shutil, sys
from datetime import date
from pathlib import Path

SHARED_TOP = ["playbook.md", "pricing.json", "cost-config.json"]
COPY_IF_MISSING = ["job-log.md"]


def sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True); ap.add_argument("--dest", required=True)
    a = ap.parse_args()
    root, dest = Path(a.root) / "seed", Path(a.dest)
    if (dest / ".master").exists():
        return
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {}
    mp = root / "notes-manifest.json"
    if mp.exists():
        try:
            manifest = json.loads(mp.read_text()).get("files", {})
        except Exception:
            manifest = {}
    state_p = dest / ".sync-state.json"
    try:
        state = json.loads(state_p.read_text())
    except Exception:
        state = {}

    files = [f for f in SHARED_TOP if (root / f).exists()]
    files += [str(p.relative_to(root)) for p in sorted((root / "clients").rglob("*")) if p.is_file() and p.name != ".DS_Store"]
    added, updated, conflicts = [], [], []
    for rel in files:
        src, dst = root / rel, dest / rel
        s = sha(src)
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src, dst); state[rel] = s; added.append(rel); continue
        l = sha(dst)
        if l == s:
            state[rel] = s; continue
        known = set(manifest.get(rel, {}).get("history", [])) | ({state[rel]} if rel in state else set())
        if l in known:  # untouched earlier plugin version -> safe to update
            shutil.copy2(src, dst); state[rel] = s; updated.append(rel)
        else:  # edited locally -> keep, park the plugin's version beside it
            side = dst.with_name(dst.name + ".from-plugin")
            if not side.exists() or sha(side) != s:
                shutil.copy2(src, side)
                conflicts.append(rel)
    for f in COPY_IF_MISSING:
        if (root / f).exists() and not (dest / f).exists():
            shutil.copy2(root / f, dest / f)
    state_p.write_text(json.dumps(state, indent=0))
    if conflicts:
        with open(dest / "sync-conflicts.md", "a") as fh:
            fh.write(f"\n## {date.today()} — plugin update vs your local edits\n"
                     "Your version was kept. The plugin's version is beside it as `<file>.from-plugin`. "
                     "Compare them, merge what you need, then delete the .from-plugin file.\n")
            fh.writelines(f"- {c}\n" for c in conflicts)
    if added or updated or conflicts:
        print(f"figma-maintainer notes synced: {len(added)} new, {len(updated)} updated, {len(conflicts)} kept as your local edits"
              + (" (see ~/.claude/figma-maintainer/sync-conflicts.md)" if conflicts else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
