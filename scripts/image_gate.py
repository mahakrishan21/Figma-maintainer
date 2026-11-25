#!/usr/bin/env python3
"""UserPromptSubmit hook: before any figma-maintainer job, make sure the image/video
source is known. If the prompt names it, pass it on; if not, tell Claude to ask first
and not start until the user answers. Silent for prompts that aren't Figma jobs."""
import json, re, sys

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_scope import prompt_is_fm  # noqa: E402

try:
    HOOK = json.load(sys.stdin)
except Exception:
    sys.exit(0)
prompt = HOOK.get("prompt", "") or ""
# Background and system messages (agent hand-backs, task notifications) aren't user prompts: stay silent
if re.match(r"\s*(another claude session sent a message|<agent-message|\[subagent hand-back\]|<task-notification>|\[SYSTEM NOTIFICATION)", prompt, re.I) \
        or re.search(r"<agent-message|<task-notification>|\[SYSTEM NOTIFICATION", prompt[:400]):
    sys.exit(0)
# Only figma-maintainer work. Website builds, other plugins and general chat get nothing from this hook.
if not prompt_is_fm(prompt, HOOK.get("transcript_path", "")):
    sys.exit(0)
import qa_gate  # noqa: E402
SESSION = qa_gate.session_of(HOOK)
CHECK_CMD = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "commands", "check-figma.md")


def account_note():
    """Figma work starts only after the user confirmed the connected Figma account in this conversation."""
    if os.environ.get("FIGMA_MAINTAINER_ACCOUNT_CHECK") == "off":
        return ""
    try:
        import figma_account
        if figma_account.confirmed(SESSION):
            return ""
    except Exception:
        pass
    return ("FIGMA ACCOUNT CHECK FIRST: this conversation hasn't confirmed which Figma account is connected. Before any Figma call or "
            f"agent launch, read {CHECK_CMD} and follow it (session id {SESSION}): show the connected account's name and email and ask "
            "the user to confirm. Continue with the request below only after they say yes (Figma edits are blocked until then). ")


def emit(ctx, account=False):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit",
                                             "additionalContext": (account_note() if account else "") + ctx}}))


if re.match(r"\s*/figma-maintainer:check-figma\b", prompt):
    emit(f"Session id for figma_account.py: {SESSION}.")
    sys.exit(0)

# "skip QA": the user waives the QA check for the pending job(s) in this session (the Stop-hook gate is cleared)
if re.search(r"\b(skip|no|without|don'?t (run|do))\s+(the\s+)?qa\b", prompt, re.I):
    import qa_gate
    marks = qa_gate.clear(qa_gate.session_of(HOOK))
    if len(prompt) < 120:
        jobs = "; ".join(m.get("job") or ", ".join(m["files"]) for m in marks) or "no job was waiting for QA"
        emit(f"figma-maintainer: the user chose to skip the QA check ({jobs}). Don't run qa-checker for it; write 'QA skipped by the user' "
            "in the report and keep the client message marked as not QA-checked.")
        sys.exit(0)

# These slash commands carry their own instructions (no image question for a read-only QA run)
if re.match(r"\s*/figma-maintainer:(client-comment|qa)\b", prompt):
    if account_note():
        emit("", account=True)
    sys.exit(0)
p = prompt.lower()

# ---- client SOP lookup: agency/project name or Figma file key -> clients/<agency>/client.md (+ project.md)
from pathlib import Path
CL = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer") / "clients"
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
        m = re.match(r"- \*\*(.+?)\*\* → `([^`]+)/`(?:[^:\n]*:\s*(.*)|.*)$", line)
        if not m:
            continue
        agency, folder, projects = m.group(1), m.group(2), [x.strip() for x in (m.group(3) or "").split(";") if x.strip()]
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


