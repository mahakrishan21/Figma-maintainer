#!/usr/bin/env python3
"""
Design Cost Report for Claude Code
----------------------------------
Reads Claude Code session transcripts (~/.claude/projects/**.jsonl), totals
tokens per model (including sub-agents), prices them with pricing.json and
writes a self-contained, client-ready HTML report.

Usage examples
  python generate_report.py                         # latest session in current folder
  python generate_report.py --session <id>          # a specific session
  python generate_report.py --all-sessions          # every session for this project
  python generate_report.py --since 2026-10-01      # sessions since a date
  python generate_report.py --hook                  # called by a Claude Code hook (reads stdin)

Per-project settings (optional) go in  <project>/.design-report.json :
  {"design_name": "Landing page v2", "client_name": "Acme Ltd",
   "studio_name": "Your Studio", "currency": "INR", "fx_rate": 84.0,
   "markup_percent": 0, "output_dir": "reports", "show_session_ids": false}
No tokens are spent: this is plain Python, no model calls.
"""
import argparse, glob, html, json, os, re, sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
# figma-maintainer: the team-editable copy wins over the bundled one
_USER_PRICING = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer") / "pricing.json"
PRICING_FILE = _USER_PRICING if _USER_PRICING.exists() else HERE.parent / "seed" / "pricing.json"


# ---------------------------------------------------------------- helpers
def claude_home() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def read_jsonl(path):
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except FileNotFoundError:
        pass
    return out


