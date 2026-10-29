---
disable-model-invocation: true
description: Show the figma-maintainer prompt cheat sheet (responsive, audits, comments, images, components, Slack, cost)
argument-hint: [topic: responsive | audits | brief | comments | images | components | slack | all]
---

Show me the cheat sheet below. If I named a topic ($ARGUMENTS), show only that section; otherwise show all of it. Print it as is: no tools, no extra commentary.

## figma-maintainer prompt cheat sheet
Replace `<url>` with a Figma link. Include the node-id to target one frame.

### Responsive (desktop only unless you ask)
- `Use figma-maintainer: <url> — make the mobile version`
- `Use figma-maintainer: <url> — make tablet and mobile versions`
- `Use figma-maintainer: <url> — update the existing mobile frame to match the latest desktop changes`
- `Use figma-maintainer: <url> — make mobile; use accordions for the FAQ and stack the pricing cards`
- `/figma-maintainer:make-responsive <url> mobile | tablet | both`

### Audits (read-only, never change the file)
- `Consistency Audit <url>` (this page vs the homepage) · `— all pages` · `— homepage only` · `— include mobile frames`
- `Content Audit <url>` (spelling, grammar, CTAs, banned words) · `— check against the client copy doc` (attach it)
- `Accessibility Audit <url>` (WCAG 2.2 AA: contrast, targets, labels, focus) · `— mobile frames only`
- `Consistency Audit and Accessibility Audit <url>` runs both in parallel
- Commands: `/figma-maintainer:consistency-audit` · `/figma-maintainer:content-audit` · `/figma-maintainer:accessibility-audit`
- Then: `apply rows 1–5` · `fix all high` · `fix the contrast issues using existing colour styles`

### Check against a brief or another version
- `/figma-maintainer:check-brief <url>` + paste or attach the client brief (lists what matches and what doesn't; changes nothing)
- `/figma-maintainer:compare-versions <url V2> <url V3>` (lists every change)

### Client comments
- QA runs by itself after every job: a verdict on top of the report, and the client message is held if something is wrong
- `skip QA` (waive the QA check for the job that just ran)
- `/figma-maintainer:doctor` (check this Mac's setup: token, scopes, notifications, version)
- `/figma-maintainer:qa` (newest job) · `/figma-maintainer:qa PIPP` · `/figma-maintainer:qa <old link> <new link>` · `/figma-maintainer:qa <link> since 2026-10-29 14:00 check: …` (QA on its own, also for manual work)
- `Use figma-maintainer: I got a client comment` (finds it from Figma's notifications, plans it, asks you to approve, then applies it)
- `/figma-maintainer:client-comment PIPP horticulture` (same, for a named file or client)
- `/figma-maintainer:read-comments <url>` (list only)
- `/figma-maintainer:apply-comments <url> — images: no new images`
- `Use figma-maintainer: apply only Jesse's comments on <url>`

### Images and video (naming the source skips the question)
- `… — images: iStock` · `… — images: Adobe Stock` · `… — images: AI-generated` · `… — no new images`
- `… — use @assets/khl-photos/ for the hero` (local files you tagged)
- `… — use these client photos: <Dropbox/Drive link>`

### Components and states
- `Use figma-maintainer: <url> — make the primary button hover darker using the existing colour styles`
- `Use figma-maintainer: <url> — add a focus state to the input component`
- `Use figma-maintainer: <url> — make the dropdown open on click in the prototype`

### Slack and usage
- `give me slack message` or `/figma-maintainer:slack` (Slack update plus a separate internal usage block)
- `/figma-maintainer:cost-report session` · `latest` · `client KHL since 2026-10-01` · `html`

### Tips
- Link to the exact frame (node-id), not the whole file.
- Paste the client's exact copy and say "don't change the copy". It gets checked line by line.
- One prompt per page, then run an audit.
- `figma-maintainer: next time …` saves the correction as a rule.