STOP = {"use", "figma", "maintainer", "figma maintainer", "page", "homepage", "home", "the", "and", "for", "with", "make", "change", "design",
        "update", "client", "frame", "section", "link", "images", "image", "mobile", "tablet", "desktop", "copy", "apply", "comments"}
# Everyday and generic business words: a typo match must rest on a distinctive word of the name, never on these
COMMON = {"a", "an", "the", "and", "or", "of", "in", "on", "at", "to", "for", "with", "from", "by", "is", "it", "its", "this", "that",
          "these", "those", "my", "our", "your", "their", "we", "you", "they", "i", "me", "us", "be", "are", "was", "as", "so", "not",
          "no", "yes", "all", "any", "many", "some", "more", "most", "new", "old", "up", "out", "into", "over", "can", "will", "just",
          "also", "then", "than", "only", "each", "every", "page", "pages", "site", "website", "web", "design", "designs", "project",
          "projects", "group", "studio", "agency", "media", "digital", "marketing", "solutions", "creative", "co", "inc", "llc", "ltd",
          "company", "services", "service", "plugin", "agent", "comment", "comments", "action", "actions", "file", "files", "home"}


def suggest_clients(limit=4):
    """Closest agency/project names to words in the prompt (typo tolerance). [(score, label, folder)]
    Compares word for word with the same number of words as the name; a match must rest on a distinctive
    (non-COMMON) word of the name, so phrases like "an action" or "many projects" never suggest a client."""
    import difflib
    idx = CL / "_index.md"
    if not idx.exists():
        return []

    def ratio(a, b):
        return difflib.SequenceMatcher(None, a, b).ratio()
    text = re.sub(r"https?://\S+", " ", prompt)
    text = re.sub(r"(?i)use\s+figma[\s_-]*maintainer\s*:?", " ", text)
    toks = [t for t in norm(text).split() if t][:600]
    grams = {}
    for n in range(1, 5):
        grams[n] = {tuple(toks[i:i + n]) for i in range(len(toks) - n + 1)}
        grams[n] = {g for g in grams[n] if not ({"figma", "maintainer"} & set(g)) and not all(t in COMMON for t in g)}
    best = {}
    for line in idx.read_text(errors="ignore").splitlines():
        m = re.match(r"- \*\*(.+?)\*\* → `([^`]+)/`(?:[^:\n]*:\s*(.*)|.*)$", line)
        if not m:
            continue
        agency, folder = m.group(1), m.group(2)
        projects = [x.strip() for x in (m.group(3) or "").split(";") if x.strip()]
        for name, label in [(agency, agency)] + [(x, f"{x} ({agency})") for x in projects]:
            nn = norm(re.sub(r"\(.*?\)", "", name))
            nt = tuple(nn.split())
            if len(nn) < 4 or nn in GENERIC or not 1 <= len(nt) <= 4:
                continue
            for g in grams[len(nt)]:
                if len(nt) == 1:
                    if g[0] in STOP or len(g[0]) < 4 or abs(len(g[0]) - len(nn)) > 3:
                        continue
                    r = ratio(nn, g[0])
                    if r < (0.9 if len(nn) <= 5 else 0.85):
                        continue
                else:
                    if not all(x == y or (len(x) > 2 and ratio(x, y) >= 0.75) for x, y in zip(nt, g)):
                        continue
                    if not any(x not in COMMON and ratio(x, y) >= 0.8 for x, y in zip(nt, g)):
                        continue
                    r = ratio(nn, " ".join(g))
                    if r < 0.8:
                        continue
                if r > best.get(folder + label, (0,))[0]:
                    best[folder + label] = (r, label, folder)
    out, seen = [], set()
    for r, label, folder in sorted(best.values(), reverse=True):
        if folder in seen:  # one option per client
            continue
        seen.add(folder); out.append((r, label, folder))
    return out[:limit]


