---
disable-model-invocation: true
name: responsive-from-desktop
description: Create or update the mobile (390px) and tablet (768px) versions of an approved desktop Figma frame. Adapts the desktop design (stacking, navigation, type scaling, touch targets, content priority) and reuses its styles, components and assets instead of redesigning. Use only when explicitly asked to create or update mobile or tablet frames, or run /figma-maintainer:responsive-from-desktop.
---

# Responsive design: desktop to mobile and tablet

> **Generic, reusable task action ("Create Tablet and Mobile Designs from Desktop Designs").** First check the client's folder for its own configuration (`clients/<agency>/task-responsive-designs.md`). **If one exists, it overrides the defaults below for that client only.** If none exists, use these defaults together with the client's SOP and design system. Never use another client's configuration. Scope is always the frame or section in the link (node-id).

The desktop design is the source of truth. Adapt it to mobile and tablet; don't design from scratch. Keep the brand, content, visual language and design system exactly. Change only structure, sizing, spacing, image positioning and component behaviour, and only as far as each screen size needs.

## Team rules (always)
- Reuse the file's existing styles, variables, components, typography, colours, spacing rules and assets. Never introduce new styles, or redesign a section, unless responsiveness requires it or the user asks.
- Keep the visual hierarchy, branding and consistency the same at every breakpoint.
- Use Figma-native features: Auto Layout and constraints (resizing set to fill or hug) wherever possible.
- Never change the desktop frame. Run an original guard: capture its text and image signature before you start and compare it at the end.
- Check every mobile and tablet frame afterwards for overflow, overlapping elements, broken alignment and bad text wrapping.

## Scope and canvas
- **Only when asked:** create mobile or tablet frames only when the request explicitly asks for them. A general "should be responsive" note in a design brief isn't a request for frames; design desktop only and offer the other sizes. (correction, 2026-10-14)
- **Breakpoints:** "mobile" means 390 only; "tablet" means 768 only; "mobile and tablet", "both" or an explicit "make it responsive" request for this frame means both. Use any other width the user names.
- **Updating, not creating:** if a mobile or tablet frame already exists for this desktop frame, update that frame to match the desktop instead of making a new one.
- Height is auto and grows with the content. Never crop or hide content to fit a height.
- **Names:** `[desktop name] — Tablet 768`, `[desktop name] — Mobile 390`, `[desktop name] — Mobile Menu`. If the client notes set a naming or placement convention, follow it instead.
- **Placement:** to the right of the desktop frame with a 120px gap: tablet first, then mobile, then the mobile menu. Align their tops with the desktop frame.

## Step 1: read and map the desktop frame
1. Read the full node tree: sections and their order, grids, components and instances, text styles, spacing values.
2. Identify the section types: nav, hero, feature grid, pricing, testimonials, gallery, logo bar, forms, tables, FAQ, footer and so on.
3. Note the spacing system (base unit, section paddings) and the type scale. Derive every mobile and tablet value from these; don't invent new ones.
4. Check the library and local components for breakpoint variants (`nav/mobile`, `Size=Mobile`, `Breakpoint=Tablet`…) and use them before building anything.
5. If the selection isn't a page or screen frame (for example, it's a single small component), say so and stop.

## Step 2: global rules

| | Tablet 768 | Mobile 390 |
|---|---|---|
| Side padding | 32px (40px if the desktop uses an 8px base with big margins) | 20px (16px with a 4px base) |
| Content width | 704px | 350px |
| Grids | 3–4 columns become 2. 2 columns stay 2 unless that crowds the text, then stack. Text-and-image pairs stay side by side when each side is at least 320px; otherwise stack. | Everything stacks into one column, in desktop reading order |
| Section vertical padding | about 25–30% less (120 → 88, 96 → 72, 64 → 48) | about 40–50% less (120 → 64, 96 → 56, 64 → 40) |
| Gaps between items | from the desktop scale, a step down when needed | 16–24px from the desktop scale |
| Headings | about 15–25% smaller (72 → 56, 56 → 44, 40 → 32, 32 → 28, 24 → 22) | about 30–40% smaller (72 → 40, 56 → 32, 40 → 28, 32 → 24, 24 → 20) |
| Body text | keep | keep 16 (never below 15); captions at least 12 |
| Buttons | intrinsic width; 48px tall | primary CTAs in stacked sections go full width (350); 48–56px tall |
| Navigation | the full nav if it fits in one row at 704px, otherwise logo + CTA + hamburger | 64px top bar: logo left, hamburger right, plus a Mobile Menu frame |

