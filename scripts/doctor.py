#!/usr/bin/env python3
"""figma-maintainer doctor: checks this Mac's setup in one go and says how to fix each problem (read-only).

  doctor.py            all checks, ✓ / ⚠ / ✗ with the fix
  doctor.py --json     machine-readable
Exit code 1 when a required check fails. Never changes anything; Figma calls are read-only.
"""
import json, os, re, sqlite3, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE))
from figma_common import FM, FigmaError, get  # noqa: E402

ROOT = HERE.parent  # plugin root
REPO = "E2M-Design/e2m-figma-marketplace"  # team marketplace; private, so unauthenticated checks skip
TEST_FILE = "lQHhvuMvDB1t4C4k3Fl5VF"
RESULTS = []


def check(name, status, detail="", fix=""):
    RESULTS.append({"check": name, "status": status, "detail": detail, "fix": fix})


def default_model():
    """(model, where): ANTHROPIC_MODEL, else the model in Claude Code's user settings.json, else ("", "")."""
    m = os.environ.get("ANTHROPIC_MODEL", "")
    if m:
        return m, "ANTHROPIC_MODEL"
    cfg_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    try:
        return str(json.loads((cfg_dir / "settings.json").read_text()).get("model") or ""), "settings.json"
    except Exception:
        return "", ""


def expensive_model(model):
    return any(k in (model or "").lower() for k in ("fable", "mythos"))


