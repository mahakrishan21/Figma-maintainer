# Figma-maintainer: getting started (E2M design team)

Figma-maintainer is our Claude Code plugin for Figma maintenance work. It handles:
- copy and form changes, image swaps, inner pages, mobile and tablet versions, hover and state changes;
- client-comment rounds;
- consistency, content and accessibility audits.

It follows each agency's SOP automatically. Every finished job gets an independent QA check, a Slack update and a ready-to-send client message.

**About 15 minutes to set up, once.** After that, you just ask in plain words.

## 1. Install (once)
1. Get `Figma-maintainer.zip` from the SOP manager (Mahakrishan) and unzip it to `~/ClaudeAI/Figma-maintainer`. Keep that folder: Claude Code runs the plugin from it.
2. In Claude Code (desktop app, VS Code or terminal), run:
   ```
   /plugin marketplace add ~/ClaudeAI/Figma-maintainer
   /plugin install figma-maintainer@e2m-figma
   ```
3. Restart Claude Code.

## 2. Connect Figma (once)
- **Figma connector:** claude.ai → Settings → Connectors → Figma. Sign in with the account that has edit access to our client files.
- **Figma token**, for reading comments and checking work. Ask the SOP manager for it privately, or create one in Figma → Settings → Security → Personal access tokens.
  - **Scopes:** File content, File metadata, Comments, File versions and Projects, all *read*.
  - **Store it in your Mac's Keychain.** Run this in Terminal and paste the token when asked. **Never paste it into chat or Slack.**
    ```bash
    security add-generic-password -U -s figma-maintainer -a FIGMA_TOKEN -w
    ```
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
1. unzip it over `~/ClaudeAI/Figma-maintainer`;
2. run `/plugin marketplace update e2m-figma`;
3. restart Claude Code;
4. run `/figma-maintainer:doctor`.

Your work folders aren't touched.

## Help
- **`/figma-maintainer:doctor`:** setup problems.
- **`/figma-maintainer:prompts`:** the prompt cheat sheet.
- **`docs/figma-maintainer-guide.html`** in the plugin folder: the full visual guide (open it in a browser).
- **`README.md`:** the complete reference.
- **Ask the SOP manager** for anything else.
