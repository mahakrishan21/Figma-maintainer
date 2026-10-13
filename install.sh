#!/usr/bin/env bash
# Installs the figma-maintainer agent for the current user. Never overwrites existing notes.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
dest="$HOME/.claude/figma-maintainer"

mkdir -p "$HOME/.claude/agents" "$dest/clients"
cp "$here/agent/figma-maintainer.md" "$HOME/.claude/agents/figma-maintainer.md"
cp "$here/README.md" "$here/install.sh" "$dest/" 2>/dev/null || true

for f in playbook.md job-log.md; do
  [ -e "$dest/$f" ] || cp "$here/$f" "$dest/$f"
done
for f in "$here"/clients/*.md; do
  [ -e "$dest/clients/$(basename "$f")" ] || cp "$f" "$dest/clients/"
done

echo "Installed. Restart Claude Code, then: Use figma-maintainer: <figma URL> — <task>"
