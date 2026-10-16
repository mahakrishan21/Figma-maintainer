# figma-maintainer (Claude Code plugin)

A Claude Code subagent that works like a senior UI/UX designer making maintenance changes directly in Figma: copy edits, form and field changes, image and video swaps, inner pages built from existing patterns, client-feedback rounds and design audits. It follows each client's SOP notes and remembers your corrections.

## Before you install
- Claude Code (CLI, desktop app or VS Code extension).
- A Figma connection. Use either:
  - the claude.ai Figma connector (claude.ai → Settings → Connectors → Figma), or
  - the official Figma plugin: `/plugin install figma@claude-plugins-official`
- Edit access to the Figma files you want it to change.
- Python 3 (built into macOS), for reading comments and fetching iStock placeholders.
- To read Figma comments: a Figma personal access token. In Figma, open Settings → Security → Personal access tokens, then create one with read access to **File content** and **Comments**. Add it to your shell profile, and never paste it into chat:
  ```bash
  echo 'export FIGMA_TOKEN=your-token-here' >> ~/.zshrc
  ```

## Install
> **Hooks load when a session starts.** After installing or updating, restart Claude Code (or reload the VS Code window). Until you do, the guard, the image question and usage logging aren't active.

1. Unzip `figma-maintainer-plugin.zip` somewhere permanent, for example `~/ClaudeAI/figma-maintainer-plugin`. Claude Code installs from this folder, so don't delete or move it afterwards.
2. In Claude Code, run:

```
/plugin marketplace add ~/ClaudeAI/figma-maintainer-plugin
/plugin install figma-maintainer@e2m-figma
```

3. Restart Claude Code, or open a new session.

## Where things live
**The plugin is the single source of truth.** Every client SOP, task SOP, project note, the playbook and the system files ship inside it, in `knowledge/`. One **SOP manager** maintains them in git and shares new plugin versions. Co-workers get every new and updated SOP just by updating the plugin. There's no separate SOP sync.

| Location | Holds |
|---|---|
| `knowledge/clients/` | `_index.md` (every agency and its projects), `<agency>/client.md` (agency SOP), `<agency>/task-*.md` (recurring task SOPs), `<agency>/<project>.md` (project notes), and `_template/` (client, project, task and contribution templates) |
| `knowledge/playbook.md` · `pricing.json` · `cost-config.json` | Team-wide Figma rules, model prices, currency settings |
| `agents/` `commands/` `skills/` `scripts/` `hooks/` | The plugin itself |
| `~/.claude/figma-maintainer/` (per person, never shared) | **Session files**, plus **links** (`clients/`, `playbook.md`…) into the plugin's `knowledge/`, created at each session start |
| `~/.claude/figma-maintainer/work/<person>/<agency>/<project>/` | **All work for one project:** `job-log.md`, `snapshots/`, `comments/`, `audits/`, `reports/`, `assets/` (downloads), `slack/`, `figma-calls.jsonl`, `usage.jsonl`. Created automatically the first time you work on that project; reused afterwards |

## When it's active (isolation from other plugins)
figma-maintainer only acts on **Figma maintenance work**. Its hooks stay silent in website builds, other plugins' sessions and general chat. It's active when:
- your prompt names it (`Use figma-maintainer: …`, "figma maintainer") or uses a `/figma-maintainer:` command;
- the session has already used a figma-maintainer agent or command (so "give me slack message" or "Consistency Audit" work later in the same session);

It runs only when you name it in your prompt ("Use figma-maintainer: …") or run a `/figma-maintainer:` command; after that, follow-ups in the same session keep using it. Having the plugin installed and enabled is not enough. A Figma link or an audit request on its own doesn't activate it, because other plugins (like the website generator's Figma import) use Figma links too. Its skills and commands can't be picked automatically by Claude, only by you or by its own agents. The Figma write guard and usage logging cover only figma-maintainer agents and sessions.

## Using it
In any Claude Code session:

```
Use figma-maintainer: <figma URL> — <what to change>
```

