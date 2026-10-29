#!/usr/bin/env python3
"""PreToolUse guard for Figma write tools (enforced guardrails, not just instructions).

Blocks or escalates Figma MCP writes that break the team's security rules:
  DENY  - writes by read-only agents (auditors, usage-reporter, client-comments, qa-checker)
  DENY  - a Figma file that wasn't given in this task (file key absent from the user's / caller's messages)
  DENY  - network or dynamic code inside use_figma scripts (fetch, XHR, WebSocket, eval, new Function, importScripts)
  DENY  - deleting pages or the document
  ASK   - creating new Figma files or pages, editing variables/styles (shared design tokens),
          bulk deletes inside loops, plugin data/client storage, renaming the document
Every Figma write that passes is appended to ~/.claude/figma-maintainer/figma-audit-log.jsonl.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fm_scope import is_fm_agent, session_used_plugin  # noqa: E402
from datetime import datetime, timezone
from pathlib import Path

FM = Path.home() / ".claude" / "figma-maintainer"
READ_ONLY_AGENTS = ("consistency-auditor", "content-auditor", "accessibility-auditor", "usage-reporter", "client-comments", "qa-checker")


def out(decision, reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": "figma-maintainer guardrail: " + reason}}))
    sys.exit(0)


def log(rec):
    try:
        FM.mkdir(parents=True, exist_ok=True)
        with open(FM / "figma-audit-log.jsonl", "a") as f:
            f.write(json.dumps(rec) + "\n")
        if rec.get("fileKey"):  # also into work/<person>/<agency>/<project>/figma-calls.jsonl
            import workdir
            r = workdir.resolve_key(rec["fileKey"]) or ("_unassigned", rec["fileKey"])
            proj = workdir.FM / "work" / workdir.person() / r[0] / r[1]
            workdir.ensure(proj)
            with open(proj / "figma-calls.jsonl", "a") as f:
                f.write(json.dumps(rec) + "\n")
    except Exception as e:
        print(f"figma_guard: could not write audit log: {e}", file=sys.stderr)


def agent_type(hook):
    a = hook.get("agent_type") or ""
    tp = hook.get("transcript_path") or ""
    if not a and "/subagents/" in tp:
        meta = Path(tp).with_suffix(".meta.json")
        try:
            a = json.loads(meta.read_text()).get("agentType", "")
        except Exception:
            pass
    return a


RECENT_USER_MESSAGES = 15  # "this task" = the last N messages typed by the user


def user_texts(path):
    """User-typed messages in a transcript (not tool results), oldest first."""
    chunks = []
    for line in open(path, encoding="utf-8", errors="ignore"):
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("type") != "user" or r.get("isMeta"):
            continue
        c = (r.get("message") or {}).get("content")
        if isinstance(c, str):
            chunks.append(c)
        elif isinstance(c, list):
            t = [b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text"]
            if t:
                chunks.append("\n".join(t))
    return chunks


def instructed_text(hook):
    """What this task was authorized by: the user's recent messages, plus (inside an agent) the agent's task brief.
    Returns None when nothing can be read, so the caller fails closed."""
    tp = hook.get("transcript_path") or ""
    texts = []
    try:
        texts += user_texts(tp)[-RECENT_USER_MESSAGES:]
    except Exception:
        pass
    aid = hook.get("agent_id") or ""
    if tp and "/subagents/" in tp:
        try:
            texts += user_texts(tp)[:3]  # the agent's own brief
        except Exception:
            pass
    elif tp and aid:
        sub = Path(tp).with_suffix("") / "subagents" / f"agent-{aid}.jsonl"
        if sub.exists():
            texts += user_texts(sub)[:3]
    return "\n".join(texts) if texts else None


WRITE_RX = re.compile(r"\.\w+\s*=(?!=)|\.(remove|appendChild|insertChild|resize|resizeWithoutConstraints|setProperties|setReactionsAsync|"
                      r"setBoundVariable|setExplicitVariableModeForCollection|swapComponent|detachInstance|clone|createInstance)\s*\(|"
                      r"figma\.(create\w+|flatten|group|union|subtract|ungroup)\s*\(|upload|setRangeFills|setRangeTextStyleIdAsync|setTextStyleIdAsync")


def is_write(tool, code):
    if tool != "use_figma":
        return True
    # reading speed-ups and declarations don't change the canvas
    code = re.sub(r"figma\.skipInvisibleInstanceChildren\s*=\s*(true|false)", "", code)
    return bool(WRITE_RX.search(re.sub(r"(const|let|var)\s+\w+\s*=", "", code)))


def node_ids(code):
    return sorted(set(re.findall(r"""getNodeByIdAsync\(\s*['"`]([0-9I;:]+)['"`]""", code)))[:40]


