---
disable-model-invocation: true
description: Show the figma-maintainer prompt cheat sheet (how to prompt, comments, QA, responsive, components, audits, images, Slack, setup)
argument-hint: [topic: basics | comments | qa | responsive | components | audits | images | outputs | setup | costs | all]
---

Show me the cheat sheet below. If I named a topic ($ARGUMENTS), show only that section; otherwise show all of it. Print it as is: no tools, no extra commentary.

## figma-maintainer prompt cheat sheet
Replace `<url>` with a Figma link to the exact frame (right-click the frame → Copy link, so it has a `node-id`).

### Basics: the pattern
`Use figma-maintainer: <client> — <url> — <what to change> — images: <source>`
- **`Use figma-maintainer:`** switches the plugin on. A Figma link alone doesn't.
- **Client:** loads its SOP (image source, delivery, naming). A typo gets "Which client is this for?".
- **Link with `node-id`:** only that frame or section is changed.
- **images:** `iStock` · `Adobe Stock` · `AI-generated` · `client: <link>` · `@assets/folder/` · `no new images`. Naming it skips the question.
- **Paste the client's exact words.** Add "don't change the copy" when it must stay word for word.

Examples:
- `Use figma-maintainer: KHL — <url> — replace the hero text with: "…" — no new images`
- `Use figma-maintainer: LSD — <url> — apply this feedback: <paste the email>`
- `Use figma-maintainer: KHL — <url> — build the About page using the Founding Families layout — images: iStock`

### Comments
- `Use figma-maintainer: I got a client comment` finds it from Figma's notifications, plans it, asks you to approve, applies it and runs QA.
- `/figma-maintainer:client-comment PIPP horticulture` does the same for a named file or client.
- `/figma-maintainer:read-comments <url>` lists them only.
- `/figma-maintainer:apply-comments <url> — images: no new images` applies the latest round on that frame.
- `Use figma-maintainer: apply only Jesse's comments on <url>`

### QA
- QA runs by itself after every job. The verdict sits at the top of the report, and the client message is held if something's wrong.
- `skip QA` waives it for the job that just ran.
- `/figma-maintainer:qa` checks the newest job · `/figma-maintainer:qa PIPP` checks a job by name.
- `/figma-maintainer:qa <old url> <new url>` checks a new version against the comments on the old one.
- `/figma-maintainer:qa <url> since 2026-10-29 14:00 check: hero says "…"` checks work done directly in a frame, including manual work.

### Responsive (desktop only unless you ask)
- `Use figma-maintainer: <url> — make the mobile version` · `— make tablet and mobile versions`
- `Use figma-maintainer: <url> — update the existing mobile frame to match the latest desktop`
- `Use figma-maintainer: <url> — make mobile; use accordions for the FAQ and stack the pricing cards`
- `/figma-maintainer:make-responsive <url> mobile | tablet | both`

### Components and states
- `Use figma-maintainer: <url> — make the primary button hover darker using the existing colour styles`
- `Use figma-maintainer: <url> — add a focus state to the input component`
- `Use figma-maintainer: <url> — make the dropdown open on click in the prototype`

### Audits and checks (read-only, never change the file)
- `Consistency Audit <url>` · `— all pages` · `— homepage only` · `— include mobile frames`
- `Content Audit <url>` · `— check against the client copy doc` (attach it)
- `Accessibility Audit <url>` · `— mobile frames only`
- `Consistency Audit and Accessibility Audit <url>` runs both in parallel.
- `/figma-maintainer:check-brief <url>` + paste the brief · `/figma-maintainer:compare-versions <old url> <new url>`
- Then: `apply rows 1–5` · `fix all high` · `fix the contrast issues using existing colour styles`

### Images, video and copy
- `… — images: iStock` · `Adobe Stock` · `AI-generated` · `no new images`
- **iStock** gives watermarked Basic-collection (Essentials) comps as placeholders, with no account needed. If it can't reach iStock on your Mac, it says why and offers to fix it first.
- `… — use these client photos: <Dropbox/Drive link>` · `… — hero: @assets/hero.jpg` · `… — use @assets/khl-photos/`
- `… — copy is in <Google Doc link>, use it word for word` (the doc must be shared as "Anyone with the link")

### Outputs: Slack, client message, cost
- Every job ends with a report (including an **Undo** line), a Slack update and a client message with prototype links.
- `give me slack message` or `/figma-maintainer:slack` gives the Slack text plus an internal usage block.
- `/figma-maintainer:client-message` writes the client message.
- `/figma-maintainer:cost-report` (this conversation) · `latest` (last task) · `html`
- `/figma-maintainer:cost-report-all` · `since 2026-11-01` · `client KHL` · `html`: your whole cost history on this Mac, only when you ask

### Setup, rules and help
- `/figma-maintainer:doctor` checks the token, scopes, Figma access, notifications and version, with fixes.
- `figma-maintainer: next time, <rule>` saves a correction as a rule.
- `/figma-maintainer:sop Lasso up — desktop width 1920` adds an SOP rule · `/figma-maintainer:sop Lasso up` shows what's set.
- **"The file changed at …" prompt:** someone edited the file mid-job. Check the frame in Figma, then allow.

### Keep costs down
- **One job per conversation:** start a new conversation or type `/clear` after each job (the plugin reminds you).
- **Opus or Sonnet, not Fable,** for routine work: `/model opus`.
- **Small text jobs** (up to 3 plain text edits in one frame) get a lighter plan and QA automatically.
- `/figma-maintainer:cost-report-all` shows the average per agent and the model mix across your history.

### Tips
- **Link to the exact frame**, not the whole file.
- **One page per prompt**, then run an audit.
- **No tablet or mobile** unless you ask.
- **Image editing is annotated, not done.**
- It **never touches originals**: current designs are duplicated as `<Frame> V<n> - <date>`.
