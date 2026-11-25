#!/usr/bin/env python3
"""Token benchmark for figma-maintainer tasks: where each task's context goes (read-only).

  token_bench.py                          every task in usage-log.jsonl that still has a transcript
  token_bench.py --since 2026-11-25       only tasks from that date on
  token_bench.py --task <id> [--task …]   specific tasks (ids from usage-log.jsonl or agent-<id>.jsonl)
  token_bench.py --transcript <path> …    specific subagent transcripts
  token_bench.py … --md <file>            also write the report as Markdown
  token_bench.py … --json                 machine-readable

Per task: input tokens (fresh + cache write + cache read), output tokens, tool calls, images that entered
context, and the characters each kind of tool result added (use_figma, get_metadata, screenshots, Markdown
reads, inline Python, script output …). Tool results stay in context for every later turn, so big early
results cost many times their size.
"""
import argparse, json, os, re, statistics, sys
from collections import defaultdict
from pathlib import Path

FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
CLAUDE = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
IMG = re.compile(r"\.(png|jpe?g|gif|webp)$", re.I)


def kind(name, inp):
    """A short label for a tool call, by what it reads."""
    if "__" in name and name.startswith("mcp__"):
        tool = name.rsplit("__", 1)[1]
        return tool if tool in ("use_figma", "get_metadata", "get_screenshot", "get_figma_skill", "get_design_context",
                                "get_variable_defs") else "mcp:other"
    if name == "Read":
        p = str(inp.get("file_path", ""))
        if IMG.search(p):
            return "read:image"
        ext = Path(p).suffix.lower().lstrip(".")
        return f"read:{ext if ext in ('md', 'json', 'txt', 'jsonl', 'html') else 'other'}"
    if name == "Bash":
        c = str(inp.get("command", ""))
        if re.search(r"python3?\s+(-I\s+)?-\s*<<|python3?\s+(-I\s+)?-c\b", c):
            return "bash:inline-python"
        m = re.search(r"scripts/([a-z_]+)\.py", c)
        if m:
            return f"script:{m.group(1)}"
        return "bash:other"
    return name.lower()


def size(content):
    """(characters, images) of a tool result."""
    if isinstance(content, str):
        return len(content), 0
    chars = imgs = 0
    for b in content or []:
        if not isinstance(b, dict):
            continue
        if b.get("type") == "image":
            imgs += 1
        elif b.get("type") == "text":
            chars += len(b.get("text", ""))
        elif b.get("type") == "tool_result":
            c, i = size(b.get("content"))
            chars += c; imgs += i
    return chars, imgs


def bench(path):
    calls, seen = {}, set()
    t = {"input": 0, "cache_write": 0, "cache_read": 0, "output": 0, "tool_calls": 0, "images": 0,
         "chars": defaultdict(int), "count": defaultdict(int), "models": set()}
    with open(path, errors="ignore") as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            msg = r.get("message") or {}
            content = msg.get("content")
            if r.get("type") == "assistant":
                mid = msg.get("id") or r.get("uuid")
                u = msg.get("usage") or {}
                if u and mid not in seen:  # one usage per API request (a request can span several rows)
                    seen.add(mid)
                    t["input"] += u.get("input_tokens", 0); t["output"] += u.get("output_tokens", 0)
                    t["cache_write"] += u.get("cache_creation_input_tokens", 0); t["cache_read"] += u.get("cache_read_input_tokens", 0)
                    if msg.get("model"):
                        t["models"].add(msg["model"])
                for b in content or []:
                    if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id") not in calls:
                        calls[b["id"]] = kind(b.get("name", ""), b.get("input") or {})
                        t["tool_calls"] += 1
            elif r.get("type") == "user" and isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get("type") == "tool_result":
                        k = calls.get(b.get("tool_use_id"), "unknown")
                        c, i = size(b.get("content"))
                        t["chars"][k] += c; t["count"][k] += 1; t["images"] += i
                        if i and k not in ("read:image", "get_screenshot"):
                            t["chars"]["images-in:" + k] += 0
    t["total_input"] = t["input"] + t["cache_write"] + t["cache_read"]
    return t


