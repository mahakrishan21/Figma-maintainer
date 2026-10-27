#!/usr/bin/env python3
"""Per-person → per-client (agency) → per-project working folder for figma-maintainer.

  workdir.py --url "<figma url>"                 resolve agency/project from the SOPs by file key
  workdir.py --agency "Lasso up" --project "Meeks Electrical"
  workdir.py --file-key <key>                    same as --url
  workdir.py ... --job "<short job name>"        also create and print jobs/<date>-<job>/ for this job's records

Creates (only if missing) and prints:
  ~/.claude/figma-maintainer/work/<person>/<agency-slug>/<project-slug>/
      PROJECT.md (living project context)  job-log.md  jobs/ snapshots/ comments/ audits/ reports/ assets/ slack/
Person = the name in ~/.claude/figma-maintainer/.person (set at first session start).
Agency/project come from the plugin SOPs (clients/): a project file (<agency>/<project>.md) or a
"### Job N: <Project>" entry in a task SOP that mentions the file key. Unknown files go to
_unassigned/<file-key>/ until the agency is known. Folders that already exist are reused as-is.
"""
import argparse, json, re, sys
from datetime import date
from pathlib import Path

FM = Path.home() / ".claude" / "figma-maintainer"
SUBDIRS = ("snapshots", "comments", "audits", "reports", "assets", "slack", "jobs")

PROJECT_TEMPLATE = """# {agency} › {project} — project context

> Living context for this project. **Read it before every job; update it at the end of every job.**
> Keep it current (rewrite sections; don't just append). The full history lives in jobs/ and job-log.md.

## Client & project
- Agency (our client): {agency}
- Project (their client): {project}
- SOP: ~/.claude/figma-maintainer/clients/{agency}/ (client.md, project/task SOPs)
- Image preference and delivery tool: see the SOP (repeat here only if this project differs)

## Figma files and latest frames
- <file name>: fileKey `<key>`
- Latest version / frames: <page › section › frame `id`>, prototype link: <link>
- Approved originals (never edit): <frames>

## Current status
- <what's done, what's in review, what's next>

## Client decisions (dated)
- <YYYY-MM-DD — decision — who / source>

## Open items / waiting on the client
- <question or asset needed — since when>

## Comment rounds applied
- <YYYY-MM-DD round (comments from … to …) — applied to <frame> — jobs/<folder>>

## Job history
- <YYYY-MM-DD — task — jobs/<folder>>
"""


def slug(s):
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (s or "").lower().replace("'", "").replace("’", ""))).strip("-") or "general"


def person():
    p = FM / ".person"
    if p.exists() and p.read_text().strip():
        return slug(p.read_text().strip())
    import getpass
    return slug(getpass.getuser())


def key_from_url(u):
    m = re.search(r"figma\.com/(?:design|file)/([A-Za-z0-9]+)(?:/branch/([A-Za-z0-9]+))?", u or "")
    return (m.group(2) or m.group(1)) if m else None


def resolve_key(key):
    """Return (agency_folder, project_slug) for a Figma file key, from the SOPs."""
    cl = FM / "clients"
    if not cl.exists():
        return None
    for f in sorted(cl.rglob("*.md")):
        if any(p.startswith("_") for p in f.relative_to(cl).parts[:-1]) or f.name == "_index.md":
            continue
        text = f.read_text(errors="ignore")
        pos = text.find(key)
        if pos < 0:
            continue
        agency = f.relative_to(cl).parts[0]
        if f.name.startswith("task-") or f.name == "client.md":
            jobs = [m for m in re.finditer(r"^#{2,4}\s*Job\s*\d+:\s*([^(\n·]+)", text, re.M) if m.start() < pos]
            if jobs:
                return agency, slug(jobs[-1].group(1))
            return agency, "general"
        return agency, slug(f.stem)
    # projects set up before their SOP: a work folder whose PROJECT.md lists the key
    for pm in sorted((FM / "work").glob("*/*/*/PROJECT.md")):
        if pm.parts[-3] != "_unassigned" and key in pm.read_text(errors="ignore"):
            return pm.parts[-3], pm.parts[-2]
    return None


def resolve_names(agency, project):
    """Map an agency name to its SOP folder via _index.md (falls back to the slug)."""
    idx = FM / "clients" / "_index.md"
    a = slug(agency)
    if idx.exists():
        na = re.sub(r"[^a-z0-9]+", " ", agency.lower()).strip()
        for line in idx.read_text(errors="ignore").splitlines():
            m = re.match(r"- \*\*(.+?)\*\* → `([^`]+)/`", line)
            if m and re.sub(r"[^a-z0-9]+", " ", m.group(1).lower()).strip() == na:
                a = m.group(2)
                break
    return a, slug(project) if project else "general"


def ensure(path):
    created = not path.exists()
    path.mkdir(parents=True, exist_ok=True)
    for d in SUBDIRS:
        (path / d).mkdir(exist_ok=True)
    jl = path / "job-log.md"
    if not jl.exists():
        jl.write_text(f"# Job log — {path.parent.name} › {path.name}\n\nNewest last. One entry per job.\n")
    pm = path / "PROJECT.md"
    if not pm.exists():
        pm.write_text(PROJECT_TEMPLATE.format(agency=path.parent.name, project=path.name))
    return created


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url"); ap.add_argument("--file-key"); ap.add_argument("--agency"); ap.add_argument("--project")
    ap.add_argument("--job", help="short job name: also creates <project>/jobs/<date>-<job>/")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    key = a.file_key or key_from_url(a.url)
    agency = project = None
    if a.agency:
        agency, project = resolve_names(a.agency, a.project)
    elif key:
        r = resolve_key(key)
        if r:
            agency, project = r
        else:
            agency, project = "_unassigned", key
    else:
        sys.exit("Pass --url / --file-key, or --agency [--project]")
    root = FM / "work" / person() / agency / project
    created = ensure(root)
    job = None
    if a.job:
        job = root / "jobs" / f"{date.today()}-{slug(a.job)}"
        n = 2
        while job.exists() and any(job.iterdir()):  # a second job with the same name today gets its own folder
            job = root / "jobs" / f"{date.today()}-{slug(a.job)}-{n}"; n += 1
        job.mkdir(parents=True, exist_ok=True)
    if a.json:
        print(json.dumps({"person": person(), "agency": agency, "project": project, "path": str(root),
                          "job_path": str(job) if job else None, "created": created}))
    else:
        print(root)
        if job:
            print(job)


if __name__ == "__main__":
    main()
