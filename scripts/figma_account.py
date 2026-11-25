#!/usr/bin/env python3
"""Which Figma account is figma-maintainer about to use? (read-only, except the confirmation record)

  figma_account.py --session <id>              the token's account (scripts, QA, snapshots) and whether this
                                               conversation has confirmed the account yet
  figma_account.py --session <id> --confirm --mcp "<handle> <email>"
                                               record the user's confirmation for this conversation
                                               (run only after the user said yes)

Two accounts matter: the Figma connector (MCP) makes the edits; the token runs the plugin's scripts. The
connector's account comes from its `whoami` tool, which only Claude can call, so it's passed in with --mcp.
Figma writes are blocked (figma_guard.py) until this conversation has a confirmation.
"""
import argparse, json, os, sys, time
from pathlib import Path

HERE = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(HERE))
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
STORE = FM / "account-checks.json"
KEEP = 200


def load():
    try:
        return json.loads(STORE.read_text())
    except Exception:
        return {}


def confirmed(session):
    """The confirmation record for this conversation, or None."""
    return load().get(session) if session else None


def record(session, mcp, rest):
    d = load()
    d[session] = {"mcp": mcp, "token": rest, "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    d = dict(sorted(d.items(), key=lambda kv: kv[1].get("at", ""))[-KEEP:])
    FM.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(d, indent=1))


def token_account():
    try:
        from figma_common import get, token
        me = get("/me", token())
        return f"{me.get('handle', '?')} <{me.get('email', '?')}>"
    except SystemExit as e:
        return f"unavailable ({e})"
    except Exception as e:
        return f"unavailable ({str(e)[:120]})"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--session", required=True); ap.add_argument("--confirm", action="store_true"); ap.add_argument("--mcp", default="")
    a = ap.parse_args()
    rest = token_account()
    if a.confirm:
        if not a.mcp.strip():
            sys.exit("Pass --mcp \"<handle> <email>\" from the Figma connector's whoami.")
        record(a.session, a.mcp.strip(), rest)
        print(f"Figma account confirmed for this conversation: connector {a.mcp.strip()} · token {rest}. Figma work can start.")
        return
    print(f"Token account (scripts, QA, snapshots): {rest}")
    c = confirmed(a.session)
    print(f"This conversation: " + (f"confirmed {c['at']} (connector {c['mcp']})" if c else "NOT confirmed yet"))


if __name__ == "__main__":
    main()