def locate(row):
    p = row.get("transcript")
    if p and Path(p).exists():
        return Path(p)
    hits = list((CLAUDE / "projects").glob(f"*/{row.get('session')}/subagents/agent-{row.get('task_id')}.jsonl"))
    return hits[0] if hits else None


def load_rows(a):
    rows = []
    try:
        with open(FM / "usage-log.jsonl") as f:
            rows = [json.loads(l) for l in f if l.strip()]
    except Exception:
        pass
    if a.task:
        rows = [r for r in rows if r.get("task_id") in a.task]
    if a.since:
        rows = [r for r in rows if r.get("date", "") >= a.since]
    return [r for r in rows if r.get("agent", "").startswith("figma-maintainer:") and "usage-reporter" not in r.get("agent", "")]


def short(n):
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}k" if n >= 1e3 else str(n)


def report(tasks):
    by_agent = defaultdict(list)
    for t in tasks:
        by_agent[t["agent"].split(":")[-1]].append(t)
    out = ["| Agent | Tasks | Median input | Total input | Median calls | Images | Result chars |", "|---|---|---|---|---|---|---|"]
    for ag, ts in sorted(by_agent.items()):
        out.append(f"| {ag} | {len(ts)} | {short(statistics.median(x['total_input'] for x in ts))} | "
                   f"{short(sum(x['total_input'] for x in ts))} | {statistics.median(x['tool_calls'] for x in ts):.0f} | "
                   f"{sum(x['images'] for x in ts)} | {short(sum(sum(x['chars'].values()) for x in ts))} |")
    kinds = defaultdict(lambda: [0, 0])
    for t in tasks:
        for k, c in t["chars"].items():
            kinds[k][0] += c; kinds[k][1] += t["count"].get(k, 0)
    out += ["", "| Tool result kind | Calls | Characters | Avg |", "|---|---|---|---|"]
    for k, (c, n) in sorted(kinds.items(), key=lambda kv: -kv[1][0])[:18]:
        if n:
            out.append(f"| {k} | {n} | {short(c)} | {short(c // n)} |")
    imgs = sum(t["images"] for t in tasks)
    out.append(f"\n{len(tasks)} task(s) · {imgs} image(s) in context · total input {short(sum(t['total_input'] for t in tasks))}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since"); ap.add_argument("--task", action="append"); ap.add_argument("--transcript", action="append")
    ap.add_argument("--md"); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    tasks = []
    if a.transcript:
        for p in a.transcript:
            meta = Path(p).with_suffix(".meta.json")
            ag = json.loads(meta.read_text()).get("agentType", "agent") if meta.exists() else "agent"
            tasks.append({**bench(p), "agent": ag, "id": Path(p).stem.replace("agent-", ""), "description": ""})
    else:
        for r in load_rows(a):
            p = locate(r)
            if p:
                tasks.append({**bench(p), "agent": r["agent"], "id": r["task_id"], "description": r.get("description", ""),
                              "date": r.get("date", "")})
    if not tasks:
        sys.exit("No figma-maintainer task transcripts found.")
    if a.json:
        print(json.dumps([{**t, "chars": dict(t["chars"]), "count": dict(t["count"]), "models": sorted(t["models"])} for t in tasks], indent=1))
        return
    text = report(tasks)
    print(text)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        rows = "\n".join(f"| {t.get('date', '')} | {t['agent'].split(':')[-1]} | {t['description'][:50]} | {short(t['total_input'])} | "
                         f"{t['tool_calls']} | {t['images']} |" for t in tasks)
        Path(a.md).write_text(f"# Token benchmark\n\n{text}\n\n## Per task\n| Date | Agent | Task | Input | Calls | Images |\n"
                              f"|---|---|---|---|---|---|\n{rows}\n")
        print(f"\nSaved {a.md}")


if __name__ == "__main__":
    main()
