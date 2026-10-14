---
description: Check a Figma page against a client brief, copy doc or confirmed list — matches vs mismatches, read-only
argument-hint: <figma URL> (paste or attach the brief / confirmed fields / copy)
---

Check this Figma page against the client information in my message (pasted text or attached document): $ARGUMENTS

Don't change anything in Figma.
1. Read the page's text with `python3 -I ~/.claude/figma-maintainer/scripts/figma_content.py --url "<url>" --out <scratch dir>/brief-check` (the copy dump lists every text layer, with its role and node ID). If the frame is a whole page, include its Thank You or related frames when the brief mentions them.
2. Compare with the brief item by item: offer and amounts, rules and conditions, copy (exact wording when the brief gives copy), form fields, labels, options and order, buttons and CTA labels, the flow (what the button does, where it goes), and pages the brief mentions.
3. Answer in this format:
   - **Matches:** short bullets.
   - **Doesn't match:** a table with columns Brief says | In Figma now | Fix.
   - **Also worth fixing or asking:** leftovers, contradictions, missing pages or states.
   - Ask whether figma-maintainer should apply the fixes. Mention the image source (usually "no new images" for fixes like these) and whether tablet or mobile frames exist and need the same fix.