Examples:
- `Use figma-maintainer: <url> — apply the client feedback below: …`
- `Use figma-maintainer: <url> — build the About inner page using the Founding Families layout`
- `Use figma-maintainer: <url> — audit only, don't change anything`
- `Use figma-maintainer: <url> — duplicate the latest section as a new version, then …`

### Mobile and tablet versions
**Desktop only by default.** Tablet and mobile frames are created only when your prompt explicitly asks for them ("make the mobile version", "desktop + mobile"). "Should be responsive" in a brief doesn't create them; the agent offers them at the end instead.

```
/figma-maintainer:make-responsive <desktop frame URL> [mobile | tablet | both]
```
Or `Use figma-maintainer: <url> — make the mobile and tablet versions`. It follows the team standard in `skills/responsive-from-desktop`:
- The desktop is the source of truth, and it's never changed.
- Mobile is 390, tablet is 768, and frames are placed to the right of the desktop.
- It reuses the file's styles, components and images, and uses Auto Layout.
- It checks for overflow, overlap, alignment and wrapping afterwards.

Responsive jobs reuse the desktop's images, so the image question is skipped unless you ask for new images.

### Component, state and interaction changes
For changes like "the button hover should be darker", "make the dropdown open on click" or "add a disabled state", it reads `skills/components-and-interactions` first. It:
- maps the component's variants, properties and prototype reactions;
- counts how many copies of the component the change would affect, and asks whether to change the component everywhere or only these copies when that's unclear;
- uses the file's existing colour and style tokens, keeps the variant grid complete, and never detaches a copy from its component;
- reports the before → after for each state and what to click through in Present mode.

You can also use it on its own: `/figma-maintainer:components-and-interactions`.

### Consistency Audit (read-only)
Say **"Consistency Audit"**, with a Figma link or after working on a page, or run:
```
/figma-maintainer:consistency-audit <figma URL> [all pages | this page | homepage only]
```
A separate agent, `consistency-auditor`, compares the homepage, the inner pages and the design system, and **never changes the file**. It checks:
- **Shared elements:** header, nav and mega menu, footer, buttons, forms, cards and icons.
- **Styles:** type, colours, spacing, radius, shadows and image treatment.
- **Layout:** container widths, grids and alignment, plus mobile and tablet frames when they exist.
- **Design system:** whether text styles, colour styles, variables and components are reused, rather than duplicated or hard-coded.

`scripts/figma_audit.py` collects the evidence through Figma's web API (it needs `FIGMA_TOKEN`). The agent then checks each item visually and leaves out intentional, page-specific differences.

You get a page-by-page report with the element, its current variation, the expected standard, and the recommended correction. It's saved to `~/.claude/figma-maintainer/audits/`. Fixes happen only if you then ask figma-maintainer to apply them. figma-maintainer also offers an audit after it finishes a page.

### Client images and video from your project folder
Already downloaded them? Put them in the project folder and tag them in your request:
```
Use figma-maintainer: <figma URL> — use @assets/khl-photos/ for the hero and "Why Join" images
Use figma-maintainer: <figma URL> — hero: @assets/hero.jpg, about: @assets/team.jpg
```
Tagged files and folders (searched inside, subfolders included) count as the image source, so there's no question. Your originals are never moved or changed; it works from resized copies. Name a slot next to a file and it uses that file there.

### Client images and video from links
Paste a Dropbox (file or folder), Google Drive file, OneDrive or SharePoint, or direct link in your request. That counts as the image source, so there's no question. The agent downloads the files (`scripts/fetch_assets.py`), makes Figma-sized copies (Figma's limit is 4096px) and thumbnails, looks through them, and places the right one in each slot.
- **Google Drive folders:** use the Google Drive connector.
- **WeTransfer, Box or private links:** it asks for a public link or a local file instead.

### Slack update after every job
Every job and audit ends with a short **Slack update (copy-paste)** block:
- what changed, as bullets
- the **Updated: <link>**
- **Questions for client:** images or video still needed, missing fonts, missing content or links, decisions

