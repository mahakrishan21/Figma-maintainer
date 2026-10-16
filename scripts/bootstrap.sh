#!/usr/bin/env bash
# Seeds and syncs ~/.claude/figma-maintainer/ (team notes from the plugin, see sync_notes.py)
# and keeps its scripts and guides current. Never overwrites local edits. Silent on success.
set -u
root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
dest="$HOME/.claude/figma-maintainer"

mkdir -p "$dest/clients" "$dest/scripts" || exit 0
# Migrate the old flat layout (clients/<project>.md) into client folders, once. Never overwrites.
for f in "$dest"/clients/*.md; do
  [ -f "$f" ] || continue
  b="$(basename "$f")"
  case "$b" in
    _index.md|_*.txt) continue ;;
    _template.md) t="$dest/clients/_template/project.md" ;;
    khl.md) t="$dest/clients/lions-share-digital/khl.md" ;;
    lsd.md) t="$dest/clients/lions-share-digital/lsd-website.md" ;;
    comfort-zone.md) t="$dest/clients/hey-mr-media/comfort-zone.md" ;;
    sj-roofing.md) t="$dest/clients/contractor-dynamics/sj-roofing.md" ;;
    *) t="$dest/clients/_unassigned/$b" ;;
  esac
  mkdir -p "$(dirname "$t")"
  if [ -e "$t" ]; then mkdir -p "$dest/clients/_old-layout"; mv "$f" "$dest/clients/_old-layout/$b"; else mv "$f" "$t"; fi
done
# Projects that were in _unassigned/ in v1.11 now have an agency
for pair in "comfort-zone.md:hey-mr-media" "sj-roofing.md:contractor-dynamics"; do
  f="$dest/clients/_unassigned/${pair%%:*}"; t="$dest/clients/${pair##*:}/${pair%%:*}"
  if [ -f "$f" ] && [ ! -e "$t" ]; then mkdir -p "$(dirname "$t")"; mv "$f" "$t"; fi
done
rm -f "$dest/clients/_unassigned/README.md"; rmdir "$dest/clients/_unassigned" 2>/dev/null || true
# Team notes (client SOPs, playbook, prices): add new, update untouched, never overwrite local edits
python3 -I "$root/scripts/sync_notes.py" --root "$root" --dest "$dest" || {
  # fallback if Python fails: copy only what's missing
  for f in playbook.md job-log.md pricing.json cost-config.json; do [ -e "$dest/$f" ] || cp "$root/seed/$f" "$dest/$f"; done
  ( cd "$root/seed/clients" && find . -type f -name '*.md' ) | while read -r rel; do
    t="$dest/clients/${rel#./}"; [ -e "$t" ] || { mkdir -p "$(dirname "$t")"; cp "$root/seed/clients/${rel#./}" "$t"; }
  done
}
# Guides are plugin-owned too: copy each skill's SKILL.md so the agent can read it.
mkdir -p "$dest/guides"
for d in "$root"/skills/*/; do
  [ -f "$d/SKILL.md" ] || continue
  t="$dest/guides/$(basename "$d").md"
  cmp -s "$d/SKILL.md" "$t" 2>/dev/null || cp "$d/SKILL.md" "$t"
done
# Scripts are plugin-owned: refresh them so updates reach everyone.
for f in "$root"/scripts/*.py; do
  t="$dest/scripts/$(basename "$f")"
  cmp -s "$f" "$t" 2>/dev/null || cp "$f" "$t"
done
exit 0
