#!/usr/bin/env python3
"""Per-task and per-session token/cost usage for figma-maintainer work (read-only, zero tokens).

Reads Claude Code's own transcripts: the main session file plus one file per agent task in
<session>/subagents/agent-*.jsonl (with agent-*.meta.json holding agent type + description).
Prices come from cost_report.py's pricing logic (~/.claude/figma-maintainer/pricing.json).
"New tokens" = input + cache writes + output (what the work actually consumed); cache reads
are reported separately because they are re-reads of context at a fraction of the price.

Usage:
  usage_report.py [--session <id|path>] [--cwd <project>]          # session summary, all tasks
  usage_report.py --task latest|<agent id>|"<description text>"     # one task
  usage_report.py --slack [--task …]                                # Slack 'Usage (internal)' block
  usage_report.py --all [--client KHL] [--since 2026-10-01] [--html]  # consolidated report of this Mac's history
                                                                    # (only via /figma-maintainer:cost-report-all; --ledger = alias)
  usage_report.py --hook-subagent-stop                              # hook: log the task + this session's totals, show the task line
History on this Mac: usage-log.jsonl (one row per plugin task) and usage-sessions.jsonl (one row per session that ran
a plugin agent: main-conversation cost, refreshed each time a plugin agent finishes).
Currency: ~/.claude/figma-maintainer/cost-config.json, e.g. {"currencies": ["USD","INR"], "fx": {"INR": 84.0}}
"""
import argparse, json, os, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_report as cr  # noqa: E402

FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
LEDGER = FM / "usage-log.jsonl"
SESSIONS = FM / "usage-sessions.jsonl"
SKIP_AGENTS = {"figma-maintainer:usage-reporter", "usage-reporter"}


def cost_cfg():
    cfg = {"currencies": ["USD"], "fx": {}}
    p = FM / "cost-config.json"
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text()))
        except Exception:
            pass
    return cfg


def money(usd, cfg):
    parts = []
    for cur in cfg.get("currencies", ["USD"]):
        if cur.upper() == "USD":
            parts.append(f"${usd:,.2f}")
        else:
            rate = (cfg.get("fx") or {}).get(cur.upper())
            sym = {"INR": "₹", "EUR": "€", "GBP": "£"}.get(cur.upper(), cur.upper() + " ")
            parts.append(f"{sym}{usd * rate:,.0f}" if rate else f"{cur.upper()} (set fx rate)")
    return " / ".join(parts)


def short(n):
    return f"{n / 1e6:.1f}M" if n >= 1e6 else f"{n / 1e3:.0f}K" if n >= 1e3 else str(int(n))


def model_label(models, pricing):
    out = []
    for m in sorted(models):
        _, p = cr.match_price(m, pricing)
        out.append(p["label"].replace("Claude ", "") if p else m)
    return ", ".join(out)


def measure(rows, pricing, sidechain_only=None):
    """Totals for one transcript's rows."""
    usage = cr.collect_usage(rows)
    t = {"new": 0, "input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "thinking": 0, "usd": 0.0, "requests": 0,
         "models": set(), "unknown": set(), "per_model": {}}
    for (model, u, ts, side) in usage.values():
        if sidechain_only is not None and side != sidechain_only:
            continue
        key, c = cr.price_request(model, u, pricing)
        if key is None:
            t["unknown"].add(model)
        cw = c["cw5"] + c["cw1h"]
        t["new"] += c["input"] + cw + c["output"]
        t["input"] += c["input"]; t["cache_write"] += cw; t["cache_read"] += c["cache_read"]
        t["output"] += c["output"]; t["thinking"] += c.get("thinking", 0)
        t["usd"] += c["cost"]
        t["requests"] += 1
        t["models"].add(model)
        pm = t["per_model"].setdefault(model, {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "thinking": 0})
        pm["input"] += c["input"]; pm["cache_write"] += cw; pm["cache_read"] += c["cache_read"]
        pm["output"] += c["output"]; pm["thinking"] += c.get("thinking", 0)
    stamps = [cr.parse_ts(r.get("timestamp")) for r in rows]
    stamps = [s for s in stamps if s]
    t["start"] = min(stamps) if stamps else None
    t["end"] = max(stamps) if stamps else None
    t["minutes"] = round((t["end"] - t["start"]).total_seconds() / 60) if stamps else 0
    tools = set()
    for r in rows:
        if r.get("type") == "assistant" and (side_ok := (sidechain_only is None or bool(r.get("isSidechain")) == sidechain_only)):
            for b in (r.get("message") or {}).get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use":
                    tools.add(b.get("id"))
    t["tool_calls"] = len(tools)
    return t


