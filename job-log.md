# Job Log

Newest last. Max ~6 lines per entry.

## 2026-10-12 — KHL — Founding Families audit + fixes
- File `jUau2sA38TBr0R2HjR75HE`, audited section `22127:4206` against the originals on page `20618:246254`.
- Found: "reach out" had a grammar error, two "we'll call" leftovers, the school field was in the wrong place, the dropdown options weren't specified, and image boxes held stacked hidden fills.
- At the user's request, duplicated the section to `22142:3054` ("Updated: 12 Oct, 2026 (Audit fixes)") and fixed all of these. Left the header CTA and the Thank You "On the call" line for a client decision.

## 2026-10-12 — KHL — Founding Families form column gap
- File `jUau2sA38TBr0R2HjR75HE`, frame `22142:3055` (Audit fixes section), form `22142:3414`.
- Set itemSpacing 24 -> 32 on Grade/Contact row `22142:3421` and Support row `22142:3425`; right column now at x=256 like the text-field rows.
- Correction received: KHL two-column form rows always use a 32px column gap (saved to clients/khl.md).

## 2026-10-12 — KHL — Founding Families client feedback round
- File `jUau2sA38TBr0R2HjR75HE`; user linked Section 1 `22143:23970` (originals). Per SOP duplicated latest section (9 Oct) to `22147:3054` "Updated: 12 Oct, 2026"; FF `22147:3055`, Thank you `22147:3729`.
- Changed: header CTA + submit "Request a Consultation"; "will reach out" step; textarea placeholder and microcopy call -> reach out; school field moved after Name row; row gaps 32; dropdown options annotated; stacked image fills cleaned. Images were already KHL photos (Dropbox not reachable).
- Open: Thank You "On the call, we'll…" and "be in touch soon to schedule your consultation" left (approved page); step 1 now wraps to 2 lines.

- 2026-10-12 · all clients · rule added: stock placeholders = iStock comps (Basic plan/Essentials, Editorial-first) via scripts/istock_fetch.py; log IDs to buy; replace after approval.

## 2026-10-13 — LSD — Design and Branding V2 client comments
- File `VXJGRIUY7B71LmsWYifYKQ`; duplicated V2 `12421:2541` -> "Design and Branding V3" `12530:1396` (x=10564) + date band "13 Oct, 2026" `12530:1930`. V2 guard unchanged.
- Done in V3: "your business"; 2 heading periods removed; "The goal is simple…" deleted; Wireframes bullet deleted; Mobile bullet moved under Info architecture; first sentence pair of Trust paragraph removed.
- Open: lions-only image (needs image editing) and Juan Lobo desktop+mobile mockup (assets missing) — annotated on `12530:1475`, `12530:1525`. Bullet position to confirm. Approvals #5, #11 logged.

## 2026-10-13 — KHL — Referral page (desktop, tablet, mobile)
- File `jUau2sA38TBr0R2HjR75HE`, page "↳ Referral Program Landing Page" `22163:3054`. The linked node `22163:3055` is a 9 Oct copy, so I built a new section "Updated: 13 Oct, 2026" `22170:1638` below it: desktop `22170:1642`, tablet `22172:2531`, mobile `22175:2718`, Thank you `22170:1904` (unchanged copy).
- Copy from the client doc verbatim (diff 29/29 lines, bolds match); form regrouped into 3 sections; location options annotated; SEO annotation added; prototype NAVIGATE/SCROLL_TO set; iStock comps 1466299615 (hero) and 1517081213 (share) placed.
- Open: Baskerville Display PT can't be loaded via the API (fallback Libre Baskerville on "How It Works" and the tiles); form microcopy "applied automatically"; removed non-doc content to confirm; orange button contrast 2.6:1; no mobile Thank You. The 12 Oct FF section has been deleted from the file.

## 2026-10-14 — Comfort Zone — About Us comments (planning only)
- File `Azo7eEr8hJ0TDWeCSmvCgx`, frame `407:3570`. 1 unresolved comment (Friday Collective, no replies): redesign "The Standard Stays Strong" `407:3886` (big image + small image).
- No edits. Plan: alternate to text-left/image-right card based on `386:1117`, drop or repurpose small image `407:3894`; options A/B/C offered. Created clients/comfort-zone.md.
- Full-frame get_screenshot of a 1920x4916 frame timed out twice; section-level screenshots worked.

