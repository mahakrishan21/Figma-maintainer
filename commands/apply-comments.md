---
disable-model-invocation: true
description: Read the Figma comments on a frame and apply them (everything except image editing)
argument-hint: <figma URL with node-id> [fast] [extra instructions]
model: sonnet
---

Apply the client's Figma comments for this request, and keep it fast: put independent steps in one tool call, keep your own messages to a line or two, and never re-type text that's already saved in a file.

My request: $ARGUMENTS

**Fast run (only when my request contains the word `fast`).** Speed comes first for this run: launch the maker with `model: sonnet` and `effort: medium` whatever the round holds, and QA with `effort: medium`. Tell me in your first line that this is a fast run, and say so again in the report. Don't pass the word on to the maker as an instruction. Nothing else changes: the copy, the snapshots, the QA check and the hold rule all stay.

**1. Setup (one Bash call, read-only).** Get the project folder and the open comments together:
`P=$(python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>") && echo "$P" && python3 -I ~/.claude/figma-maintainer/scripts/figma_comments.py --url "<figma url>" --out "$P/comments"`
`$P` is the project folder (person › agency › project; created only if missing). Store every file this job produces there. If my request has no Figma URL, ask me for it first.

**2. Image/video source.** It must be settled before the agent starts:
- my request names it, or the client check says the client SOP sets it ("IMAGE PREFERENCE REMINDER"): use it without asking, and tell me in one line;
- otherwise ask me with AskUserQuestion: "Which image/video source for this job?" Options: Client-provided / iStock / Adobe Stock / AI-generated (notes can add existing assets or no new images). Mark the preferred source from the project or client notes (~/.claude/figma-maintainer/clients/<client>/) as "(Recommended)", and don't launch the agent until I answer.

**3. Which comments.** **If the script reports older open comments** besides the current round, ask me with AskUserQuestion: "Which comments should I apply?". Use these options, with the real counts and dates:
- "Latest round only: <N> from <dates> (Recommended)"
- "Latest + older since <date>"
- "All open comments (<total>)"

If I don't choose, or there are no older comments, use the latest round only.

**4. Launch the maker** (figma-maintainer:figma-maintainer, client comments mode) with a short brief. It reads the SOP, the project notes and the saved comments itself, so don't summarise them:
```
Client comments mode.
Figma URL: <url>
Client: <agency> › <project>
Image/video source: <source>
Comments to apply: latest round only        (or `--since <date>` / `--round all`, as I chose)
Project folder: <P> (the comments are already saved in <P>/comments)
<my extra instructions, verbatim, if any>
```
**Model by job weight** (the Agent tool's `model`; a fast run overrides this): pass `sonnet` when every comment in the round is a plain text edit (copy, numbers, labels, punctuation) with nothing to add, remove, move, restyle or swap. Otherwise pass no model: the agent's own (Opus) handles layout, new elements and images.

It reads the comments pinned to that frame (the whole file if the URL has no node-id), the latest round by default, applies the copy and layout changes, annotates the image-editing requests instead of doing them, and reports every comment by number.

**5. QA (automatic).** As soon as the maker returns, launch **figma-maintainer:qa-checker** with `Job folder: <its job folder>` and `File: <fileKey>` (add `Level: light` when the round was at most 3 plain text edits in one frame). Don't save or re-type anything first: the plugin saves the maker's reply as `report.md` and QA's reply as `qa.md` in the job folder by itself. Only if one is missing after QA returns (one `ls`), save it yourself. There's no approved plan on this path, so QA checks against the comments only; say so in its report. On FAIL with AUTO-FIX items, send only those items back to figma-maintainer once as a "QA fix round" (same job folder and output frames, no new duplicate), apply QA's message fixes, and run qa-checker again. If it still fails, or has USER items, hold the client message ("HELD: not ready to send") and ask me: send another fix round / I'll fix it in Figma / accept with an override. Record my choice at the end of `qa.md`.

**6. Report to me, short.** The QA verdict at the top; then one line per comment (done, not done, waiting on the client), needs a human check, approvals and decisions needed, and the output link; then the Slack update and the client message as the maker wrote them. Leave out layer ids and anything else that's in `report.md` and `qa.md`, and link those two files instead. End with the usage block: run `python3 -I ~/.claude/figma-maintainer/scripts/usage_report.py --session <session id from the client check> --slack` yourself (a script, not an agent) and show its output as "Usage (internal)".
