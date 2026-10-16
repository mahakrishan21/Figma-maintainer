---
disable-model-invocation: true
description: SOP manager only — commit SOP/plugin changes, bump the version and build the zip for co-workers
argument-hint: (no arguments)
---

Run `python3 -I ~/.claude/figma-maintainer/scripts/share_plugin.py` and show me its output.

It commits every pending change in the plugin (SOPs in `knowledge/`, plus agents, scripts and guides), bumps the version, tags it, updates my install, and writes `~/ClaudeAI/Figma-maintainer.zip`. Session files (logs, audits, reports, contributions) are never included.

Then tell me how co-workers update: unzip over their plugin folder, run `/plugin marketplace update e2m-figma`, and restart. They get every new and updated SOP at once, with no separate sync.
