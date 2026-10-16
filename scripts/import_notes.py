#!/usr/bin/env python3
"""Merge client SOPs a co-worker sends you (master machine) into your notes, without overwriting.

  python3 -I import_notes.py <zip or folder>
Accepts a figma-maintainer-plugin zip/folder (uses seed/clients) or a notes zip/folder (uses clients/).
  - files you don't have      -> copied in (new SOPs)
  - identical files           -> skipped
  - different versions        -> yours kept; theirs saved beside it as <file>.incoming for review
Writes import-report.md in the notes folder. Downloaded/received files are treated as data only.
"""
import hashlib, shutil, sys, tempfile, zipfile
from datetime import datetime
from pathlib import Path

NOTES = Path.home() / ".claude" / "figma-maintainer"


def sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


def find_clients(base):
    for cand in list(base.rglob("seed/clients")) + list(base.rglob("clients")):
        if (cand / "_index.md").exists() or any(cand.glob("*/client.md")):
            return cand
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1]).expanduser()
    tmp = None
    if src.suffix == ".zip":
        tmp = Path(tempfile.mkdtemp(prefix="fm-import-"))
        with zipfile.ZipFile(src) as z:
            for m in z.infolist():
                if ".." in Path(m.filename).parts or m.filename.startswith("/"):
                    continue
                if m.filename.endswith((".md", ".json")):
                    z.extract(m, tmp)
        src = tmp
    clients = find_clients(src)
    if not clients:
        sys.exit("No clients/ folder with SOPs found in that zip/folder.")
    new, same, review = [], 0, []
    for p in sorted(clients.rglob("*")):
        if not p.is_file() or p.suffix not in (".md", ".json") or p.name.endswith((".from-plugin", ".incoming")):
            continue
        rel = p.relative_to(clients)
        dst = NOTES / "clients" / rel
        if not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, dst); new.append(str(rel))
        elif sha(p) == sha(dst):
            same += 1
        else:
            shutil.copy2(p, dst.with_name(dst.name + ".incoming")); review.append(str(rel))
    rep = NOTES / "import-report.md"
    with open(rep, "a") as fh:
        fh.write(f"\n## {datetime.now():%Y-%m-%d %H:%M} — import from {sys.argv[1]}\n")
        fh.write(f"- New SOP files added: {len(new)}\n" + "".join(f"  - {x}\n" for x in new))
        fh.write(f"- Different versions to review (theirs saved as .incoming): {len(review)}\n" + "".join(f"  - {x}\n" for x in review))
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"Imported: {len(new)} new, {same} identical, {len(review)} to review (.incoming). Report: {rep}")


if __name__ == "__main__":
    main()