### Content Audit and Accessibility Audit (read-only)
Say **"Content Audit"** or **"Accessibility Audit"** (or "proofread", "WCAG check"), or run `/figma-maintainer:content-audit <url>` or `/figma-maintainer:accessibility-audit <url>`. Like the Consistency Audit, they never change the file.
- **Content:** spelling, grammar, punctuation, capitalisation, CTA wording, tone and client copy rules, banned words, placeholder text, and facts that must match (names, phone numbers, years, prices). Uses `scripts/figma_content.py`.
- **Accessibility (WCAG 2.2 AA):** contrast with passing alternative colours, text size, tap and click targets, form labels, focus, hover and disabled states, colour-only meaning, text over images, and alt-text and annotation notes for developers. Uses `scripts/figma_a11y.py`.

You can ask for several audits at once, for example "Consistency Audit and Accessibility Audit"; they run in parallel. Reports are saved to `~/.claude/figma-maintainer/audits/`.

### Token usage and cost (USD + INR)
Built from the design-cost-report kit. The counting is done by script from Claude Code's own logs, so it costs no tokens.
- **Automatic:** when any agent task finishes, a usage line appears, for example "KHL — Design KHL Referral page — 255K tokens (+10.1M cached), $3.35, 23 min, 74 tool calls". It's also added to `~/.claude/figma-maintainer/usage-log.jsonl`.
- **"give me slack message":** you get the Slack update, then a separate **Usage (internal)** block for the session. Token and cost numbers never go in the client-facing message.
- **Ask** "how many tokens" or "cost report", or run `/figma-maintainer:cost-report [latest | session | client KHL since 2026-10-01 | html]`. The `usage-reporter` agent (Haiku) answers. HTML reports are only made when you ask.
- **Settings:**
  - `~/.claude/figma-maintainer/pricing.json`: USD per million tokens, from the kit. Check it against Anthropic's pricing page.
  - `~/.claude/figma-maintainer/cost-config.json`: currencies and your INR rate (`"fx": {"INR": 84.0}`). The rate is never guessed.
- "New tokens" means input, cache writes and output. Cached reads are shown separately, because they're cheap re-reads of context. On a Pro or Max plan, the cost is the equivalent API value, not a charge.

### Client comments in Figma
```
/figma-maintainer:read-comments <figma URL>     # list the comments on that frame (read-only)
/figma-maintainer:apply-comments <figma URL>    # apply them
```
You can also just say `Use figma-maintainer: apply the comments on <url>`.

It reads every unresolved comment pinned to the frame (add `--all-frames` for the whole file) and matches each one to the text or image it points at. Then it:
- applies copy and layout changes in a new version frame when the file works in versions, leaving the commented frame untouched;
- doesn't do image editing (retouching, removing objects, new renders, mockups that need screenshots the file doesn't have), and annotates it on the image instead;
- records approvals ("I like this") in the client notes;
- lists anything unclear as a question.

It reports every comment by number. It never resolves, replies to or deletes comments.

To correct it, just say so, for example `figma-maintainer: next time, KHL buttons are always full width in forms.` It applies the fix and saves it as a rule.

## Client SOPs (automatic)
Name the agency or project in your prompt, or paste its Figma link, and the agent follows that client's SOP. You never have to say "use the SOP".
- **Example:** "Lasso up – update Meeks Electrical homepage" follows `clients/lasso-up/client.md`, which says Adobe Stock, always. Images come from Adobe Stock with no question.
- **Precedence:** your prompt, then the project file, then the agency's `client.md`, then the playbook.
- **When the SOP has no image source**, the agent asks, with iStock as the suggested default (most agencies use it).
- **SOPs are never invented.** Rules are added only when you or the client state them, for example "figma-maintainer: Lasso Up always uses Adobe Stock".

### SOP format
Every agency has `clients/<agency>/client.md`, and every project has a `<project>.md` with the same structure (templates in `clients/_template/`).

