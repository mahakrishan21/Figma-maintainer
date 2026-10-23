# Comfort Zone
Client: Hey Mr Media (see client.md in this folder) · teaming project: Comfort Zone Web Tasks E2M

> **Project SOP.** One of the agency's clients. Anything set here overrides the agency's `client.md`. Fill in only known facts, with their source and date. Leave `<not set>` otherwise.

## 1. Project
- Brand / business: Comfort Zone LLC, heating & air conditioning and geothermal, Westerly, Rhode Island (from the copy docs and design, 2026-10-23)
- Live website: https://comfortzonegeo.com (current site; contact page `/contact`, checked 2026-10-23)
- Status / current phase: homepage rounds V2–V6 done; internal pages in progress. Contact Us and Financing first drafts, Membership V2 (2026-10-23).

## 2. Files and page map
- Comfort Zone: fileKey `Azo7eEr8hJ0TDWeCSmvCgx` (homepage rounds V2–V6, internal pages, components)
- Homepage rounds: pages "Homepage V2 15-Sep-2026" … "Homepage V6 30-Sep-2026" (`335:1777`), one dated page per round.
- Internal pages: page `386:148` "Internal pages" (it is a PAGE, not a section; desktop 1920 only). Frames in a row at y=0, 428px apart: Heating & Cooling `386:824`, Geothermal `391:2863`, Membership `447:17`, Resources `437:5216`, About Us `407:3570` (original, client-commented), About Us Page V2 14-Oct-2026 `497:17`, Contact Us Page `543:32` (x=10434, new 2026-10-23), Financing Page `543:328` (x=12782, new 2026-10-23). Membership Page V2 23-Oct-2026 `542:381` sits 200px below Membership (x=1270, y=5282).
- About Us sections: Hero `407:3667`, "Built to Last" `407:3912` (dark bg, image left + overlapping card right), "The Standard Stays Strong" `407:3886` (50/50: full-bleed image left `407:3889`, text right with small 240x280 image `407:3894`), "Values Behind Every Job" cards `407:3922` (5 instances), CTA `407:3737`, Footer `457:1054`.
- Components page "Componants" `41:4807` (homepage card sets only; no form, FAQ or header components).
- Copy docs (client, 2026-10-23): "Comfort_Zone_Int Website Copy_Sept 2026", Google Doc `19lERUXRmFL4VLjscDY68MnQGI-PgpDugDX671krkZug` (H&C, Geothermal, Resources, About). **Membership copy = tab `t.fzu39kinparo` of that doc** (the link the client sent). "Comfort_Zone_Contact Us Page_Sept 2026", Google Doc `16uo8BE2TjHM0CCm071K8xaVjEUcnk8CpqrwHBxKJ_wI`.
- Reading a tab: `https://docs.google.com/document/d/<id>/export?format=docx&tab=<tabId>` (or `format=txt`). The txt export drops pending suggestions and shows the pre-suggestion text; the docx keeps them as `w:ins`/`w:del` with the author. Check both (2026-10-23).
- Approved originals (never edit): <not set>
- Latest round: Membership V2 23-Oct-2026 `542:381`; About Us V2 14-Oct-2026 `497:17`.

## 3. Overrides of the agency SOP
- Image/video source (overrides client.md): <not set> (per job so far: 2026-10-14 existing assets; 2026-10-23 iStock, from the user)
- Desktop width / breakpoints: 1920, desktop only (as built in the file, 2026-10-14)
- Versioning: Homepage: new dated page per round ("Homepage V# DD-Mon-YYYY"). Internal pages: duplicate the frame per revision round as "<Page> V# DD-Mon-YYYY", placed 200px right of the previous version on the same page; original keeps its comments (set 2026-10-14). There's no room right of Membership, so on 2026-10-23 its V2 went 200px below instead (placement not yet confirmed, see §8).
- Other: <not set>

## 4. Design system
- Colours (paint styles): button red #9A2D2A (raw 154,45,42), accent red "Trusted Heating/Brown/Mexican Red 7" #A72024, gold "Trusted Heating/Orange/Golden Tainoi 31" #FFCB6F, dark card #262626, body grey #555555 on light sections.
- Type (text styles): H1 Red Hat Display ExtraBold 64 (hero); H2 Light / H2 Ex Bold 56 (two-weight titles, Light line + ExtraBold line); H3 semibold 28 (FAQ questions); price Red Hat Display Regular 70; Body copy Mona Sans Medium 18; button Mona Sans Bold 16 (uppercase); Text Mona Sans Regular 16 (consent copy).
- Components: none on canvas for page parts. Every section is a plain frame copied per page (Top, Header, Hero Section, Footer Section). Header active page = gold nav text + gold "Line 1" underline.
- Patterns: "When Something Feels Off" `386:1117` (blush card, text left + image right, red CTA); dark textured band `451:570` (image left + dark card right); FAQ accordion `391:3014` (Geothermal Questions); price cards `447:135`; red CTA band `447:165`. Form: the footer newsletter field (`457:914`, underline field) + SMS consent (`457:924`). The full contact form lives in Contact Us `543:148` ("Get In Touch" band); reuse it.
- Layout: container 1440 (240 side padding), section padding 120.

