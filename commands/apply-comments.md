---
disable-model-invocation: true
description: Read the Figma comments on a frame and apply them (everything except image editing)
argument-hint: <figma URL with node-id> [extra instructions]
---

First, unless the request below already says where images and video come from, ask me with AskUserQuestion: "Which image/video source for this job?" Options: Client-provided / iStock / Adobe Stock / AI-generated (notes can add existing assets or no new images). Mark the preferred source from the project or client notes (~/.claude/figma-maintainer/clients/<client>/) as "(Recommended)". Do nothing else until I answer.

Next, check which comments are open: run `python3 -I ~/.claude/figma-maintainer/scripts/figma_comments.py --url "<figma url>" --out <project folder>/comments` (read-only). **If it reports older open comments** besides the current round, ask me with AskUserQuestion: "Which comments should I apply?". Use these options, with the real counts and dates:
- "Latest round only: <N> from <dates> (Recommended)"
- "Latest + older since <date>"
- "All open comments (<total>)"

If I don't choose, or there are no older comments, use the latest round only.

Then use the figma-maintainer agent (figma-maintainer:figma-maintainer) in client comments mode for this request, adding the line "Image/video source: <my answer>" and the line "Comments to apply: latest round only" (or `--since <date>` / `--round all`, as I chose):

$ARGUMENTS

It reads the comments pinned to that frame (the whole file if the URL has no node-id), the latest round by default, applies the copy and layout changes, annotates the image-editing requests instead of doing them, and reports every comment by number.

**QA (automatic):** when it's done, save any job files it returned as text, then launch **figma-maintainer:qa-checker** with `Job folder: <its job folder>` and `File: <fileKey>` (add `Level: light` when the round was at most 3 plain text edits in one frame), and save the result as `qa.md`. There's no approved plan on this path, so QA checks against the comments only; say so in its report. On FAIL with AUTO-FIX items, send only those items back to figma-maintainer once as a "QA fix round" (same job folder and output frames, no new duplicate), apply QA's message fixes, and run qa-checker again. If it still fails, or has USER items, hold the client message ("HELD: not ready to send") and ask me: send another fix round / I'll fix it in Figma / accept with an override.

Then pass me the report in full, with the QA verdict at the top: done, not done, needs a human check, approvals and decisions needed.

Store every file this produces in the project folder from `python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>"` (person › agency › project; created only if missing).