| Agency SOP (`client.md`) | Project SOP (`<project>.md`) |
|---|---|
| 1. Overview: teaming name, service lines, team | 1. Project: brand, live site, phase |
| 2. Contacts and communication | 2. Files and page map, approved originals |
| 3. Workflow and versioning | 3. **Overrides** of the agency SOP |
| 4. Design standards: width, breakpoints, fonts, accessibility | 4. Design system: colours, type, components |
| 5. Content and copy: source, tone, case, CTAs, banned words | 5. Content rules, confirmed form fields |
| 6. Images and video: **source**, licence, AI, people rules | 6. Asset log |
| 7. Forms and functionality | 7. Fonts |
| 8. Handoff and reporting | 8. Open decisions |
| 9. Hard rules (always / never) | 9. Change log |
| 10. Rule log (date, rule, source) | |

- **Task SOPs** (`clients/<agency>/task-<name>.md`) hold a reusable method for a recurring task type, for example `digital-drive/task-responsive-designs.md`. They apply to every project of that agency and list each job under "Jobs". Template: `clients/_template/task.md`.
- `<not set>` means unknown: the agent asks, and never guesses.
- Fill one in by saying it, for example `figma-maintainer: Lasso Up desktop frames are 1920`, or with `/figma-maintainer:sop Lasso up — desktop width 1920`.
- `/figma-maintainer:sop <name>` on its own shows what's set and what's missing.

