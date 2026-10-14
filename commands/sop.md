---
description: View or fill in an agency's (or project's) SOP — e.g. /figma-maintainer:sop Lasso up, or /figma-maintainer:sop Lasso up — images always Adobe Stock
argument-hint: <agency or project name> [— rule to add]
---

Request: $ARGUMENTS

1. Find the agency folder: look up the name in `~/.claude/figma-maintainer/clients/_index.md` (agency or project name), or match a folder name under `~/.claude/figma-maintainer/clients/`. If the rule is about a recurring task type, use (or create from `_template/task.md`) `task-<name>.md` in the agency folder. If it matches a project, use that project's file (create it from `_template/project.md` if it doesn't exist) as well as the agency's `client.md`. If nothing matches, ask me which agency.
2. **No rule given:** show the SOP compactly:
   - what's **set**, by section;
   - a count of the `<not set>` items per section;
   - the 5 most useful missing items to fill next (image source, versioning, desktop width, copy source, contacts).

   Change nothing.
3. **Rule given:** write it into the matching numbered section of `client.md`. If it applies to one project only, write it into that project's section 3 "Overrides". Replace the `<not set>` value; never delete existing set values without asking me. Add the source and today's date, e.g. `(the user, YYYY-MM-DD)`, and add a line to "10. Rule log". For the image source, keep the exact label `- Image/video source:` so the automatic SOP detection reads it.
4. Never invent rules or fill other fields. Show me the changed lines.
