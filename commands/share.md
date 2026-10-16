---
disable-model-invocation: true
description: Package figma-maintainer for co-workers with all current client SOPs and team notes (master machine)
argument-hint: (no arguments)
---

Run `python3 -I ~/ClaudeAI/figma-maintainer-plugin/scripts/share_plugin.py` and show me its output.

It copies my current notes (every client SOP, task SOP, project notes, playbook, prices, cost settings, job log) into the plugin, bumps the version, commits it, updates my install and writes `~/ClaudeAI/figma-maintainer-plugin.zip`. Personal logs aren't included.

Then tell me what to send: the zip. A co-worker who already has the plugin unzips it over the same folder, runs `/plugin marketplace update e2m-figma`, and restarts. Their notes then update automatically: new SOPs are added, updated SOPs replace untouched copies, and their own edits are kept with the plugin's version beside them as `.from-plugin`.
