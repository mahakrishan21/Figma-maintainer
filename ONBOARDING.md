# Figma-maintainer: getting started (E2M design team)

Figma-maintainer is our Claude Code plugin for Figma maintenance work. It handles:
- copy and form changes, image swaps, inner pages, mobile and tablet versions, hover and state changes;
- client-comment rounds;
- consistency, content and accessibility audits.

It follows each agency's SOP automatically. Every finished job gets an independent QA check, a Slack update and a ready-to-send client message.

**About 15 minutes to set up, once.** After that, you just ask in plain words.

## 1. Install (once)
Get `Figma-maintainer.zip` from the SOP manager (Mahakrishan). **Use the zip exactly as you received it: don't unzip it and zip it again** (that breaks the upload). Then choose one route:

**A) Upload it in the Claude app (easiest)**
1. In the Claude app or claude.ai: **Customize → Plugins → Add → Upload plugin**, then choose `Figma-maintainer.zip`.
2. Open **Claude Code** (the desktop app's Code tab, VS Code or terminal), signed in with the same Claude account. The plugin syncs at the start of the next session (or run `/reload-plugins`).
3. Use it in **Claude Code**. In regular Chat its agents and safety checks don't run.

**B) Install from a folder**
1. Double-click the zip. Your Mac makes a `Figma-maintainer` folder. Move it into `~/ClaudeAI/`, so it's `~/ClaudeAI/Figma-maintainer`, and keep it there.
2. In Claude Code, run:
   ```
   /plugin marketplace add ~/ClaudeAI/Figma-maintainer
   /plugin install figma-maintainer@e2m-figma
   ```
3. Restart Claude Code.

## 2. Connect Figma (once)
**a) Figma access for edits.** Choose one, and sign in with our team Figma account (Design Studio):
- **Figma MCP in Claude Code** (desktop app, VS Code or terminal): run `/plugin install figma@claude-plugins-official`, restart Claude Code, and sign in to Figma when it asks.
- **claude.ai connector** (if you use Claude on the web): claude.ai → Settings → Connectors → Figma → Connect. It also works in Claude Code when you're signed in with the same claude.ai account.

You only need one of the two.

**b) The team Figma token**, for reading comments and checking work. **Everyone uses the same token.** Ask the SOP manager for it in a private message, and never post it in a Slack channel or paste it into chat. Store it in your Mac's Keychain: run this in Terminal and paste the token when asked.
```bash
security add-generic-password -U -s figma-maintainer -a FIGMA_TOKEN -w
```
If the team token is ever replaced, the SOP manager sends the new one: run the same command again.

- **Optional but recommended:**
  - `python3 -m pip install --user pillow`, used for QA's before/after image comparisons;
  - System Settings → Privacy & Security → **Full Disk Access** for Claude Code / VS Code / Terminal, so it can find new client comments from Figma's notifications without a link. Only Figma's notifications are read.

## 3. Check your setup
```
/figma-maintainer:doctor
```
It checks everything above and tells you exactly what to fix. When it says **"Setup is ready."**, you're done.

## 4. How to ask
One line:
```
Use figma-maintainer: <client> — <Figma link to the frame> — <what to change> — images: <source>
```
- **Start with `Use figma-maintainer:`.** A Figma link on its own doesn't switch the plugin on.
- **Name the client** (agency or project). Its SOP loads automatically: image source, delivery account, rules.
- **Link the exact frame** (right-click the frame in Figma → Copy link). Only that frame changes.
- **Say the image source** if you know it: `images: iStock` / `Adobe Stock` / `client: <link>` / `no new images`. Otherwise it asks.

Examples:
```
Use figma-maintainer: KHL — <frame link> — replace the hero heading with "…" — no new images
Use figma-maintainer: LSD — <frame link> — apply this client feedback, copy word for word: <paste email>
Use figma-maintainer: I got a client comment
Use figma-maintainer: <desktop frame link> — make the mobile and tablet versions
Use figma-maintainer: Consistency Audit <frame link>
```
More examples: `/figma-maintainer:prompts`.

## 5. What to expect
- **Questions first, never guesses:** which client, which image source, or "Approve this plan?" for client comments. Nothing changes in Figma before you approve.
- **Originals are never edited:** a current design is duplicated as `<Frame> V<n> - <date>` and only the copy changes.
- **Permission prompts** before risky edits (deleting layers, shared components, styles), or when someone else changed the file mid-job. Check in Figma, then allow or deny.
- **"Font needed: <font>"** when the design uses a font Figma can't load. Install or activate it (e.g. Adobe Fonts), say "installed", and it continues with the real font. It never substitutes a font.
- **QA runs automatically** after every job that changed Figma. The verdict appears at the top of the report. If QA fails, the client message is held until it's fixed. Say `skip QA` only when you really mean to.
- **Every job ends with:**
  - the report, including an **Undo** line;
  - a **Slack update** and a **client message** (with prototype links), ready to copy;
  - an internal usage line (time and cost).
- **Your work is saved** in `~/.claude/figma-maintainer/work/<you>/<agency>/<project>/`, one folder per job, plus a `PROJECT.md` that remembers the project for next time.

## 6. Rules and corrections
- **SOPs are read-only for you.** They're maintained centrally, so everyone gets the same rules.
- **Teach it something**, e.g. `figma-maintainer: next time, KHL buttons are full width in forms`. Your note becomes a proposal.
- **Send proposals** with `/figma-maintainer:contribute`, which makes a zip, to the SOP manager. Approved rules reach everyone in the next version.

## 7. Updates
When you get a new zip:
- **Route A:** upload the new zip the same way (Customize → Plugins → Upload plugin) and replace the old figma-maintainer if asked. Then restart Claude Code or run `/reload-plugins`.
- **Route B:** double-click it, replace `~/ClaudeAI/Figma-maintainer` with the new `Figma-maintainer` folder, run `/plugin marketplace update e2m-figma`, and restart Claude Code.

Then run `/figma-maintainer:doctor`. Your work folders aren't touched.

## Help
- **`/figma-maintainer:doctor`:** setup problems.
- **`/figma-maintainer:prompts`:** the prompt cheat sheet.
- **`docs/figma-maintainer-guide.html`** in the plugin folder: the full visual guide (open it in a browser).
- **`README.md`:** the complete reference.
- **Ask the SOP manager** for anything else.
