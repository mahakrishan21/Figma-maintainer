---
disable-model-invocation: true
description: SOP manager only — run the release check, commit and tag a new version, build the zip and refresh the team marketplace
argument-hint: [--version X.Y.Z | --bump minor] [--message "what changed"]
---

Run `python3 -I ~/.claude/figma-maintainer/scripts/share_plugin.py $ARGUMENTS` and show me its output.

What it does:
1. **Release check:** every script compiles, the offline tests pass, and the manifests are valid. If it fails, nothing is committed or packaged; show me what failed.
2. **Commit and tag:** commits every pending change in the plugin (SOPs in `knowledge/`, agents, scripts, docs), bumps the version (patch by default) and makes an annotated tag.
3. **Zip:** writes `~/ClaudeAI/Figma-maintainer.zip` from exactly that tagged version.
4. **Marketplace:** refreshes the team marketplace repo (`~/ClaudeAI/e2m-figma-marketplace`) with the same build, then validates, commits and tags it there.

Tests, release tools and the management briefing (`export-ignore` in `.gitattributes`) never reach the team. Session files (work folders, logs, audits, contributions) are never included.

It doesn't push to GitHub and doesn't change my own Claude Code plugin install. Tell me:
- that both repos are published when I say "push" (`git push origin main --tags` in each);
- to run `/reload-plugins` to use the new version myself.

Then tell me how co-workers update, after the push:
1. run `/plugin marketplace update e2m-figma`;
2. run `/reload-plugins`;
3. run `/figma-maintainer:doctor`.

The first time, they run `/plugin marketplace add mahakrishan21/e2m-figma-marketplace` and then `/plugin install figma-maintainer@e2m-figma`.