def file_keys(rows):
    text = ""
    for r in rows[:3]:
        c = (r.get("message") or {}).get("content")
        text += c if isinstance(c, str) else " ".join(b.get("text", "") for b in c or [] if isinstance(b, dict))
    return sorted(set(re.findall(r"figma\.com/(?:design|file)/([A-Za-z0-9]{10,})", text)))


def client_for(rows):
    """Match a Figma file key in the task prompt to a client notes file."""
    text = ""
    for r in rows[:3]:
        c = (r.get("message") or {}).get("content")
        text += c if isinstance(c, str) else " ".join(b.get("text", "") for b in c or [] if isinstance(b, dict))
    keys = set(re.findall(r"figma\.com/(?:design|file)/([A-Za-z0-9]{10,})", text)) | set(re.findall(r"\b([A-Za-z0-9]{22})\b", text))
    for f in sorted((FM / "clients").rglob("*.md")):
        if f.name == "client.md" or any(part.startswith("_template") for part in f.parts):
            continue
        body = f.read_text(errors="ignore")
        if any(k in body for k in keys):
            m = re.search(r"^#\s*(.+?)(\s+[—-].*)?$", body, re.M)
            project = m.group(1).strip() if m else f.stem
            cm = f.parent / "client.md"
            if cm.exists():
                cmh = re.search(r"^#\s*(.+)$", cm.read_text(errors="ignore"), re.M)
                if cmh:
                    return f"{cmh.group(1).strip()} › {project}"
            return project
    return ""


def find_session(a):
    if a.session:
        p = Path(os.path.expanduser(a.session))
        if p.suffix == ".jsonl" and p.exists():
            return p
        hits = [h for h in (cr.claude_home() / "projects").glob(f"**/{a.session}*.jsonl") if "subagents" not in h.parts]
        if hits:
            return hits[0]
        sys.exit(f"Session {a.session} not found")
    tdir = cr.project_transcript_dir(a.cwd or os.getcwd())
    if not tdir:
        sys.exit("No Claude Code transcripts for this project")
    files = cr.main_session_files(tdir)
    if not files:
        sys.exit("No sessions found")
    return files[0]


def tasks_of(session_file, pricing):
    out = []
    d = session_file.with_suffix("") / "subagents"
    for f in sorted(d.glob("agent-*.jsonl"), key=lambda p: p.stat().st_mtime):
        meta = {}
        mp = f.with_suffix(".meta.json")
        if mp.exists():
            try:
                meta = json.loads(mp.read_text())
            except Exception:
                pass
        rows = cr.read_jsonl(f)
        t = measure(rows, pricing)
        if not t["requests"]:
            continue
        t.update({"id": f.stem.replace("agent-", ""), "agent": meta.get("agentType", "agent"),
                  "description": meta.get("description", f.stem), "client": client_for(rows), "file": str(f),
                  "file_keys": file_keys(rows)})
        out.append(t)
    return out


def pick_task(tasks, sel):
    if not tasks:
        sys.exit("No agent tasks in this session")
    if sel in (None, "latest"):
        return max(tasks, key=lambda t: t["end"] or datetime.min.replace(tzinfo=timezone.utc))
    for t in tasks:
        if t["id"].startswith(sel) or sel.lower() in t["description"].lower():
            return t
    sys.exit(f"No task matching '{sel}'")


def n(x):
    return f"{int(x or 0):,}"


def tokens_text(d):
    """'input X (uncached a, cache write b, cache read c) · output Y (reasoning r) · total T' for one token bucket."""
    inp = d.get("input", 0) + d.get("cache_write", 0) + d.get("cache_read", 0)
    out = d.get("output", 0)
    reason = f" (reasoning {n(d['thinking'])})" if d.get("thinking") else ""
    return (f"input {n(inp)} (uncached {n(d.get('input'))}, cache write {n(d.get('cache_write'))}, cache read {n(d.get('cache_read'))})"
            f" · output {n(out)}{reason} · total {n(inp + out)}")


