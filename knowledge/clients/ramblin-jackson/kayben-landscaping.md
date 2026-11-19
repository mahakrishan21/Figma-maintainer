# Kayben Landscaping
Client: Ramblin Jackson (confirmed by the user, 2026-11-18; not in the teaming.rocks snapshot) · teaming project: <not set>

> **Project SOP.** One of the agency's clients. Anything set here overrides the agency's `client.md`. Fill in only known facts, with their source and date. Leave `<not set>` otherwise.
> Moved from `_unassigned/` to `ramblin-jackson/` on 2026-11-18.

## 1. Project
- Brand / business: Kayben Landscaping, landscaping company in Okotoks, Alberta (residential design & construction, commercial enhancements, commercial maintenance & snow management) (from the file content, 2026-10-29)
- Live website: <not set>
- Status / current phase: homepage visual design. Two options per round (V1 / V2). Client picked option 1 as the base with three option-2 sections, applied in "Homepage V1-02 Rev - 18 Nov, 2026" `737:187` (2026-11-18)

## 2. Files and page map
- Kayben Landscaping: fileKey `qab5UVaUoEerCUNIbHpSLn` (homepage wireframe, desktop 1600 only)
- Pages: Cover `0:1`; Homepage - Wireframe `1:3`; Components `137:2408`; Extra `2:5` (older Homepage iterations 137:1884, 137:4739 and section drafts; read-only)
- Homepage - Wireframe `1:3`: Homepage (V1, client-reviewed, backup) `1:4`; "Homepage V2 - 29 Oct 2026" `225:132` (round 1 feedback), 600px below V1
- Approved originals (never edit): Homepage `1:4` (client-reviewed round 1 frame)
- Prototype flow starting points: "Homepage V2 - 29 Oct 2026" → 225:132 (added 2026-10-29). V1 has no named flow; its link works through starting-point-node-id=1:4.
- Latest round: "Homepage V2 - 29 Oct 2026" `225:132`, prototype https://www.figma.com/proto/qab5UVaUoEerCUNIbHpSLn/Kayben-Landscaping?page-id=1%3A3&node-id=225-132&starting-point-node-id=225-132&scaling=scale-down-width&content-scaling=fixed
- No tablet or mobile frames exist in the file (checked 2026-10-29).
- Design pages (observed 2026-11-18): "Homepage V1 - Design" `282:516`, "Homepage V2 - Design" `323:1551`, "Home page V3-Design (13 Nov 2026)" `563:1872`, "Home page V4-Design (16 Nov 2026)" `610:889`. Frames "Homepage V1-02 - <d Mon, yyyy>" = design option 1, "Homepage V2-02 - <d Mon, yyyy>" = option 2 (when the client says "number 1/2" or "version 1/2", this is what they mean). 16 Nov pair: option 1 `610:1364`, option 2 `610:959` (client-reviewed, never edit).
- Latest (2026-11-18): "Homepage V1-02 Rev - 18 Nov, 2026" `737:187` on page `610:889`, prototype https://www.figma.com/proto/qab5UVaUoEerCUNIbHpSLn/Kayben-Landscaping?page-id=610%3A889&node-id=737-187&starting-point-node-id=737-187&scaling=scale-down-width&content-scaling=fixed — approved by the client (via the user, 2026-11-18)
- Inner pages (observed 2026-11-18): wireframe pages "Outdoor Living from V1 - Wireframe" `279:906` (`287:1428`) and "Service Area Calgary from V1 - Wireframe" `388:482` (`388:1062`). Page "Inner page Design" `748:717` › section `748:1888`: approved wireframe copies "Outdoor Living" `748:720` and "Service Area" `748:1306` (in colour, no Overlay), then designs "Outdoor Living - Design V1 - 18 Nov, 2026" `772:265` and "Service Area Calgary - Design V1 - 18 Nov, 2026" `774:402`.

## 3. Overrides of the agency SOP
- Image/video source (overrides client.md): <not set> (asked per job; round 1 was "no new images"; 2026-11-18 design round and inner-pages job: client-provided)
- Wireframe phase: no real photos, stock or AI images; any new or enlarged image area is a grey placeholder with the placeholder image icon only (rule from the user, 2026-10-29)
- Desktop width / breakpoints: 1600 desktop only (observed, 2026-10-29)
- Versioning: follows the playbook default (every feedback round = duplicate of the current frame, changes only in the duplicate, previous version kept untouched as backup; name "Homepage V# - <d Mon yyyy>"). Round 1 = "Homepage V2 - 29 Oct 2026" (correction from the user, 2026-10-29)
- Other: the page frame is not Auto Layout; sections are stacked by y with 1px overlaps. A locked full-page "Overlay" vector (white, COLOR blend) on top turns the wireframe greyscale; it must be resized with the frame (observed, 2026-10-29).

