---
description: Compare two Figma frames (e.g. V2 vs V3) and list every change — read-only
argument-hint: <figma URL of older frame> <figma URL of newer frame>
---

Compare these two Figma frames and list every difference, without changing anything: $ARGUMENTS

1. Get both frames' text with `python3 -I ~/.claude/figma-maintainer/scripts/figma_content.py --file <key> --frames <oldId>,<newId> --out <scratch dir>/compare`, and diff the copy dumps by section.
2. Check the visual and structural changes with `python3 -I ~/.claude/figma-maintainer/scripts/figma_audit.py --file <key> --home <oldId> --frames <newId> --out <scratch dir>/compare-audit` (sections, header and footer, colours, type, components), plus `get_screenshot` of any section that changed.
3. Report:
   - **Copy changes:** a table with columns Section | Before | After.
   - **Added or removed:** sections, fields, buttons, images.
   - **Visual or layout changes:** what changed and where.
   - **Unchanged:** one line.

Finish with a Slack-ready "What changed" block of 3–8 bullets for the developer or the client.
