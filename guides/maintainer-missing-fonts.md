# Missing fonts

> On-demand guide for the figma-maintainer agent. Read it when the task needs it; the core rules in the agent still apply.

Rule from the user (2026-10-29; the same choice they made on 14 Oct, when they added Inter Tight and the job then used the real font):
- **Check fonts before any text edit.** In a read-only script, list every font the target text uses (`getStyledTextSegments(['fontName'])`, including text inside instances), and try `figma.loadFontAsync` for each family and style. Do this in step 2 (Inspect), before you duplicate anything or change text.
- **If a font can't load, stop before editing text and tell the user.** Don't substitute it. Don't type around it with annotations. Don't hand it to "a designer in the desktop app" on your own. Return exactly:
  `Font needed: <family> — <styles> (<n> text layers in <frames/sections>). Please install or activate it so Figma can use it (Adobe Fonts / the font file on this Mac, or a shared team font in Figma), then tell me and I'll continue with the real font.`
  You may finish parts of the task that don't touch that text (images, layout), but only when the task or plan clearly allows it. Say what's done and what waits for the font.
- **When the user says the font is installed:** run the load check again first. If it loads, do the text changes with the real font. If it still doesn't load, report that Figma's editing tools still can't see it, which usually means it must be a shared team font in Figma rather than only on the Mac, and stop again.
- **Annotations or a designer typing it in the desktop app** are only used when the user chooses that.
