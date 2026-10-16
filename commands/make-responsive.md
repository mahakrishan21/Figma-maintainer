---
disable-model-invocation: true
description: Create or update the mobile (390) and tablet (768) versions of a desktop Figma frame
argument-hint: <desktop frame URL> [mobile | tablet | both] [extra instructions]
---

Use the figma-maintainer agent (figma-maintainer:figma-maintainer) in responsive mode for this request:

$ARGUMENTS

Add these lines to its task:
- "Breakpoints: <mobile / tablet / both>". Use exactly what I named; if I named nothing, use both (running this command is the explicit request).
- "Image/video source: existing assets in the file". Use a different source only if I asked for new images, and then ask me which source first.

The agent follows ~/.claude/figma-maintainer/guides/responsive-from-desktop.md. When it's done, pass me its report in full: the frames with links, the pattern used for each section, anything removed or changed, and flags for review.

Store every file this produces in the project folder from `python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>"` (person › agency › project; created only if missing).
