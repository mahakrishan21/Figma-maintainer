#!/usr/bin/env python3
"""Ask a question of a job's data files and get a short answer back (read-only, no network).

Use this instead of writing your own Python over evidence.json, inbox.json, snapshots or Figma REST dumps:
the file stays on disk and only the answer enters the conversation.

  fm_query.py evidence <qa dir or evidence.json>                     counts per change kind, flags, records
  fm_query.py evidence <…> --kind text,fills [--node <id>] [--pair N] one line per change of those kinds
  fm_query.py inbox <inbox.json> [--new] [--frame <id>] [--id <comment id>]
  fm_query.py nodes <json> [--root <id>] [--ids a,b] [--text "words"] [--type TEXT] [--depth N]
        Figma REST dumps ({"nodes": {id: {"document": …}}}, {"document": …} or a bare node) and
        figma_snapshot.py files: id, type, name or text, and the box relative to --root.

Every answer is capped (--max, default 4000 characters) with a count of what was left out; narrow the
question rather than raising the cap.
"""
import argparse, json, sys
from pathlib import Path

KINDS = ("text", "font", "fills", "visibility", "annotations", "interactions", "component", "name", "layout", "moved",
         "added", "removed", "reordered", "hover", "hover_missing_dest", "flags")


class Out:
    def __init__(self, cap):
        self.cap, self.n, self.lines, self.dropped = cap, 0, [], 0

    def add(self, s):
        if self.dropped or self.n + len(s) > self.cap:
            self.dropped += 1
            return
        self.lines.append(s); self.n += len(s) + 1

    def done(self, hint="narrow with --kind / --node / --ids / --text"):
        print("\n".join(self.lines))
        if self.dropped:
            print(f"(… {self.dropped} more line(s) not shown; {hint})")


def load(p):
    p = Path(p).expanduser()
    if p.is_dir():
        p = p / "evidence.json"
    try:
        return json.loads(p.read_text())
    except Exception as e:
        sys.exit(f"Can't read {p}: {e}")


def val(v, n=70):
    s = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + "…"


def change_line(k, c):
    if not isinstance(c, dict):
        return f"{k}: {val(c, 160)}"
    ids = " → ".join(x for x in (c.get("src"), c.get("out")) if x)
    head = f"{k} {ids} {c.get('type', '')} '{val(c.get('name', ''), 40)}'" + (" (hidden)" if c.get("hidden") else "")
    if "before" in c or "after" in c:
        return f"{head}: {val(c.get('before'))} ⇒ {val(c.get('after'))}"
    for key in ("changes", "props"):
        if c.get(key):
            return f"{head}: " + "; ".join(f"{p} {val(a, 30)}⇒{val(b, 30)}" if isinstance(ab := v, list) and len(ab) == 2 else f"{p} {val(v, 40)}"
                                          for p, v in c[key].items() for a, b in [(v + [None, None])[:2] if isinstance(v, list) else (v, None)])
    if c.get("text"):
        return f"{head}: \"{val(c['text'], 80)}\""
    return head


def q_evidence(a, out):
    ev = load(a.path)
    pairs = ev.get("pairs", []) + [dict(p, inplace=True) for p in ev.get("inplace", [])]
    kinds = [k.strip() for k in (a.kind or "").split(",") if k.strip()]
    for i, p in enumerate(pairs, 1):
        if a.pair and i != a.pair:
            continue
        label = f"{p.get('source', '?')} → {p.get('output', '?')}" if not p.get("inplace") else f"in place {p.get('frame', p.get('output', '?'))}"
        out.add(f"## Pair {i}: {label} '{val(p.get('output_name') or p.get('source_name') or '', 50)}'")
        if not kinds:
            counts = [f"{k} {len(p[k])}" for k in KINDS if isinstance(p.get(k), list) and p[k]]
            out.add("changes: " + (", ".join(counts) or "none"))
            crops = (p.get("render") or {}).get("crops") or []
            if crops:
                out.add(f"crops: {len(crops)} (" + ", ".join(Path(c['file']).name for c in crops[:8]) + ")")
            continue
        for k in kinds:
            for c in p.get(k) or []:
                if a.node and isinstance(c, dict) and a.node not in (c.get("src"), c.get("out")):
                    continue
                out.add(change_line(k, c))
    if not kinds:
        for pg in ev.get("pages", []):
            out.add(f"page '{val(pg.get('page_name'), 40)}': protected changes {pg.get('protected_changes')}, "
                    f"elsewhere {len(pg.get('other_changes') or [])}, new top-level {len(pg.get('new_top_level') or [])}")
        if ev.get("flags"):
            out.add("FLAGS: " + "; ".join(map(str, ev["flags"])))
        r = ev.get("records") or {}
        if r:
            out.add("records: " + ", ".join(f"{k} {'✓' if v else '✗'}" for k, v in r.items() if k.endswith((".md", ".json")))
                    + f" · plan {r.get('plan_status')} · writes {r.get('writes_logged')}")
        cm = ev.get("comments") or {}
        if cm.get("new_replies"):
            out.add(f"new client replies: {len(cm['new_replies'])}")
        for fn, m in (ev.get("messages") or {}).items():
            bad = [l for l in m.get("links", []) if not l.get("ok")]
            miss = [q["text"] for q in m.get("quoted", []) if not q.get("in_figma")]
            out.add(f"{fn}: {len(m.get('links', []))} link(s), {len(bad)} wrong" + (f", quotes not in Figma: {len(miss)}" if miss else "")
                    + (f", leaks: {', '.join(m['leaks'])}" if m.get("leaks") else ""))
    out.done()