## 4. Design system
- Colours: hero green #2c5234 (variable), dark #181e1a (variable), grey #3a3d3b (variable), beige #e3dfd6 (variable), CTA green #30b700, leaf mark #6c7d68 (variable). Rendered greyscale by the Overlay.
- Type: Playfair Display (H1 55, H2 - Bold 40, H3 - Bold 30, H4 22) and Inter (Body - Regular 16/22, Sub Heading - Bold 16/22, CTA 16 Medium, Caption 12). Local text styles.
- Components: Button (green, Inter CTA + arrow) on the Components page `137:2408`.
- Design-phase CTAs (observed 2026-11-18): "Button" `99:7` and "Button 1" `99:16` (Default = fill Brand/Accent - Light Green #30B700 `VariableID:7:44`, white label `Other/White`; hover Variant2 = white fill, green label, ON_HOVER Smart Animate 300ms). "Button 2" `547:952` = outline variant (no fill, green label), same layer structure as Button 1. Header is a plain absolute frame, not a component; logo is a vector.
- Design-phase page frames (observed 2026-11-18): vertical Auto Layout, itemSpacing -1, height FIXED (refit after section swaps), header absolute on top, hidden locked "Overlay" vector left over from the wireframe.
- Layout: 1600 frame, 1200 container (200 side padding), sections 150 top/bottom padding.
- Image placeholders: grey/dark fill + image hash `b57dcddc…` (placeholder icon, 512x512) at low opacity.
- Design-phase components for inner pages (observed 2026-11-18): Card 20/21/22 (`548:970`/`548:980`/`548:1032`, photo + #3a3d3b bottom gradient + white Playfair Bold 25 uppercase label), Gallery 31-36 (`637:3661`…`637:3696`), Step 34-44 (`620:2489`…`620:2659`). Wireframe Card 1-3 / Gallery 1-6 / Step 1-11 have the same labels and text. Homepage frame has no white sections: design sections use the grey `737:205`, dark `737:217` and green `738:347` fill variables with white text (variable on `737:193`).
- Homepage Service Area section `737:377`: the map pins are separate layers over a FILL map image; keep the section at 1101px tall or the pins drift off their towns (2026-11-18).
- Leaf artwork (after round 1): small leaf mark kept only above the Enjoy, A Clear Plan and Good Work Start headings; other leaf marks and the large faint leaves are hidden in V2 (2026-10-29).

## 5. Content rules
- Approved wording / CTA labels: <not set>
- Banned wording: <not set>
- Confirmed form fields: <not set>

## 6. Asset log
- Hero image (V2 `226:262`) — image — grey placeholder + placeholder icon (no new images, wireframe) — none — n/a — awaiting the client's hero photo/video (2026-10-29)
- CTA Banner "Wondering What Your New Yard Might Cost?" background (`737:270`, 1600x657, landscape) — image — client-provided, Google Drive file id 1WzERHM_4GP8_hnJvQgyXz7CnPGQfzVwF — not placed: the link needs Google sign-in — n/a — waiting for a public link or the file (2026-11-18)
- Inner pages (2026-11-18) — images — existing photos in the file (source per the user: client-provided; reused, not new) — hashes 817eb3, c50cc5, d61fe7, f6d8c3, 954d84, cfa2c9, 0978a3, a8140f, c45dd5, cc330c (Outdoor Living 772:265); 0978a3, c50cc5, 2fb0cd, 75c907, 954d84 (Service Area Calgary 774:402) — n/a — not yet client-reviewed
- Inner pages placeholders (2026-11-18) — image — client photo needed — none — n/a — open: outdoor kitchens 772:396, privacy screens/hot tub 772:403, landscape lighting 772:405, putting greens/turf 772:410, spring cleanups 774:529, commercial irrigation 774:536, fall cleanups 774:538, snow & ice 774:540, snow management block 774:466

## 7. Fonts
- Licensed / available: Playfair Display, Inter, Mona Sans (all load in the plugin, 2026-10-29)
- Missing in Figma (needs designer fix): none

## 8. Open decisions / client questions
- 2026-10-29 — Commercial landscape maintenance & snow management service areas were never listed (closed accordion, header only). Are they the same 5 areas, or do they differ? — waiting on client
- 2026-10-29 — Hero headline set to H2 40px (from 55px). Smaller still (H3 30px)? — waiting on client
- 2026-10-29 — Hero subline = the bold intro sentence ("Your property is a big investment…"). Keep, or a shorter subline? — waiting on client
- 2026-10-29 — Leaf marks kept on 3 headings; footer link leaf bullets kept. Reduce further? — waiting on client
- 2026-10-29 — Agency: Ramblin Jackson (answered by the user, 2026-11-18). Delivery in the client's Figma or E2M's? — still waiting on the user
- 2026-11-18 — Logo enlarged to 60px tall (footer logo size) and phone to 16px: big enough? — waiting on client
- 2026-11-18 — With option 2's dark A Clear Plan, Portfolio, A Clear Plan and Testimonial are three dark sections in a row. Keep, or a green background on one? — waiting on client
- 2026-11-18 — Green CTAs (white on #30B700) are ≈2.7:1 contrast, below WCAG AA. Raise with the client? — waiting on the user
- 2026-11-18 — Inner pages keep the wireframe's image cards (Love Your Finished Yard) and step carousel; the homepage uses tabs and an accordion for the same content. Switch to match? Add green highlight words to inner-page headings? — waiting on client

## 9. Change log
- 2026-10-29 — round 1 (5 client comments, pasted by the user) — hero rebuilt as large image placeholder with headline + subline only, body copy and CTA moved below; leaf artwork reduced; Service Area accordion replaced by a simple list — Homepage V2 `225:132`
- 2026-10-29 — follow-up — V2 renamed "Homepage V2 - 29 Oct 2026"; prototype flow starting point added for V2; V1 `1:4` confirmed unchanged as the backup (correction from the user: version + date in the name; previous version stays untouched)
- 2026-11-18 — inner pages: Outdoor Living `772:265` and Service Area Calgary `774:402` designed from the approved wireframes `748:720` / `748:1306` in the homepage `737:187` style (copy verbatim; header/footer/service area from the homepage)
- 2026-11-18 — design round (6 client changes, pasted by the user) — option 1 `610:1364` duplicated as "Homepage V1-02 Rev - 18 Nov, 2026" `737:187`; header logo and phone bigger; hero CTA to green Button 1; Love Your New, There's Something and A Clear Plan from option 2 `610:959`; CTA Banner kept from option 1, photo swap blocked (Drive sign-in)