def sop_line(folder, proj, label_rx):
    for f in [proj, folder / "client.md"]:
        if f and f.exists():
            for line in f.read_text(errors="ignore").splitlines():
                m = re.match(r"\s*-\s*" + label_rx + r"[^:]*:\s*(.+)$", line)
                if m:
                    return m.group(1).strip()
    return None


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
    conflict = sop_line(folder, proj, r"⚠️\s*SOP sheet")
    if conflict:
        SOP_SOURCE = None  # conflicting SOP entries: ask instead of auto-applying
    delivery = sop_line(folder, proj, r"Delivery tool \(Figma\)") or ""
    if "client" in delivery.lower() and "e2m" not in delivery.lower():
        deliv_ctx = ("DELIVERY REMINDER: this client's delivery tool is THEIR OWN Figma account (" + delivery + "). Tell the user at the start of the job "
                     "and again in the final report and Slack update: \"Deliver this in the client's Figma account, not E2M's.\" ")
    elif delivery and not delivery.startswith("<"):
        deliv_ctx = "Delivery tool: " + delivery + " (mention it in the final report). "
    else:
        deliv_ctx = ("Delivery tool isn't set in this client's SOP: in the final report, ask once whether delivery is in E2M's Figma or the client's "
                     "Figma account, and save the answer as a rule in this client's SOP. ")
    CLIENT_CTX = (f"Client detected: {folder.name} → follow its SOP in {folder / 'client.md'} (agents load it as a digest with "
                  f"scripts/job_context.py; don't cat the SOP files)"
                  + (f"; task SOPs available: {'; '.join(tasks)}. If the request matches one, follow it" if tasks else "")
                  + (f"; project notes {proj}" if proj else "") + " (precedence: prompt > project > task SOP > client). "
                  + (f"IMAGE PREFERENCE REMINDER: the SOP sets the image/video source to {SOP_SOURCE} (from {src_file.name}). Use it without asking, but tell the user "
                     f"in one line at the start of the job (\"{folder.name} image preference: {SOP_SOURCE}\") and repeat it in the report. " if SOP_SOURCE else "")
                  + (f"IMAGE SOURCE CONFLICT in the SOP: {conflict} Ask the user which source applies before starting, then save the answer as a rule in this client's SOP. " if conflict else "")
                  + deliv_ctx)

QA_NOTE = (" AFTER the figma-maintainer agent finishes a job that changed Figma: launch figma-maintainer:qa-checker with the job folder "
           "and file key (add 'Level: light' when the job was at most 3 plain text edits in one frame) BEFORE showing the client message. On FAIL with AUTO-FIX items, send only those items back to figma-maintainer "
           "once as a 'QA fix round' (same job folder and output frames, no new duplicate), then run qa-checker again; if it still "
           "fails, hold the client message and ask the user (send another fix round / I'll fix it / accept with an override).")
SID = str(HOOK.get("session_id") or "")
if re.fullmatch(r"[A-Za-z0-9-]{8,64}", SID):  # usage_report.py finds this conversation with it, whatever the shell's folder
    QA_NOTE += f" Session id for usage_report.py --session: {SID}."

# "I got a client comment": the client-comment workflow finds, analyses and plans it before any job starts.
# The phrase must open the request (first ~300 characters) and not describe a feature ("client comment agent"),
# so a long spec or a discussion about the plugin doesn't start the workflow.
# "check" isn't a trigger ("cross check the work with the client comments" is a QA request, not a new comment).
CC_RX = (r"\b(got|get|have|has|received|new|there'?s|there is|any|another)\b[^.\n?]{0,40}?\bclient('?s)?\s+(figma\s+)?comments?\b"
         r"(?!\s*(automation|agent|feature|workflow|mode|command|script|hook|plugin|inbox|discovery|with|against|vs|versus|qa)\b)"
         r"|\bclient\s+(has\s+)?(left|added|posted|commented|replied)\b")
