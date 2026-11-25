#!/usr/bin/env python3
"""figma-maintainer version and build information, and the update check against the live team repo.

  version_info.py            the About block: version, build date, install source, what it can do,
                             what's new, and whether a newer version is live (exit 2 when one is)
  version_info.py --session  SessionStart: one line of context only when a newer version is live
                             (checked at most every 12 hours; silent otherwise and on the SOP manager's Mac)
  version_info.py --json     machine-readable
Read-only: it never updates anything itself.
"""
import json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
ROOT = HERE.parent  # plugin root
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
CACHE = FM / "version-check.json"
REPO = "E2M-Design/e2m-figma-marketplace"  # team marketplace (private)
MARKET = "e2m-figma"
PLUGIN_ID = "figma-maintainer@e2m-figma"
UPDATE_CMDS = [f"claude plugin marketplace update {MARKET}", f"claude plugin update {PLUGIN_ID}"]
CAN_DO = [
    "Client comments: finds new ones, plans the changes, asks you to approve, applies them (client-comment, apply-comments)",
    "Edits: copy, forms, image swaps (iStock / Adobe Stock / client images), components, hover states",
    "New designs: mobile and tablet from desktop (make-responsive); inner pages in the homepage's style (make-inner-page)",
    "Independent QA after every job, or on its own for manual work (qa)",
    "Read-only checks: comments, brief check, version compare, consistency / content / accessibility audits",
    "Hand-off: Slack update, client message, token and cost reports",
]


def semver(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "0")[:3])


def installed():
    try:
        return json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text()).get("version", "?")
    except Exception:
        return "?"


def changelog():
    """[(version, date, [lines])] newest first, from CHANGELOG.md ('## 1.36.0 · 25 Nov 2026' + '- ...' lines)."""
    out = []
    try:
        text = (ROOT / "CHANGELOG.md").read_text()
    except Exception:
        return out
    for m in re.finditer(r"^## (\d+\.\d+\.\d+)(?: · (.+))?\n((?:(?!## ).*\n?)*)", text, re.M):
        lines = [l[2:].strip() for l in m.group(3).splitlines() if l.startswith("- ")]
        out.append((m.group(1), (m.group(2) or "").strip(), lines))
    return out


def source():
    """Where this copy came from: the SOP manager's source folder, the team marketplace, or something else."""
    if (FM / ".master").exists():
        return "master"
    if "/plugins/cache/" in str(ROOT) or "/plugins/marketplaces/" in str(ROOT):
        return "marketplace"
    return "folder"


def latest(timeout=15):
    """Newest released version in the live repo, or None (offline, not signed in, or no access)."""
    market = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins" / "marketplaces" / MARKET
    repo = ROOT if (ROOT / ".git").exists() else market if (market / ".git").exists() else None
    try:
        if repo:
            r = subprocess.run(["git", "-C", str(repo), "ls-remote", "--tags", "origin"], capture_output=True, text=True,
                               timeout=timeout, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
            tags = re.findall(r"refs/tags/v(\d+\.\d+\.\d+)$", r.stdout, re.M)
        else:
            req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/tags?per_page=100", headers={"User-Agent": "figma-maintainer"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                tags = [t["name"].lstrip("v") for t in json.load(resp) if re.match(r"v?\d+\.\d+\.\d+$", t["name"])]
        return max(tags, key=semver) if tags else None
    except Exception:
        return None


def cached_latest(max_age_h=12, timeout=8):
    try:
        c = json.loads(CACHE.read_text())
        if time.time() - c.get("t", 0) < max_age_h * 3600:
            return c.get("latest")
    except Exception:
        pass
    v = latest(timeout)
    try:
        CACHE.write_text(json.dumps({"t": time.time(), "latest": v}))
    except Exception:
        pass
    return v


def info(live=None):
    local = installed()
    log = changelog()
    built = next((d for v, d, _ in log if v == local), "")
    live = live if live is not None else latest()
    return {"installed": local, "built": built, "source": source(), "latest": live,
            "update_available": bool(live and local != "?" and semver(live) > semver(local)),
            "whats_new": [{"version": v, "date": d, "changes": c} for v, d, c in log if local == "?" or semver(v) <= semver(local)][:3],
            "update_commands": UPDATE_CMDS}


def main():
    if "--session" in sys.argv:
        if source() == "master":
            return
        local, live = installed(), cached_latest()
        if live and local != "?" and semver(live) > semver(local):
            print(f"figma-maintainer update available: installed {local}, latest {live} in the team repo. Before the first "
                  f"figma-maintainer request in this session, ask the user once with AskUserQuestion: 'Update now (Recommended)' "
                  f"runs `{UPDATE_CMDS[0]}` then `{UPDATE_CMDS[1]}` in Bash, then tell them to type /reload-plugins (or restart "
                  f"Claude Code) and say what's new from /figma-maintainer:about; 'Later' continues on {local}. Don't ask again in this session.")
        return
    d = info()
    if "--json" in sys.argv:
        print(json.dumps(d, indent=2))
        sys.exit(2 if d["update_available"] else 0)
    where = {"master": "SOP manager's source folder", "marketplace": f"team marketplace {MARKET}",
             "folder": "a local folder or zip"}[d["source"]]
    print(f"figma-maintainer v{d['installed']}" + (f" · released {d['built']}" if d["built"] else "") + f" · installed from {where}")
    print("\nWhat it can do:")
    for c in CAN_DO:
        print(f"  - {c}")
    print("\nWhat's new:")
    for w in d["whats_new"]:
        print(f"  v{w['version']}" + (f" ({w['date']})" if w["date"] else ""))
        for c in w["changes"]:
            print(f"    - {c}")
    print()
    if d["source"] == "master":
        print(f"Live version: {d['latest'] or 'unknown'}. This is the source Mac: release a new version from here, no update needed.")
    elif d["update_available"]:
        print(f"UPDATE AVAILABLE: v{d['installed']} → v{d['latest']}")
        print("Update with:\n  " + "\n  ".join(UPDATE_CMDS) + "\nthen /reload-plugins (or restart Claude Code).")
    elif d["latest"]:
        print(f"Up to date (latest live version: v{d['latest']}).")
    else:
        print("Couldn't check the live version (offline, or GitHub isn't signed in on this Mac: run `gh auth login`).")
    sys.exit(2 if d["update_available"] else 0)


if __name__ == "__main__":
    main()
