#!/usr/bin/env python3
"""Read-only accessibility checks for Figma frames (REST API; WCAG 2.2 AA oriented).

Checks: text contrast against the solid background behind it (alpha-composited through
ancestors; text over images is listed for visual review), minimum text size, line height,
long all-caps / justified text, touch/click target size (44px on mobile frames, 24px on
desktop — WCAG 2.5.8), form fields without a visible label, interactive component sets
without a Focus state (and Hover/Disabled for buttons), and image count for alt-text notes.

Usage:
  python3 -I figma_a11y.py --url "<figma url with node-id>" [--frames id,id] [--pages "A,B"] --out <dir>
Writes <dir>/a11y.json and <dir>/a11y.md; prints a11y.md.
"""
import argparse, json, os, re, sys
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figma_common import get, link, resolve_targets  # noqa: E402
import urllib.parse  # noqa: E402

INTERACTIVE = re.compile(r"\b(button|btn|cta|link|toggle|switch|checkbox|radio|tab|chip|close|menu|hamburger|icon[- ]?button|dropdown|select|input|field|textarea|search|pagination|arrow|chevron|nav item)\b", re.I)
FIELD = re.compile(r"\b(input|field|textarea|text area|select|dropdown|combo|search)\b", re.I)


def lum(c):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def blend(top, alpha, bottom):
    return tuple(top[i] * alpha + bottom[i] * (1 - alpha) for i in range(3))


def solid(paints):
    """Topmost visible paint: ('solid', rgb, alpha) | ('image',) | ('gradient', rgb, alpha) | None."""
    for p in reversed(paints or []):
        if p.get("visible", True) is False or p.get("opacity", 1) == 0:
            continue
        if p["type"] == "SOLID":
            c = p["color"]
            return ("solid", (c["r"], c["g"], c["b"]), c.get("a", 1) * p.get("opacity", 1))
        if p["type"] == "IMAGE":
            return ("image",)
        if p["type"].startswith("GRADIENT"):
            stops = p.get("gradientStops") or []
            if stops:
                cs = [s["color"] for s in stops]
                avg = tuple(sum(c[k] for c in cs) / len(cs) for k in "rgb")
                return ("gradient", avg, sum(c.get("a", 1) for c in cs) / len(cs) * p.get("opacity", 1))
    return None


def hexs(c):
    return "#%02X%02X%02X" % tuple(round(v * 255) for v in c)