cc_text = re.sub(r"^\s*(use\s+)?figma[\s_-]*maintainer\s*[:,]?\s*", "", p)
cc = re.search(CC_RX, cc_text)
# "I don't have any client comments yet" / "no new client comments": not a new comment
if cc and re.search(r"\b(don'?t|do not|didn'?t|haven'?t|no|not|never|without)\b", cc_text[max(0, cc.start() - 12):cc.end()]):
    cc = None
if cc and cc.start() < 300:
    cmd = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "commands", "client-comment.md")
    emit(CLIENT_CTX +
        f"figma-maintainer client comment: the user says they have a new client comment. Read {cmd} and follow it step by step "
        "(the arguments are this prompt): find the comment with comment_inbox.py (Figma's Mac notifications; a Figma link or file name "
        "in the prompt takes priority), analyse it with the read-only figma-maintainer:client-comments agent, show the plan and ask the "
        "user to approve it, and only then hand it to figma-maintainer:figma-maintainer. Don't ask the image/video question now: "
        "it's settled after the analysis, from the client SOP or by asking. No Figma edits before the user approves the plan." + QA_NOTE, account=True)
    sys.exit(0)

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
    emit(CLIENT_CTX + f"figma-maintainer: the user asked for {names}. Launch {agents} (read-only, report only, never changes the file; "
        "several audits can run in parallel) with the Figma URL from this prompt or from the conversation. "
        "If there is no Figma URL in either, ask for it. No image/video source question is needed. "
        "Show each audit's summary, high-severity rows and its 'Slack update' block.", account=True)
    sys.exit(0)

# "give me slack message" / token usage / cost report
SLACK = ""
if re.search(r"slack\s*(message|msg|update)|token(s)?\s*(usage|used|count|report)|how many tokens|cost\s*report|usage\s*report|how much did (this|it) cost", p):
    SLACK = ("figma-maintainer: the user wants a Slack message and/or usage. If they asked for a Slack message: write the Slack update for the work done "
             "(format: *Client — task* (date) / Updated: <link> / 3–6 short bullets / Questions for client), reusing the agents' Slack blocks. "
             "Then ALWAYS launch figma-maintainer:usage-reporter (session scope, or the task they named) and add its output as a separate "
             "'Usage (internal)' block after the Slack message. Never put token or cost numbers in the client-facing message.")

# A job = a Figma link, a job command, or the plugin named as the one to use ("Use figma-maintainer: …", "figma-maintainer, …").
# A bare mention of the plugin (e.g. while discussing its development) is not a job.
is_job = bool(re.search(r"figma\.com/(design|file)/", p) or re.search(r"/figma-maintainer:(apply-comments|make-responsive|make-inner-page)\b", p)
              or re.search(r"\buse\s+(the\s+)?figma[\s_-]*maintainer\b|(^|\n)\s*figma[\s_-]*maintainer\s*[:,]", p))
if not is_job and CLIENT and not SLACK:
    emit(CLIENT_CTX)
    sys.exit(0)
if not is_job:
    if SLACK:
        emit(CLIENT_CTX + SLACK)
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
if not CLIENT:
    sugg = suggest_clients()
    if sugg:
        opts = "; ".join(f"\"{lab}\" → clients/{fol}/client.md" for _, lab, fol in sugg)
        msg = ("figma-maintainer client check: the prompt doesn't name a known client exactly. Closest matches: " + opts + ". "
               "Before anything else (no Figma reads, no agent launch), ask the user with AskUserQuestion: 'Which client is this for?', "
               "with these names as options (best match first, marked '(Recommended)' only if it is clearly the closest), plus 'None of these'. ")
    else:
        msg = ("figma-maintainer client check: the prompt doesn't name a client. Before anything else (no Figma reads, no agent launch), "
               "ask the user which client (agency) and project this is for; check clients/_index.md for the exact name. ")
    msg += ("After the user confirms the client, read that client's client.md: §6 'Image/video source' → if set, use it and remind the user "
            "in one line (e.g. 'Lasso up image preference: Adobe Stock'); if not set, ask the image/video source question "
            "(Client-provided / iStock / Adobe Stock / other stock such as Getty, Shutterstock, Depositphotos, Envato / AI-generated). "
            "Also apply §3 'Delivery tool (Figma)' (remind if it's the client's own Figma account). Pass 'Client: <name>' and "
            "'Image/video source: …' to the figma-maintainer agent. If the source is iStock, first run "
            "python3 -I ~/.claude/figma-maintainer/scripts/istock_fetch.py --check and, if it prints 'iStock setup needed', tell the user the reason "
            "and the fix and ask whether to fix it now, use another source, or continue without iStock." + QA_NOTE)
    if SLACK:
        msg += " ALSO, after the job: " + SLACK
    emit(msg, account=True)
    sys.exit(0)

