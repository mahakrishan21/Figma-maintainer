---
description: Show figma-maintainer's version and build, what it can do and what's new, and check the team repo for an update (asks before updating)
---

Run `python3 -I ~/.claude/figma-maintainer/scripts/version_info.py` and show me its output as it is.

If it says **UPDATE AVAILABLE**, ask me with AskUserQuestion:
- **Update now (Recommended):** run the two update commands it prints, one after the other, in Bash. When both succeed, tell me to type `/reload-plugins` (or restart Claude Code) to load the new version. If one fails, show the error; "Repository not found" or "authentication failed" means GitHub isn't signed in on this Mac as the team account (`gh auth login`).
- **Later:** do nothing.

If it says this is the source Mac, don't offer an update. Change nothing else.
