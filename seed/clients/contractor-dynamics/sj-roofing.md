# SJ Roofing
Client: Contractor Dynamics (see client.md in this folder) · teaming project: SJ Roofing

## Files
- SJ Roofing (Copy): fileKey `XnnS0Tk7HdOXvj0AeDEiJJ` — website design, 11 desktop pages (1920 wide, full Auto Layout, no components/instances).

## Page map
- "AI Compatible Final" `2776:1365` (latest, source of truth). Section "Section 1" `4179:2` holds 11 desktop frames (top y=1163 in section, 2720px apart):
  Homepage `2776:1643`, Financing `2776:1370` (named "Financing Your Roofing Project Section"), About us `2777:2072`, Residential Roofing `4016:4385`, Commercial Roofing Page Design `4017:8564`, Exterior Services `4021:426`, Project Gallery `4025:413`, Review Page `4028:2352`, Contact Us `4030:3630`, Service Areas -Ventnor City `4031:1341`, Service locations page `4031:2530`.
- "AI Compatible - 01 oct 2026" `2587:1456`: older copy of the same pages (+ 3 banner frames, loose stroke vectors). Treat as archive.
- Tablet 768 + Mobile 390 for all 11 pages (2026-10-14), inside Section 1, a row below each desktop (tablet at desktop x, mobile at x+888, y = desktop bottom + 400). Named "<desktop name> — Tablet 768" / "— Mobile 390".
  Homepage 4205:2416 / 4205:3158 · Financing 4205:3895 / 4205:4394 · About 4205:4888 / 4205:5439 · Residential 4206:2636 / 4206:3385 · Commercial 4206:4129 / 4206:4913 · Exterior 4206:5692 / 4206:6216 · Gallery 4207:2416 / 4207:3025 · Review 4207:3629 / 4207:4278 · Contact 4207:4922 / 4207:5457 · Ventnor 4208:3733 / 4208:4207 · Service locations 4208:4676 / 4208:5244.
  Shared "Mobile Menu — 390" frame 4188:2 next to Homepage mobile.
- Page-level frame "Responsive components (tablet/mobile)" 4187:2 (left of Section 1): Header / Mobile 4187:3, Header / Tablet 4187:12, Section / Locations — Tablet 4209:5018 / Mobile 4209:7840, Get In Touch — Tablet 4209:5041 / Mobile 4209:7863, Footer — Tablet 4209:5122 / Mobile 4209:7944. Every responsive page uses instances of these.

## Versioning SOP
- Responsive frames: a row BELOW each desktop frame inside Section 1, desktop frames never moved (user decision 2026-10-14).

## Design system
- Fonts: Inter Tight (Regular/Medium/SemiBold/Bold) on ~99% of text, Outfit Regular on a few. Inter Tight was added to Figma by the user on 2026-10-14 (now loads in the plugin runtime; 0 missing). Re-check hasMissingFont before API text work.
- Responsive type styles (2026-10-14): "Responsive/Tablet/<style> <size> → <size>" and "Responsive/Mobile/…" for every heading style ≥28px (H1 80→60/40, H2 60→48/34, H2 50→42/30, Call 36→32/28, NUM 34→30/26, Initials 32→28/24, Phone 30→28/24, H6 28→26/24). Body text keeps desktop styles.
- 43 local text styles (H1 80, H2 60/50, H6 24-28, Body 20, p 18, Button 16, Navbar 14...), 106 paint styles, 1 variable collection (26 vars).
- Shared sections repeat across pages: header (in hero), Locations We Proudly Serve, Get In Touch, Footer (with Free Estimate form), Partners, FAQs, Testimonial, How We Get It.

## Content rules
- None recorded yet.

## Images
- Preferred source: unknown. 2026-10-14 responsive job: existing assets (no new media).
- Asset log: (none)

## Open decisions
- Responsive review items (2026-10-14): Financing page form is a flat screenshot image (unreadable at 350; needs live embed in dev); map pin labels ~8px on mobile (list above covers all towns); footer link groups kept expanded (not accordions); hero headline contrast on Commercial mobile crop; icon overlaps the "Roof Repairs" open-card title (Residential/Commercial).
- Decorative vectors (swooshes, outline shapes, angled strips, carousel arrows, Homepage trucks) are removed in tablet/mobile.
