# Client comments mode

> On-demand guide for the figma-maintainer agent. Read it when the task needs it; the core rules in the agent still apply.

Use this when the task says to read or apply the Figma comments ("apply the client's comments", "fix the comments on <url>").

1. **Read them:** `python3 -I ~/.claude/figma-maintainer/scripts/figma_comments.py --url "<figma url>" --out <project folder>/comments`. With an approved plan and `context.json`, add `--brief` (one line per comment) and open `comments.md` only for a comment you need detail on. Add `--all-frames` when the user wants the whole file, `--author "<name>"` to keep one reviewer, and `--include-resolved` only if asked.
   - **Latest round only, by default.** Designers rarely mark comments resolved, so old comments stay open forever. The script splits them by date: the **current round** (the newest comment's date and up to 2 days before it) is what you apply. **Older open comments are never applied by default**, even though they're unresolved, because they were most likely handled in earlier rounds. (rule, 2026-10-27)
   - **When the task says which round**, use it: `--since <YYYY-MM-DD>` for "comments since the 20th", `--round all` for "every open comment", `--window-days N` for "the last N days".
   - **When older open comments exist and the task didn't say,** apply the latest round only. Then list the older ones in the report: *"Older open comments: N from <dates>, not applied. They look handled in earlier rounds; tell me if any still need doing. Consider marking them resolved in Figma."* If an older comment clearly conflicts with the current design and today's round doesn't cover it, mention it as a question; don't change it.
   - **If a current-round comment and an older one touch the same element,** the newer comment wins. The script prints each unresolved comment with replies, its pin position, and the nearest text and image layers. If it exits with "No Figma token found", stop and tell the user to set `FIGMA_TOKEN` (Figma → Settings → Security → Personal access tokens, read access to File content and Comments). Never ask for the token in chat.
2. **Confirm each match.** "Nearest" is a hint, not proof. A pin on a list or paragraph refers to the whole block, so read every item in it (the full list, the whole paragraph with its line breaks) before you decide what "2nd bullet" or "these two lines" means. When it's ambiguous, take a screenshot of the area around the pin.
3. **Sort into:**
   - **Apply:** copy edits, punctuation, removing or reordering items, spacing, alignment, colour or style swaps that use existing styles, layout changes built from existing components.
   - **New or replacement image or video:** use the source settled at the start (see "Images and video — always ask").
   - **Image editing (never do it):** retouching, removing or adding objects in a photo, generating or re-rendering imagery, mockups that need screenshots the file doesn't have. Leave the image, add an annotation on it quoting the comment, and list it under "Not done" with what's needed.
   - **Approval / no change:** "I like this", "approved", "good work". Record these in the client notes.
   - **Question or unclear:** don't guess. List it with the options.
4. **Version:** follow the client SOP, or the file's own convention if the notes have none (for example, a new "V#" frame per round next to the previous one). The commented frame stays untouched, so the comments remain pinned to what the client reviewed.
5. **Apply and verify** as in the workflow above. Find edited nodes in a duplicate by their text content, not their IDs.
6. **Report every comment by number:** done (node ID), not done (image editing, with an annotation), approval, or needs a decision. Never resolve, reply to or delete comments in Figma.
