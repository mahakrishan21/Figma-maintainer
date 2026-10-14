# Task SOP: Create Tablet and Mobile Designs from Desktop Designs (Digital Drive configuration)
Agency: Digital Drive - SEO (see client.md) · Recurring task · Applies to **every Digital Drive project** with this request, and **only to Digital Drive**.

> **Scope of this file:** this is Digital Drive's configuration of the plugin's reusable task type "Create Tablet and Mobile Designs from Desktop Designs" (`responsive-from-desktop`). Its requirements (1024/768/368, variable modes, boilerplate, the hard rules) are Digital Drive's own. For any other client, use the generic task type with that client's SOP, design system and project requirements. Never copy these rules.

> Generic method, taken from the finished reference work (first job: St Fanchea's College, 2026-10-14). Project-specific IDs belong under "Jobs" at the end, never in the method.
> Precedence: the user's prompt, then this task SOP, then client.md, then the team playbook.

## 1. When this applies
- Any request to create or update responsive versions (Tablet Landscape / Tablet / Mobile) of approved desktop designs for a Digital Drive project, including when the teaming comment says "similar to our previous projects".

## 2. Hard rules
- **Scope = the frame or section in the link the user shares (its node-id).** Work only inside it, and put new frames inside it, wherever it sits. The page name (usually "UX Design - Responsive") isn't the scope: other frames on the same page, and every other page (UI Kit & Design System, Boilerplate Templates, UX Design - Client), are read-only. If the link has no node-id, or points to a whole page, stop and ask for the exact frame or section. (correction, 2026-10-14)
- **Never change** the UI Kit, Figma variables, styles or components. Never create new styles, variables or components, and never recreate existing ones.
- Use the project's existing design system: variables, text styles, components, variants, and the boilerplate blocks.
- The designer may adjust anything necessary for the responsive versions; templates may be brand-adjusted, so they won't always map perfectly. Every adjustment goes in the report.
- Breakpoints: **Tablet Landscape 1024 · Tablet 768 · Mobile 368** (desktop 1440). If a project's boilerplate shows other widths, use the boilerplate's widths and report the difference.
- Images: reuse the desktop images (no image question).

## 3. Read first (read-only)
1. Open the **linked node** (the scope). The desktop frames to adapt (1440 wide) are its children. Also list the pages (read-only) to locate "UI Kit & Design System" and "Boilerplate Templates" for reference.
2. **Variable collections and modes:** in a read-only `use_figma` script, call `figma.variables.getLocalVariableCollectionsAsync()` and list each collection with its modes. Expect two responsive collections:
   - **type/spacing/padding** (font sizes, line heights, `padding/component-vertical/*`, `spacing/*`);
   - **grid** (`grid/screen-size`, `columns`, `gutter`, `margin`).

   Each has modes Desktop / Tablet Landscape / Tablet / Mobile. Record their IDs under "Jobs".
3. **Boilerplate:** map each desktop section ("<Block> - Desktop") to its boilerplate versions ("<Block> - Tablet Landscape / Tablet / Mobile"). List the blocks that have no boilerplate version; those are custom and adapted by hand.
4. **If a finished reference exists** (a previous similar project, or a responsive page in another copy of the file), read how it adapted each block. Use it according to the build mode the user picks (see §7).
5. Check for missing fonts. **Never substitute fonts.**

## 4. Build method (per desktop page × breakpoint)
1. **Copy the desktop page frame** inside the linked section or frame (the scope). Resize it to the breakpoint width and keep vertical Auto Layout, with height hugging the content.
2. **Set the explicit variable modes on the frame** for both responsive collections (type/spacing and grid) to the breakpoint's mode. Bound type, padding, spacing, radius and layout grids then adapt automatically. Don't override bound values by hand.
3. **Layout adaptations** (the reference's pattern):
   - Sections that are horizontal on desktop (Image Left Right, Image Left Right Contained, USP Horizontal, Page Cards Horizontal, and similar side-by-side blocks) become **vertical on mobile**. On tablet, keep or stack according to the boilerplate's Tablet version.
   - Card rows: wrap, or stack to the grid's column count.
   - Children fill the container width.
   - **Mobile:** remove the Top Bar, and use the boilerplate's mobile Header plus the Mobile Menu and Mobile Menu - Dropdowns frames.
   - Component Header, Featured Content + 3 Images, Facebook-feed and similar blocks: follow the boilerplate version, or keep horizontal if it fits.
   - Custom blocks with no boilerplate version: adapt them with the same patterns (stack, wrap, grid columns from the variables) and list each one in the report.
4. Use existing components and variants only. Never detach or flatten. Text stays on its text style.
5. **Naming:** "<Page> - Tablet Landscape" / "<Page> - Tablet" / "<Page> - Mobile". Inner section names follow the user's choice (keep "– Desktop" as the reference did, or rename to the breakpoint).
6. **Placement:** follow the file's existing pattern. In the reference, each page has a label bar (2560×100) with Tablet Landscape, Tablet and Mobile in a row underneath. Otherwise, place them below the desktop frames.

## 5. QA before reporting
- For every frame: no horizontal overflow, nothing overlapping, sensible text wrapping (flag headings of 4+ lines), tap targets of at least 44px on mobile, images not distorted.
- **Variable modes are set** on every responsive frame, for both collections.
- No new styles, variables or components. **Nothing changed outside the linked section or frame**: run a snapshot compare of its page with `--targets <linked node-id>`, plus a snapshot of the Boilerplate page.
- If a reference exists: a structural comparison per section and breakpoint (layout direction, wrap, modes, section order), with the differences listed.

## 6. Report and estimate
- Report: frames (with links) per page and breakpoint; the custom blocks and how each was adapted; deviations from the boilerplate; the fonts check; the comparison with the reference; questions. Then the Slack update and the internal usage block.
- **Estimate guide** (designer hours, all 3 breakpoints for one page; the variable modes do most of the work):
  - a short page (under 5 sections, no custom blocks): about 1.5–2 h
  - a standard page (8–15 sections): about 3–4 h
  - +0.5–1 h for each custom block type
  - +2 h QA and consistency pass per job

  Delivery is usually 3 working days for about 8 pages. The client asks for an hour estimate and a delivery date up front.

## 7. Decisions to confirm per job
- **Build mode, when a finished reference exists:**
  - **A:** build independently, then compare with the reference (recommended to prove the method);
  - **B:** copy the reference's decisions.
- Duplicate desktop frames: build once or for each?
- Inner section names: keep "– Desktop" or rename?
- Which pages, and whether all 3 breakpoints are needed.

## 8. Jobs

### Job 1: St Fanchea's College (2026-10-14) · teaming project: St Fanchea's College

#### 1. Project
- Brand / business: St Fanchea's College (school website)
- Status / current phase: **Responsive designs (Tablet Landscape / Tablet / Mobile) for 8 desktop pages. Plan approved for saving; build not started.** Next step: run the build in a fresh session (see §8 for the open decisions).

#### 2. Files and page map
- **Reference (finished human work, READ-ONLY):** "St Fanchea's College", fileKey `UOX5VAS8ibgMhAGWGM08Yf`
  - Cover `4162:548`; UI Kit & Design System `0:1`; Boilerplate Templates `5380:3498` (233 frames); UX Design - Client `9015:2667`; **UX Design - Responsive** `9098:350`; Search `9026:3661`.
  - **Finished responsive frames** are in frame "for - M" `9139:7380` (https://www.figma.com/design/UOX5VAS8ibgMhAGWGM08Yf/St-Fanchea-s-College?node-id=9139-7380). The 24 frames:
    - Home: TL `9139:1623`, T `9139:1845`, M `9139:2071`
    - School Development: `9139:2281` / `9139:2490` / `9139:2703`
    - School Staffs: `9139:2903` / `9139:3482` / `9139:4071`
    - School Policies: `9139:4618` / `9139:4867` / `9139:5121`
    - Principal's Welcome: `9139:5355` / `9139:5565` / `9139:5779`
    - Sub Navigation: `9139:5978` / `9139:6036` / `9139:6094`
    - Search – Empty: `9139:6141` / `9139:6190` / `9139:6239` (the mobile frame is mislabelled "Tablet")
    - Search – Results: `9139:6277` / `9139:6334` / `9139:6391`
    - Label bars "Group 1–8" `9139:6437…6458`.
  - Layout: each page gets a label bar (2560×100), with Tablet Landscape, Tablet and Mobile in a row underneath (x step 1224 / 968; gap between pages 3560).
- **Working file (write here ONLY):** "St Fanchea's College - Agentic", fileKey `o1oqyFAFAbgTiVkL2PD3hW`
  - **UX Design - Responsive** page `9098:350` → section `9123:2690` (https://www.figma.com/design/o1oqyFAFAbgTiVkL2PD3hW/St-Fanchea-s-College---Agentic?node-id=9123-2690). It holds the 9 desktop frames (1440):
    - Home `9098:351`
    - Sub Navigation `9098:1875`
    - Search – Empty `9098:1946`
    - Search – Results `9098:2008`
    - Principal's Welcome `9098:1652`
    - School Staffs `9098:808`
    - School Policies `9098:1390`
    - School Development `9098:586`, plus an **identical duplicate** `9121:2424`
  - **Boilerplate Templates** page `5380:3498` → section `9123:2689` (233 frames). READ-ONLY; copy blocks from it.
- **Approved originals (never edit):** all desktop frames, the Boilerplate section, the UI Kit, variables, styles and components, and the whole reference file.

#### 3. Overrides of the agency SOP
- Image/video source (overrides client.md): existing assets in the file (responsive work reuses the desktop images) (2026-10-14)
- Desktop width / breakpoints: 1440 → 1024 / 768 / 368
- Versioning: new frames next to the desktops in the same section, laid out like the reference

#### 4. Design system (from the reference, read via get_variable_defs on `9139:2071`)
- **Variable collections switched per breakpoint** (`explicitVariableModes` on each responsive page frame):

  | Collection | Tablet Landscape | Tablet | Mobile |
  |---|---|---|---|
  | `VariableCollectionId:3:8` (type, spacing, padding) | `4012:3` | `3:2` | `3:1` |
  | `VariableCollectionId:12:218` (grid) | `4012:2` | `12:2` | `12:1` |

  Desktop is the default mode. **Verify that the same collection and mode IDs exist in the Agentic file before building** (they should, since it's a copy).
- Mobile values, as an example:
  - grid: `grid/screen-size` 368, `grid/columns` 2, `grid/gutter` 20, `grid/margin` 16
  - `padding/component-vertical/2xl` 120 (desktop) → 48 on mobile (`/lg` 48, `/sm` 32)
  - type: display 46, h1 36, h2 32, h3 28, h4 24, body 16/28, lg-body 20/30, intro 20/32, button 18/24
- **Bindings on Home desktop:** 80/80 text layers are bound (font family, size, line height and style). Also bound: about 55 paddings, 63 gaps, 172 fills, 40 radii and 15 layout grids. Text styles: Heading/Display, H1–H4, Eyebrow; Body/Body, Intro, Lg Body, Lg Body - Strong, Sm Body, Caption - Strong.
- **Fonts:** Lexend (headings, SemiBold/Medium); Atkinson Hyperlegible Next (body).
- **Colours:** brand berry `#8b064f`, pink `#ee8cc9`, blue `#71b6e9`; surface-primary `#fbf0ed`, surface-hero `#cee1f3`; text-primary `#2a2327`.
- **Components (local):** Button, Social Media Icons, UI Icons. Page sections are plain frames copied from the boilerplate (named "<Block> - Desktop"), not instances.

#### 5. How the reference adapted each section (Home, desktop → mobile)
- Type and spacing adapt through the variable modes: side padding 64→16, vertical 120→48 or 64→32.
- **Horizontal → vertical on mobile:** Image Left Right, USP Horizontal, Page Cards Horizontal, Image Left Right Contained.
- **Stay horizontal:** Header (mobile header form), Component Header, Featured Content + 3 Images, Facebook Live Feed.
- The Top Bar is removed on mobile. One block wraps. More children fill the width.
- Section names inside the responsive frames were left as "– Desktop" by the designer.
- **Blocks with no boilerplate breakpoint version** (adapt them by hand, using boilerplate patterns): Contained Image Content Left Right, Search Overlay, Page Cards Horizontal, Facebook Live Feed, Dropdown Navigation, Gallery, Filter, and the staff grids (Leadership Team, Coordinators, Teaching Staff, Classroom Assistants, Support Staff).
- **Boilerplate blocks with all breakpoints:** Component Header, Top Bar, Header, Footer, USP Horizontal/Vertical, CTA Block Contained, Hero Centre, Image Left Right, Secondary Hero v2, Featured Content + 3 Images, Page Cards, and others. Image Left Right Contained has no Tablet frame; Mobile Menu and Mobile Menu - Dropdowns exist.

#### 6. Asset log
- No new images: the desktop images are reused.

#### 7. Fonts
- Lexend, Atkinson Hyperlegible Next. Check for missing fonts before editing; **never substitute**.

#### 8. Open decisions / client questions
- 2026-10-14 — **Build mode (the user decides when starting):**
  - **A** (recommended): build independently from the desktop pages, the boilerplate and the variables, then compare structurally with the reference frames and report the differences.
  - **B**: copy the reference's decisions per section.
- 2026-10-14 — School Development is duplicated (`9098:586` and `9121:2424`): build responsive versions once or twice?
- 2026-10-14 — Inner section names: keep the reference's "– Desktop" names, or rename them to the breakpoint?
- 2026-10-14 — Estimate shared with the user: about 22 designer hours, about 3 working days (start Thu 15 Oct, deliver Mon 19 Oct 2026). Earlier figure before the variable-mode analysis: 32 hours. The client asked for hours and a delivery date in teaming.

#### 9. Change log
- 2026-10-14 — Read-only analysis of both files and the plan saved. No Figma changes.