def overlaps(a, b):
    return not (a["x"] + a["width"] <= b["x"] or b["x"] + b["width"] <= a["x"] or a["y"] + a["height"] <= b["y"] or b["y"] + b["height"] <= a["y"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url"); ap.add_argument("--file")
    ap.add_argument("--frames", default=""); ap.add_argument("--pages", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    key, ids, tok, page_of, fname = resolve_targets(a)
    docs, comps, sets = {}, {}, {}
    for i in range(0, len(ids), 3):
        part = ids[i:i + 3]
        res = get(f"/files/{key}/nodes?ids={urllib.parse.quote(','.join(part), safe=',:')}", tok)["nodes"]
        for nid, v in res.items():
            if v and v.get("document"):
                docs[nid] = v["document"]
                comps.update(v.get("components", {}))
                sets.update({k: s.get("name", "") for k, s in v.get("componentSets", {}).items()})

    findings, review, stats = [], [], defaultdict(int)

    def add(sev, kind, frame, nid, detail, wcag):
        findings.append({"severity": sev, "type": kind, "frame": frame, "id": nid, "detail": detail, "wcag": wcag, "link": link(key, nid)})

    used_sets = set()
    for fid in ids:
        doc = docs.get(fid)
        if not doc:
            continue
        fw = doc["absoluteBoundingBox"]["width"]
        mobile = fw < 600
        fname_ = doc["name"]

        def walk(n, ancestors, in_target):
            if n.get("visible", True) is False:
                return
            t = n["type"]
            b = n.get("absoluteBoundingBox")
            if t == "INSTANCE":
                c = comps.get(n.get("componentId"), {})
                if c.get("componentSetId"):
                    used_sets.add(c["componentSetId"])
            name = n.get("name") or ""
            label = name
            if t == "INSTANCE":
                c = comps.get(n.get("componentId"), {})
                label = f"{sets.get(c.get('componentSetId'), '')} {c.get('name', '')} {name}"
            # Targets: top-most interactive-looking node
            if b and not in_target and t in ("INSTANCE", "FRAME", "COMPONENT") and (INTERACTIVE.search(label) or n.get("reactions")):
                stats["targets"] += 1
                need = 44 if mobile else 24
                if b["width"] < need or b["height"] < need:
                    add("high" if mobile else "medium", "target-size", fname_, n["id"],
                        f"'{name}' is {round(b['width'])}×{round(b['height'])}px; minimum {need}×{need} ({'mobile' if mobile else 'desktop'})", "2.5.8")
                if FIELD.search(label) and t in ("INSTANCE", "FRAME"):
                    stats["fields"] += 1
                    texts = []

                    def tx(m):
                        if m.get("visible", True) is False:
                            return
                        if m["type"] == "TEXT":
                            texts.append(m)
                        for k in m.get("children", []) or []:
                            tx(k)
                    tx(n)
                    has_label = any(re.search(r"label", k.get("name") or "", re.I) for k in texts)
                    if not has_label and len(texts) <= 1:
                        add("medium", "field-label", fname_, n["id"], f"form field '{name}' shows no visible label (placeholder-only labels disappear when typing)", "3.3.2 / 1.3.1")
                in_target = True
            if t == "TEXT" and b and n.get("characters", "").strip():
                stats["texts"] += 1
                s = n.get("style", {}) or {}
                size, weight = s.get("fontSize", 16) or 16, s.get("fontWeight", 400) or 400
                large = size >= 24 or (size >= 18.66 and weight >= 700)
                fg = solid(n.get("fills"))
                if size < 12:
                    add("medium", "text-size", fname_, n["id"], f"{size}px text: “{n['characters'][:50]}”", "1.4.4")
                elif mobile and size < 14 and len(n["characters"]) > 40:
                    add("low", "text-size", fname_, n["id"], f"{size}px body text on mobile", "1.4.4")
                lh = s.get("lineHeightPx")
                if lh and size <= 20 and len(n["characters"]) > 120 and lh / size < 1.3:
                    add("low", "line-height", fname_, n["id"], f"line height {round(lh / size, 2)} on a paragraph (aim ≥1.5)", "1.4.12")
                if s.get("textCase") == "UPPER" and len(n["characters"]) > 40:
                    add("low", "all-caps", fname_, n["id"], "long all-caps text is harder to read", "best practice")
                if s.get("textAlignHorizontal") == "JUSTIFIED":
                    add("low", "justified", fname_, n["id"], "justified text creates uneven spacing", "1.4.8 (AAA)")
                if fg and fg[0] in ("solid", "gradient"):
                    # Background: walk ancestors top-down, compositing solid fills; note images under the text
                    bg, on_image = (1.0, 1.0, 1.0), False
                    for anc in ancestors:
                        pnt = solid(anc.get("fills"))
                        if pnt and pnt[0] == "image":
                            on_image = True
                        elif pnt:
                            bg = blend(pnt[1], pnt[2] * anc.get("opacity", 1), bg)
                            on_image = on_image and pnt[2] < 0.95
                    # Siblings drawn below the text's branch that overlap it (e.g. an image or a card behind)
                    for depth, anc in enumerate(ancestors):
                        branch = ancestors[depth + 1] if depth + 1 < len(ancestors) else n
                        for sib in anc.get("children", []) or []:
                            if sib is branch:
                                break
                            sb = sib.get("absoluteBoundingBox")
                            if sib.get("visible", True) is False or not sb or not overlaps(sb, b):
                                continue
                            pnt = solid(sib.get("fills"))
                            if pnt and pnt[0] == "image":
                                on_image = True
                            elif pnt and sb["width"] >= b["width"] and sb["height"] >= b["height"]:
                                bg = blend(pnt[1], pnt[2] * sib.get("opacity", 1), bg)
                                on_image = on_image and pnt[2] < 0.95
                    col = blend(fg[1], fg[2] * n.get("opacity", 1), bg)
                    r = ratio(col, bg)
                    need = 3.0 if large else 4.5
                    if on_image:
                        stats["on_image"] += 1
                        if len(review) < 40:
                            review.append({"frame": fname_, "id": n["id"], "text": n["characters"][:60], "link": link(key, n["id"])})
                    elif r < need:
                        add("high" if r < need - 1 else "medium", "contrast", fname_, n["id"],
                            f"{round(r, 2)}:1 ({hexs(col)} on {hexs(bg)}), needs {need}:1 for {'large' if large else 'normal'} text: “{n['characters'][:50]}”", "1.4.3")
            if t == "TEXT" or not n.get("children"):
                pass
            if any(p.get("type") == "IMAGE" and p.get("visible", True) for p in n.get("fills", []) or []):
                stats["images"] += 1
            for c in n.get("children", []) or []:
                walk(c, ancestors + [n], in_target)

        walk(doc, [], False)

    # Interactive component sets missing states
    variants = defaultdict(list)
    for c in comps.values():
        if c.get("componentSetId") in used_sets:
            variants[c["componentSetId"]].append(c.get("name", "").lower())
    for sid, names in variants.items():
        sname = sets.get(sid, "")
        if not INTERACTIVE.search(sname):
            continue
        allv = " ".join(names)
        missing = [s for s in ("focus", "hover", "disabled") if s not in allv]
        if re.search(r"button|btn|cta", sname, re.I) is None:
            missing = [m for m in missing if m == "focus"]
        if missing:
            add("medium" if "focus" in missing else "low", "missing-states", "component set", sid,
                f"'{sname}' has no {', '.join(missing)} state" + (" (keyboard users need a visible focus state)" if "focus" in missing else ""), "2.4.7 / 2.4.11")

    findings.sort(key=lambda f: ({"high": 0, "medium": 1, "low": 2}[f["severity"]], f["frame"], f["type"]))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / "a11y.json").write_text(json.dumps({"file": key, "frames": ids, "stats": stats, "findings": findings, "text_on_images": review}, indent=2, ensure_ascii=False))
    md = [f"# Accessibility checks — {fname}",
          f"Frames: {', '.join(docs[i]['name'] for i in ids if i in docs)}. Text layers {stats['texts']}, targets {stats['targets']}, form fields {stats['fields']}, images {stats['images']}.",
          "Mechanical checks only — verify visually. Alt text, heading order, focus order and motion must be specified for developers (annotations)."]
    for f in findings:
        md.append(f"- [{f['severity']}] {f['type']} (WCAG {f['wcag']}) — {f['frame']}: {f['detail']}  {f['link']}")
    if review:
        md.append(f"\n## Text over images — check contrast visually ({stats['on_image']})")
        md += [f"- {r['frame']}: “{r['text']}”  {r['link']}" for r in review]
    (out / "a11y.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
