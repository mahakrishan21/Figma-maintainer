#!/usr/bin/env python3
"""Co-worker contributions to the central SOPs.

  contribute.py --pack                 zip ~/.claude/figma-maintainer/contributions/*.md for the SOP manager
  contribute.py --extract <zip|dir>    (SOP manager) unpack received contributions to a review folder, list them
  contribute.py --review-old <session> <knowledge>   (bootstrap) list old local SOP copies that differ from the plugin
"""
import hashlib, shutil, sys, tempfile, zipfile, os
from datetime import datetime
from pathlib import Path

FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")


def sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


def pack():
    c = FM / "contributions"
    files = sorted(x for x in c.glob("*.md")) if c.exists() else []
    if not files:
        sys.exit("No contribution files in ~/.claude/figma-maintainer/contributions/.")
    out = Path.home() / "ClaudeAI" / f"figma-maintainer-contributions-{datetime.now():%Y%m%d-%H%M}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, f"contributions/{f.name}")
    sent = c / "sent" / f"{datetime.now():%Y%m%d-%H%M}"
    sent.mkdir(parents=True, exist_ok=True)
    for f in files:
        shutil.move(str(f), sent / f.name)
    print(f"{len(files)} contribution(s) packed → {out}\nSend this zip to the SOP manager. (Originals moved to contributions/sent/.)")


def extract(src):
    src = Path(src).expanduser()
    dest = FM / "contributions" / "received" / f"{datetime.now():%Y%m%d-%H%M}"
    dest.mkdir(parents=True, exist_ok=True)
    if src.suffix == ".zip":
        with zipfile.ZipFile(src) as z:
            for m in z.infolist():
                n = Path(m.filename)
                if m.is_dir() or ".." in n.parts or m.filename.startswith("/") or n.suffix != ".md":
                    continue
                (dest / n.name).write_bytes(z.read(m))
    else:
        for f in src.rglob("*.md"):
            shutil.copy2(f, dest / f.name)
    files = sorted(dest.glob("*.md"))
    print(f"{len(files)} contribution(s) to review in {dest}:")
    for f in files:
        print(f"  - {f.name}")


def review_old(session, knowledge):
    session, knowledge = Path(session), Path(knowledge)
    old_root = session / "_old-local-notes"
    rows = []
    for f in old_root.rglob("*"):
        if not f.is_file() or f.suffix not in (".md", ".json"):
            continue
        parts = f.relative_to(old_root).parts[1:]  # drop timestamp folder
        rel = Path(*parts)
        cur = knowledge / rel
        if not cur.exists() or sha(cur) != sha(f):
            rows.append((str(rel), "new (not in the plugin)" if not cur.exists() else "differs from the plugin"))
    if rows:
        rep = session / "contributions" / f"{datetime.now():%Y-%m-%d}-old-local-notes-review.md"
        with open(rep, "w") as fh:
            fh.write("# Contribution: old local SOP copies\n\nThese local notes from an earlier plugin version differ from the "
                     "central SOPs. If any of them hold real client rules, describe the change here and send this file to "
                     "the SOP manager (python3 -I ~/.claude/figma-maintainer/scripts/contribute.py --pack zips them). The old files are under ~/.claude/figma-maintainer/_old-local-notes/.\n\n")
            fh.writelines(f"- `{r}`: {why}\n" for r, why in sorted(rows))
        print(f"figma-maintainer: {len(rows)} old local SOP file(s) differ from the plugin; see {rep}", file=sys.stderr)


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--pack"]:
        pack()
    elif a[:1] == ["--extract"] and len(a) == 2:
        extract(a[1])
    elif a[:1] == ["--review-old"] and len(a) == 3:
        review_old(a[1], a[2])
    else:
        sys.exit(__doc__)
