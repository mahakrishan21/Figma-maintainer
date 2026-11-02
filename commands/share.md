---
disable-model-invocation: true
description: SOP manager only — run the release check, commit and tag a new version, and build the zip for co-workers
argument-hint: [--version X.Y.Z | --bump minor] [--message "what changed"]
---

Run `python3 -I ~/.claude/figma-maintainer/scripts/share_plugin.py $ARGUMENTS` and show me its output.

What it does:
1. Runs the release check: every script compiles, the offline tests pass, and the manifests are valid. If the check fails, nothing is committed or packaged; show me what failed.
2. Commits every pending change in the plugin (SOPs in `knowledge/`, agents, scripts, docs), bumps the version (patch by default), and makes an annotated tag.
3. Writes `~/ClaudeAI/Figma-maintainer.zip` from exactly that tagged version. Session files (work folders, logs, audits, contributions) are never included.

It doesn't push to GitHub and doesn't change my Claude Code plugin install. Tell me:
- to run `git push origin main --tags` when I want it published;
- to run `/reload-plugins` to use the new version myself.

Then tell me how co-workers update:
1. unzip over their plugin folder;
2. run `/plugin marketplace update e2m-figma`;
3. restart Claude Code;
4. run `/figma-maintainer:doctor`.

The first time, after unzipping to `~/ClaudeAI/Figma-maintainer`, they run `/plugin marketplace add ~/ClaudeAI/Figma-maintainer` and then `/plugin install figma-maintainer@e2m-figma`.