def main():
    try:
        hook = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    if "--post" in sys.argv:  # PostToolUse: record that the call actually ran (after any approval)
        if not (is_fm_agent(agent_type(hook)) or session_used_plugin(hook.get("transcript_path", ""))):
            sys.exit(0)
        inp = hook.get("tool_input") or {}
        resp = json.dumps(hook.get("tool_response", ""))[:400]
        err = bool(re.search(r'"is_error"\s*:\s*true|Error:', resp))
        if is_write(hook.get("tool_name", "").split("__")[-1], inp.get("code") or ""):
            log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": hook.get("tool_name", "").split("__")[-1],
                 "fileKey": inp.get("fileKey", ""), "agent": agent_type(hook), "description": (inp.get("description") or "")[:200],
                 "decision": "completed-with-error" if err else "completed"})
        sys.exit(0)
    tool = hook.get("tool_name", "")
    inp = hook.get("tool_input") or {}
    short = tool.split("__")[-1]
    who = agent_type(hook)
    # Scope: only figma-maintainer agents and sessions that use the plugin. Other plugins' Figma calls are untouched.
    if not (is_fm_agent(who) or session_used_plugin(hook.get("transcript_path", ""))):
        sys.exit(0)
    key = inp.get("fileKey") or inp.get("file_key") or ""

    if any(who.endswith(a) for a in READ_ONLY_AGENTS):
        out("deny", f"{who} is read-only and may not write to Figma ({short}).")

    if short in ("create_new_file",):
        out("ask", "creates a new Figma file. Confirm this is wanted.")

    if key:
        text = instructed_text(hook)
        if text is None:
            out("deny", "can't read this task's instructions to confirm the file is authorized (failing closed). Link the Figma file in the prompt and retry.")
        if key not in text:
            out("deny", f"file {key} was not linked in this task (the user's recent messages or the agent's brief). Only edit files the task links.")

    code = inp.get("code") or ""
    if short == "use_figma" and code:
        if re.search(r"\bfetch\s*\(|XMLHttpRequest|WebSocket|importScripts|\beval\s*\(|new\s+Function\s*\(", code):
            out("deny", "network calls or dynamic code are not allowed inside Figma scripts (data-exfiltration risk).")
        if re.search(r"figma\.root\.remove\s*\(|figma\.root\.children[^;\n]*\.remove\s*\(|figma\.currentPage\s*\.remove\s*\(|\b(page|pages\[[^\]]*\]|targetPage|oldPage)\s*\.remove\s*\(|type\s*===?\s*['\"]PAGE['\"][\s\S]{0,200}?\.remove\s*\(", code):
            out("deny", "deleting pages or the document is never allowed. Ask the user to do it in Figma.")
        risky = []
        if re.search(r"createPage\s*\(", code):
            risky.append("creates a page")
        if re.search(r"setValueForMode|createVariable(Collection)?\s*\(|\.addMode\s*\(|\.removeMode\s*\(|variable\w*\.remove\s*\(", code, re.I):
            risky.append("changes variables (shared design tokens)")
        if re.search(r"create(Paint|Text|Effect|Grid)Style\s*\(|style\w*\.remove\s*\(|(Paint|Text|Effect|Grid)Style[^;\n]*\.(paints|fontSize|fontName|effects|name)\s*=", code):
            risky.append("changes shared styles")
        scan = re.sub(r"for\s*\(\s*(let|var)\s+(\w+)\s*=[^;]*;\s*\2\s*;\s*\2\s*=\s*\2\.parent\s*\)", "", code)  # ancestor-walk scope checks
        n_remove = len(re.findall(r"\.remove\s*\(\s*\)", scan))
        loop_remove = re.search(r"(\.forEach\s*\(|\.map\s*\(|for\s*\(\s*(const|let|var)\s+\w+\s+of\b|while\s*\()[^;{]*[{(]?[\s\S]{0,200}?\.remove\s*\(\s*\)", scan)
        if loop_remove or n_remove > 3:
            risky.append("deletes nodes in a loop (bulk delete)")
        if re.search(r"\.detachInstance\s*\(", code):
            risky.append("detaches component instances")
        if re.search(r"figma\.flatten\s*\(|\.outlineStroke\s*\(|figma\.union\s*\(|figma\.subtract\s*\(", code):
            risky.append("flattens or merges layers")
        if re.search(r"addComponentProperty|editComponentProperty|deleteComponentProperty|combineAsVariants|createComponent(FromNode)?\s*\(|swapComponent\s*\(", code) or \
           re.search(r"(mainComponent|getMainComponentAsync\(\))[\s\S]{0,400}?\.(characters|fills|strokes|resize|appendChild|insertChild|remove|cornerRadius|layoutMode|itemSpacing|padding\w*|effects|setReactionsAsync)\b", code):
            risky.append("edits a main component (affects every instance)")
        if n_remove and "deletes nodes in a loop (bulk delete)" not in risky:
            risky.append(f"deletes {n_remove} node(s)")
        if re.search(r"setSharedPluginData|setPluginData|clientStorage", code):
            risky.append("writes plugin data or storage")
        if re.search(r"figma\.root\.name\s*=", code):
            risky.append("renames the document")
        if risky:
            log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": short, "fileKey": key, "agent": who,
                 "description": inp.get("description", "")[:200], "nodes": node_ids(code), "decision": "ask", "why": risky})
            out("ask", "this script " + ", ".join(risky) + ". Confirm it's in scope.")

    log({"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "tool": short, "fileKey": key, "agent": who,
         "description": (inp.get("description") or "")[:200], "nodes": node_ids(code),
         "decision": "allow" if is_write(short, code) else "read"})
    sys.exit(0)


if __name__ == "__main__":
    main()