def models_tokens(t, pricing):
    """One segment per model: '<Model>: <tokens>' (most tasks use one model)."""
    pm = t.get("per_model") or {}
    if len(pm) <= 1:
        return f"{model_label(t['models'], pricing)} — {tokens_text(t)}"
    return "; ".join(f"{model_label({m}, pricing)}: {tokens_text(v)}" for m, v in sorted(pm.items()))


HEAVY = {"figma-maintainer:figma-maintainer": (6_000_000, 60)}  # input tokens incl. cache, tool calls; others: (3M, 50)


def budget_flag(t):
    """' ⚠ heavy task: <why>' when a task used far more tokens or calls than usual, or ran on Fable (no prices: they change)."""
    agent = t.get("agent", "")
    if not agent.startswith("figma-maintainer:") or agent.endswith("usage-reporter"):
        return ""
    tok_limit, call_limit = HEAVY.get(agent, (3_000_000, 50))
    models = " ".join(t.get("models") or []).lower()
    inp = t.get("input", 0) + t.get("cache_write", 0) + t.get("cache_read", 0)
    causes = []
    if "fable" in models or "mythos" in models:
        causes.append("ran on Fable, the most expensive model: pin the model or /model opus")
    if t.get("tool_calls", 0) > call_limit:
        causes.append(f"{t['tool_calls']} tool calls")
    if inp > tok_limit:
        causes.append(f"{short(inp)} input tokens (big screenshots or dumps, long context)")
    return (" ⚠ heavy task: " + "; ".join(causes)) if causes else ""


def task_line(t, cfg, pricing):
    """One task, tokens only (no prices: they change)."""
    who = f"{t['client']} — " if t["client"] else ""
    return (f"{who}{t['description']} · {models_tokens(t, pricing)} · {t['tool_calls']} tool calls · {t['minutes']} min"
            + budget_flag(t))


def log_task(t, session_id):
    FM.mkdir(parents=True, exist_ok=True)
    done = set()
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try:
                done.add(json.loads(line)["task_id"])
            except Exception:
                pass
    if t["id"] in done:
        return False
    rec = {"date": (t["end"] or datetime.now(timezone.utc)).strftime("%Y-%m-%d"), "session": session_id, "task_id": t["id"],
           "agent": t["agent"], "description": t["description"], "client": t["client"], "new_tokens": t["new"],
           "input_tokens": t.get("input", 0), "cache_write_tokens": t.get("cache_write", 0), "cache_read": t["cache_read"],
           "output_tokens": t.get("output", 0), "thinking_tokens": t.get("thinking", 0),
           "usd": round(t["usd"], 4), "minutes": t["minutes"], "tool_calls": t["tool_calls"],
           "models": sorted(t["models"]), "transcript": t.get("file", "")}
    with open(LEDGER, "a") as f:
        f.write(json.dumps(rec) + "\n")
    try:  # also into work/<person>/<agency>/<project>/usage.jsonl
        import workdir
        for k in t.get("file_keys", []):
            r = workdir.resolve_key(k)
            if r:
                proj = workdir.FM / "work" / workdir.person() / r[0] / r[1]
                workdir.ensure(proj)
                with open(proj / "usage.jsonl", "a") as f:
                    f.write(json.dumps(rec) + "\n")
                break
    except Exception:
        pass
    return True