## 5. Content rules
- Copy source: the two Google Docs in §2, verbatim (client, 2026-10-23). The Int Website Copy doc holds pending suggestions (tracked insertions/deletions). Read them from a .docx export; plain-text reads merge both.
- Contact Us form fields: Name, Email, Phone, Service Needed, Message; button "Send Message" (Contact Us doc, 2026-10-23)
- Contact forms must carry the SMS consent disclaimer from the current Contact page; the new site also needs the Terms & Conditions and Privacy Policy pages, which are required by the phone service and CRM/payments provider (client note in the Contact Us doc, 2026-10-23)
- Financing page: a text block with a button that links out to a third party, then an FAQ block and a contact form (client message, 2026-10-23). Client likes the H&C "When Something Feels Off" module `386:1117` for the financing section (Friday Collective, Figma comment, 2026-10-14).
- Banned wording: <not set>

## 6. Asset log
- About V2 "The Standard Stays Strong" `497:147` — image — existing asset `a9e70d7a` (rooftop technician) — reused — approval pending. Small worker photo (`522f4bb4`) removed from that section (2026-10-14).
- Contact Us hero bg `543:127` — image — iStock (Essentials, creative) — 2243404936 — watermarked comp, not licensed — placeholder (2026-10-23)
- Contact Us "Get In Touch" band `543:161` — image — iStock — 2255240295 — comp, not licensed — placeholder (2026-10-23)
- Contact Us "Serving Our Local Communities" `543:176` — image — iStock (creative, Napatree Point, Watch Hill) — 2187324102 — comp, not licensed — placeholder (2026-10-23)
- Financing hero bg `543:423` — image — iStock — 1180558234 — comp, not licensed — placeholder (2026-10-23)
- Financing text block `543:458` — image — iStock — 1418831339 — comp, not licensed — placeholder (2026-10-23)
- Financing "Get In Touch" band `543:518` — image — iStock — 2255240295 (same as Contact) — comp, not licensed — placeholder (2026-10-23)

## 7. Fonts
- Licensed / available: Red Hat Display and Mona Sans load in Figma (no missing fonts on internal pages, 2026-10-23)
- Missing in Figma (needs designer fix): none found (2026-10-23)

## 8. Open decisions / client questions
- 2026-10-14: Comment (Friday Collective) on `407:3886` (redesign large+small image section): Option A applied in V2 `497:144`; awaiting client approval.
- 2026-10-14: Resources page: "add FAQ section to resources page. FAQ on rebates" (Friday Collective, Figma comment). Not done yet; needs FAQ copy and a go-ahead.
- 2026-10-23: The Membership tab `t.fzu39kinparo` holds pending suggestions by Greg Rives (15 Sep 2026): the hero adds "equipment … preserves the air quality in your home … your system"; What to Expect adds the twice-yearly visit sentence plus "clean and", "change filters", "measure for optimal performance"; tier names, prices and benefits fill the placeholders. There's also a comment "to review on our next call" (Maddie DeVane, 3 Sep) on "Choose the Right Membership". Originals 447:17 and V2 542:381 show the suggested version. The user (via the coordinator) asked for the tab's plain text, which is the pre-suggestion version. Hero and What to Expect are held pending a decision: keep the suggested version, or revert to the base text.
- 2026-10-23: The tab has placeholders for tier name, price and benefit. V2 keeps the current names, prices and benefits (coordinator instruction) and uses "Starting at:" on all three cards, the doc's pattern. Switch to placeholders if preferred.
- 2026-10-23: Financing page copy (text block, button label, third-party URL, FAQ questions and answers) not supplied; placeholders in `543:328`.
- 2026-10-23: Contact Us: business hours and the "Service Needed" dropdown options not supplied.
- 2026-10-23: Membership V2 placed below the original (no room on the right). Confirm, or name another spot for internal-page versions.
- 2026-10-23: Replace the 6 iStock placeholders with licensed stock or client photos before handoff.

## 9. Change log
- 2026-10-14: About Us comments planned; About Us V2 `497:17` built (Option A). https://www.figma.com/design/Azo7eEr8hJ0TDWeCSmvCgx/?node-id=497-17
- 2026-10-23: Membership V2 `542:381` (4 copy fixes from the doc); Contact Us `543:32` and Financing `543:328` built from existing patterns with 6 iStock placeholders. https://www.figma.com/design/Azo7eEr8hJ0TDWeCSmvCgx/?node-id=543-32
- 2026-10-23 (fix): Membership V2 checked against tab `t.fzu39kinparo`. "Starting at:" now on all three cards (`542:730`, `542:731`, new `549:32`); CTAs already matched. Hero and What to Expect held (pending suggestions, see §8). https://www.figma.com/design/Azo7eEr8hJ0TDWeCSmvCgx/?node-id=542-381
