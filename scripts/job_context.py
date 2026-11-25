#!/usr/bin/env python3
"""Everything a figma-maintainer job needs to know, in one compact call (read-only, except folders and context.md).

  job_context.py --url "<figma url>" --job "<short task name>" [--for <task type>]
  job_context.py --agency "Lasso up" [--project "Meeks Electrical"] [--job …] [--for …]
  job_context.py --url … --job-dir <existing job folder> --for …      (saves context.md there, no new folder)

--for: copy | images | responsive | inner-page | comments | components | audit | qa (several: --for images,copy)

Prints, filtered for the task type:
  - the project folder and this job's folder (same as workdir.py);
  - the client: agency SOP and project SOP, only the rules that are set (template text dropped; the
    keys still <not set> listed in one line per section, because the agent asks about those);
  - task SOPs: each one's "When this applies"; the full method only for the matching task type, with its
    Jobs section cut to the last two jobs;
  - the playbook: the sections every job needs plus the ones for this task type;
  - PROJECT.md without template placeholders, the last job's report summary and the last 10 job-log entries.
Also saves the same text to <job folder>/context.md, so QA and later steps read it instead of the files again.
The full files stay where they are; open one only when the digest says a section matters and is cut.
"""
import argparse, os, re, sys
from datetime import date
from pathlib import Path

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE))
import workdir as wd  # noqa: E402

FM = wd.FM
PLAYBOOK_ALWAYS = ("Inspecting", "Editing: scope", "Editing: text", "Editing: layout", "Quality checks", "Plugin API gotchas")
PLAYBOOK_FOR = {"images": ("Images",), "responsive": ("Responsive builds", "Images"), "copy": ("Copy docs",),
                "inner-page": ("Images", "Copy docs"), "comments": ("Images", "Copy docs")}
TASK_SOP_FOR = {"responsive": "responsive", "inner-page": "inner-page", "comments": "comment", "audit": "audit",
                "components": "component", "copy": "copy", "images": "image"}
NOT_SET = re.compile(r"<not set[^>]*>")
PLACEHOLDER = re.compile(r"<[^<>\n]{2,80}>")


def digest_sop(text, keep_jobs=2, project=None):
    """Only the set rules of an SOP file: headings that have content, bullets with real values.
    With `project`, a task SOP's Jobs section keeps only that project's jobs (others listed by title)."""
    out, not_set, section = [], [], None

    def flush():
        if not_set:
            out.append(f"- (not set: {', '.join(not_set)})")
            not_set.clear()

    lines = text.splitlines()
    # Jobs section of a task SOP: keep only the last `keep_jobs` jobs
    jobs_at = next((i for i, l in enumerate(lines) if re.match(r"^##\s+\d*\.?\s*Jobs\b", l)), None)
    if jobs_at is not None:
        starts = [i for i, l in enumerate(lines) if i > jobs_at and re.match(r"^###\s+Job\b", l)]
        if project is not None and starts:
            blocks = [lines[s:e] for s, e in zip(starts, starts[1:] + [len(lines)])]
            mine = [b for b in blocks if project.replace("-", "") in re.sub(r"[^a-z0-9]", "", b[0].lower())]
            others = [b[0].lstrip("# ") for b in blocks if b not in mine]
            lines = lines[:jobs_at + 1] + ([f"(other projects' jobs, not for this one: {'; '.join(others)})"] if others else []) \
                + [l for b in mine[-keep_jobs:] for l in b]
            starts = []
        if len(starts) > keep_jobs:
            cut = starts[-keep_jobs]
            lines = lines[:jobs_at + 1] + [f"(… {len(starts) - keep_jobs} older job(s) in the full file)"] + lines[cut:]
    for line in lines:
        s = line.rstrip()
        if s.startswith(">"):
            continue  # template guidance
        if re.match(r"^#{1,6}\s", s):
            flush()
            section = s
            out.append(s)
            continue
        if not s.strip():
            continue
        if NOT_SET.search(s) and not re.sub(r"\(.*?\)", "", NOT_SET.sub("", s)).split(":", 1)[-1].strip():
            key = re.sub(r"^[-*]\s*", "", s.split(":", 1)[0]).strip("* ")
            not_set.append(key[:40])
            continue
        if re.fullmatch(r"\s*[-*]\s*<[^>]*>\s*", s):
            continue  # an empty template bullet like "- <YYYY-MM-DD — rule — source>"
        out.append(s)
    flush()
    # long lists (teaming.rocks project snapshots, asset logs): first 6 bullets, then a count
    capped, run = [], 0
    for l in out:
        run = run + 1 if l.lstrip().startswith("- ") else 0
        if run == 7:
            capped.append("- (… more in the full file)")
        if run < 7:
            capped.append(l)
    out = capped
    # drop headings left with nothing under them
    res = []
    for i, l in enumerate(out):
        if re.match(r"^#{2,6}\s", l):
            nxt = next((x for x in out[i + 1:]), "")
            if not nxt or (re.match(r"^#{1,6}\s", nxt) and nxt.count("#") <= l.count("#")):
                continue
        res.append(l)
    return "\n".join(res)


