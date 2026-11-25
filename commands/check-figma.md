---
description: Check which Figma account is connected (name and email) and confirm it before any figma-maintainer work; Figma edits stay blocked in this conversation until you confirm
---

Check the Figma account before any figma-maintainer work. Change nothing in Figma.

1. Call the Figma MCP `whoami` tool (read-only). Note the handle, the email, and the plan and seat. If the Figma connector isn't connected, say so, tell me to connect it (Claude Code: `/mcp`; Claude app: Settings → Connectors → Figma), and stop.
2. Run `python3 -I ~/.claude/figma-maintainer/scripts/figma_account.py --session <session id>`. Use the session id this conversation's figma-maintainer hook gave; if there's none, use the id of this conversation's transcript. It prints the account behind the Figma token, which the plugin's scripts, QA and snapshots use.
3. Show me:

   | | Name | Email |
   |---|---|---|
   | Figma connector (makes the edits) | … | … |
   | Figma token (scripts and QA) | … | … |

   Add the plan and seat in one line. If the two accounts differ, say so in bold; scripts and edits would then see different files and permissions.
4. Ask me with AskUserQuestion: "Is this the right Figma account for this work?"
   - **Yes, continue:** run `python3 -I ~/.claude/figma-maintainer/scripts/figma_account.py --session <same id> --confirm --mcp "<handle> <email>"`, say it's confirmed, then go on with the request I made, if any.
   - **No, wrong account:** don't start any Figma work. Tell me how to switch:
     - the connector: disconnect and reconnect it with the right account (Claude Code: `/mcp` → Figma; Claude app: Settings → Connectors);
     - the token: `security add-generic-password -U -s figma-maintainer -a FIGMA_TOKEN -w`, then paste the right account's token at the hidden prompt. Never in the chat.

     Then run `/figma-maintainer:check-figma` again.

Never run the `--confirm` step without my "Yes" in this conversation.
