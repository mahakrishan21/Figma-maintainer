#!/usr/bin/env bash
# figma-maintainer session setup (runs at every session start, silent on success).
#
# The PLUGIN is the single source of truth for SOPs and system files (knowledge/, scripts/, skills/).
# ~/.claude/figma-maintainer/ is this person's SESSION folder: logs, audits, reports, contributions.
# It gets links into the plugin so agents read SOPs at fixed paths:
#   clients/, playbook.md, pricing.json, cost-config.json -> <plugin>/knowledge/...
#   scripts/ -> <plugin>/scripts      guides/<skill>.md -> <plugin>/skills/<skill>/SKILL.md
#   guides/<name>.md -> <plugin>/guides/<name>.md (on-demand agent guides)
# On the SOP manager's machine (.master file: "source: <plugin source folder>") the links point to
# the plugin SOURCE, so SOP edits land in git. Everyone else reads their installed copy.
set -u
root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
dest="$HOME/.claude/figma-maintainer"
mkdir -p "$dest" "$dest/work" "$dest/contributions" "$dest/guides" || exit 0

src="$root"
if [ -f "$dest/.master" ]; then
  m="$(sed -n 's/^source: *//p' "$dest/.master" | head -1)"
  [ -n "$m" ] && [ -d "$m/knowledge" ] && src="$m"
fi
K="$src/knowledge"
[ -d "$K" ] || exit 0
stamp="$(date +%Y%m%d-%H%M%S)"

link() {  # link <target> <name>: replace old real copies (kept under _old-local-notes/) with a link
  local target="$1" path="$dest/$2"
  if [ -L "$path" ]; then
    [ "$(readlink "$path")" = "$target" ] || ln -sfn "$target" "$path"
  elif [ -e "$path" ]; then
    mkdir -p "$dest/_old-local-notes/$stamp"; mv "$path" "$dest/_old-local-notes/$stamp/"; ln -s "$target" "$path"
    echo "$2" >> "$dest/.old-notes-moved"
  else
    ln -s "$target" "$path"
  fi
}
link "$K/clients" clients
for f in playbook.md pricing.json cost-config.json; do link "$K/$f" "$f"; done
# plugin-owned code: old copied folders are simply replaced
[ -d "$dest/scripts" ] && [ ! -L "$dest/scripts" ] && rm -rf "$dest/scripts"
link "$src/scripts" scripts
for d in "$src"/skills/*/; do
  n="$(basename "$d")"; [ -f "$d/SKILL.md" ] && ln -sfn "$d/SKILL.md" "$dest/guides/$n.md"
done
# on-demand guides (plain files, not skills, so they don't add to every session's skill list)
for f in "$src"/guides/*.md; do
  [ -f "$f" ] && ln -sfn "$f" "$dest/guides/$(basename "$f")"
done
# Per person -> per client -> per project work folders live under work/<person>/ (created on demand by workdir.py)
if [ ! -s "$dest/.person" ]; then
  n="$(git config --global user.name 2>/dev/null)"; [ -n "$n" ] || n="${USER:-me}"
  printf '%s\n' "$n" > "$dest/.person"
fi
pslug="$(tr '[:upper:]' '[:lower:]' < "$dest/.person" | head -1 | sed -E "s/['’]//g; s/[^a-z0-9]+/-/g; s/^-+|-+$//g")"
mkdir -p "$dest/work/${pslug:-me}"
[ -e "$dest/job-log.md" ] || printf '# Job Log\n\nNewest last. Max ~6 lines per entry. (Personal session log, not shared.)\n' > "$dest/job-log.md"
rm -f "$dest/.sync-state.json"
# Old local SOP copies (from earlier plugin versions) that differ from the plugin -> listed for contribution
if [ -f "$dest/.old-notes-moved" ]; then
  python3 -I "$src/scripts/contribute.py" --review-old "$dest" "$K" 2>/dev/null || true
  rm -f "$dest/.old-notes-moved"
fi
exit 0