def sections(text, wanted):
    """The `## ` sections of a Markdown file whose titles start with any of `wanted`."""
    parts = re.split(r"(?m)^(?=## )", text)
    return "\n".join(p.rstrip() for p in parts if any(p[3:].startswith(w) for w in wanted))


def project_md(path):
    if not path.exists():
        return ""
    keep = [l for l in path.read_text(errors="ignore").splitlines()
            if l.strip() and not l.startswith(">") and not (l.lstrip().startswith("-") and PLACEHOLDER.search(l) and
                                                            not re.sub(PLACEHOLDER, "", l).strip(" -:·,`"))]
    return "\n".join(keep)


def last_report(root):
    reports = sorted((root / "jobs").glob("*/report.md"), key=lambda p: p.stat().st_mtime)
    if not reports:
        return ""
    text = reports[-1].read_text(errors="ignore")
    head = text.split("\n## ", 2)
    summary = "\n## ".join(head[:2])[:1800]
    return f"{reports[-1].relative_to(root)}:\n{summary}"


def job_log(root, n=10):
    p = root / "job-log.md"
    if not p.exists():
        return ""
    entries = re.split(r"(?m)^(?=## |### |- \d{4}-\d{2}-\d{2})", p.read_text(errors="ignore"))
    entries = [e.strip() for e in entries if re.match(r"(## |### |- )\d{4}-\d{2}-\d{2}", e.strip())]
    return "\n".join(entries[-n:])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url"); ap.add_argument("--file-key"); ap.add_argument("--agency"); ap.add_argument("--project")
    ap.add_argument("--job"); ap.add_argument("--for", dest="kinds", default="")
    ap.add_argument("--job-dir", help="an existing job folder (handed over from the client-comment workflow): save context.md there")
    a = ap.parse_args()
    kinds = [k.strip() for k in a.kinds.split(",") if k.strip()]
    key = a.file_key or wd.key_from_url(a.url)
    if a.agency:
        agency, project = wd.resolve_names(a.agency, a.project)
    elif key:
        agency, project = wd.resolve_key(key) or ("_unassigned", key)
    else:
        sys.exit("Pass --url / --file-key, or --agency [--project]")
    root = FM / "work" / wd.person() / agency / project
    wd.ensure(root)
    job = Path(a.job_dir).expanduser() if a.job_dir else None
    if job:
        job.mkdir(parents=True, exist_ok=True)
    elif a.job:
        job = root / "jobs" / f"{date.today()}-{wd.slug(a.job)}"
        n = 2
        while job.exists() and any(p.name != "context.md" for p in job.iterdir()):
            job = root / "jobs" / f"{date.today()}-{wd.slug(a.job)}-{n}"; n += 1
        job.mkdir(parents=True, exist_ok=True)

    out = [f"# Job context: {agency} › {project}", f"Project folder: {root}"]
    if job:
        out.append(f"Job folder: {job}")
    cl = FM / "clients" / agency
    if agency == "_unassigned":
        out.append("\n## Client\nUNKNOWN: no SOP matches this file. Ask which client this is for (closest names: grep clients/_index.md).")
    else:
        cm = cl / "client.md"
        if cm.exists():
            out += [f"\n## Agency SOP (digest of {cm})", digest_sop(cm.read_text(errors="ignore"))]
        pf = next((p for p in cl.glob("*.md") if p.name not in ("client.md",) and not p.name.startswith("task-")
                   and wd.slug(p.stem) == project), None)
        if pf:
            out += [f"\n## Project SOP (digest of {pf})", digest_sop(pf.read_text(errors="ignore"))]
        tasks = sorted(cl.glob("task-*.md"))
        if tasks:
            out.append("\n## Task SOPs for this agency (apply only when the request matches)")
            for t in tasks:
                body = t.read_text(errors="ignore")
                when = sections(body, ("1. When this applies", "When this applies")).split("\n", 1)[-1].strip()
                match = any(TASK_SOP_FOR.get(k, "~") in t.name for k in kinds)
                if match:
                    out += [f"### {t.name} (matches this task: follow it)", digest_sop(body, project=project)]
                else:
                    out.append(f"- {t} · when: {when[:240] or 'see file'}")
    pb = FM / "playbook.md"
    if pb.exists():
        want = PLAYBOOK_ALWAYS + tuple(w for k in kinds for w in PLAYBOOK_FOR.get(k, ()))
        out += [f"\n## Playbook ({pb}: sections for this task)", sections(pb.read_text(errors="ignore"), want)]
    pm = project_md(root / "PROJECT.md")
    if pm:
        out += ["\n## PROJECT.md", pm]
    rep = last_report(root)
    if rep:
        out += ["\n## Last job report (summary)", rep]
    log = job_log(root)
    if log:
        out += ["\n## Job log (last 10)", log]
    text = "\n".join(out).rstrip() + "\n"
    if job:
        (job / "context.md").write_text(text)
        text += f"\n(Saved to {job / 'context.md'}: pass that path on instead of re-reading the SOPs.)\n"
    print(text)


if __name__ == "__main__":
    main()
