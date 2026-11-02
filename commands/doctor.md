---
disable-model-invocation: true
description: Check this Mac's figma-maintainer setup (token and scopes, Figma access, notifications, image library, plugin version, settings) and say how to fix each problem
---

Check my figma-maintainer setup. Read-only: don't change anything, and don't ask about images.

1. Run `python3 -I ~/.claude/figma-maintainer/scripts/doctor.py` and read the result. If that path doesn't exist yet, run it from the plugin folder: `python3 -I <plugin folder>/scripts/doctor.py`.
2. Call the Figma MCP `whoami` (read-only). Compare that account with the token's account from the doctor's "Token works (/me)" line:
   - **Same account:** say so.
   - **Different accounts:** say that the agent edits as the MCP account, so files must be shared with edit access to that account.
   - **MCP not connected:** say how to connect one of them, signed in with the team account (Design Studio):
     - the Figma MCP in Claude Code: `/plugin install figma@claude-plugins-official`, then sign in;
     - or the claude.ai connector: claude.ai → Settings → Connectors → Figma.
3. Show me the result as a short list. Problems (✗) come first, each with its fix in one line, then warnings (⚠), then one line saying everything else is fine. Never show or ask for the token itself.
4. If there are no problems, end with: "Setup is ready."