def semver(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def main():
    as_json = "--json" in sys.argv

    # ---- Python and image library
    v = sys.version_info
    check("Python", "ok" if v >= (3, 9) else "fail", f"{v.major}.{v.minor}.{v.micro}", "Install Python 3.9 or newer.")
    try:
        from figma_qa import pil
        Image, _ = pil()
        check("Image library (PIL)", "ok" if Image else "warn", "available" if Image else "not installed",
              "python3 -m pip install --user pillow   (needed for QA pixel diffs and image downloads)")
    except Exception as e:
        check("Image library (PIL)", "warn", str(e)[:80], "python3 -m pip install --user pillow")

    # ---- session folder and links
    check("Session folder", "ok" if FM.is_dir() else "fail", str(FM), "Start a new Claude Code session: the plugin creates it.")
    for name in ("clients", "playbook.md", "scripts"):
        p = FM / name
        ok = p.exists()
        check(f"Link: {name}", "ok" if ok else "fail", str(p.resolve()) if ok else "missing",
              "Restart Claude Code (the session-start hook re-creates the links).")
    person = (FM / ".person").read_text().strip() if (FM / ".person").exists() else ""
    check("Your name (.person)", "ok" if person else "warn", person or "not set",
          f"echo 'Your Name' > {FM / '.person'}   (used for your work folder)")

    # ---- Figma token and scopes
    tok = None
    try:
        from figma_common import token
        tok = token()
        check("Figma token", "ok", "found (Keychain or FIGMA_TOKEN)")
    except SystemExit:
        check("Figma token", "fail", "not found",
              "Ask the SOP manager for the team Figma token (private message), then run: security add-generic-password -U -s figma-maintainer -a FIGMA_TOKEN -w")
    if tok:
        try:
            me = get("/me", tok, retries=1, timeout=20)
            check("Token works (/me)", "ok", f"{me.get('handle')} ({me.get('email', '')})")
        except FigmaError as e:
            check("Token works (/me)", "fail", str(e)[:120], "The team token may have been replaced: ask the SOP manager for the current one and store it again with the Keychain command.")
            tok = None
    if tok:
        key = TEST_FILE
        try:
            get(f"/files/{key}/meta", tok, retries=1, timeout=20)
        except FigmaError:
            try:
                sys.path.insert(0, str(HERE))
                from comment_inbox import known_keys
                key = sorted(known_keys())[0]
            except Exception:
                key = None
        probes = [("File metadata", f"/files/{key}/meta"), ("File content", f"/files/{key}?depth=1"),
                  ("Comments (read)", f"/files/{key}/comments"), ("Version history", f"/files/{key}/versions?page_size=1")] if key else []
        for name, path in probes:
            try:
                get(path, tok, retries=1, timeout=30)
                check(f"Scope: {name}", "ok", f"on file {key}")
            except FigmaError as e:
                check(f"Scope: {name}", "fail", str(e)[:120], "The team token lacks this scope: the SOP manager makes a new team token with it (keeping the others) and shares it.")
        teams = []
        try:
            raw = (Path.home() / "Library/Application Support/Figma/settings.json").read_text()
            teams = sorted(set(re.findall(r"/team/(\d{6,})", raw)))
        except Exception:
            pass
        if teams:
            try:
                get(f"/teams/{teams[0]}/projects", tok, retries=1, timeout=30)
                check("Scope: projects:read", "ok", "files can be found by name across the team")
            except FigmaError as e:
                check("Scope: projects:read", "warn", "missing" if e.status == 403 else str(e)[:100],
                      "Recommended: the SOP manager adds projects:read to the team token, so client comments are found "
                      "in files you haven't opened recently.")
        else:
            check("Scope: projects:read", "skip", "no Figma team id in the desktop app's settings")

    # ---- Mac sources for comment discovery
    db = Path.home() / "Library/Group Containers/group.com.apple.usernoted/db2/db"
    try:
        con = sqlite3.connect(f"file:{urllib.parse.quote(str(db))}?mode=ro", uri=True)
        n = con.execute("SELECT count(*) FROM record r JOIN app a ON a.app_id = r.app_id WHERE a.identifier = 'com.figma.desktop'").fetchone()[0]
        con.close()
        check("Figma notifications (Mac)", "ok", f"readable, {n} Figma notification(s) kept")
    except Exception as e:
        check("Figma notifications (Mac)", "warn", str(e)[:80],
              "System Settings → Privacy & Security → Full Disk Access → allow your terminal / VS Code. (Only needed to find "
              "client comments without a link.)")
    st = Path.home() / "Library/Application Support/Figma/settings.json"
    try:
        s = json.loads(st.read_text())
        tabs = sum(len(w.get("tabs", [])) for w in s.get("windows", [])) + len(s.get("sharedTabHistory", []) or [])
        check("Figma desktop tabs", "ok", f"{tabs} recent tab(s) readable")
    except Exception:
        check("Figma desktop tabs", "warn", "settings.json not readable", "Install/open the Figma desktop app once.")

    # ---- default model (drives the main conversation's cost; agents are pinned to their own models)
    model, where = default_model()
    if expensive_model(model):
        check("Default model", "warn", f"{model} ({where})",
              "Fable costs 2.5–5× Opus. For routine Figma work run /model opus or /model sonnet (the plugin's agents use their own models anyway).")
    else:
        check("Default model", "ok", model or "Claude Code default (not set)")

    # ---- cost settings
    try:
        cfg = json.loads((ROOT / "knowledge" / "cost-config.json").read_text())
        inr = (cfg.get("fx") or {}).get("INR")
        check("INR exchange rate", "ok" if inr else "warn", f"{inr} per USD" if inr else "not set",
              "Set fx.INR in knowledge/cost-config.json (SOP manager), e.g. the current rate, so usage shows INR too.")
    except Exception:
        check("INR exchange rate", "skip", "cost-config.json not found")

    # ---- plugin version and install
    try:
        local = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text()).get("version", "?")
    except Exception:
        local = "?"
    latest = None
    try:
        # The source folder (SOP manager) or the team marketplace clone: ls-remote uses this Mac's GitHub sign-in.
        market = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "plugins" / "marketplaces" / "e2m-figma"
        repo = ROOT if (ROOT / ".git").exists() else market if (market / ".git").exists() else None
        if repo:
            r = subprocess.run(["git", "-C", str(repo), "ls-remote", "--tags", "origin"], capture_output=True, text=True, timeout=15)
            tags = re.findall(r"refs/tags/v(\d+\.\d+\.\d+)$", r.stdout, re.M)
        else:
            req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/tags?per_page=100", headers={"User-Agent": "figma-maintainer"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                tags = [t["name"].lstrip("v") for t in json.load(resp) if re.match(r"v?\d+\.\d+\.\d+$", t["name"])]
        latest = max(tags, key=semver) if tags else None
    except Exception:
        pass
    if latest and local != "?":
        newer = semver(latest) > semver(local)
        check("Plugin version", "warn" if newer else "ok", f"installed {local}, latest {latest}",
              "Update: /plugin marketplace update e2m-figma, then /reload-plugins.")
    else:
        check("Plugin version", "skip" if latest is None else "ok", f"installed {local}" + ("" if latest else ", latest unknown (offline or private repo)"))
    try:
        r = subprocess.run(["claude", "plugin", "list"], capture_output=True, text=True, timeout=30)
        m = re.search(r"figma-maintainer(@\S*)?", r.stdout)  # local marketplace install or a plugin synced from an upload
        block = r.stdout[m.end():] if m else ""
        block = re.split(r"\n\s*\n|❯", block)[0]  # only this plugin's entry
        status = (re.search(r"Status:\s*(.+)", block) or [None, ""])[1].lower()
        enabled = "enabled" in status and "disabled" not in status
        check("Plugin enabled", "ok" if enabled else "fail", "figma-maintainer is enabled" if enabled else ("installed but disabled" if block else "not installed"),
              "claude plugin enable figma-maintainer@e2m-figma (then restart)")
    except Exception:
        check("Plugin enabled", "skip", "claude CLI not found from this shell")

    # ---- iStock placeholders (no account needed; a live test search)
    try:
        import istock_fetch
        r = istock_fetch.check()
        check("iStock images", "ok" if r["ok"] else "fail",
              f"{r.get('results')} test results via {r.get('via')}" if r["ok"] else r.get("reason", ""), r.get("fix", ""))
    except Exception as e:
        check("iStock images", "fail", f"the iStock script couldn't run ({e})"[:150],
              "Update the plugin: /plugin marketplace update e2m-figma, then /reload-plugins.")

    # ---- work folder, pending QA, recent guard activity
    work = FM / "work"
    if work.exists():
        size = sum(f.stat().st_size for f in work.rglob("*") if f.is_file())
        check("Work folder size", "ok" if size < 2e9 else "warn", f"{size / 1e6:.0f} MB in {work}", "Archive old job folders (assets, renders).")
    try:
        from qa_gate import load
        pend = load()
        n = sum(len(v) for v in pend.values())
        check("Jobs waiting for QA", "ok" if not n else "warn", f"{n}" + (": " + "; ".join(m.get("job") or ",".join(m["files"]) for v in pend.values() for m in v)[:200] if n else ""),
              "Run QA on them (/figma-maintainer:qa) or say 'skip QA' in that session.")
    except Exception:
        pass
    log = FM / "figma-audit-log.jsonl"
    if log.exists():
        last = (log.read_text(errors="ignore").strip().splitlines() or ["{}"])[-1]
        try:
            check("Guard activity", "ok", f"last Figma call logged {json.loads(last).get('ts')}")
        except Exception:
            pass

    if as_json:
        print(json.dumps(RESULTS, indent=1))
    else:
        icon = {"ok": "✓", "warn": "⚠", "fail": "✗", "skip": "–"}
        print("# figma-maintainer doctor\n")
        for r in RESULTS:
            print(f"{icon[r['status']]} {r['check']}: {r['detail']}")
            if r["status"] in ("warn", "fail") and r["fix"]:
                print(f"    fix: {r['fix']}")
        fails = sum(r["status"] == "fail" for r in RESULTS)
        warns = sum(r["status"] == "warn" for r in RESULTS)
        print(f"\n{fails} problem(s), {warns} warning(s). Figma edit access is per file: the agent checks it at the start of each job.")
    sys.exit(1 if any(r["status"] == "fail" for r in RESULTS) else 0)


if __name__ == "__main__":
    main()
