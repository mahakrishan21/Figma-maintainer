# KHL — Kastner Hill Learning website
Client: Lion's Share Digital (see client.md in this folder) · teaming project: Lion's Share (KHL tasks: Founding Families, Referral)

## Files
- KHL-DEV: fileKey `jUau2sA38TBr0R2HjR75HE` — landing pages, website, style guide, components.
- An older brief mentioned fileKey `Zy59v6jz…` (same project name). The user works in `jUau2sA38…`.

## Page map
- "↳ Founding Families and Referral" `20618:246254`
  - Originals (approved baseline, top-level at y=0; the "Section 1" wrapper is gone): Founding Families `20618:246255`, Referral `20620:247085`, Thank you (consultation) `20627:249198`, Thank you (referral) `20626:248983`.
  - "Updated: 9 Oct, 2026" section `22127:4206` — the designer's revision. Founding Families `22123:1632`, Referral `22123:2015`, Thank you (referral) `22123:2277`.
  - The "Updated: 12 Oct, 2026" section `22147:3054` (FF client-feedback round) was deleted from the file by 2026-10-13. Its fixes (Request a Consultation, reach out, 32px gaps) are not in any surviving FF frame — confirm with the user before the next FF task.
- "↳ Referral Program Landing Page" `22163:3054` — the Referral page's own page.
  - "Updated: 9 Oct, 2026" `22163:3055`: an identical copy of the 9 Oct round (FF `22163:3056`, Referral `22163:3440`, Thank you referral `22163:3702`). Don't edit.
  - "Updated: 13 Oct, 2026" `22170:1638` (date bar `22170:1639`): Referral desktop `22170:1642`, Thank you (referral) `22170:1904`. Latest Referral round. As of 2026-10-14 the Tablet `22172:2531` and Mobile `22175:2718` frames no longer exist anywhere in the file, the 9 Oct copy `22163:3055` is gone, and loose top-level frames "Referral " `22202:6503` / "Thank you" `22202:6765` sit left of the section (not ours, don't touch).
- Other pages: STYLE GUIDE `18427:16856`, IMAGES (NoDEV) `18427:21710`, Inputs `85:1269`, Dropdowns `18:0`, Buttons `1:1183`. Don't edit these.

## Versioning SOP
- The designer's convention: each revision round goes in a new section named "Updated: D Mon, YYYY", with a black date-label bar (Group "Group 1" holding the date text) at the top and frames laid out in a row underneath. Originals at y=0 are never edited.
- When the user asks for a new version: duplicate the latest section, put it below, rename it, update the date label.

## Design system
- Colors: Primary/900 #00212D (headings, dark bands), Primary/500 #00A3E1 (blue), orange #F68839 (`--orange`, primary buttons), Gray/700 #344054 (labels), Gray/500 #667085 (body/placeholder), Gray/300 #D0D5DD (input borders).
- Type: headings Baskerville Display PT Bold; body Open Sans (Text lg 18/28, Text md 16/24, Text sm 14/20, labels SemiBold 14/20).
- Components: "Input field" (Type=Default, 48px input; Type=Leading dropdown, 44px input), "Textarea input field", "Button" (orange, 48px tall), "Check item text" (bullet list), "Dropdown header navigation".
- Form card: white, radius 20, padding 60, inner width 480, field gap 24, rows of two columns.
- Two-column form rows always use a 32px column gap (two 224px columns, right column at x=256), dropdown rows included. (correction, 2026-10-12)
- Founding Families `22147:3055` form: "Form fields" `22147:3414`; Name row `22147:3415`, School `22147:3424`, Email/Phone `22147:3418`, Grade/Contact `22147:3421`, Support `22147:3425`. Dropdown options annotated on `22147:3422/3423/3426`.
- No mobile frames exist for Founding Families (all 1440 desktop), and no mobile Thank You exists for either page.
- Font: Baskerville Display PT can't be loaded by the plugin API. Missing-font text can be moved, `rescale`d and resized, but its characters, size and auto-resize can't be edited. New or changed headings use Libre Baskerville Bold (already used for the step titles). The designer swaps them to Baskerville Display PT in the desktop app.
- The header nav is the "Dropdown header navigation" Desktop instance (logo + CTA, transparent: it sits on the navy hero). Its Mobile variants are template placeholders (Home/Products/Sign up); don't use them. Mobile header = navy bar with a Logo instance (`18121:62973`, scaled 0.62) and a Button Size=lg "Request a Consultation".
- Referral 13 Oct form (re-IDed by a designer edit to `22202:*`; card content `22202:7699`, form `22202:7701`, fields `22202:7702`). Client-confirmed fields (Jesse, 2026-10-14): Your Information = Name / Email Address (row) + Phone Number (full-width, Leading dropdown variant, row `22205:1998`); Family You’re Referring = Parent/Guardian Name / Email Address (row) + Phone Number (row `22202:7714`); Location of Interest = "Which location interests them?" dropdown `22202:7720` (options annotated). No notes textarea. Submit "Refer a Family" `22202:7722` NAVIGATEs to Thank You `22170:1904`. Phone (Leading dropdown) inputs are 44px vs 48px text inputs (component).
- Thank You (referral) `22170:1904` header = navy "Header" wrapper `22205:2011` holding a copy of the Referral nav instance `22205:2012` (template "Get Started!/Login" header removed 2026-10-14).

## Content rules
- Follow-up: a KHL team member "will reach out within one business day". Never "call", because first contact may be by email. That covers placeholders and microcopy too.
- Form submit CTA and header nav CTA: "Request a Consultation". Never "Schedule … Consultation". No Calendly or scheduling step: the form goes straight to the Thank You page.
- The Thank You page is client-approved. Don't change it unless asked.
- Referral page copy = the client's copy doc (Referral tab), used verbatim with curly apostrophes. The SEO title and meta description are an annotation on the desktop frame. Location options: North Austin (Opening January 2027) / Current KHL Location / Not Sure Yet.
- Form field order (Founding Families): Parent/Guardian name, Student name → Which school do you attend? (text input) → Email, Phone → Grade level, Best way to contact → Type of support → Questions/notes → Who referred you? (optional).
- Dropdown options: Grade 8th/9th/10th/11th/12th/Other; Contact Phone Call/Text Message/Email; Support Not Sure Yet / Let's Talk, Test Prep (SAT/ACT), Academic/AP Tutoring, Executive Function Coaching, College Admission Essays.

## Images
- Referral page (13 Oct round) uses iStock comps, at the user's instruction (Basic/Essentials, Editorial first; no Editorial results were found). PURCHASE LIST, not approved yet:
  - Hero `22170:1652` (+ tablet/mobile copies): iStock 1466299615, "Caucasian mother with teenager daughter make homework at home", creative (not Editorial), https://www.istockphoto.com/photo/caucasian-mother-with-teenager-daughter-make-homework-at-home-gm1466299615-498336663
  - "Share KHL With Someone You Know" `22170:2757` (+ copies): iStock 1517081213, "father son … conversation", creative (not Editorial), https://www.istockphoto.com/photo/father-son-family-man-child-conversation-talking-parent-boy-happy-discussion-gm1517081213-524339641
  - Replaced the KHL client photo (tutor with students, 9 Oct Referral hero). Still available if the client prefers a real photo.
- Preferred source: client photos on Dropbox ("The People of KHL", "More Photos of Guys"). Download with scripts/fetch_assets.py (Dropbox links work), or use files the user tagged in the project.
- Asset log:
  - Founding Families › "A Special Opportunity" image: KHL tutor at whiteboard (hash 86ce663f…). Client photo, approved with the 9 Oct round.
  - Founding Families › "Why Join KHL Early?": KHL students at table (hash 617726cc…). Client photo. Both replaced the original placeholders (45c22879 whiteboard-stock, 6455b183 family) in the 9 Oct round.
  - Stacked hidden fills removed in `22147:3164` / `22147:3310` (12 Oct round).

## Open decisions
- Thank You page bullet "On the call, we'll…" conflicts with "reach out". Optional, because the client approved the page.
- Dropdown height 44 vs text input 48 comes from the component, which predates this work.
- Referral form, client questions (2026-10-14): field label "Which location interests them?" (heading already covers it); Thank You "Check your inbox for a confirmation of your referral" accuracy (Jesse asked us to confirm); the SEO annotation on the desktop frame is gone (removed by the later edit), restore if still needed.
- Referral (13 Oct), awaiting the client: the form microcopy "We’ll record the referral under your name so your credit is applied automatically." was kept from the approved design (confirm the "automatically" promise); there's no form intro or helper copy; content not in the copy doc was removed ("Four steps, start to credit", the orange "Referring a family before December 1, 2026? / See Founding Families" band, the footer disclaimer, the extra Who Can button); the hero benefit tiles reuse doc phrases verbatim; white-on-orange buttons fail contrast (2.6:1, component); the Libre Baskerville fallback needs swapping.