- Line height: 1.1–1.2 for headings, 1.5–1.6 for body. Use existing text styles where a matching size exists. Otherwise override only the size and line height on the same style family, and list each override in the report.
- Every stacked section uses vertical Auto Layout, so the frames stay editable.
- Never shorten copy. If a heading wraps to four or more lines, flag it; don't rewrite it.
- Left-align long text blocks on mobile even when the desktop centres them. Short hero text and section titles can stay centred.
- **Touch targets:** at least 44×44 for every interactive element, with at least 8px between neighbouring targets.
- **Images:** full-bleed images can run edge to edge; contained images stay inside the content width. Keep aspect ratios, but change very wide crops (21:9) to 4:3 or 1:1 on mobile (16:9 is fine on tablet), focused on the subject. Use the desktop's images only, never new ones. Scale down or remove decorative background elements that crowd a small screen, and report every removal.

## Step 3: section patterns
- **Navigation:**
  - Mobile Menu frame: the menu shown open, with links stacked at a 56px row height.
  - A prominent CTA stays in the top bar if it fits; otherwise it's the first item in the open menu.
  - An app-like screen with 3–5 main destinations gets a 56px bottom tab bar instead of a hamburger.
- **Hero:**
  - Mobile stacks heading → subheading → CTAs → image. The image goes first when the image is the message.
  - Two side-by-side CTAs stack on mobile, primary on top, with a 12px gap. On tablet they stay side by side.
- **Feature grids:**
  - Mobile stacks them by default. Use a horizontal swipe carousel only for four or more visually rich cards, logos or testimonials.
  - Tablet uses 2 columns.
  - Card padding is about 25% less on mobile.
- **Logo bars:**
  - Mobile: 2 rows or one scrolling row, logos 28–32px tall.
  - Tablet: one row if it fits, otherwise 2.
- **Pricing:**
  - Mobile stacks the plans with the recommended plan first. If there's a comparison table, each card lists its own features instead, and the matrix change goes in the report.
  - Tablet: 2 columns, or stacked.
- **Data tables:** if a table is wider than the content width, each row becomes a card (stacked label: value pairs) for six or fewer simple columns. Dense numeric tables scroll sideways with the first column pinned.
- **Forms:**
  - Mobile: every field full width and stacked, 48–56px tall, labels above the fields (never placeholder only). Short pairs such as ZIP and City can stay side by side.
  - Tablet: two-column rows stay.
- **FAQ:** accordions on mobile, with the first item open. Long testimonial walls become a carousel showing one testimonial at a time.
- **Footer:** on mobile the columns stack, and four or more link groups become accordions; legal text and social icons go last. On tablet use 2 columns.
- **Sticky sidebar CTA:** on mobile it becomes a sticky bottom bar with a full-width button and 16px padding.

## Step 4: content priority
Keep the desktop section order. The one exception: purely decorative filler that sits before the main CTA can move below it on mobile; report the move. Never delete content.

## Step 5: verify and report
1. Check every new or updated frame:
   - nothing overflows sideways (no child wider than the frame's content width)
   - nothing overlaps
   - columns line up
   - body text is at least 15px
   - touch targets are at least 44px
   - Auto Layout is on for every stacked section
   - the desktop frame is unchanged (original guard)
   Take a screenshot of each frame and look at the wrapping.
2. **Report:**
   - the frames delivered, with node IDs and links
   - the pattern used for each section
   - anything removed, cropped, reordered or converted
   - text-style overrides
   - flags for review: headings of four or more lines, dense tables, unclear nav CTA placement
   - components that were detached or rebuilt, and why

## Guardrails
- Never invent content, copy or imagery; everything comes from the desktop frame.
- Never restyle: colours, fonts, corner radius, shadows and effects stay the same as the desktop.
- Use existing components and their mobile or tablet variants. Detach or rebuild only when no variant fits, and report each case.
