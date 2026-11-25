---
disable-model-invocation: true
description: Design a new desktop inner page from the homepage, in the homepage's exact style (header, footer, grid, type, colours, components)
argument-hint: <homepage frame URL> <page name> [— copy: <doc link or text>] [— sections: …] [— images: …]
---

Use the figma-maintainer agent (figma-maintainer:figma-maintainer) in inner-page mode for this request. Use the default model (no `model` override).

$ARGUMENTS

Add these lines to its task:
- "Inner page mode: design a new desktop inner page from the homepage in the link. The homepage is the style source and stays read-only."
- "Page: <the page name and purpose I gave>".
- "Copy source: <the doc link or pasted text I gave, or 'none: write placeholder copy and mark it'>".
- "Image/video source: …". Use the source I named or the client SOP's; if neither, ask me first (Client-provided / iStock / Adobe Stock / AI-generated / existing assets in the file / no new images).
- "Sections: …" only if I listed sections or named a reference page.

If the link has no node-id, ask me for the homepage frame link (right-click the frame → Copy link) before launching.

The agent follows ~/.claude/figma-maintainer/guides/inner-page-from-homepage.md. When it's done, pass me its report in full: the new frame with its link, the page structure table (each section and where it came from), the placeholders, and any off-system values or new patterns.

Store every file this produces in the project folder from `python3 -I ~/.claude/figma-maintainer/scripts/workdir.py --url "<figma url>"` (person › agency › project; created only if missing).