def q_inbox(a, out):
    d = load(a.path)
    th = d.get("threads", [])
    out.add(f"{d.get('file_name', '')} · {len(th)} thread(s), {sum(1 for t in th if t.get('new'))} new · round from {d.get('round_from')}")
    for t in sorted(th, key=lambda t: (t.get("frame_id") or "", t.get("created_at") or "")):
        if (a.new and not t.get("new")) or (a.frame and t.get("frame_id") != a.frame) or (a.id and t.get("comment_id") != a.id):
            continue
        out.add(f"- {t.get('comment_id')} {str(t.get('created_at'))[:16]} {t.get('author')} · frame {t.get('frame_id')} "
                f"'{val(t.get('frame'), 30)}' node {t.get('node_id')} pin {t.get('pin')}" + (" NEW" if t.get("new") else "")
                + (" handled" if t.get("handled") else ""))
        out.add(f"  \"{val(t.get('message'), 400 if a.id else 200)}\"")
        for r in t.get("replies", []):
            out.add(f"  ↳ {r.get('author')}: \"{val(r.get('message'), 160)}\"")
    out.done("narrow with --new / --frame / --id")


def roots(d, root):
    if isinstance(d, list):  # a list of nodes, or Figma's comments list
        return d
    if isinstance(d.get("nodes"), dict) and d["nodes"] and "anc" in next(iter(d["nodes"].values())):
        return None  # a figma_snapshot.py file: flat
    if isinstance(d.get("nodes"), dict):
        docs = [v.get("document", v) for v in d["nodes"].values() if v]
    elif "document" in d:
        docs = [d["document"]]
    else:
        docs = [d]
    if root:
        found = []

        def find(n):
            if n.get("id") == root:
                found.append(n); return
            for c in n.get("children") or []:
                find(c)
        for doc in docs:
            find(doc)
        return found
    return docs


def q_nodes(a, out):
    d = load(a.path)
    ids = set(x.strip() for x in (a.ids or "").split(",") if x.strip())
    text = (a.text or "").lower()

    def want(nid, typ, name, chars):
        return ((not ids or nid in ids) and (not a.type or typ == a.type)
                and (not text or text in (chars or "").lower() or text in (name or "").lower()))
    docs = roots(d, a.root)
    if docs is None:  # snapshot
        nodes = d["nodes"]
        for nid, n in nodes.items():
            if a.root and nid != a.root and a.root not in n.get("anc", []):
                continue
            if a.depth is not None and a.root and len(n.get("anc", [])) - (len(nodes.get(a.root, {}).get("anc", [])) + 1) >= a.depth:
                continue
            if want(nid, n.get("type"), n.get("name"), n.get("text")):
                out.add(f"{nid} {n.get('type')} '{val(n.get('name'), 50)}'" + (f" \"{val(n['text'], 80)}\"" if n.get("text") else ""))
        return out.done()
    if not docs:
        sys.exit(f"No node {a.root} in {a.path}")
    if docs and "message" in docs[0] and "user" in docs[0]:  # REST comments
        for c in docs:
            if want(c.get("id"), "COMMENT", "", c.get("message")) or (ids and c.get("parent_id") in ids):
                out.add(f"{c.get('id')}{' ↳' + c['parent_id'] if c.get('parent_id') else ''} {str(c.get('created_at'))[:16]} "
                        f"{(c.get('user') or {}).get('handle')}: \"{val(c.get('message'), 200)}\"" + (" resolved" if c.get("resolved_at") else ""))
        return out.done()
    for doc in docs:
        ob = doc.get("absoluteBoundingBox") or {}
        ox, oy = ob.get("x", 0), ob.get("y", 0)

        def walk(n, depth, hidden):
            hid = hidden or n.get("visible") is False
            if want(n.get("id"), n.get("type"), n.get("name"), n.get("characters")):
                b = n.get("absoluteBoundingBox") or {}
                box = f" [{round(b['x'] - ox)},{round(b['y'] - oy)} {round(b['width'])}×{round(b['height'])}]" if b else ""
                st = n.get("style") or {}
                font = f" {st.get('fontFamily', '')} {st.get('fontSize', '')}" if n.get("type") == "TEXT" and st else ""
                out.add(f"{'  ' * min(depth, 6)}{n.get('id')} {n.get('type')} '{val(n.get('name'), 40)}'{box}{font}"
                        + (f" \"{val(n['characters'], 80)}\"" if n.get("characters") else "") + (" (hidden)" if hid else ""))
            if a.depth is not None and depth >= a.depth:
                return
            for c in n.get("children") or []:
                walk(c, depth + 1, hid)
        walk(doc, 0, False)
    out.done()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=("evidence", "inbox", "nodes"))
    ap.add_argument("path")
    ap.add_argument("--kind"); ap.add_argument("--node"); ap.add_argument("--pair", type=int)
    ap.add_argument("--new", action="store_true"); ap.add_argument("--frame"); ap.add_argument("--id")
    ap.add_argument("--root"); ap.add_argument("--ids"); ap.add_argument("--text"); ap.add_argument("--type")
    ap.add_argument("--depth", type=int)
    ap.add_argument("--max", type=int, default=4000)
    a = ap.parse_args()
    out = Out(a.max)
    {"evidence": q_evidence, "inbox": q_inbox, "nodes": q_nodes}[a.what](a, out)


if __name__ == "__main__":
    main()
