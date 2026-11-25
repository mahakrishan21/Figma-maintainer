---
disable-model-invocation: true
name: inner-page-from-homepage
description: Design a new desktop inner page (About, Services, Contact, a service detail page and so on) in Figma from an approved homepage, using the homepage's exact style system (header, footer, grid, type, colours, buttons, components, image treatment) and the team's page-design standard. Use only via /figma-maintainer:make-inner-page or when explicitly asked to design an inner page from a homepage.
---

# Inner page from the homepage

> **Generic, reusable task action ("Design an inner page from the homepage").** First check the client's folder for its own configuration (`clients/<agency>/task-inner-pages.md`). **If one exists, it overrides the defaults below for that client only.** If none exists, use these defaults together with the client's SOP and design system. Never use another client's configuration.

The homepage is the source of truth for the style. The new page must look like it was designed by the same designer on the same day: same header and footer, same grid, same type, same colours, same buttons and cards, same image treatment, same rhythm. You design the **structure and content flow** of the new page; you never invent a new visual language.

## Scope and inputs
- **Style source:** the homepage frame in the link (node-id). It is **read-only**: never edit, move or rename it. Run an original guard (snapshot before, compare at the end).
- **What you create:** exactly one new desktop frame, next to the homepage. Nothing else on the page changes.
- **Inputs from the task:**
  - `Page:` the page name and purpose (for example "About — company story, team, values").
  - `Copy source:` a Google Doc link (get it with `fetch_doc.py`), pasted text, or "none".
  - `Image/video source:` settled before the job (the image gate). iStock gives watermarked Essentials placeholders.
  - Optional: `Sections:` a section list, a sitemap, or a reference page ("like the Services page"). A given section list wins over your own plan.
- **Desktop only.** Tablet and mobile only when asked (then follow `responsive-from-desktop.md` afterwards).

## Step 1: the style map (read-only)
In one read-only `use_figma` script on the homepage, collect only what you need and write it to `<job folder>/style-map.md`:
1. **Frame:** width, background, Auto Layout or not.
2. **Grid:** container width, side margins, columns and gutter (from layout grids, or measured from the section contents).
3. **Rhythm:** each section's name, vertical padding and background, in order. Note the background alternation pattern (for example white → light grey → white → brand dark).
4. **Type:** the text styles actually used, per level: eyebrow, H1, H2, H3, H4, body large, body, caption, button, nav. Note the family, size and line height of each.
5. **Colour:** the colour styles and variables actually used (text, backgrounds, accents, borders).
6. **Components:** the header and footer (node IDs; instance or frame), button and link components with their variants, cards, icons, badges, form fields.
7. **Shape and effects:** corner radii, shadows, strokes, overlays on images.
8. **Images:** aspect ratios per usage (hero, card, split section), corner radius, overlay or gradient, full-bleed or contained.
9. **Section catalogue:** every homepage section as a reusable pattern, with its id: hero, split text + image, 3-card grid, stats band, testimonials, logos, CTA band, FAQ, form and so on.

Everything on the new page comes from this map. If the file has a library or local components for a pattern, they come first.

## Step 2: plan the page
Write the plan to `<job folder>/page-plan.md` before building: one line per section with its purpose, its copy (or "placeholder"), and its source (component / homepage section `<id>` cloned / composed).

Standard structure:
1. **Header:** the homepage header, as an instance (or an exact clone if it's a plain frame). If a nav variant or state exists, mark this page's item as active.
2. **Inner hero:** shorter than the homepage hero (about 50–65% of its height), built from the same parts: one H1 (the page title), a short intro line, the homepage's primary or secondary button if the page has a clear action, an optional breadcrumb in the caption style, and an image treated exactly like the homepage hero (or the homepage's hero background style without an image). Never a second H1 on the page.
3. **Content sections:** follow the copy's story (what → why → how → proof → action). Map each block of copy to the best-fitting pattern from the section catalogue.
4. **CTA band:** the homepage's CTA band, cloned, with this page's call to action.
5. **Footer:** the homepage footer, as an instance or exact clone. Never rebuilt.

