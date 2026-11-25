# Figma maintainer (Claude Code plugin)

A Claude Code plugin that does Figma maintenance work like a senior UI/UX designer:
- copy and form changes;
- image and video swaps;
- inner pages built from existing patterns;
- mobile and tablet versions;
- component and hover changes;
- client-comment rounds.

It follows each client's SOP and keeps a record of every job. An independent QA agent checks the work before anything goes to the client.

> **New to it?** Start with [`ONBOARDING.md`](ONBOARDING.md) (15-minute setup). **Visual guide:** open `docs/figma-maintainer-guide.html` in a browser for the same guide with copy-ready prompts. `docs/figma-maintainer-briefing.html` is the management briefing.

**What's inside**

| Agent | Does | Changes Figma? |
|---|---|---|
| `figma-maintainer` | The designer: makes the changes | Yes, within strict guardrails |
| `client-comments` | Reads a new client comment and writes a plan for your approval | No |
| `qa-checker` | Checks finished work against the client's comments or your request | No |
| `consistency-auditor` · `content-auditor` · `accessibility-auditor` | Audits | No |
| `usage-reporter` | Exact token usage per task or conversation (estimated cost only in the consolidated history) | No |

---

## 1. Quick start
1. **Install** (details in [Setup](#9-setup-and-troubleshooting)):
   ```
   /plugin marketplace add E2M-Design/e2m-figma-marketplace
   /plugin install figma-maintainer@e2m-figma
   ```
   The repo is private: you need read access and GitHub signed in on your Mac.
2. **Restart Claude Code** (or run `/reload-plugins`). Hooks only load at the start of a session.
3. **Run** `/figma-maintainer:doctor`. It checks your token, Figma access, notifications and plugin version, and tells you what to fix.
4. **Your first job:**
   ```
   Use figma-maintainer: Lasso Up — https://www.figma.com/design/<file>/…?node-id=12-345 — change the hero heading to "…", no new images
   ```
5. **Read the result:** QA verdict, report, Slack update and client message.

---

## 2. How to prompt

### The pattern
```
Use figma-maintainer: <client> — <Figma link with node-id> — <what to change> — images: <source>
```
| Part | Why it matters |
|---|---|
| `Use figma-maintainer:` | Switches the plugin on. Without it, a Figma link alone does nothing (other plugins use Figma links too). Later prompts in the same session keep using it. |
| **Client** (agency or project) | Loads that client's SOP automatically: image source, delivery account, naming, rules. A typo gets a quick "Which client is this for?" with the closest names. |
| **Figma link with `node-id`** | The scope. Only the frame or section in the link is changed, never the rest of the page. Right-click the frame in Figma → Copy link. |
| **What to change** | Paste the client's exact words or email. Say "don't change the copy" when the copy must stay word for word. |
| **Images** | `images: iStock` / `Adobe Stock` / `AI-generated` / `client: <link>` / `@assets/folder/` / `no new images`. Naming it skips the image question. If the client's SOP sets a source, it's used automatically and shown to you. |

### Examples
| You want to… | Prompt |
|---|---|
| Edit copy | `Use figma-maintainer: KHL — <url> — replace the hero text with: "…" — no new images` |
| Apply a client email | `Use figma-maintainer: LSD — <url> — apply this feedback: <paste the email>` |
| Handle a new Figma comment | `Use figma-maintainer: I got a client comment` (no link needed) |
| Apply comments on a frame | `/figma-maintainer:apply-comments <url>` |
| Design an inner page from the homepage | `/figma-maintainer:make-inner-page <homepage url> About — copy: <Google Doc link> — images: iStock` |
| Build an inner page from a layout | `Use figma-maintainer: KHL — <url> — build the About page using the Founding Families layout — images: iStock` |
| Make mobile / tablet | `Use figma-maintainer: <url> — make the mobile version` (or `/figma-maintainer:make-responsive <url> both`) |
| Change a hover or state | `Use figma-maintainer: <url> — make the primary button hover darker using the existing colour styles` |
| Use client photos | `… — use these photos: <Dropbox/Drive link>` or `… — hero: @assets/hero.jpg` |
| Use client copy from a doc | `… — copy is in <Google Doc link>, use it word for word` |
| Audit, no changes | `Use figma-maintainer: Consistency Audit <url>` (also Content / Accessibility Audit) |
| Check against a brief | `/figma-maintainer:check-brief <url>`, then paste the brief |
| Compare two versions | `/figma-maintainer:compare-versions <old url> <new url>` |
| QA a job again, or a designer's manual work | `/figma-maintainer:qa PIPP` or `/figma-maintainer:qa <link> since 2026-10-29 14:00` |
| Slack text / cost | `give me slack message` · `/figma-maintainer:cost-report` (this conversation) · `latest` (last task) |
| Cost history on this Mac | `/figma-maintainer:cost-report-all [since 2026-11-01] [client PIPP] [html]` (only when you ask) |
| Teach it a rule | `figma-maintainer: next time, KHL buttons are always full width in forms` |
| Skip QA once | `skip QA` |

`/figma-maintainer:prompts` shows the full cheat sheet in Claude Code.

### What it will ask you, and why
- **"Which client is this for?"** when the client isn't named or recognised. Pick from the closest matches.
- **"Which image/video source?"** when neither your prompt nor the client SOP says. Answer once; the job starts after that.
- **Approve this plan?** for client comments: Approve, Approve with changes, or Not now. Nothing changes in Figma before you approve.
- **Permission prompts from the guard** for risky edits:
  - deleting layers, editing a main component, a new page or file, variables or styles;
  - **the file changed while the job was running.**

  Check in Figma, then allow or deny.
- **"Font needed: Proxima Soft — Regular, Bold (12 layers)"** when the design uses a font Figma can't load. Install or activate it, then say so, and it continues with the real font. It never substitutes a font. You can choose instead to have a designer type it in the desktop app.
- **Questions in the report** when something is unclear. It never guesses: it finishes the clear parts and asks about the rest.

### Tips
- **Link to the exact frame** (node-id), not the whole file.
- **One page per prompt**, then run an audit.
- **Desktop only** unless you say "mobile" or "tablet". "Should be responsive" in a brief isn't a request for frames.
- **Corrections become rules:** start with `figma-maintainer: next time …`.

### Keep costs down
- **One job per conversation.** When a job is done, start a new conversation or type `/clear`. A long conversation re-reads everything on every message: one two-week conversation cost about $134 on its own. The plugin reminds you after each job.
- **Use Opus or Sonnet for routine work** (`/model opus`). Fable costs 2.5–5× more, and `/figma-maintainer:doctor` warns if it's your default. The plugin picks the model by job weight, whatever your session runs on: the editor on Opus (Sonnet for text-only jobs, Fable for responsive builds and component or state work); analysis, QA and audits on Sonnet; usage on Haiku; and `/figma-maintainer:apply-comments` runs its own steps on Sonnet. Add the word `fast` to that command to run the editor on Sonnet at medium effort whatever the round holds: quicker, with more layout risk for QA to catch.
- **Link the exact frame, one page per prompt.** Small text jobs (up to 3 plain text edits in one frame) automatically get a lighter plan and QA.
- **Built in (nothing to do):** the agents carry only the tools they use (about 25k fewer tokens on every step), load the client SOP as one digest (`job_context.py`), ask job files short questions instead of reading them (`fm_query.py`, `figma_outline.py`), get a short QA summary with all crops on one contact sheet, and a hook asks you before an agent looks at more images than its budget. `scripts/token_bench.py` measures where a task's tokens went (see `docs/benchmarks/`).
- **Check where it goes:** usage lines flag heavy tasks and say why (Fable, many tool calls, very large input). `/figma-maintainer:cost-report` shows this conversation or one task; `/figma-maintainer:cost-report-all` shows your whole history on this Mac (sessions, clients, averages per agent and model mix), only when you ask.

### What it won't do
- **No image editing:** no retouching, no removing objects, no new renders. It adds an annotation instead.
- **No new tablet or mobile frames** unless you ask.
- **Never edits originals** or the frame the client reviewed; it duplicates them first.
- **Never edits main components, styles, variables or library pages** unless you ask.
- **Never substitutes fonts.** A font that won't load is named to you so you can install it.
- **Never resolves, replies to or deletes Figma comments.**

---

## 3. How a job works
1. **Prompt check.** The hook confirms it's a figma-maintainer job, finds the client and its SOP, and settles the image source (asking if needed).
2. **Project folder.** `work/<you>/<agency>/<project>/` is found or created. The agent reads `PROJECT.md` (latest frames, client decisions, open items, rounds already applied) and the last job's report, so it continues where the last job ended.
3. **Inspect.** It takes a screenshot, looks at the structure and takes a **before snapshot** of the page. The snapshot also records the **undo point**: the latest saved Figma version.
4. **Versioning** (agency rule, every client):
   - **Work file or blank frame:** edits it directly.
   - **Current design** (live, approved, or what the client commented on): **duplicates it first** and edits only the copy, named `<Frame> V<n> - <DD Mon YYYY>` and placed below the original.
   - **Not sure:** asks you.
5. **Edit.** Every Figma write passes the **guard**. It blocks writes to files you didn't link, network code and page deletion. It asks you before risky edits, or when someone else changed the file mid-job.
6. **Validate.** It takes screenshots and reads the changes back. An after snapshot shows that nothing outside the target changed. It checks fonts.
7. **Report.** You get the target, the changes, the protected scope, a checklist (anything unchecked is marked UNVERIFIED), the **Undo** line, questions, a **Slack update**, and a **client message** with prototype links.
8. **QA (automatic, enforced).** The `qa-checker` agent checks the work independently (see [QA](#5-qa-check)). If it fails, fixable items go back to figma-maintainer **once**, and QA checks again. If it still fails, the client message is **held** and you decide.
9. **Records and usage.** Everything is saved in the job folder, and `PROJECT.md` is rewritten. A usage line appears: the model, input tokens (uncached, cache write, cache read), output tokens (with reasoning), total, tool calls and minutes.

---

## 4. Client comments

### Found automatically: "I got a client comment"
```
Use figma-maintainer: I got a client comment
/figma-maintainer:client-comment [optional: link, file name or client]
```
1. **Find.** It reads **only Figma's** Mac notifications (read-only): who commented, the file, the text and the time.
   - It matches the file name to the file using your Figma desktop tabs, our SOPs and project folders, and the team's file list.
   - Then it finds the exact comment thread, its page and frame, and the rest of that round.
   - No notification? It scans recent files, or you give the link or file name.
2. **Client.** It comes from our SOPs. For a new file, the Figma project folder suggests the client and you confirm.
3. **Analyse (read-only).** The `client-comments` agent reads the project history, SOPs and frames. It writes `analysis.md` and `plan.md`: each comment, the change, a measurable `Check:` line, the target frame and open questions.
4. **Approve.** Choose Approve, Approve with changes, or Not now.
5. **Apply → QA → records.** figma-maintainer applies the approved plan, and QA checks it. The comments are marked handled so they don't come back.

Every commenter counts as the client: our team doesn't comment on its own designs. To find files you haven't opened recently, the token needs `projects:read` (see [Setup](#9-setup-and-troubleshooting)).

### With a link
```
/figma-maintainer:read-comments <url>     # list them, matched to their layers (read-only)
/figma-maintainer:apply-comments <url>    # apply them
```
**Latest round only, by default.** Comments are rarely marked resolved, so only the newest round is applied: the latest comment date and up to 2 days before it. If older open comments exist, you're asked: latest only, latest plus older since a date, or all. Image-editing requests are annotated, not done. Approvals are recorded. Unclear comments come back as questions.

---

## 5. QA check
**Automatic.** After every figma-maintainer job that changed Figma, `qa-checker` runs before you see the client message, and it's **enforced**:
- a hook marks the job "QA pending";
- the session can't finish its turn until QA has run (it nudges once, then only warns);
- say `skip QA` to waive it for that job.

**What it checks:**
- **Independent:** it starts from the client's comments (or your request) and the approved plan, not from the maker's report.
- **Its own evidence:** `scripts/figma_qa.py` compares the edited copy with its source layer by layer (text, fonts, images, visibility, annotations, interactions, components) and takes a pixel diff with before/after crops. It also checks:
  - that originals and other frames are unchanged;
  - prototype hovers;
  - the links and quoted text in the client message;
  - the job records;
  - edits made by other people.
- **Both ways:** every comment is done as asked, and every change belongs to a comment. Anything extra is flagged.
- **Messages:** the client message may only claim what's true in Figma: right prototype links, no internal details, nothing unverified described as working.

**Verdict:** PASS · PASS WITH NOTES (e.g. "check the hover in Present mode") · FAIL · INCONCLUSIVE. It's saved as `jobs/<job>/qa.md`, with the evidence in `qa/`.

**On demand:** `/figma-maintainer:qa` runs QA on one task, separately.

| Command | Checks |
|---|---|
| `/figma-maintainer:qa` or `latest` | The newest job |
| `/figma-maintainer:qa PIPP` | A job by project or name |
| `/figma-maintainer:qa <old link> <new link>` | The new version against the comments on the old one |
| `/figma-maintainer:qa <link> since 2026-10-29 14:00 check: hero says "…"` | Work done directly in a frame, including a designer's manual work, compared with Figma's saved version from before that time |

Work done by figma-maintainer gets one automatic fix round. Manual work is only reported; you choose what happens next.

---

## 6. Audits and checks (read-only, never change the file)
| Say or run | Checks |
|---|---|
| `Consistency Audit <url>` · `/figma-maintainer:consistency-audit` | Homepage vs inner pages vs design system: header, footer, buttons, forms, cards, type, colours, spacing, grids, responsive frames |
| `Content Audit <url>` · `/figma-maintainer:content-audit` | Spelling, grammar, CTAs, tone, banned words, placeholder text, facts (names, phones, prices) |
| `Accessibility Audit <url>` · `/figma-maintainer:accessibility-audit` | WCAG 2.2 AA: contrast (with passing colours), text size, targets, labels, focus/hover/disabled states, alt-text notes |
| `/figma-maintainer:check-brief <url>` + brief | What matches the client brief and what doesn't |
| `/figma-maintainer:compare-versions <old> <new>` | Every change between two frames |

Ask for several audits at once and they run in parallel. Reports go to the project folder (`audits/`). Fixes happen only when you ask, for example `apply rows 1–5` or `fix all high`.

---

## 7. Images, video and client copy
- **Asked first.** Every client sources media differently. If neither the prompt nor the SOP says, you're asked before anything starts, with the client's usual source marked recommended. This applies to video too.
- **Links:** Dropbox (file or folder), Google Drive file or public folder, OneDrive or SharePoint, or a direct link. `scripts/fetch_assets.py` downloads them, makes Figma-sized copies (4096 px max) and thumbnails, and places the right one in each slot. Private links: it asks for a public link or local files.
- **Local files:** tag them, e.g. `@assets/khl-photos/` or `hero: @assets/hero.jpg`. Originals are never moved or changed.
- **Client copy:** Google Docs (all tabs → Markdown + plain text for word-for-word checks), Sheets (CSV) and Slides (text + PDF) via `scripts/fetch_doc.py`. The file must be shared as "Anyone with the link".
- **Responsive jobs** reuse the desktop's images, so there's no image question.

---

## 8. What you get, and where it's saved

**After every job:**
- **Report:** target, changes, protected scope, checklist, **Undo** line, questions, and a QA hand-off.
- **QA verdict** at the top, and a fix list if anything failed.
- **Slack update (copy-paste):** what changed, the link, and questions for the client. No costs.
- **Client message (copy-paste):**
  - the SOP greeting, if one is set;
  - each page with a short note and its **prototype link**;
  - a Note listing what we still need;
  - "Thank you!".

  It's held if QA failed.
- **Usage (internal):** exact tokens per task and model (no prices, which change), for the team only. Estimated cost appears only in `/figma-maintainer:cost-report-all`.

**Folders** (`~/.claude/figma-maintainer/`, per person):
```
work/<you>/<agency>/<project>/
  PROJECT.md                  living context: files, latest frames + prototype links, decisions, open items, rounds applied, job history
  jobs/<date>-<task>/         request.md, plan.md, analysis.md, report.md, qa.md + qa/, slack.md, client-message.md, comments-applied.md
  snapshots/ comments/ audits/ assets/ reports/ slack/
  job-log.md  figma-calls.jsonl  usage.jsonl
work/<you>/_unassigned/<file-key>/   files whose client isn't known yet
work/<you>/comment-inbox.json         client comments already found and handled
figma-audit-log.jsonl · qa-pending.json · usage-log.jsonl
```
SOPs, the playbook and prices are **links** into the plugin's `knowledge/` folder (see [SOP manager](#11-sop-manager-co-workers-and-releases)).

---

## 9. Setup and troubleshooting

### Requirements
- Claude Code: CLI, desktop app or VS Code extension.
- **Figma access for edits**, one of:
  - the **Figma MCP** in Claude Code: `/plugin install figma@claude-plugins-official`, then sign in to Figma;
  - the **claude.ai connector** (Claude on the web): claude.ai → Settings → Connectors → Figma. It also works in Claude Code with the same claude.ai account.

  Sign in with the team Figma account (Design Studio). It needs **edit access** to the files you'll change.
- **Python 3** (built into macOS). For QA pixel diffs and image downloads: `python3 -m pip install --user pillow`.
- **The team Figma token:** one personal access token for the whole team (Design Studio account), shared privately by the SOP manager. Store it in the macOS Keychain, and never paste it into chat or a Slack channel:
  ```bash
  security add-generic-password -U -s figma-maintainer -a FIGMA_TOKEN -w     # paste the token when asked
  ```
  Scopes:
  - **Required:** File content (read), File metadata (read), Comments (read), File versions (read).
  - **Recommended:** Projects (read), so client comments are found in files you haven't opened recently.
- **Finding comments without a link** needs access to the Mac's notifications: System Settings → Privacy & Security → Full Disk Access → your terminal or VS Code. Only Figma's notifications are ever read.

### Install and update
**Team marketplace (recommended).** The team installs from the private repo `E2M-Design/e2m-figma-marketplace`. That repo holds only the released plugin: no tests, no release tools, no git history of the source.
1. **Access:** the repo belongs to the `E2M-Design` organization. The team's GitHub account `E2M-Design-Team` has **Read** access; ask the SOP manager for its login.
2. **GitHub sign-in on your Mac** with that account: install the GitHub CLI (`brew install gh`, or the installer from cli.github.com), run `gh auth login` in Terminal and answer GitHub.com → HTTPS → **Yes** to "Authenticate Git" → Login with a web browser. Being signed in on github.com in the browser alone isn't enough.
3. **Install:**
   ```
   /plugin marketplace add E2M-Design/e2m-figma-marketplace
   /plugin install figma-maintainer@e2m-figma
   ```
4. **Finish:** restart Claude Code (or `/reload-plugins`), then run `/figma-maintainer:doctor`.

**To update:** when a newer version is live, the plugin asks once at the start of a session (checked at most every 12 hours); choose **Update now**, then `/reload-plugins`. Any time: `/figma-maintainer:about`. By hand: `claude plugin marketplace update e2m-figma` and `claude plugin update figma-maintainer@e2m-figma`, then `/reload-plugins`. What changed in each version is in `CHANGELOG.md`.

**Switching from a zip install:** remove it first, so the agents don't load twice:
- **Uploaded zip:** Customize → Plugins → remove figma-maintainer.
- **Folder install:** `/plugin marketplace remove e2m-figma`.

**Fallback without GitHub: the zip.** Use it exactly as shared; re-zipping in Finder breaks uploads.
- **Install:** upload it under Customize → Plugins → Add → Upload plugin. It syncs into Claude Code at the next session start.
- **Update:** upload the new zip.
- **Where it runs:** Claude Code only. Regular Chat ignores plugin agents and hooks.

SOPs update with every version; your work folders are untouched.

### When something's wrong
Run **`/figma-maintainer:doctor`** first. It checks:
- Python and the image library;
- the session folder links;
- the token and every scope;
- notifications and desktop tabs;
- the INR rate;
- the plugin version and that it's enabled;
- jobs waiting for QA;
- the Figma connector account.

| Symptom | Fix |
|---|---|
| No image question, no guard, no usage line | The session predates the install or update: restart or `/reload-plugins` |
| "File … was not linked in this task" | Put the Figma link (with node-id) in your prompt |
| "Looks like you don't have edit access" | Connect the Figma MCP or connector with the team account (Design Studio), or share the file with edit access to the account the doctor shows |
| "the token lacks the scope …" | The SOP manager updates the team token with that scope and shares it; store it again with the Keychain command above |
| A client comment isn't found | Give the file name or link, or add `projects:read` to the token |
| Usage shows no INR | The SOP manager sets `fx.INR` in `knowledge/cost-config.json` |
| QA keeps asking to run | Let it run, or say `skip QA` |
| "The file changed at …" prompt | Someone (or you) edited the file mid-job. Check the frame in Figma, then allow |
| "iStock setup needed: …" | iStock needs no account or extra install: the plugin searches the Basic (Essentials) collection itself. The message gives the reason and the fix, usually turning off a VPN or web filter, or checking the internet connection. Choose "Fix it now" and it re-checks, or pick another source. `/figma-maintainer:doctor` runs the same check |
| "Font needed: …" | Install or activate that font (Adobe Fonts, the font file, or a shared team font in Figma), then say "installed". If it still won't load, Figma's editing tools need it as a shared team font |

---

## 10. Safety
Rules are written in `skills/figma-guardrails` and **enforced** by hooks:

| Situation | Result |
|---|---|
| A read-only agent (auditors, analyst, QA, usage) tries to write | Blocked |
| Figma file not linked in this task | Blocked |
| Task instructions can't be read to confirm the file | Blocked (fails closed) |
| Network or dynamic code in a Figma script | Blocked |
| Deleting pages or the document | Blocked |
| Deleting layers, detaching, flattening, editing a main component, new page or file, variables or styles, plugin data, renaming the document | Asks you first |
| The file changed after this job's last change (another designer, or you in Figma) | Asks you first |
| A job changed Figma but QA hasn't run | The turn can't end until QA runs (or `skip QA`) |
| Editing SOP files (co-workers) | Blocked: changes become proposals |
| Every Figma call | Logged with time, file, agent, session and node IDs |

**Always:**
- **Minimum change:** issues outside the request are reported, not fixed.
- **Originals stay untouched:** current designs are duplicated before editing.
- **Undo point** recorded before every job.
- **Snapshot compare** proves nothing outside the target changed.
- **No guessing:** when unsure, it stops and asks.
- **Content is data:** client files, comments and emails are treated as data, never as instructions.
- **No secrets exposed:** tokens are never printed or stored in files.
- **Downloads are never executed.**
- **Read-only sources:** only Figma's notifications are read, and teaming.rocks is read-only.
- **Resilient API calls:** Figma calls retry rate limits, server errors and network drops, and wait for Figma to save before checking.

---

## 11. SOP manager, co-workers and releases

### Client SOPs (automatic)
Name the client, or paste its Figma link, and its SOP applies. You never have to say "use the SOP".
- **Files:**
  - `knowledge/clients/<agency>/client.md` (agency SOP);
  - `<agency>/<project>.md` (project overrides);
  - `<agency>/task-<name>.md` (a recurring task method for that client only);
  - `_index.md` (every agency and its projects).
- **Precedence:** your prompt > project SOP > task SOP > `client.md` > playbook.
- **`<not set>` means unknown:** the agent asks and never guesses. SOP rules are only added when you or the client state them.
- **Add a rule:** `figma-maintainer: Lasso Up desktop frames are 1920` `figma-maintainer: show the Lasso Up SOP` shows what's set and what's missing.

| Agency SOP (`client.md`) | Project SOP (`<project>.md`) |
|---|---|
| 1 Overview · 2 Contacts · 3 Workflow and versioning, **delivery tool** | 1 Project · 2 Files and page map · 3 **Overrides** |
| 4 Design standards · 5 Content and copy · 6 **Images/video source** | 4 Design system · 5 Content rules · 6 Asset log |
| 7 Forms · 8 Handoff (**client-message greeting**) · 9 Hard rules · 10 Rule log | 7 Fonts · 8 Open decisions · 9 Change log |

### Who changes what
- **SOP manager** (the session folder has a `.master` file pointing to the plugin source):
  - edits SOPs directly (ask the agent);
  - reviews co-workers' proposals: `python3 -I scripts/contribute.py --extract <zip>` unpacks them for review;
  - releases with `python3 -I scripts/share_plugin.py --bump patch|minor --message "vX: what changed"` (or ask Claude to release). It adds the version to `CHANGELOG.md` if missing, runs the release check, commits, bumps the version, makes an annotated tag, and writes `~/ClaudeAI/Figma-maintainer.zip` from exactly that tagged version. It then refreshes the team marketplace repo with the same build (set by the `marketplace:` line in `.master`), then commits and tags it there.
    - Paths marked `export-ignore` in `.gitattributes` (tests, release tools, the management briefing) never reach the team.
    - It doesn't push: run `git push origin main --tags` in both repos. It doesn't touch your own plugin install either (`/reload-plugins` picks up changes).
- **Co-workers:** SOPs are read-only. New rules or corrections become proposals in `~/.claude/figma-maintainer/contributions/`. `python3 -I ~/.claude/figma-maintainer/scripts/contribute.py --pack` zips them for the SOP manager.

### Release check (before every version)
```bash
bash scripts/release_check.sh
```
It compiles every script with this Mac's Python, runs the offline test suite in `tests/` (no Figma, no token), checks the JSON files and validates the plugin. Tag a version only when it prints **RELEASE CHECK PASSED**. `tests/prompts.json` holds real prompts, including every one the plugin once misrouted: **add a case whenever routing gets something wrong.**

### Task types vs client task configurations
| Task type (any client) | Generic action | Client configurations |
|---|---|---|
| Tablet and mobile from desktop | `/figma-maintainer:make-responsive` | `digital-drive/task-responsive-designs.md` |
| Inner page from the homepage | `/figma-maintainer:make-inner-page` | none yet (`<agency>/task-inner-pages.md` overrides the defaults) |
| Client comments | `/figma-maintainer:client-comment` (finds them) · `:apply-comments` (with a link) | none yet |
| Audits | `/figma-maintainer:*-audit` | none yet |
| Brief check, version compare | `:check-brief`, `:compare-versions` | none yet |

A client's `task-<name>.md` applies **only to that client**. **Scope is always the frame or section in the link**, never the whole page.

---

## 12. All commands
| Command | What it does |
|---|---|
| `/figma-maintainer:prompts [topic]` | Prompt cheat sheet |
| `/figma-maintainer:doctor` | Check this Mac's setup and say how to fix each problem |
| `/figma-maintainer:client-comment [link\|file\|client]` | Find a new client comment, plan, ask to approve, apply, QA |
| `/figma-maintainer:read-comments <url>` | List the comments on a frame, matched to their layers |
| `/figma-maintainer:apply-comments <url>` | Apply the comments on a frame (latest round) |
| `/figma-maintainer:qa [latest\|job\|links] [since …] [check: …]` | QA one task on its own, including manual work |
| `/figma-maintainer:make-responsive <url> [mobile\|tablet\|both]` | Mobile and tablet versions of a desktop frame |
| `/figma-maintainer:make-inner-page <homepage url> <page> [— copy: …] [— images: …]` | A new desktop inner page in the homepage's exact style, next to the homepage |
| `/figma-maintainer:components-and-interactions` | Guide for hover, variant and prototype changes |
| `/figma-maintainer:consistency-audit <url>` | Read-only consistency audit |
| `/figma-maintainer:content-audit <url>` | Read-only copy audit |
| `/figma-maintainer:accessibility-audit <url>` | Read-only WCAG 2.2 AA audit |
| `/figma-maintainer:check-brief <url>` + brief | Page vs client brief |
| `/figma-maintainer:compare-versions <old> <new>` | Every change between two frames |
| `/figma-maintainer:client-message [notes]` | Write the client message for the work done |
| `/figma-maintainer:slack [task]` | Slack update plus an internal usage block |
| `/figma-maintainer:cost-report [latest\|"task"\|html]` | Tokens and cost of this conversation or one task |
| `/figma-maintainer:cost-report-all [since …] [client …] [html]` | Consolidated cost history on this Mac (only when asked) |
| `/figma-maintainer:about` | Version, release date, what it can do, what's new; offers an update when one is live |
