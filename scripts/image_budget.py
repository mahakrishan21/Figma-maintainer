#!/usr/bin/env python3
"""PreToolUse hook: keeps figma-maintainer agents within their image budget.

Every image an agent looks at (a screenshot, or a PNG it reads) stays in its context for the rest of the job
and is paid for again on every later step. Each agent has a budget; when it reaches it, the hook asks the user
before the next image (and again every 4 images), with a hint for a cheaper way. Below the budget it says
nothing. Only figma-maintainer's own agents are counted; other plugins and the main conversation are untouched.
It never blocks Figma writes.
"""
import json, os, re, sys
from pathlib import Path

BUDGET = {"figma-maintainer": 8, "qa-checker": 5, "client-comments": 6}
DEFAULT = 6
EVERY = 4
IMG = re.compile(r"\.(png|jpe?g|gif|webp)$", re.I)
HINTS = {
    "qa-checker": "Look at the QA contact sheet (all crops in one image) and use fm_query.py for details; open a single crop only for fine text.",
    "client-comments": "Use figma_outline.py or fm_query.py for structure and text; screenshot only the commented sections, at reduced scale.",
}


def transcript(hook):
    tp = hook.get("transcript_path") or ""
    aid = hook.get("agent_id") or ""
    if "/subagents/" in tp:
        return Path(tp)
    if tp and aid:
        return Path(tp).with_suffix("") / "subagents" / f"agent-{aid}.jsonl"
    return None


def agent_type(hook, tp):
    a = hook.get("agent_type") or ""
    if not a and tp:
        try:
            a = json.loads(tp.with_suffix(".meta.json").read_text()).get("agentType", "")
        except Exception:
            pass
    return a


def images_so_far(tp):
    n = 0
    try:
        with open(tp, errors="ignore") as f:
            for line in f:
                if '"image"' not in line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                for b in (r.get("message") or {}).get("content") or []:
                    if isinstance(b, dict) and b.get("type") == "tool_result" and isinstance(b.get("content"), list):
                        n += sum(1 for c in b["content"] if isinstance(c, dict) and c.get("type") == "image")
    except Exception:
        return 0
    return n


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        return
    name, inp = hook.get("tool_name", ""), hook.get("tool_input") or {}
    if name == "Read" and not IMG.search(str(inp.get("file_path", ""))):
        return
    if name != "Read" and not name.endswith("__get_screenshot"):
        return
    tp = transcript(hook)
    if not tp:
        return
    who = agent_type(hook, tp)
    if not who.startswith("figma-maintainer:"):
        return
    short = who.split(":", 1)[1]
    budget = BUDGET.get(short, DEFAULT)
    n = images_so_far(tp)
    if n < budget or (n - budget) % EVERY:
        return
    hint = HINTS.get(short, "Use the scripts' summaries, fm_query.py or figma_outline.py, and screenshot sections at reduced scale.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                      "permissionDecisionReason": f"figma-maintainer image budget: {short} has looked at {n} images (budget {budget}). "
                                                  f"Each one stays in context for the rest of the job. {hint} Allow this one?"}}))


if __name__ == "__main__":
    main()
