#!/usr/bin/env python3
"""UserPromptSubmit hook: before any figma-maintainer job, make sure the image/video
source is known. If the prompt names it, pass it on; if not, tell Claude to ask first
and not start until the user answers. Silent for prompts that aren't Figma jobs."""
import json, re, sys

try:
    prompt = json.load(sys.stdin).get("prompt", "") or ""
except Exception:
    sys.exit(0)
p = prompt.lower()

# ---- client SOP lookup: agency/project name or Figma file key -> clients/<agency>/client.md (+ project.md)
from pathlib import Path
CL = Path.home() / ".claude" / "figma-maintainer" / "clients"
GENERIC = {"design", "web", "seo", "ppc", "misc", "tasks", "website", "homepage", "landing page", "maintenance", "wordpress tasks",
           "shopify tasks", "maintenance projects", "daily task list", "design task", "social media", "general"}


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower().replace("'", "").replace("’", "")).strip()


def find_client():
    if not CL.is_dir():
        return None
    np_ = " " + norm(prompt) + " "
    # file key first (most precise)
    for key in set(re.findall(r"figma\.com/(?:design|file)/([A-Za-z0-9]{10,})", prompt)):
        for f in CL.rglob("*.md"):
            if f.name != "client.md" and not f.parent.name.startswith("_") and key in f.read_text(errors="ignore"):
                return f.parent, f
    idx = CL / "_index.md"
    if not idx.exists():
        return None
    best = None
    for line in idx.read_text(errors="ignore").splitlines():
        m = re.match(r"- \*\*(.+?)\*\* → `([^`]+)/`[^:]*:\s*(.*)$", line)
        if not m:
            continue
        agency, folder, projects = m.group(1), m.group(2), [x.strip() for x in m.group(3).split(";")]
        for name, is_agency in [(agency, True)] + [(x, False) for x in projects]:
            n = norm(re.sub(r"\(.*?\)", "", name))
            if len(n) < 4 or n in GENERIC:
                continue
            if f" {n} " in np_ and (best is None or len(n) > best[0]):
                proj = None
                if not is_agency:
                    cand = CL / folder / (re.sub(r"[^a-z0-9]+", "-", n).strip("-") + ".md")
                    proj = cand if cand.exists() else None
                best = (len(n), CL / folder, proj)
    return (best[1], best[2]) if best else None


def sop_source(folder, proj):
    for f in [proj, folder / "client.md"]:
        if f and f.exists():
            for line in f.read_text(errors="ignore").splitlines():
                m = re.match(r"\s*-\s*Image/video source[^:]*:\s*(.+)$", line)
                if m and not m.group(1).strip().startswith("<"):
                    return re.sub(r"\*\*", "", m.group(1)).split(" (")[0].split(".")[0].strip(), f
    return None, None


CLIENT = find_client()
CLIENT_CTX = ""
SOP_SOURCE = None
if CLIENT:
    folder, proj = CLIENT
    SOP_SOURCE, src_file = sop_source(folder, proj)
    tasks = []
    for tf in sorted(folder.glob("task-*.md")):
        h = re.search(r"^#\s*(.+)$", tf.read_text(errors="ignore"), re.M)
        tasks.append(f"{tf.name} ({h.group(1).strip() if h else tf.stem})")
    if proj and proj.name.startswith("task-"):
        proj = None
    CLIENT_CTX = (f"Client detected: {folder.name} → follow its SOP in {folder / 'client.md'}"
                  + (f"; task SOPs available: {'; '.join(tasks)}. If the request matches one, follow it" if tasks else "")
                  + (f"; project notes {proj}" if proj else "") + " (precedence: prompt > project > task SOP > client). "
                  + (f"SOP image/video source: {SOP_SOURCE} (from {src_file.name}); use it without asking. " if SOP_SOURCE else ""))

# "Consistency Audit" is read-only: route it to the auditor, no image question.
AUDITS = [
    ("Consistency Audit", "consistency-auditor", r"consisten(cy|t)\s*(audit|check|review)|audit\s+(the\s+)?consisten|design\s+consistency"),
    ("Content Audit", "content-auditor", r"content\s*(audit|check|review)|copy\s*(audit|check|review)|proof\s*-?read"),
    ("Accessibility Audit", "accessibility-auditor", r"accessib\w*\s*(audit|check|review)|a11y|wcag|contrast\s+check"),
]
asked = [(n, ag) for n, ag, rx in AUDITS if re.search(rx, p)]
if asked:
    names = " + ".join(n for n, _ in asked)
    agents = ", ".join(f"figma-maintainer:{ag}" for _, ag in asked)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext":
        CLIENT_CTX + f"figma-maintainer: the user asked for {names}. Launch {agents} (read-only, report only, never changes the file; "
        "several audits can run in parallel) with the Figma URL from this prompt or from the conversation. "
        "If there is no Figma URL in either, ask for it. No image/video source question is needed. "
        "Show each audit's summary, high-severity rows and its 'Slack update' block."}}))
    sys.exit(0)