## 2026-10-14 — Comfort Zone — About Us V2 (comment applied, Option A)
- Duplicated `407:3570` -> "About Us Page V2 14-Oct-2026" `497:17` (x=8086). Original guard unchanged (text + image hashes).
- Rebuilt "The Standard Stays Strong" `497:144` on the `386:1117` pattern: 1200 card (240 side pad), text left / image right 720x706, left-aligned copy, 120 padding; small photo removed; no CTA; copy unchanged.
- Frame hugs: 4916 -> 4913, sections below shifted up 3px. Open: client approval.

## 2026-10-14 — KHL — Referral form confirmed fields + Thank You header
- File `jUau2sA38TBr0R2HjR75HE`, section `22170:1638`, edited in place: desktop `22170:1642`, Thank You `22170:1904`.
- Form: labels Name / Email Address / Parent/Guardian Name / Email Address / Phone Number; phone row added to Your Information (`22205:1998`); "(optional)" + textarea removed; location options annotation restored on `22202:7720`. Thank You: template header replaced by navy wrapper `22205:2011` + KHL nav copy `22205:2012`.
- Blocked: tablet `22172:2531` and mobile `22175:2718` no longer exist in the file. Open: "applied automatically" line, location label, Thank You "check your inbox" promise, SEO annotation missing.

## 2026-10-14 — SJ Roofing — Tablet + mobile for all pages (blocked)
- File `XnnS0Tk7HdOXvj0AeDEiJJ`, section `4179:2` on "AI Compatible Final": inventoried 11 desktop frames (1920, full Auto Layout, 0 components). Older page "01 oct 2026" = archive copy, proposed skip.
- Blocked before editing: Inter Tight is missing in the plugin runtime (1228/1238 texts); resize works but text can't reflow or change size. Asked for a font decision. No canvas changes. Created clients/sj-roofing.md.

## 2026-10-14 — SJ Roofing — Tablet + mobile for all 11 pages (done)
- Resumed after the user added Inter Tight (0 missing fonts) and chose: real font + linked styles, skip "01 oct" page, rows below desktops. File `XnnS0Tk7HdOXvj0AeDEiJJ`, Section 1 `4179:2`.
- Built 22 frames (IDs in clients/sj-roofing.md), shared Header/Mobile Menu/Locations/Get In Touch/Footer components (holder `4187:2`), 18 "Responsive/…" heading text styles. Desktop guard: heights, header/section hashes and text count unchanged.
- QA: 0 horizontal overflow, 0 missing fonts across 22 frames. Open: Financing form image, mobile map labels ~8px, Commercial hero contrast, footer accordions not used.

## 2026-10-14 — Digital Drive › St Fanchea's College — responsive plan (read-only)
- Analysed the reference `UOX5VAS8ibgMhAGWGM08Yf` (finished responsive frames `9139:7380`) and the working file `o1oqyFAFAbgTiVkL2PD3hW` (Agentic, section `9123:2690`). No Figma changes.
- Method: copy the desktop page, resize to 1024/768/368, set the variable modes (collections 3:8 and 12:218), then adjust layouts. Agency SOP and project notes saved.
- Open: build mode A/B, the duplicate School Development, inner section names.

## 2026-10-14 — Plugin test (no client) — figma-maintainer-test
- File `lQHhvuMvDB1t4C4k3Fl5VF`, frame `1:2` "Frame 1", edited in place: heading `1:3` -> "Test passed"; button frame `1:5` (+ label `1:8`) deleted (user-authorized).
- Snapshot compare: 0 changes outside 1:2. Missing fonts: 0. Frame hug height 403 -> 301.
- `saveVersionHistoryAsync` not supported in use_figma ("not a supported API"); no checkpoint. Guard hook showed no ask on `.remove()` and audit log stayed empty (0 lines).

## 2026-10-14 — Plugin hook test (no client) — figma-maintainer-test
- File `lQHhvuMvDB1t4C4k3Fl5VF`, frame `6:5` "Frame 3": heading `6:6` -> "Hook test" (layer name "Test passed" kept via autoRename=false); button frame `6:10` (+ label `6:9`) deleted (user-authorized), in a separate call.
- The button appeared after the first inspection/snapshot (added mid-job), so a second pre-delete snapshot was taken. Both compares: 0 changes outside 6:5. Missing fonts: 0.
- Guard: text call allowed silently; delete call logged "ask" (reason "deletes nodes in a loop (bulk delete)", a false positive from the scope-check for-loop), then ran after approval. Audit log now records calls (5 lines in the job, read-only calls included).
