#!/usr/bin/env python3
"""PreToolUse guard for Write/Edit: SOPs live only in the plugin and are changed only by the SOP manager.

- Co-workers (no .master): editing anything under knowledge/ (via ~/.claude/figma-maintainer/clients,
  playbook.md, pricing.json, cost-config.json, or the installed plugin) is denied, and Claude is told to
  write a proposal in ~/.claude/figma-maintainer/contributions/ instead.
- SOP manager (.master): edits to the plugin SOURCE knowledge/ are allowed; edits to an installed copy
  in the plugin cache are denied (they'd be overwritten on the next update).
Every other path is ignored (this hook is silent for all non-SOP files).
"""
import json, os, sys
from pathlib import Path

FM = Path.home() / ".claude" / "figma-maintainer"
SHARED = ("clients", "playbook.md", "pricing.json", "cost-config.json")


def out(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": "figma-maintainer SOP guard: " + reason}}))
    sys.exit(0)


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    fp = (hook.get("tool_input") or {}).get("file_path") or (hook.get("tool_input") or {}).get("notebook_path") or ""
    if not fp:
        sys.exit(0)
    p = Path(os.path.expanduser(fp))
    try:
        real = p.resolve()
    except Exception:
        real = p
    s, r = str(p), str(real)
    via_session = any(s == str(FM / x) or s.startswith(str(FM / x) + os.sep) for x in SHARED)
    in_cache = "/.claude/plugins/cache/" in r and "/figma-maintainer/" in r and "/knowledge/" in r
    master_src = None
    mf = FM / ".master"
    if mf.exists():
        for line in mf.read_text().splitlines():
            if line.startswith("source:"):
                master_src = str(Path(line.split(":", 1)[1].strip()).expanduser().resolve())
    in_source = master_src and (r.startswith(master_src + "/knowledge/") or r == master_src + "/knowledge")
    if not (via_session or in_cache or in_source):
        sys.exit(0)
    if master_src:
        if in_source:
            sys.exit(0)  # SOP manager editing the plugin source: allowed
        out("this file is an installed copy of the plugin; edit the plugin source "
            f"({master_src}/knowledge/...) instead, then commit and run /figma-maintainer:share.")
    out("client SOPs, the playbook and system files are managed centrally by the SOP manager and come with "
        "the plugin. Don't edit them here. Write the proposed change as a contribution file in "
        "~/.claude/figma-maintainer/contributions/ (format: clients/_template/contribution.md), and tell the user "
        "to send it with /figma-maintainer:contribute.")


if __name__ == "__main__":
    main()
