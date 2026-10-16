---
disable-model-invocation: true
description: Co-workers — send your proposed SOP changes (new client requirements, notes, workflow improvements) to the SOP manager
argument-hint: (optional) a new requirement to add as a contribution first
---

If I described a new requirement or improvement ($ARGUMENTS), first write it as a contribution file in `~/.claude/figma-maintainer/contributions/<YYYY-MM-DD>-<agency>-<topic>.md`, using the format in `~/.claude/figma-maintainer/clients/_template/contribution.md`. Fill in only what I actually said, plus the source.

Then run `python3 -I ~/.claude/figma-maintainer/scripts/contribute.py --pack` and tell me which zip to send to the SOP manager. Don't edit any SOP files: they're managed centrally.
