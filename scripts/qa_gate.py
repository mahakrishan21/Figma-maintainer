#!/usr/bin/env python3
"""QA gate (hooks): a figma-maintainer job that changed Figma can't end without the QA check.

  qa_gate.py --subagent-stop   SubagentStop: figma-maintainer finished with completed Figma writes → mark "QA pending"
                               for this session (files + job folder); qa-checker finished → clear the matching marks.
  qa_gate.py --stop            Stop: if this session has a pending mark and no QA run in progress, block the end of
                               the turn once and tell Claude to run figma-maintainer:qa-checker. Never blocks twice in a
                               row (stop_hook_active); then it only warns.
The user can skip it for a job by saying "skip QA" (image_gate.py calls clear()).
State: ~/.claude/figma-maintainer/qa-pending.json · log: qa-gate-log.jsonl. Only sessions where figma-maintainer
wrote to Figma ever get a mark, so other plugins and sessions are never affected.
"""
import json, os, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
STATE = FM / "qa-pending.json"
GATE_LOG = FM / "qa-gate-log.jsonl"
MAKER, QA = "figma-maintainer:figma-maintainer", "figma-maintainer:qa-checker"
JOB_RX = re.compile(r"(/[^\s\"'`]*?/work/[^\s\"'`]+?/jobs/\d{4}-\d{2}-\d{2}-[a-z0-9-]+)")


def now():
    return datetime.now(timezone.utc)


def iso(t):
    return t.isoformat(timespec="seconds")


def ts(s):
    return datetime.fromisoformat(str(s).replace("Z", "+00:00"))


def session_of(hook):
    tp = hook.get("transcript_path") or ""
    if "/subagents/" in tp:
        return Path(tp).parent.parent.name
    return Path(tp).stem if tp else (hook.get("session_id") or "")


def load():
    try:
        st = json.loads(STATE.read_text())
    except Exception:
        st = {}
    cutoff = now() - timedelta(days=3)  # stale marks expire
    return {s: [m for m in ms if ts(m["at"]) > cutoff] for s, ms in st.items() if ms}


def save(st):
    FM.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({s: ms for s, ms in st.items() if ms}, indent=1))


def gate_log(rec):
    try:
        with open(GATE_LOG, "a") as f:
            f.write(json.dumps(dict(rec, ts=iso(now()))) + "\n")
    except Exception:
        pass


def maker_writes(agent_id):
    """File keys this agent run completed writes to (from figma_guard's audit log)."""
    files = []
    f = FM / "figma-audit-log.jsonl"
    if agent_id and f.exists():
        for line in f.read_text(errors="ignore").splitlines()[-5000:]:
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("agent_id") == agent_id and str(r.get("decision", "")).startswith("completed") and r.get("fileKey"):
                if r["fileKey"] not in files:
                    files.append(r["fileKey"])
    return files


def text_of(path, limit=4_000_000):
    try:
        p = Path(path)
        size = p.stat().st_size
        with open(p, "rb") as f:
            if size > limit:
                f.seek(size - limit)
            return f.read().decode("utf-8", "ignore")
    except Exception:
        return ""


def first_brief(path):
    """The subagent's brief (its first user message)."""
    try:
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                if d.get("type") == "user":
                    c = (d.get("message") or {}).get("content")
                    if isinstance(c, str):
                        return c
                    return " ".join(x.get("text", "") for x in c or [] if isinstance(x, dict))
    except Exception:
        pass
    return ""


def subagent_stop(hook):
    kind, aid = hook.get("agent_type") or "", hook.get("agent_id") or ""
    sess = session_of(hook)
    if kind == MAKER:
        files = maker_writes(aid)
        if not files:
            return
        jobs = JOB_RX.findall(text_of(hook.get("agent_transcript_path") or ""))
        st = load()
        st.setdefault(sess, []).append({"agent_id": aid, "files": files, "job": jobs[-1] if jobs else None, "at": iso(now())})
        save(st)
        gate_log({"event": "pending", "session": sess, "files": files, "job": jobs[-1] if jobs else None})
    elif kind == QA:
        brief = first_brief(hook.get("agent_transcript_path") or "") or text_of(hook.get("agent_transcript_path") or "", 200_000)
        st = load()
        keep, cleared = [], []
        for m in st.get(sess, []):
            hit = (m.get("job") and m["job"] in brief) or any(k in brief for k in m.get("files", []))
            (cleared if hit else keep).append(m)
        if cleared:
            st[sess] = keep
            save(st)
            gate_log({"event": "qa-done", "session": sess, "cleared": [c.get("job") or c["files"] for c in cleared]})


def qa_started_since(transcript, since):
    """True when the main session launched qa-checker after `since` (it may still be running in the background)."""
    for line in text_of(transcript).splitlines():
        if QA not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") != "assistant" or not d.get("timestamp"):
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use" and (c.get("input") or {}).get("subagent_type") == QA:
                if ts(d["timestamp"]) >= ts(since):
                    return True
    return False


def stop(hook):
    sess = session_of(hook)
    marks = load().get(sess, [])
    if not marks:
        return None
    pending = [m for m in marks if not qa_started_since(hook.get("transcript_path") or "", m["at"])]
    if not pending:
        return None
    desc = "; ".join(f"file {', '.join(m['files'])}" + (f" (job folder {m['job']})" if m.get("job") else "") for m in pending)
    if hook.get("stop_hook_active"):
        gate_log({"event": "warned", "session": sess, "pending": desc})
        return {"systemMessage": f"figma-maintainer: QA hasn't run yet for {desc}. Say 'run QA' to check it, or 'skip QA' to skip it."}
    gate_log({"event": "blocked", "session": sess, "pending": desc})
    return {"decision": "block", "reason": (
        f"figma-maintainer QA gate: figma-maintainer changed Figma ({desc}) and the QA check hasn't run. Before finishing, "
        f"launch figma-maintainer:qa-checker in the foreground with 'Job folder: <job folder>' and 'File: <fileKey>', save its "
        "result as qa.md, and follow the QA fix-round rule (one automatic fix round for AUTO-FIX items, then re-check; "
        "otherwise hold the client message and ask the user). If the user said to skip QA, tell them it was skipped.")}


def clear(session, why="skipped by the user"):
    st = load()
    marks = st.pop(session, [])
    save(st)
    if marks:
        gate_log({"event": "cleared", "session": session, "why": why, "jobs": [m.get("job") or m["files"] for m in marks]})
    return marks


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    try:
        if "--subagent-stop" in sys.argv:
            subagent_stop(hook)
        elif "--stop" in sys.argv:
            out = stop(hook)
            if out:
                print(json.dumps(out))
    except Exception as e:  # the gate must never break a session
        print(f"qa_gate: {e}", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
