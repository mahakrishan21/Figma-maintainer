# KHL — Kastner Hill Learning

## Files
- KHL-DEV: fileKey `jUau2sA38TBr0R2HjR75HE` — landing pages, website, style guide, components.
- An older brief mentioned fileKey `Zy59v6jz…` (same project name). The user works in `jUau2sA38…`.

## Page map
- "↳ Founding Families and Referral" `20618:246254`
  - "Section 1" `22143:23970` wraps the originals (users link to it). Originals (approved baseline, y=0 row): Founding Families `20618:246255`, Referral `20620:247085`, Thank you (consultation) `20627:249198`, Thank you (referral) `20626:248983`.
  - "Updated: 9 Oct, 2026" section `22127:4206` — the designer's revision. Founding Families `22123:1632`.
  - "Updated: 12 Oct, 2026" section `22147:3054` — client-feedback round (built from 9 Oct). Founding Families `22147:3055`, Thank you (consultation) `22147:3729`. (The earlier "Audit fixes" section `22142:3054` no longer exists.)
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
- No mobile frames exist for Founding Families (all 1440 desktop).

## Content rules
- Follow-up: a KHL team member "will reach out within one business day". Never "call", because first contact may be by email. That covers placeholders and microcopy too.
- Form submit CTA and header nav CTA: "Request a Consultation". Never "Schedule … Consultation". No Calendly or scheduling step: the form goes straight to the Thank You page.
- The Thank You page is client-approved. Don't change it unless asked.
- Form field order (Founding Families): Parent/Guardian name, Student name → Which school do you attend? (text input) → Email, Phone → Grade level, Best way to contact → Type of support → Questions/notes → Who referred you? (optional).
- Dropdown options: Grade 8th/9th/10th/11th/12th/Other; Contact Phone Call/Text Message/Email; Support Not Sure Yet / Let's Talk, Test Prep (SAT/ACT), Academic/AP Tutoring, Executive Function Coaching, College Admission Essays.

## Images
- Preferred source: client photos on Dropbox ("The People of KHL", "More Photos of Guys"). Claude can't open Dropbox, so the user has to provide the files locally or on Drive.
- Asset log:
  - Founding Families › "A Special Opportunity" image: KHL tutor at whiteboard (hash 86ce663f…). Client photo, approved with the 9 Oct round.
  - Founding Families › "Why Join KHL Early?": KHL students at table (hash 617726cc…). Client photo. Both replaced the original placeholders (45c22879 whiteboard-stock, 6455b183 family) in the 9 Oct round.
  - Stacked hidden fills removed in `22147:3164` / `22147:3310` (12 Oct round).

## Open decisions
- Thank You page bullet "On the call, we'll…" conflicts with "reach out". Optional, because the client approved the page.
- Dropdown height 44 vs text input 48 comes from the component, which predates this work.
