#!/usr/bin/env python3
"""Read-only before/after snapshot of a Figma page (REST API) to prove nothing outside the
authorized targets changed.

  # before editing
  python3 -I figma_snapshot.py --file <key> --page <pageId> --out before.json
  # after editing: snapshot again and compare
  python3 -I figma_snapshot.py --file <key> --page <pageId> --out after.json \
      --compare before.json --targets 22202:7699,22170:1904 [--allow-new]

Each node's signature covers type, name, visibility, text, fills/strokes (colour, image ref),
size and position, layout, padding, gap, radius, opacity, effects and component link.
Compare prints: changes inside targets (expected), changes OUTSIDE targets (problems),
added/removed top-level frames. Exit code 2 when anything outside the targets changed.
Note: the REST API reflects Figma's saved state; wait ~5 s after the last edit before 'after'.
"""
import argparse, hashlib, json, os, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figma_common import get, token  # noqa: E402


def paint_sig(paints):
    out = []
    for p in paints or []:
        c = p.get("color") or {}
        out.append([p.get("type"), p.get("visible", True), round(p.get("opacity", 1), 3),
                    [round(c.get(k, 0), 3) for k in "rgba"] if c else None, p.get("imageRef")])
    return out


def node_sig(n):
    b = n.get("absoluteBoundingBox") or {}
    keys = ("layoutMode", "paddingLeft", "paddingRight", "paddingTop", "paddingBottom", "itemSpacing",
            "cornerRadius", "opacity", "componentId", "characters", "visible", "textAlignHorizontal")
    d = {k: n.get(k) for k in keys if k in n}
    d.update({"type": n["type"], "name": n.get("name"), "fills": paint_sig(n.get("fills")), "strokes": paint_sig(n.get("strokes")),
              "box": [round(b.get(k, 0)) for k in ("x", "y", "width", "height")] if b else None,
              "effects": [[e.get("type"), e.get("visible", True), e.get("radius")] for e in n.get("effects") or []],
              "style": {k: (n.get("style") or {}).get(k) for k in ("fontFamily", "fontWeight", "fontSize", "lineHeightPx")} if n["type"] == "TEXT" else None,
              "kids": [c["id"] for c in n.get("children", [])]})
    return hashlib.sha1(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


def snapshot(key, page, tok):
    res = get(f"/files/{key}/nodes?ids={urllib.parse.quote(page, safe=':')}", tok)["nodes"].get(page)
    if not res:
        sys.exit(f"Page/node {page} not found in {key}")
    doc, nodes = res["document"], {}

    def walk(n, anc):
        nodes[n["id"]] = {"sig": node_sig(n), "anc": anc, "name": n.get("name"), "type": n["type"]}
        for c in n.get("children", []) or []:
            walk(c, anc + [n["id"]])
    walk(doc, [])
    top = [c["id"] for c in doc.get("children", [])]
    return {"file": key, "page": page, "page_name": doc.get("name"), "top": top, "nodes": nodes}


def compare(before, after, targets, allow_new):
    tset = set(targets)

    def in_target(nid, snap):
        n = snap["nodes"].get(nid)
        return nid in tset or (n and any(a in tset for a in n["anc"]))

    new_top = [t for t in after["top"] if t not in before["top"]]
    removed_top = [t for t in before["top"] if t not in after["top"]]
    inside, outside = [], []
    for nid, n in after["nodes"].items():
        b = before["nodes"].get(nid)
        if b and b["sig"] == n["sig"]:
            continue
        kind = "changed" if b else "added"
        under_new = any(a in new_top for a in n["anc"]) or nid in new_top
        if in_target(nid, after) or (under_new and allow_new):
            inside.append((kind, nid, n))
        elif nid == after["page"] and set(after["top"]) - set(before["top"]) and allow_new:
            continue  # the page itself changes when new top-level frames are added
        else:
            outside.append((kind, nid, n))
    for nid, b in before["nodes"].items():
        if nid not in after["nodes"]:
            (inside if in_target(nid, before) else outside).append(("removed", nid, b))
    return new_top, removed_top, inside, outside


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True); ap.add_argument("--page", required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--compare")
    ap.add_argument("--targets", default=""); ap.add_argument("--allow-new", action="store_true",
                                                              help="new top-level frames created by this task are expected")
    a = ap.parse_args()
    snap = snapshot(a.file, a.page, token())
    Path(a.out).write_text(json.dumps(snap))
    print(f"Snapshot: {snap['page_name']} ({a.page}), {len(snap['nodes'])} nodes, {len(snap['top'])} top-level → {a.out}")
    if not a.compare:
        return
    before = json.loads(Path(a.compare).read_text())
    targets = [t.strip() for t in a.targets.split(",") if t.strip()]
    new_top, removed_top, inside, outside = compare(before, snap, targets, a.allow_new)

    def label(n):
        return f"{n['type'].lower()} '{(n.get('name') or '')[:40]}'"
    print(f"\nInside targets ({', '.join(targets) or 'none'}): {len(inside)} node change(s)")
    for k, nid, n in inside[:15]:
        print(f"  {k:7} {nid} {label(n)}")
    if new_top:
        print(f"New top-level frames: {', '.join(new_top)}" + ("" if a.allow_new else "  ← not allowed without --allow-new"))
    if removed_top:
        print(f"REMOVED top-level frames: {', '.join(removed_top)}")
    print(f"\nOUTSIDE targets: {len(outside)} node change(s)" + ("  ✓ protected scope unchanged" if not outside else "  ✗ REPORT THESE"))
    for k, nid, n in outside[:30]:
        print(f"  {k:7} {nid} {label(n)}")
    sys.exit(2 if outside or removed_top else 0)


if __name__ == "__main__":
    main()