Senior-designer rules:
- **Hierarchy:** H1 once, H2 per section, H3 for items. Use the homepage's eyebrow style above H2s only if the homepage does.
- **Rhythm:** keep the homepage's background alternation and section padding. Never put two sections with the same background and the same layout next to each other.
- **Variety:** don't repeat the same layout twice in a row; alternate split-section image sides the way the homepage does.
- **Actions:** at most one primary button per section; secondary actions use the homepage's secondary or link style.
- **Density:** match the homepage's text widths (long text no wider than the homepage's body measure) and its card counts per row.
- **Content-led:** the number of sections comes from the content. Don't pad with filler sections; don't drop copy.

## Step 3: section sources, in this order
1. The file's components or library (instances, with overrides; swap variants rather than detaching).
2. **Clone a matching homepage section** and replace its content. This is the default for most sections: it keeps spacing, type and effects exact.
3. **Compose a new section** only when no homepage pattern fits, and only from style-map values: the same container, paddings, text styles, colour styles, radii, shadows and components.

Never introduce a new font, size, colour, radius, shadow, spacing value or icon style. If the content truly needs something the homepage doesn't have (for example a data table), build it from the closest existing styles and list it under "New patterns" in the report.

## Step 4: content and images
- **Copy given:** use it word for word, in its order. Headings and labels exactly as written. If copy doesn't fit a pattern, change the pattern, not the copy.
- **No copy:** write realistic, specific placeholder copy from the page purpose and the client's business (never lorem ipsum, never invented facts like figures, awards, names or prices). Name every placeholder text layer `Placeholder – <what it is>` and list them in the report and the client message.
- **Images:** from the settled source only. Name image layers by source (`iStock <id> – placeholder`, `Client – <file>`, `Existing – <name>`). With "no new images", reuse the homepage's images only where they fit the meaning; otherwise leave an image placeholder in the homepage's image style.

## Step 5: build
- **Frame:** a new top-level frame at the homepage's width, named `<Page> V1 - <D Mon YYYY>` unless the client SOP sets a naming rule.
- **Placement:** on the same page, to the right of the homepage's row with a 200px gap; if something already sits there, to the right of the last frame in that row. Align its top with the homepage. Never overlap existing frames.
- **Layout:** vertical Auto Layout for the page frame, sections set to fill width and hug height, the same as the homepage (if the homepage stacks sections without Auto Layout, keep its gaps).
- **Binding:** fills, strokes and text use the homepage's styles and variables, never raw values.
- Build section by section (one `use_figma` script per section or two), returning only ids.

## Step 6: verify
1. **Off-system check (read-only script):** walk the new frame and list every fill, stroke, effect and text node that is not bound to a style, variable or component that the homepage uses. Target: zero. Fix what you can; anything left gets a reason in the report.
2. **Header and footer:** confirm they're instances of (or identical to) the homepage's.
3. **Layout:** nothing overflows the container, nothing overlaps, columns line up with the homepage grid, no text wraps badly (no 1-word last lines in headings, no headings over 3 lines).
4. **Copy:** read back every text node against the copy source (word for word) or confirm it's a named placeholder.
5. **Original guard:** the homepage is unchanged.
6. **Screenshots:** section by section at reduced scale, within the job's screenshot budget; compare each one side by side with the homepage section it came from.

## Report (add to the normal completion report)
- The new frame: name, node id and link.
- **Page structure table:** section · purpose · source (component / homepage section `<id>` / composed) · copy (client / placeholder).
- **Placeholders:** text and images still to come from the client.
- **Off-system values:** none, or each one with its reason. **New patterns:** anything the homepage didn't have.
- "Tablet/mobile versions available on request."

## Guardrails
- The homepage and every other frame are read-only. Only the new frame is created and edited.
- Never restyle: no new fonts, colours, radii, shadows, spacing or icon styles.
- Never invent facts (numbers, names, awards, prices, testimonials). Placeholders say what's needed.
- Never detach the header or footer.