found = [name for name, rx in SOURCES if re.search(rx, p)]
if not found and SOP_SOURCE:
    found = [f"{SOP_SOURCE} (client SOP)"]
# Responsive jobs reuse the desktop's images, so they don't need the question.
if not found and re.search(r"\b(mobile|tablet|responsive)\b", p) and not re.search(r"\b(new|replace|replacing|swap|swapping|change|add|adding|different)\b(\s+\S+){0,3}?\s+(images?|photos?|pictures?|videos?|imagery)\b", p):
    found = ["existing assets in the file (responsive adaptation reuses the desktop's images)"]

ISTOCK_CHECK = "python3 -I ~/.claude/figma-maintainer/scripts/istock_fetch.py --check"
ISTOCK_ASK = ("ask the user with AskUserQuestion: 'iStock isn't working on this Mac: <reason>. What now?' Options: "
              "'Fix it now (Recommended)': do the fix with them (run commands only with their OK), then run " + ISTOCK_CHECK + " again until it says READY; "
              "'Use another source'; 'Continue without iStock' (the agent leaves image placeholders and lists iStock search terms per slot).")


def istock_note():
    """iStock is the source: check it works on this Mac (a pass is cached for a day) so a failure is fixed before the job."""
    try:
        import istock_fetch
        r = istock_fetch.cached_check()
    except Exception as e:
        r = {"ok": False, "reason": f"the iStock script couldn't run ({e})"[:200], "fix": "Update the plugin: /figma-maintainer:about, then /reload-plugins."}
    if r.get("ok"):
        return ""
    return (f" iStock CHECK FAILED on this Mac: {r.get('reason')}. Fix: {r.get('fix')} Before launching the agent, " + ISTOCK_ASK)


if found:
    msg = (f"figma-maintainer image gate: the prompt names the image/video source ({', '.join(found)}). "
           "Pass it to the figma-maintainer agent verbatim as 'Image/video source: …' and proceed.")
    if any(f.lower().startswith("istock") for f in found):
        msg += istock_note()
else:
    msg = ("figma-maintainer image gate: this prompt doesn't say where images and video come from. "
           "Before doing anything else (no Figma reads, no agent launch, no edits), ask the user with AskUserQuestion: "
           "'Which image/video source for this job?' Options: Client-provided (they'll share files) / iStock / "
           "Adobe Stock / AI-generated. Notes can add 'Use existing assets in the file' or 'No new images or video'. "
           "If the project or client notes (~/.claude/figma-maintainer/clients/<client>/<project>.md and client.md; find them with grep -rl <fileKey>) list a preferred source, mark it '(Recommended)'. "
           "Do not proceed until the user answers. Then pass the answer to the figma-maintainer agent as 'Image/video source: …'. "
           "If they pick iStock, first run " + ISTOCK_CHECK + "; if it prints 'iStock setup needed', " + ISTOCK_ASK)
msg += QA_NOTE
if SLACK:
    msg = msg + " ALSO, after the job: " + SLACK
emit(CLIENT_CTX + msg, account=True)
