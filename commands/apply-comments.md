---
disable-model-invocation: true
description: Read the Figma comments on a frame and apply them (everything except image editing)
argument-hint: <figma URL with node-id> [extra instructions]
---

First, unless the request below already says where images and video come from, ask me with AskUserQuestion: "Which image/video source for this job?" Options: Client-provided / iStock / Adobe Stock / AI-generated (notes can add existing assets or no new images). Mark the preferred source from the project or client notes (~/.claude/figma-maintainer/clients/<client>/) as "(Recommended)". Do nothing else until I answer.

Then use the figma-maintainer agent (figma-maintainer:figma-maintainer) in client comments mode for this request, adding the line "Image/video source: <my answer>":

$ARGUMENTS

It reads every unresolved comment pinned to that frame (the whole file if the URL has no node-id), applies the copy and layout changes, annotates the image-editing requests instead of doing them, and reports every comment by number. When it's done, pass its report to me in full: done, not done, approvals and decisions needed.
