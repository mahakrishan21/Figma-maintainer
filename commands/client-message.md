---
disable-model-invocation: true
description: Write the client-facing final comment for the figma-maintainer work done in this session (what we did → page · note · link → Note → Thank you)
argument-hint: [optional: extra notes, placeholders, or which pages/links to include]
---

Write the **Client message (copy-paste)** for the figma-maintainer work done in this session, in the format from the figma-maintainer agent's "Client message" section:
1. greeting (only if the client SOP sets one);
2. a 1–2 sentence opening on what we've done;
3. one block per changed page: `<Page name> - <short note>`, with its link on the next line. For Figma work this is always the **prototype link**, built with `python3 -I ~/.claude/figma-maintainer/scripts/proto_link.py --file <fileKey> --node <id>…`, never a `figma.com/design` page link;
4. `Note:` with placeholders, what we need from the client, and open questions (left out if there's nothing);
5. `Thank you!`

Use the agents' reports, Slack updates and links from this conversation, plus anything I add: $ARGUMENTS
Read the client's `client.md` (§8 Handoff and reporting → Client message) for the greeting and sign-off. Plain English, correct grammar, no node IDs, tool names or costs. Never invent changes. Put it in one plain-text code block, ready to paste.