# "give me slack message" / token usage / cost report
SLACK = ""
if re.search(r"slack\s*(message|msg|update)|token(s)?\s*(usage|used|count|report)|how many tokens|cost\s*report|usage\s*report|how much did (this|it) cost", p):
    SLACK = ("figma-maintainer: the user wants a Slack message and/or usage. If they asked for a Slack message: write the Slack update for the work done "
             "(format: *Client — task* (date) / Updated: <link> / 3–6 short bullets / Questions for client), reusing the agents' Slack blocks. "
             "Then ALWAYS launch figma-maintainer:usage-reporter (session scope, or the task they named) and add its output as a separate "
             "'Usage (internal)' block after the Slack message. Never put token or cost numbers in the client-facing message.")

is_job = ("figma.com/design" in p or "figma.com/file" in p or "figma-maintainer" in p
          or "figma maintainer" in p)
if not is_job and CLIENT and not SLACK:
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CLIENT_CTX}}))
    sys.exit(0)
if not is_job:
    if SLACK:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CLIENT_CTX + SLACK}}))
    sys.exit(0)

SOURCES = [
    ("iStock", r"\bi-?stock\b"),
    ("Adobe Stock", r"\badobe\s*stock\b"),
    ("AI-generated", r"\bai[- ]?(generated|gen|images?|videos?)\b|\bgenerate (the )?(images?|videos?)\b"),
    ("client-provided (download from the shared link)", r"dropbox\.com|drive\.google\.com|1drv\.ms|onedrive\.live\.com|sharepoint\.com|wetransfer\.com|we\.tl/"),
    ("client-provided (local files the user tagged or saved in the project)", r"@\S+\.(jpe?g|png|webp|gif|heic|tiff?|svg|mp4|mov|webm|psd)\b|@\S+/|(^|\s)(~|\.{0,2})/\S+\.(jpe?g|png|webp|gif|heic|svg|mp4|mov)\b|\b(in|from) (the |my |our )?(project|local) (folder|directory)\b|\b(images?|photos?|videos?) (i|we) (added|saved|downloaded|put)\b"),
    ("client-provided", r"\bclient[- ]?(provided|supplied|images?|photos?|videos?|assets?)\b|\b(our|their) (own )?(photos?|images?)\b|\bimages? (are )?(attached|provided)\b"),
    ("existing assets in the file", r"\bexisting (images?|assets?|photos?)\b|\bimages? (already )?in the file\b"),
    ("no new images or video", r"\bno (new )?(images?|photos?|videos?|media)\b|\bwithout (new )?(images?|media)\b|\bkeep (the )?(current )?images?\b|\bleave (the )?images?\b|\bdon'?t (change|touch) (the )?images?\b"),
]
found = [name for name, rx in SOURCES if re.search(rx, p)]
if not found and SOP_SOURCE:
    found = [f"{SOP_SOURCE} (client SOP)"]
# Responsive jobs reuse the desktop's images, so they don't need the question.
if not found and re.search(r"\b(mobile|tablet|responsive)\b", p) and not re.search(r"\b(new|replace|replacing|swap|swapping|change|add|adding|different)\b(\s+\S+){0,3}?\s+(images?|photos?|pictures?|videos?|imagery)\b", p):
    found = ["existing assets in the file (responsive adaptation reuses the desktop's images)"]

if found:
    msg = (f"figma-maintainer image gate: the prompt names the image/video source ({', '.join(found)}). "
           "Pass it to the figma-maintainer agent verbatim as 'Image/video source: …' and proceed.")
else:
    msg = ("figma-maintainer image gate: this prompt doesn't say where images and video come from. "
           "Before doing anything else (no Figma reads, no agent launch, no edits), ask the user with AskUserQuestion: "
           "'Which image/video source for this job?' Options: Client-provided (they'll share files) / iStock / "
           "Adobe Stock / AI-generated. Notes can add 'Use existing assets in the file' or 'No new images or video'. "
           "If the project or client notes (~/.claude/figma-maintainer/clients/<client>/<project>.md and client.md; find them with grep -rl <fileKey>) list a preferred source, mark it '(Recommended)'. "
           "Do not proceed until the user answers. Then pass the answer to the figma-maintainer agent as 'Image/video source: …'.")
if SLACK:
    msg = msg + " ALSO, after the job: " + SLACK
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": CLIENT_CTX + msg}}))