def load_pricing():
    with open(PRICING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def match_price(model, pricing):
    """Longest prefix match of the model id against pricing keys."""
    best = None
    for key in pricing["models"]:
        if model.startswith(key) and (best is None or len(key) > len(best)):
            best = key
    return (best, pricing["models"][best]) if best else (None, None)


def load_config(project_dir: Path):
    cfg = {
        "design_name": project_dir.name,
        "client_name": "",
        "studio_name": "",
        "currency": "USD",
        "fx_rate": 1.0,
        "markup_percent": 0,
        "output_dir": "reports",
        "show_session_ids": False,
    }
    p = project_dir / ".design-report.json"
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception as e:
            print(f"[design-cost-report] could not read {p}: {e}", file=sys.stderr)
    return cfg


# ------------------------------------------------------- finding sessions
def encode_cwd(cwd: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def project_transcript_dir(cwd: str):
    base = claude_home() / "projects"
    d = base / encode_cwd(cwd)
    if d.is_dir():
        return d
    # fallback: look for a folder whose transcripts mention this cwd
    norm = os.path.normcase(os.path.abspath(cwd))
    for sub in base.glob("*"):
        for f in list(sub.glob("*.jsonl"))[:3]:
            for row in read_jsonl(f)[:20]:
                c = row.get("cwd")
                if c and os.path.normcase(os.path.abspath(c)) == norm:
                    return sub
    return None


def main_session_files(tdir: Path):
    return sorted(tdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def subagent_files(session_file: Path):
    """Newer Claude Code keeps sub-agent transcripts in <session-id>/subagents/."""
    d = session_file.with_suffix("")
    return sorted(d.glob("subagents/*.jsonl")) + sorted(d.glob("*.jsonl"))


# ---------------------------------------------------------------- parsing
def new_bucket():
    return {"requests": 0, "input": 0, "output": 0, "cw5": 0, "cw1h": 0,
            "cache_read": 0, "web_search": 0, "cost": 0.0}


def price_request(model, u, pricing):
    key, p = match_price(model, pricing)
    inp = u.get("input_tokens", 0) or 0
    out = u.get("output_tokens", 0) or 0
    cr = u.get("cache_read_input_tokens", 0) or 0
    cc = u.get("cache_creation_input_tokens", 0) or 0
    det = u.get("cache_creation") or {}
    cw1h = det.get("ephemeral_1h_input_tokens", 0) or 0
    cw5 = det.get("ephemeral_5m_input_tokens", 0) or 0
    if cw5 + cw1h == 0 and cc:
        cw5 = cc                      # no breakdown given: assume 5-minute cache
    ws = (u.get("server_tool_use") or {}).get("web_search_requests", 0) or 0
    cost = 0.0
    if p:
        rates = p
        lc = p.get("long_context")
        if lc and (inp + cr + cw5 + cw1h) > lc["threshold"]:
            rates = {**p, **lc}
        cost = (inp * rates["input"] + out * rates["output"] + cw5 * rates["cache_write_5m"]
                + cw1h * rates["cache_write_1h"] + cr * rates["cache_read"]) / 1_000_000
    cost += ws * pricing.get("web_search_per_1000", 10.0) / 1000
    return key, {"input": inp, "output": out, "cw5": cw5, "cw1h": cw1h,
                 "cache_read": cr, "web_search": ws, "cost": cost}


def collect_usage(rows):
    """Return {(msg_id, req_id): (model, usage, ts, is_sidechain)} keeping the
    most complete usage per API response (Claude Code writes one line per
    content block, all repeating the same message id)."""
    seen = {}
    for r in rows:
        if r.get("type") != "assistant":
            continue
        m = r.get("message") or {}
        u = m.get("usage")
        model = m.get("model") or ""
        if not u or not model or model.startswith("<"):   # skip <synthetic>
            continue
        k = (m.get("id") or r.get("uuid"), r.get("requestId"))
        prev = seen.get(k)
        if prev is None or (u.get("output_tokens", 0) or 0) >= (prev[1].get("output_tokens", 0) or 0):
            seen[k] = (model, u, r.get("timestamp"), bool(r.get("isSidechain")))
    return seen


def analyse_session(session_file: Path, pricing):
    rows = read_jsonl(session_file)
    sub_rows = []
    sub_files = subagent_files(session_file)
    for sf in sub_files:
        for r in read_jsonl(sf):
            r["isSidechain"] = True
            sub_rows.append(r)

    usage = collect_usage(rows)
    for k, v in collect_usage(sub_rows).items():
        usage.setdefault(k, v)

    per_model = defaultdict(new_bucket)
    main_cost = sub_cost = 0.0
    unknown = set()
    for (model, u, ts, side) in usage.values():
        key, c = price_request(model, u, pricing)
        if key is None:
            unknown.add(model)
        b = per_model[model]
        b["requests"] += 1
        for f in ("input", "output", "cw5", "cw1h", "cache_read", "web_search", "cost"):
            b[f] += c[f]
        if side:
            sub_cost += c["cost"]
        else:
            main_cost += c["cost"]

    # timeline, prompts, sub-agents, files touched
    stamps = [parse_ts(r.get("timestamp")) for r in rows + sub_rows]
    stamps = [s for s in stamps if s]
    prompts = 0
    agent_types = defaultdict(int)
    files = {}
    title = None
    cwd = None
    for r in rows:
        cwd = cwd or r.get("cwd")
        if r.get("type") == "summary" and r.get("summary"):
            title = r["summary"]
        m = r.get("message") or {}
        if r.get("type") == "user" and not r.get("isMeta") and not r.get("isSidechain"):
            c = m.get("content")
            if isinstance(c, str) and c.strip() and not c.lstrip().startswith("<"):
                prompts += 1
            elif isinstance(c, list) and any(b.get("type") == "text" for b in c if isinstance(b, dict)) \
                    and not any(b.get("type") == "tool_result" for b in c if isinstance(b, dict)):
                prompts += 1
        if r.get("type") == "assistant":
            for b in m.get("content") or []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                name, inp = b.get("name"), b.get("input") or {}
                if name in ("Task", "Agent"):
                    agent_types[inp.get("subagent_type") or "general-purpose"] += 1
                fp = inp.get("file_path") or inp.get("notebook_path")
                if name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and fp:
                    files[fp] = files.get(fp) or ("created" if name == "Write" else "edited")

    return {
        "id": session_file.stem,
        "file": str(session_file),
        "title": title,
        "cwd": cwd,
        "start": min(stamps) if stamps else None,
        "end": max(stamps) if stamps else None,
        "prompts": prompts,
        "per_model": dict(per_model),
        "main_cost": main_cost,
        "sub_cost": sub_cost,
        "subagent_runs": max(len(sub_files), sum(agent_types.values())),
        "agent_types": dict(agent_types),
        "files": files,
        "unknown_models": sorted(unknown),
    }


# ---------------------------------------------------------------- report
def fmt_int(n):
    return f"{int(n):,}"


def fmt_dur(sec):
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, _ = divmod(rem, 60)
    return f"{h}h {m}m" if h else f"{m}m"


def money(v, cfg):
    cur = cfg["currency"].upper()
    v = v * float(cfg.get("fx_rate") or 1)
    sym = {"USD": "$", "INR": "₹", "EUR": "€", "GBP": "£", "AED": "AED "}.get(cur, cur + " ")
    return f"{sym}{v:,.4f}" if v < 1 else f"{sym}{v:,.2f}"


CSS = """
:root{--bg:#f6f5f1;--card:#ffffff;--ink:#1d1d1b;--muted:#6b6a64;--line:#e4e2da;
--accent:#c2552d;--a2:#2f6f62;--a3:#d9a441;--a4:#6a5acd;--a5:#8a8a80;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--card:#1f1f1c;--ink:#f0eee8;
--muted:#a3a198;--line:#33322d;--accent:#e57a50;--a2:#5fb3a1;--a3:#e6bd62;--a4:#9d8ff0;--a5:#77776f;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.55 "Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
.wrap{max-width:960px;margin:0 auto;padding:40px 24px 64px}
header{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:18px;margin-bottom:28px}
.eyebrow{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
h1{font:600 32px/1.15 Georgia,"Times New Roman",serif;margin:6px 0 0}
.meta{text-align:right;color:var(--muted);font-size:13px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin-bottom:28px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 18px}
.kpi .v{font:600 26px/1.2 Georgia,serif;margin-top:4px}.kpi.hero{border-color:var(--accent)}
.kpi.hero .v{color:var(--accent)}
section{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px 22px;margin-bottom:18px}
h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 14px;font-weight:600}
.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:9px 8px;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}th{font-weight:600;color:var(--muted);font-size:12px}
tfoot td{font-weight:700;border-bottom:none;border-top:2px solid var(--ink)}
.bar{display:flex;height:14px;border-radius:7px;overflow:hidden;background:var(--line);margin:6px 0 12px}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:13px;color:var(--muted)}
.dot{display:inline-block;width:10px;height:10px;border-radius:3px;margin-right:6px;vertical-align:-1px}
ul.files{margin:0;padding-left:18px}ul.files li{margin:3px 0;word-break:break-all}
.tag{font-size:11px;border:1px solid var(--line);border-radius:4px;padding:1px 6px;color:var(--muted);margin-left:6px}
.note{font-size:12px;color:var(--muted);margin-top:22px;line-height:1.6}
.warn{color:var(--accent)}
@media print{body{background:#fff}.wrap{padding:0}section,.kpi{break-inside:avoid}}
"""


def build_html(sessions, cfg, pricing):
    agg = defaultdict(new_bucket)
    for s in sessions:
        for model, b in s["per_model"].items():
            for f, v in b.items():
                agg[model][f] += v
    total_cost = sum(b["cost"] for b in agg.values())
    markup = float(cfg.get("markup_percent") or 0)
    billed = total_cost * (1 + markup / 100)
    tok = {f: sum(b[f] for b in agg.values()) for f in ("input", "output", "cw5", "cw1h", "cache_read")}
    total_tokens = sum(tok.values())
    starts = [s["start"] for s in sessions if s["start"]]
    ends = [s["end"] for s in sessions if s["end"]]
    active = sum(((s["end"] - s["start"]).total_seconds() for s in sessions if s["start"] and s["end"]), 0)
    prompts = sum(s["prompts"] for s in sessions)
    sub_runs = sum(s["subagent_runs"] for s in sessions)
    sub_cost = sum(s["sub_cost"] for s in sessions)
    agent_types = defaultdict(int)
    files = {}
    for s in sessions:
        for k, v in s["agent_types"].items():
            agent_types[k] += v
        files.update(s["files"])
    unknown = sorted({m for s in sessions for m in s["unknown_models"]})

    e = html.escape
    label = lambda m: (match_price(m, pricing)[1] or {}).get("label", m)
    period = ""
    if starts:
        a, b = min(starts).astimezone(), max(ends).astimezone()
        period = a.strftime("%d %b %Y") if a.date() == b.date() else f"{a:%d %b} – {b:%d %b %Y}"

    rows = []
    for m, b in sorted(agg.items(), key=lambda kv: -kv[1]["cost"]):
        share = (b["cost"] / total_cost * 100) if total_cost else 0
        rows.append(f"<tr><td>{e(label(m))}<span class='tag'>{e(m)}</span></td>"
                    f"<td>{fmt_int(b['requests'])}</td><td>{fmt_int(b['input'])}</td>"
                    f"<td>{fmt_int(b['output'])}</td><td>{fmt_int(b['cw5'] + b['cw1h'])}</td>"
                    f"<td>{fmt_int(b['cache_read'])}</td><td>{money(b['cost'], cfg)}</td>"
                    f"<td>{share:.0f}%</td></tr>")
    model_table = "".join(rows) or "<tr><td colspan=8>No usage found.</td></tr>"

    colors = ["var(--accent)", "var(--a2)", "var(--a3)", "var(--a4)", "var(--a5)"]
    parts = [("Input", tok["input"]), ("Output", tok["output"]),
             ("Cache write", tok["cw5"] + tok["cw1h"]), ("Cache read", tok["cache_read"])]
    bar = "".join(f"<span style='width:{(v / total_tokens * 100) if total_tokens else 0:.2f}%;background:{colors[i]}'></span>"
                  for i, (_, v) in enumerate(parts))
    legend = "".join(f"<span><i class='dot' style='background:{colors[i]}'></i>{n}: {fmt_int(v)}</span>"
                     for i, (n, v) in enumerate(parts))

    cost_split = ""
    if total_cost:
        mp = (total_cost - sub_cost) / total_cost * 100
        cost_split = (f"<div class='bar'><span style='width:{mp:.2f}%;background:var(--accent)'></span>"
                      f"<span style='width:{100 - mp:.2f}%;background:var(--a2)'></span></div>"
                      f"<div class='legend'><span><i class='dot' style='background:var(--accent)'></i>Main agent: {money(total_cost - sub_cost, cfg)}</span>"
                      f"<span><i class='dot' style='background:var(--a2)'></i>Sub-agents ({sub_runs} run{'' if sub_runs == 1 else 's'}): {money(sub_cost, cfg)}</span></div>")
    agents_list = ", ".join(f"{e(k)} × {v}" for k, v in sorted(agent_types.items(), key=lambda kv: -kv[1]))

    design_files = {k: v for k, v in files.items() if re.search(r"\.(html?|css|js|jsx|tsx|svg|vue)$", k, re.I)}
    base = Path(sessions[0]["cwd"]) if sessions and sessions[0]["cwd"] else None

    def rel(p):
        try:
            return str(Path(p).relative_to(base)) if base else p
        except ValueError:
            return p
    file_items = "".join(f"<li>{e(rel(k))}<span class='tag'>{v}</span></li>" for k, v in sorted(design_files.items()))

    sess_rows = ""
    for s in sorted(sessions, key=lambda s: s["start"] or datetime.min.replace(tzinfo=timezone.utc)):
        cost = sum(b["cost"] for b in s["per_model"].values())
        toks = sum(b["input"] + b["output"] + b["cw5"] + b["cw1h"] + b["cache_read"] for b in s["per_model"].values())
        when = s["start"].astimezone().strftime("%d %b %Y, %H:%M") if s["start"] else "—"
        dur = fmt_dur((s["end"] - s["start"]).total_seconds()) if s["start"] and s["end"] else "—"
        name = e(s["title"] or "Session")
        if cfg.get("show_session_ids"):
            name += f"<span class='tag'>{e(s['id'][:8])}</span>"
        sess_rows += (f"<tr><td>{name}</td><td>{when}</td><td>{dur}</td><td>{s['prompts']}</td>"
                      f"<td>{fmt_int(toks)}</td><td>{money(cost, cfg)}</td></tr>")

    markup_kpi = ""
    if markup:
        markup_kpi = f"<div class='kpi hero'><div class='eyebrow'>Billed (incl. {markup:g}% service)</div><div class='v'>{money(billed, cfg)}</div></div>"
    fx_note = ""
    if cfg["currency"].upper() != "USD":
        fx_note = f" Converted from USD at 1 USD = {float(cfg['fx_rate']):g} {e(cfg['currency'].upper())}."
    warn = ""
    if unknown:
        warn = f"<p class='warn'>Not priced (add to pricing.json): {e(', '.join(unknown))}</p>"

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI usage report – {e(cfg['design_name'])}</title><style>{CSS}</style></head><body><div class="wrap">
<header><div><div class="eyebrow">AI usage &amp; cost report{(' · ' + e(cfg['studio_name'])) if cfg.get('studio_name') else ''}</div>
<h1>{e(cfg['design_name'])}</h1></div>
<div class="meta">{('Client: <b>' + e(cfg['client_name']) + '</b><br>') if cfg.get('client_name') else ''}
{period}<br>Generated {datetime.now().astimezone():%d %b %Y, %H:%M}</div></header>

<div class="kpis">
<div class="kpi {'hero' if not markup else ''}"><div class="eyebrow">AI cost (API rates)</div><div class="v">{money(total_cost, cfg)}</div></div>
{markup_kpi}
<div class="kpi"><div class="eyebrow">Total tokens</div><div class="v">{fmt_int(total_tokens)}</div></div>
<div class="kpi"><div class="eyebrow">Models used</div><div class="v">{len(agg)}</div></div>
<div class="kpi"><div class="eyebrow">Sub-agent runs</div><div class="v">{sub_runs}</div></div>
<div class="kpi"><div class="eyebrow">Active time · prompts</div><div class="v">{fmt_dur(active)} · {prompts}</div></div>
</div>

<section><h2>Cost by model</h2><div class="scroll"><table>
<thead><tr><th>Model</th><th>API calls</th><th>Input</th><th>Output</th><th>Cache write</th><th>Cache read</th><th>Cost</th><th>Share</th></tr></thead>
<tbody>{model_table}</tbody>
<tfoot><tr><td>Total</td><td>{fmt_int(sum(b['requests'] for b in agg.values()))}</td><td>{fmt_int(tok['input'])}</td>
<td>{fmt_int(tok['output'])}</td><td>{fmt_int(tok['cw5'] + tok['cw1h'])}</td><td>{fmt_int(tok['cache_read'])}</td>
<td>{money(total_cost, cfg)}</td><td>100%</td></tr></tfoot></table></div>{warn}</section>

<section><h2>Where the tokens went</h2><div class="bar">{bar}</div><div class="legend">{legend}</div>
{('<h2 style="margin-top:22px">Main agent vs sub-agents</h2>' + cost_split) if cost_split else ''}
{('<p class="note" style="margin-top:10px">Sub-agents used: ' + agents_list + '</p>') if agents_list else ''}</section>

<section><h2>Sessions ({len(sessions)})</h2><div class="scroll"><table>
<thead><tr><th>Session</th><th>Started</th><th>Duration</th><th>Prompts</th><th>Tokens</th><th>Cost</th></tr></thead>
<tbody>{sess_rows}</tbody></table></div></section>

{('<section><h2>Design files produced</h2><ul class="files">' + file_items + '</ul></section>') if file_items else ''}

<p class="note">Costs are calculated from the token counts Claude Code records for each API call, priced at Anthropic's
published per-token API rates (pricing table updated {e(pricing.get('_updated', ''))}). If the work ran on a Claude
subscription plan rather than an API key, this is the API-equivalent value, not an amount charged.{fx_note}
Cache writes are billed at 1.25× (5-min) or 2× (1-hour) the input rate; cache reads at a small fraction of it.</p>
</div></body></html>"""


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="Claude Code design cost report")
    ap.add_argument("--hook", action="store_true", help="read hook JSON from stdin")
    ap.add_argument("--cwd", default=None, help="project folder (default: current)")
    ap.add_argument("--session", action="append", help="session id or .jsonl path (repeatable)")
    ap.add_argument("--all-sessions", action="store_true", help="every session for the project")
    ap.add_argument("--since", help="only sessions starting on/after YYYY-MM-DD")
    ap.add_argument("--design-name"); ap.add_argument("--client-name")
    ap.add_argument("--out", help="output .html path")
    ap.add_argument("--json", action="store_true", help="also print a JSON summary")
    a = ap.parse_args()

    hook = {}
    if a.hook:
        try:
            hook = json.load(sys.stdin)
        except Exception:
            hook = {}
    cwd = a.cwd or hook.get("cwd") or os.getcwd()
    project_dir = Path(cwd)
    cfg = load_config(project_dir)
    if a.design_name: cfg["design_name"] = a.design_name
    if a.client_name: cfg["client_name"] = a.client_name
    pricing = load_pricing()

    files = []
    if hook.get("transcript_path"):
        files = [Path(os.path.expanduser(hook["transcript_path"]))]
    elif a.session:
        tdir = project_transcript_dir(cwd)
        for s in a.session:
            p = Path(os.path.expanduser(s))
            if p.suffix == ".jsonl" and p.exists():
                files.append(p)
            else:
                hits = list((tdir or claude_home() / "projects").glob(f"**/{s}*.jsonl"))
                files += [h for h in hits if "subagents" not in h.parts][:1]
    else:
        tdir = project_transcript_dir(cwd)
        if not tdir:
            sys.exit(f"No Claude Code transcripts found for {cwd} under {claude_home() / 'projects'}")
        allf = main_session_files(tdir)
        files = allf if (a.all_sessions or a.since) else allf[:1]

    sessions = [analyse_session(f, pricing) for f in files if f.exists()]
    if a.since:
        cut = datetime.fromisoformat(a.since).replace(tzinfo=timezone.utc)
        sessions = [s for s in sessions if s["start"] and s["start"] >= cut]
    sessions = [s for s in sessions if s["per_model"]]
    if not sessions:
        sys.exit("No token usage found in the selected session(s).")

    out = Path(a.out) if a.out else None
    if not out:
        od = project_dir / cfg.get("output_dir", "reports")
        od.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9]+", "-", cfg["design_name"].lower()).strip("-") or "design"
        tag = sessions[0]["id"][:8] if len(sessions) == 1 else f"{len(sessions)}-sessions"
        out = od / f"ai-cost-{slug}-{datetime.now():%Y%m%d-%H%M}-{tag}.html"
    out.write_text(build_html(sessions, cfg, pricing), encoding="utf-8")

    total = sum(b["cost"] for s in sessions for b in s["per_model"].values())
    toks = sum(b["input"] + b["output"] + b["cw5"] + b["cw1h"] + b["cache_read"]
               for s in sessions for b in s["per_model"].values())
    models = sorted({m for s in sessions for m in s["per_model"]})
    msg = f"Design cost report: {out}  |  {toks:,} tokens  |  ${total:,.4f} USD  |  models: {', '.join(models)}"
    if a.hook:
        # SessionEnd/Stop hooks: keep stdout short; it may be shown in the transcript
        print(json.dumps({"systemMessage": msg}))
    else:
        print(msg)
    if a.json:
        print(json.dumps({"report": str(out), "usd": round(total, 6), "tokens": toks, "models": models,
                          "sessions": [s["id"] for s in sessions]}, indent=2))


if __name__ == "__main__":
    main()