## Security guardrails
`skills/figma-guardrails` holds the written rules. `scripts/figma_guard.py` **enforces** them on every Figma write:
| Check | Result |
|---|---|
| Write by an auditor or usage-reporter | Blocked |
| Figma file not linked in this task (your recent messages or the agent's brief) | Blocked |
| Task instructions can't be read to confirm the file | Blocked (fails closed) |
| Network or dynamic code in a Figma script (fetch, XHR, eval…) | Blocked |
| Deleting pages or the document | Blocked |
| Any node deletion, detaching instances, flattening, editing a main component, new Figma file or page, variable or style edits, plugin data, renaming the document | Asks you first |
| Every allowed write | Logged to `~/.claude/figma-maintainer/figma-audit-log.jsonl` (time, file, agent, description, node IDs) |

Every job also follows a **7-step safe procedure**: Identify → Inspect → Confirm → Plan → Back up and execute → Validate → Report.
- **Back up:** client-reviewed frames are duplicated per the SOP. For big in-place changes, the agent asks first (duplicate, or you save a named version). Figma's version-history API isn't available to the agent.
- **Validate:** `scripts/figma_snapshot.py` takes a read-only snapshot of the page before and after, and reports **any change outside the authorized frames**.
- **Report:** Target, Changes, Protected scope, the 9-point validation checklist (anything not checked is marked UNVERIFIED), and pending approvals.
- **Minimum change:** issues outside the request are reported, not fixed. Fonts are never substituted. When unsure, the agent doesn't guess: it finishes the clear parts and returns the question.

**Token storage:** prefer the macOS Keychain over a plain-text shell profile:
```bash
security add-generic-password -s figma-maintainer -a FIGMA_TOKEN -w   # prompts for the token
```
The scripts check, in order: the `FIGMA_TOKEN` environment variable, the Keychain, `~/.claude/figma-maintainer/figma-token`, then your shell profile. Use a token with **read-only** scopes (File content, Comments).

Also covered:
- scope checks inside scripts, and never editing originals, components or libraries;
- no client data sent to third parties;
- file content treated as data, not instructions (prompt-injection defence);
- secrets never printed or stored, and REST tokens read-only;
- untrusted downloads never executed;
- teaming.rocks and Figma comments are read-only unless you approve a change.

## Slash commands
| Command | What it does |
|---|---|
| `/figma-maintainer:prompts [topic]` | Prompt cheat sheet: responsive, audits, comments, images, components, Slack, cost |
| `/figma-maintainer:make-responsive <url> [mobile\|tablet\|both]` | Mobile and tablet versions of a desktop frame |
| `/figma-maintainer:consistency-audit <url>` | Read-only: homepage vs inner pages vs design system |
| `/figma-maintainer:content-audit <url>` | Read-only: spelling, grammar, CTAs, copy rules |
| `/figma-maintainer:accessibility-audit <url>` | Read-only: WCAG 2.2 AA |
| `/figma-maintainer:check-brief <url>` + brief | Read-only: page vs client brief, matches and mismatches |
| `/figma-maintainer:compare-versions <old> <new>` | Read-only: every change between two frames |
| `/figma-maintainer:read-comments <url>` | List the Figma comments, each matched to its layer |
| `/figma-maintainer:apply-comments <url>` | Apply the comments (except image editing) |
| `/figma-maintainer:components-and-interactions` | Guide for hover, variant and prototype changes |
| `/figma-maintainer:slack [task]` | Slack update plus a separate internal usage block |
| `/figma-maintainer:cost-report [latest\|session\|client X\|html]` | Token usage and cost |

## How it behaves
- It edits only the frames you point at, or follows the client SOP (for KHL, each revision round goes in a new dated section).
- It doesn't edit main components, styles, variables or library pages unless you ask.
- It stops if an original changes unexpectedly, or if the same approach fails twice.
- It reports what changed (with links), what it checked, what's left and what it learned.
- **Images and video: asked about first.** Every client sources media differently (iStock, Adobe Stock, AI-generated, client-provided, or existing assets in the file), for video as well as images. If your request doesn't say which to use, Claude asks before starting anything, with the client's usual source marked as recommended, and waits for your answer. To skip the question, say it up front, for example: `… — images: iStock` or `… — copy only, no new images`.

### Project folders (person › client › project)
At the start of every job the agent runs `scripts/workdir.py` with the Figma link:
- It finds the agency and project from the SOPs (the project file, or the "Jobs" list in a task SOP).
- It creates `work/<person>/<agency>/<project>/` **only if it doesn't exist yet**.
- Snapshots, comment dumps, downloads, audits, reports and Slack text for that job are stored there, along with the project's job log.
- The Figma call log and usage log also get a per-project copy.

Files the SOPs don't know yet go to `work/<person>/_unassigned/<file-key>/`. The person's name is in `~/.claude/figma-maintainer/.person`, taken from your git name on first run; edit it if you like. `~/.claude/figma-maintainer/job-log.md` is a one-line-per-job index pointing to the project folders.

## SOP manager and co-workers
**SOP manager** (one person; their session folder has a `.master` file pointing to the plugin source):
- Adds and updates SOPs directly in the plugin, either by asking the agent or with `/figma-maintainer:sop <client> — <rule>`. Edits land in `knowledge/` in the plugin source.
- Shares with `/figma-maintainer:share`, which commits, bumps the version, tags it, updates their own install and writes `~/ClaudeAI/figma-maintainer-plugin.zip`.
- Reviews co-workers' proposals with `/figma-maintainer:review-contributions <zip>`, applies the approved ones, then shares again.

**Co-workers:**
- **Install or update** from the zip, then restart. All SOPs come with it.
- **SOPs are read-only for them.** A guard blocks edits to SOP files.
- **When they learn something new** (a client requirement, a correction, a workflow improvement), the agent writes it as a proposal in `~/.claude/figma-maintainer/contributions/`. `/figma-maintainer:contribute` packs those into a zip to send to the SOP manager.

## Updating
When you get a new zip, unzip it over the same folder, run `/plugin marketplace update e2m-figma`, and restart Claude Code. The new SOPs are live immediately; your session files are untouched.

## Task types (reusable actions) vs client task configurations
| Task type (works for any client) | Generic action | Client configurations |
|---|---|---|
| Create Tablet and Mobile Designs from Desktop Designs | `responsive-from-desktop` skill · `/figma-maintainer:make-responsive` | `digital-drive/task-responsive-designs.md` (Digital Drive only) |
| Apply client comments | `/figma-maintainer:apply-comments` | none yet |
| Consistency / Content / Accessibility Audit | `/figma-maintainer:*-audit` | none yet |
| Check against brief, compare versions | `/figma-maintainer:check-brief`, `:compare-versions` | none yet |

- A client's `task-<name>.md` applies **only to that client**. For other clients, the generic action runs with their own SOP.
- **Scope is always the frame or section in the link (node-id)**, never the whole page it sits on.
