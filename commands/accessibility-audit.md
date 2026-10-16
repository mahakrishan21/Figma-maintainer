---
disable-model-invocation: true
description: Read-only Accessibility Audit of Figma pages — report only, never changes the file
argument-hint: <figma URL of the file or page> [all pages | this page | homepage only]
---

Use the accessibility-auditor agent (figma-maintainer:accessibility-auditor) for:

$ARGUMENTS

If no URL is given, use the Figma file and page from the current conversation. If there isn't one, ask me for the link before doing anything.

The audit is read-only. When it's done, show me the summary, the high-severity rows, where the report file is, and the "Slack update" block. Then ask whether figma-maintainer should apply any corrections, and wait for my answer.

Store every file this produces in the project folder from `python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>"` (person › agency › project; created only if missing).
