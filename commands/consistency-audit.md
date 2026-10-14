---
description: Read-only Consistency Audit — homepage vs inner pages vs design system; report only, never changes the file
argument-hint: <figma URL of the file or of the page being worked on> [all pages | this page | homepage only]
---

Use the consistency-auditor agent (figma-maintainer:consistency-auditor) for:

$ARGUMENTS

If no URL is given, use the Figma file and page from the current conversation. If there isn't one, ask me for the link before doing anything.

The audit is read-only: nothing in Figma changes. When it's done, show me the report summary and the high-severity rows, and tell me where the full report file is. Then ask whether figma-maintainer should apply any of the corrections, and wait for my answer.