def update_session_row(sf, tasks, pricing):
    """Upsert this session's totals (main conversation + plugin tasks) into usage-sessions.jsonl."""
    rows = cr.read_jsonl(sf)
    m = measure(rows, pricing, sidechain_only=False)
    fm = [t for t in tasks if str(t["agent"]).startswith("figma-maintainer:") and t["agent"] not in SKIP_AGENTS]
    folder = next((r.get("cwd") for r in rows if r.get("cwd")), "")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    row = {"session": sf.stem, "first": m["start"].strftime("%Y-%m-%d") if m["start"] else today,
           "last": m["end"].strftime("%Y-%m-%d") if m["end"] else today, "folder": folder,
           "main_new_tokens": m["new"], "main_input": m["input"], "main_cache_write": m["cache_write"],
           "main_cache_read": m["cache_read"], "main_output": m["output"], "main_thinking": m["thinking"], "main_usd": round(m["usd"], 4),
           "main_models": sorted(m["models"]), "tasks": len(fm), "tasks_usd": round(sum(t["usd"] for t in fm), 4),
           "clients": sorted({t["client"] for t in fm if t["client"]}),
           "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), "transcript": str(sf)}
    keep = []
    if SESSIONS.exists():
        for line in SESSIONS.read_text().splitlines():
            try:
                r = json.loads(line)
            except Exception:
                continue
            if r.get("session") != row["session"]:
                keep.append(r)
    keep.append(row)
    FM.mkdir(parents=True, exist_ok=True)
    SESSIONS.write_text("".join(json.dumps(r) + "\n" for r in keep))
    return row


def load_jsonl(path):
    out = []
    if Path(path).exists():
        for line in Path(path).read_text().splitlines():
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out


def report_all(a, cfg):
    """Consolidated report of this Mac's plugin history (tasks + sessions). Only on explicit request."""
    tasks = [r for r in load_jsonl(LEDGER) if str(r.get("agent", "")).startswith("figma-maintainer:")]  # other plugins' old rows out
    sessions = load_jsonl(SESSIONS)
    if a.since:
        tasks = [r for r in tasks if r.get("date", "") >= a.since]
        sessions = [r for r in sessions if r.get("last", "") >= a.since]
    if a.client:
        c = a.client.lower()
        tasks = [r for r in tasks if c in (r.get("client") or "").lower()]
        sessions = [r for r in sessions if any(c in x.lower() for x in r.get("clients") or [])]
    t_usd = sum(r["usd"] for r in tasks)
    m_usd = sum(r.get("main_usd", 0) for r in sessions)

    def task_tok(r):
        return {"input": r.get("input_tokens", 0), "cache_write": r.get("cache_write_tokens", 0), "cache_read": r.get("cache_read", 0),
                "output": r.get("output_tokens", 0), "thinking": r.get("thinking_tokens", 0)}

    def sess_tok(r):
        return {"input": r.get("main_input", 0), "cache_write": r.get("main_cache_write", 0), "cache_read": r.get("main_cache_read", 0),
                "output": r.get("main_output", 0), "thinking": r.get("main_thinking", 0)}

    def add(acc, d):
        for k, v in d.items():
            acc[k] = acc.get(k, 0) + v
        return acc
    tt = {}; [add(tt, task_tok(r)) for r in tasks]
    mt = {}; [add(mt, sess_tok(r)) for r in sessions]
    allt = add(add({}, tt), mt)
    old_rows = sum(1 for r in tasks if "input_tokens" not in r) + sum(1 for r in sessions if "main_input" not in r)
    scope = (f" · client {a.client}" if a.client else "") + (f" · since {a.since}" if a.since else "")
    out = [f"Consolidated usage on this Mac{scope}: {len(sessions)} session(s), {len(tasks)} plugin task(s)",
           f"Tokens: {tokens_text(allt)}",
           f"  main conversations: {tokens_text(mt)}",
           f"  plugin tasks: {tokens_text(tt)}",
           f"Estimated cost (list prices in pricing.json, which change): {money(t_usd + m_usd, cfg)} = main conversations "
           f"{money(m_usd, cfg)} + plugin tasks {money(t_usd, cfg)}"]
    if old_rows:
        out.append(f"({old_rows} older row(s) have no token breakdown (their transcripts are gone); they count in the estimated cost, "
                   "and only their cache reads count in the token totals.)")
    if sessions:
        out.append("\nPer session (newest first):")
        for r in sorted(sessions, key=lambda r: r.get("last", ""), reverse=True):
            mtk = sess_tok(r)
            out.append(f"• {r.get('last')} · {', '.join(r.get('clients') or []) or '(no client)'} · main conversation "
                       f"{n(mtk['input'] + mtk['cache_write'] + mtk['cache_read'] + mtk['output'])} tokens, est. {money(r.get('main_usd', 0), cfg)}"
                       f" · {r.get('tasks', 0)} task(s) est. {money(r.get('tasks_usd', 0), cfg)} · session {str(r.get('session', ''))[:8]}")
    by = defaultdict(lambda: [0, 0.0, 0])
    for r in tasks:
        b = by[r.get("client") or "(no client)"]; b[0] += 1; b[1] += r["usd"]
        tk = task_tok(r); b[2] += tk["input"] + tk["cache_write"] + tk["cache_read"] + tk["output"]
    if by:
        out.append("\nPer client (plugin tasks):")
        for k, (cnt, usd, tok) in sorted(by.items(), key=lambda kv: -kv[1][1]):
            out.append(f"• {k}: {cnt} task(s), {n(tok)} tokens, est. {money(usd, cfg)}")
    ag = defaultdict(lambda: {"n": 0, "usd": 0.0, "calls": 0, "cached": 0, "tok": {}, "models": defaultdict(float)})
    for r in tasks:
        g = ag[r["agent"].split(":", 1)[1]]
        g["n"] += 1; g["usd"] += r["usd"]; g["calls"] += r.get("tool_calls", 0); g["cached"] += r.get("cache_read", 0)
        add(g["tok"], task_tok(r))
        ms = r.get("models") or ["?"]
        for mm in ms:
            g["models"][mm.replace("claude-", "")] += r["usd"] / len(ms)
    if ag:
        out.append("\nPer agent (average per task):")
        for k, g in sorted(ag.items(), key=lambda kv: -kv[1]["usd"]):
            mix = ", ".join(f"{mm} {v / g['usd']:.0%}" for mm, v in sorted(g["models"].items(), key=lambda kv: -kv[1])) if g["usd"] else ""
            avg = {kk: v // g["n"] for kk, v in g["tok"].items()}
            out.append(f"• {k}: {g['n']} task(s), avg per task: {tokens_text(avg)}, {g['calls'] // g['n']} tool calls, "
                       f"est. {money(g['usd'] / g['n'], cfg)} · cost by model: {mix}")
    out.append("\nNote: each session's main-conversation cost is recorded when a plugin agent finishes, so the part after its last agent "
               "isn't included; sessions from before the session history started (v1.33.1) show only their plugin tasks.")
    text = "\n".join(out)
    print(text)
    if a.html:
        import html as h
        rep = FM / "reports"; rep.mkdir(parents=True, exist_ok=True)
        f = rep / f"cost-all-{datetime.now().strftime('%Y-%m-%d')}.html"
        body = "".join(f"<li>{h.escape(l[2:])}</li>" if l.startswith("• ") else
                       (f"<h2>{h.escape(l.strip())}</h2>" if l.strip().endswith(":") else f"<p>{h.escape(l)}</p>") for l in out if l.strip())
        f.write_text("<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>"
                     "<title>Plugin cost history</title><style>body{font:15px/1.6 system-ui,sans-serif;max-width:860px;margin:32px auto;padding:0 16px;"
                     "color:#151a24;background:#f6f7f9}h1{font-size:26px}h2{font-size:17px;margin-top:24px}li{margin:4px 0}"
                     "@media(prefers-color-scheme:dark){body{color:#e7eaf0;background:#10141c}}</style></head><body>"
                     f"<h1>figma-maintainer cost history</h1>{body}</body></html>")
        print(f"\nHTML: {f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session"); ap.add_argument("--cwd")
    ap.add_argument("--task"); ap.add_argument("--slack", action="store_true")
    ap.add_argument("--all", action="store_true", help="consolidated report of this Mac's history (cost-report-all only)")
    ap.add_argument("--ledger", action="store_true", help="alias of --all")
    ap.add_argument("--client"); ap.add_argument("--since"); ap.add_argument("--html", action="store_true")
    ap.add_argument("--rebuild-sessions", action="store_true",
                    help="one-time: rebuild usage-sessions.jsonl from the transcripts the task log points to")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hook-subagent-stop", action="store_true")
    a = ap.parse_args()
    pricing, cfg = cr.load_pricing(), cost_cfg()

    if a.hook_subagent_stop:
        try:
            hook = json.load(sys.stdin)
        except Exception:
            sys.exit(0)
        tp = hook.get("transcript_path")
        if not tp or not Path(tp).exists():
            sys.exit(0)
        sf = Path(tp)
        tasks = tasks_of(sf, pricing)
        aid = hook.get("agent_id") or ""
        cand = [t for t in tasks if aid and t["id"].startswith(aid)] or tasks[-1:]
        if not cand or cand[0]["agent"] in SKIP_AGENTS or not cand[0]["agent"].startswith("figma-maintainer:"):
            sys.exit(0)  # only figma-maintainer agents are logged
        t = cand[0]
        logged = log_task(t, sf.stem)
        try:  # this session's totals (main conversation + plugin tasks) for the consolidated history
            update_session_row(sf, tasks, pricing)
        except Exception as e:
            print(f"usage_report: session row not saved: {e}", file=sys.stderr)
        if logged:
            print(json.dumps({"systemMessage": "Usage: " + task_line(t, cfg, pricing)}))
        sys.exit(0)

    if a.rebuild_sessions:
        seen, n = set(), 0
        for r in load_jsonl(LEDGER):
            tp = Path(r.get("transcript") or "")
            sf = tp.parent.parent.with_suffix(".jsonl") if tp.parent.name == "subagents" else None
            if not sf or sf in seen or not sf.exists() or not str(r.get("agent", "")).startswith("figma-maintainer:"):
                continue
            seen.add(sf)
            update_session_row(sf, tasks_of(sf, pricing), pricing); n += 1
        # past task rows: exact token breakdown re-measured from their transcripts
        rows, fixed = load_jsonl(LEDGER), 0
        for r in rows:
            tp = Path(r.get("transcript") or "")
            if r.get("transcript") and tp.is_file() and "input_tokens" not in r:
                t = measure(cr.read_jsonl(tp), pricing)
                r.update({"input_tokens": t["input"], "cache_write_tokens": t["cache_write"], "cache_read": t["cache_read"],
                          "output_tokens": t["output"], "thinking_tokens": t["thinking"]}); fixed += 1
        if fixed:
            LEDGER.write_text("".join(json.dumps(r) + "\n" for r in rows))
        print(f"Session history rebuilt: {n} session(s) → {SESSIONS}; token breakdown added to {fixed} past task(s)")
        return

    if a.all or a.ledger:
        report_all(a, cfg)
        return

    sf = find_session(a)
    tasks = [t for t in tasks_of(sf, pricing) if t["agent"] not in SKIP_AGENTS]
    main_t = measure(cr.read_jsonl(sf), pricing, sidechain_only=False)
    total = {k: main_t[k] + sum(t.get(k, 0) for t in tasks) for k in ("input", "cache_write", "cache_read", "output", "thinking")}
    models = set(main_t["models"]).union(*[t["models"] for t in tasks]) if tasks else main_t["models"]
    unknown = set(main_t["unknown"]).union(*[t["unknown"] for t in tasks]) if tasks else main_t["unknown"]

    if a.json:
        keep = ("input", "cache_write", "cache_read", "output", "thinking")
        print(json.dumps({"session": sf.stem, "tokens": total, "models": sorted(models),
                          "main": {k: main_t[k] for k in keep},
                          "tasks": [{"id": t["id"], "agent": t["agent"], "description": t["description"], "client": t["client"],
                                     "models": sorted(t["models"]), "tool_calls": t["tool_calls"], "minutes": t["minutes"],
                                     **{k: t[k] for k in keep}} for t in tasks]}, indent=2, default=str))
        return

    if a.task:
        t = pick_task(tasks, a.task)
        line = task_line(t, cfg, pricing)
        print(f"Usage (internal)\n• {line}" if a.slack else line)
        return

    lines = ["Usage (internal)"] if a.slack else [f"Session {sf.stem[:8]} — {main_t['start']:%d %b %Y}" if main_t["start"] else "Session"]
    for t in tasks:
        lines.append("• " + task_line(t, cfg, pricing))
    lines.append(f"• Main conversation · {models_tokens(main_t, pricing)}")
    lines.append(f"• Session total · {len(tasks)} task(s) · {tokens_text(total)} · models: {model_label(models, pricing)}")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
