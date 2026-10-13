# figma-maintainer

A Claude Code subagent that makes Figma maintenance changes directly (copy edits, form changes, image swaps, inner pages, feedback rounds, audits). It follows client SOP notes and remembers corrections.

## Requirements
- Claude Code (CLI, desktop or VS Code).
- The Figma connector: either the claude.ai Figma connector (authorized at claude.ai → Settings → Connectors) or the official Figma plugin (`/plugin install figma@claude-plugins-official`). Edit access to the Figma file is needed for changes.

## Install
Unzip `figma-maintainer.zip` and run:

```bash
cd figma-maintainer && ./install.sh
```

This copies:
- `~/.claude/agents/figma-maintainer.md` (the agent)
- `~/.claude/figma-maintainer/` (playbook, client notes, job log)

Your existing notes and job log are never overwritten. Restart Claude Code (or open a new session) so the agent loads.

## Use
In any Claude Code session:

```
Use figma-maintainer: <figma URL> — <what to change>
```

Examples:
- `Use figma-maintainer: <url> — apply the client feedback below: …`
- `Use figma-maintainer: <url> — build the About inner page using the Founding Families layout`
- `Use figma-maintainer: <url> — audit only, don't change anything`
- `Use figma-maintainer: <url> — duplicate the latest section as a new version, then …`

Corrections: just say so, e.g. `figma-maintainer: next time, KHL buttons are always full width in forms.` It applies the fix and saves the rule.

## What it remembers
| File | Holds |
|---|---|
| `playbook.md` | General Figma/design rules for every client |
| `clients/<client>.md` | One client's SOP: file keys, page map, components, copy rules, image source, open decisions |
| `job-log.md` | One short entry per job |

To add a client, copy `clients/_template.md`, or let the agent create the file on its first job for that client.

## Behaviour
- It edits the frames you point at. It makes a new version only when you ask for one, or when the client SOP says to.
- It never edits main components, styles, variables or library pages unless asked.
- If an original changes unexpectedly, or the same approach fails twice, it stops.
- It reports what changed (with links), what it verified, what's left and what it learned.

## Sharing notes with the team
Client notes are only useful when everyone has the latest copy. To share them, keep `~/.claude/figma-maintainer/clients/` in a shared git repo (or synced folder) and symlink it:
`ln -s <shared-path>/clients ~/.claude/figma-maintainer/clients`
