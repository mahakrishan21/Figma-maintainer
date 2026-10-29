#!/usr/bin/env python3
"""Read-only design-consistency extractor for Figma (REST API — cannot modify the file).

Fingerprints the homepage frame and every compared page frame (typography, colours,
radius, shadows, spacing, container widths, header/footer, buttons and other component
usage, style/variable usage, likely-detached components) and diffs each page against
the homepage and against the rest of the pages. Output is evidence for the
consistency-auditor agent, which verifies and judges intent before reporting.

Token: same lookup as figma_comments.py (FIGMA_TOKEN env, ~/.claude/figma-maintainer/
figma-token, or an `export FIGMA_TOKEN=` line in ~/.zshrc etc.).

Usage:
  # 1. See pages and top-level frames to pick from
  python3 -I figma_audit.py --file <key> --list
  # 2. Audit
  python3 -I figma_audit.py --file <key> --home <frameId> --frames <id,id,...> --out <dir>
  python3 -I figma_audit.py --url "<figma url of the page being worked on>" --home <frameId> \
      [--frames ...] [--pages "Page A,Page B"] --out <dir>
--pages takes every top-level frame >= 1000px wide on those pages. --url adds its node.
Writes <dir>/audit.json and <dir>/audit.md; prints audit.md.
"""
import argparse, colorsys, json, os, re, sys, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

API = "https://api.figma.com/v1"
MAX_EX = 5


# ---------- API ----------
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figma_common import get, token  # noqa: E402  (shared: retries, clear errors, test fixtures)


def parse_url(url):
    m = re.search(r"figma\.com/(?:design|file)/([A-Za-z0-9]+)(?:/branch/([A-Za-z0-9]+))?", url)
    if not m:
        sys.exit("Not a figma.com/design URL")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    node = q.get("node-id", [None])[0]
    return m.group(2) or m.group(1), (node.replace("-", ":") if node else None)


# ---------- helpers ----------
def hexc(c, opacity=1.0):
    a = c.get("a", 1) * opacity
    h = "#%02X%02X%02X" % tuple(round(c[k] * 255) for k in "rgb")
    return h if a >= 0.999 else f"{h}@{round(a * 100)}%"


def rgb_of(h):
    h = h.split("@")[0].lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cdist(a, b):
    (r1, g1, b1), (r2, g2, b2) = rgb_of(a), rgb_of(b)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def link(key, nid):
    return f"https://www.figma.com/design/{key}/?node-id={nid.replace(':', '-')}"


class FP:
    """Fingerprint of one page frame."""

    def __init__(self, fid, name, page):
        self.id, self.name, self.page = fid, name, page
        self.width = 0
        self.text = Counter(); self.text_ex = defaultdict(list)
        self.text_unstyled = 0; self.text_total = 0; self.unstyled_ex = []
        self.fill = Counter(); self.fill_ex = defaultdict(list)
        self.fill_raw = 0; self.fill_total = 0; self.raw_ex = []
        self.radius = Counter(); self.radius_ex = defaultdict(list)
        self.shadow = Counter(); self.shadow_ex = defaultdict(list)
        self.comp = Counter(); self.comp_ex = defaultdict(list)
        self.detached = []
        self.sections = []
        self.header = None; self.footer = None

    def add(self, counter, ex, key, nid):
        counter[key] += 1
        if len(ex[key]) < MAX_EX:
            ex[key].append(nid)


def sig_of_section(n, ctx):
    """Header/footer signature: component identity if an instance, else structure."""
    if n["type"] == "INSTANCE":
        c = ctx["components"].get(n.get("componentId"), {})
        return {"kind": "instance", "component": c.get("name", "?"), "set": ctx["sets"].get(c.get("componentSetId"), ""),
                "componentId": n.get("componentId"), "height": round(n["absoluteBoundingBox"]["height"])}
    texts = []

    def walk(m):
        if m.get("visible", True) is False:
            return
        if m["type"] == "TEXT":
            texts.append(m.get("characters", "").strip()[:30])
        for c in m.get("children", []):
            walk(c)
    walk(n)
    return {"kind": "frame", "name": n.get("name"), "height": round(n["absoluteBoundingBox"]["height"]),
            "texts": texts[:25]}


def find_bars(doc):
    """Header = smallest full-width node near the top that looks like a nav bar (40-200px tall).
    Footer = smallest full-width ancestor of the copyright text."""
    box = doc["absoluteBoundingBox"]
    W, top = box["width"], box["y"]
    hdr, ftr, copy_paths = None, None, []

    def walk(n, path):
        if n.get("visible", True) is False:
            return
        b = n.get("absoluteBoundingBox")
        nonlocal hdr
        if b and n is not doc and b["width"] >= 0.85 * W and b["y"] - top < 160 and 40 <= b["height"] <= 200:
            if hdr is None or b["height"] < hdr["absoluteBoundingBox"]["height"] or \
               (b["height"] == hdr["absoluteBoundingBox"]["height"] and n["type"] == "INSTANCE"):
                hdr = n
        if n["type"] == "TEXT" and re.search(r"©|copyright|all rights reserved", n.get("characters", ""), re.I):
            copy_paths.append(path + [n])
        for c in n.get("children", []) or []:
            walk(c, path + [n])

    walk(doc, [])
    for path in copy_paths:
        for anc in reversed(path):
            b = anc.get("absoluteBoundingBox")
            if anc is not doc and b and b["width"] >= 0.85 * W and b["height"] >= 120:
                if ftr is None or b["y"] > ftr["absoluteBoundingBox"]["y"]:
                    ftr = anc
                break
    return hdr, ftr


def fingerprint(doc, page, ctx):
    fp = FP(doc["id"], doc["name"], page)
    box = doc["absoluteBoundingBox"]
    fp.width = round(box["width"])
    ox = box["x"]
    comp_names = ctx["component_names"]

    kids = [k for k in doc.get("children", []) if k.get("visible", True) is not False and k.get("absoluteBoundingBox")]
    kids.sort(key=lambda k: k["absoluteBoundingBox"]["y"])
    # Unwrap a single full-height wrapper (common: one auto-layout frame holding all sections)
    if len(kids) == 1 and kids[0].get("children") and kids[0]["absoluteBoundingBox"]["height"] > 0.8 * box["height"]:
        kids = [k for k in kids[0]["children"] if k.get("visible", True) is not False and k.get("absoluteBoundingBox")]
        kids.sort(key=lambda k: k["absoluteBoundingBox"]["y"])
    for k in kids:
        b = k["absoluteBoundingBox"]
        tx = []

        def texts_in(m):
            if m.get("visible", True) is False:
                return
            mb = m.get("absoluteBoundingBox")
            if m["type"] == "TEXT" and mb and 0 <= mb["x"] - ox <= box["width"]:
                tx.append((mb["x"] - ox, mb["x"] - ox + mb["width"]))
            for c in m.get("children", []) or []:
                texts_in(c)
        texts_in(k)
        content_x = round(min(t[0] for t in tx)) if tx else None
        content_w = round(max(t[1] for t in tx) - min(t[0] for t in tx)) if tx else None
        fp.sections.append({
            "id": k["id"], "name": k.get("name"), "type": k["type"], "y": round(b["y"] - box["y"]),
            "w": round(b["width"]), "h": round(b["height"]), "content_w": content_w, "content_x": content_x,
            "pad": [k.get(p) for p in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft")] if k.get("layoutMode") else None,
            "gap": k.get("itemSpacing") if k.get("layoutMode") else None, "layout": k.get("layoutMode"),
        })
    hdr, ftr = find_bars(doc)
    if hdr:
        fp.header = dict(sig_of_section(hdr, ctx), id=hdr["id"])
    if ftr:
        fp.footer = dict(sig_of_section(ftr, ctx), id=ftr["id"])

    def walk(n, in_instance):
        if n.get("visible", True) is False:
            return
        nid, t = n["id"], n["type"]
        styles = n.get("styles", {}) or {}
        bv = n.get("boundVariables", {}) or {}
        if t == "INSTANCE":
            c = ctx["components"].get(n.get("componentId"), {})
            setname = ctx["sets"].get(c.get("componentSetId"), "")
            label = f"{setname} › {c.get('name', '?')}" if setname else c.get("name", "?")
            fp.add(fp.comp, fp.comp_ex, label, nid)
        elif t in ("FRAME", "GROUP") and not in_instance:
            nm = (n.get("name") or "").strip().lower()
            if nm and nm in comp_names and len(nm) > 2:
                fp.detached.append({"id": nid, "name": n.get("name")})
                in_instance = True  # don't report its children separately
        if t == "TEXT":
            s = n.get("style", {}) or {}
            fp.text_total += 1
            key = (s.get("fontFamily"), s.get("fontWeight"), round(s.get("fontSize") or 0, 1),
                   round(s.get("lineHeightPx", 0) or 0), round(s.get("letterSpacing", 0) or 0, 2), s.get("textCase", "ORIGINAL"))
            styled = "text" in styles or "fontSize" in bv or "fontFamily" in bv
            fp.add(fp.text, fp.text_ex, key, nid)
            if not styled and not in_instance:
                fp.text_unstyled += 1
                if len(fp.unstyled_ex) < MAX_EX:
                    fp.unstyled_ex.append(nid)
        for kind in ("fills", "strokes"):
            for i, paint in enumerate(n.get(kind, []) or []):
                if paint.get("type") != "SOLID" or paint.get("visible", True) is False:
                    continue
                h = hexc(paint["color"], paint.get("opacity", 1))
                fp.add(fp.fill, fp.fill_ex, h, nid)
                fp.fill_total += 1
                styled = (kind[:-1] in styles) or (kind in styles) or bool(bv.get(kind)) or bool(paint.get("boundVariables"))
                if not styled and not in_instance and t != "TEXT":
                    fp.fill_raw += 1
                    if len(fp.raw_ex) < MAX_EX:
                        fp.raw_ex.append(nid)
        if t not in ("TEXT", "LINE", "VECTOR") and (n.get("fills") or n.get("strokes")):
            r = n.get("cornerRadius")
            rr = n.get("rectangleCornerRadii")
            if rr and len(set(rr)) > 1:
                fp.add(fp.radius, fp.radius_ex, "/".join(str(round(x)) for x in rr), nid)
            elif r:
                fp.add(fp.radius, fp.radius_ex, str(round(r)), nid)
        for e in n.get("effects", []) or []:
            if e.get("visible", True) and e.get("type") in ("DROP_SHADOW", "INNER_SHADOW"):
                o = e.get("offset", {})
                key = f"{e['type'][0]} {round(o.get('x', 0))},{round(o.get('y', 0))} blur{round(e.get('radius', 0))} spread{round(e.get('spread', 0) or 0)} {hexc(e['color'])}"
                fp.add(fp.shadow, fp.shadow_ex, key, nid)
        for c in n.get("children", []) or []:
            walk(c, in_instance or t == "INSTANCE")

    walk(doc, False)
    return fp


def tkey(k):
    fam, w, size, lh, ls, case = k
    s = f"{fam} {w} {size}/{lh}"
    if ls:
        s += f" ls{ls}"
    if case and case != "ORIGINAL":
        s += f" {case.lower()}"
    return s


# ---------- diff ----------
def diff(home, pages, key):
    out = []
    all_fps = [home] + pages

    def ex(ids):
        return [link(key, i) for i in ids[:3]]

    # Pre-compute "standard" sets: tokens on home, or on >= half of the pages
    def standard(attr):
        on_home = set(getattr(home, attr))
        votes = Counter()
        for f in all_fps:
            votes.update(set(getattr(f, attr)))
        common = {k for k, v in votes.items() if v >= max(2, (len(all_fps) + 1) // 2)}
        return on_home | common

    std_text, std_fill, std_rad, std_shadow, std_comp = (standard(a) for a in ("text", "fill", "radius", "shadow", "comp"))
    home_sizes = sorted({k[2] for k in home.text if k[2]})
    home_fams = {k[0] for k in home.text}

    for f in all_fps:
        fnd = []
        cmp_label = "homepage" if f is not home else "the other pages"
        # Header/footer
        if f is not home:
            for part in ("header", "footer"):
                a, b = getattr(home, part), getattr(f, part)
                if not a or not b:
                    continue
                if a["kind"] == "instance" and b["kind"] == "instance":
                    if a["componentId"] != b["componentId"]:
                        fnd.append({"type": f"{part}-variant", "severity": "high",
                                    "current": f"{b['set']} › {b['component']}", "expected": f"{a['set']} › {a['component']} (homepage)",
                                    "examples": ex([b["id"]])})
                elif a["kind"] != b["kind"]:
                    fnd.append({"type": f"{part}-not-shared", "severity": "high",
                                "current": f"{b['kind']} '{b.get('name') or b.get('component')}'",
                                "expected": f"{a['kind']} '{a.get('name') or a.get('component')}' as on the homepage",
                                "examples": ex([b["id"]])})
                else:
                    if a["kind"] == "frame" and (abs(a["height"] - b["height"]) > 2 or a.get("texts") != b.get("texts")):
                        missing = [t for t in a.get("texts", []) if t not in b.get("texts", [])]
                        extra = [t for t in b.get("texts", []) if t not in a.get("texts", [])]
                        fnd.append({"type": f"{part}-differs", "severity": "high",
                                    "current": f"height {b['height']}, texts differ: missing {missing[:6]} extra {extra[:6]}",
                                    "expected": f"same as homepage (height {a['height']}); ideally one shared component",
                                    "examples": ex([b["id"]])})
            if f.width != home.width:
                fnd.append({"type": "frame-width", "severity": "medium", "current": f"{f.width}px",
                            "expected": f"{home.width}px (homepage)", "examples": ex([f.id])})
        # Fonts
        for k, n in f.text.items():
            if k in std_text:
                continue
            reason = None
            if k[0] not in home_fams:
                reason = f"font family '{k[0]}' not used on the homepage"
            else:
                near = [s for s in home_sizes if k[2] and s != k[2] and abs(s - k[2]) <= 2]
                reason = f"near-miss size (homepage uses {near})" if near else "type combination not used elsewhere"
            fnd.append({"type": "typography", "severity": "medium" if "near-miss" in reason or "family" in reason else "low",
                        "current": f"{tkey(k)} ×{n}", "expected": reason, "examples": ex(f.text_ex[k])})
        # Colours
        for h, n in f.fill.items():
            if h in std_fill:
                continue
            near = sorted((cdist(h, s), s) for s in std_fill if s.split("@")[0] != h.split("@")[0])
            if near and near[0][0] < 18:
                fnd.append({"type": "color-near-miss", "severity": "medium", "current": f"{h} ×{n}",
                            "expected": f"{near[0][1]} (standard)", "examples": ex(f.fill_ex[h])})
            else:
                fnd.append({"type": "color-new", "severity": "low", "current": f"{h} ×{n}",
                            "expected": f"not used on the {cmp_label}", "examples": ex(f.fill_ex[h])})
        # Radius
        std_r = sorted(std_rad, key=lambda x: float(x.split('/')[0]))
        for r, n in f.radius.items():
            if r in std_rad:
                continue
            fnd.append({"type": "radius", "severity": "low", "current": f"{r}px ×{n}",
                        "expected": f"standard radii {std_r[:8]}", "examples": ex(f.radius_ex[r])})
        # Shadows
        for s, n in f.shadow.items():
            if s not in std_shadow:
                fnd.append({"type": "shadow", "severity": "low", "current": f"{s} ×{n}",
                            "expected": f"not used on the {cmp_label}", "examples": ex(f.shadow_ex[s])})
        # Components: same set, variant never used elsewhere (e.g. a different button variant)
        home_sets = defaultdict(set)
        for lbl in std_comp:
            if " › " in lbl:
                s, v = lbl.split(" › ", 1)
                home_sets[s].add(v)
        for lbl, n in f.comp.items():
            if lbl in std_comp or " › " not in lbl:
                continue
            s, v = lbl.split(" › ", 1)
            if s in home_sets:
                fnd.append({"type": "component-variant", "severity": "medium", "current": f"{lbl} ×{n}",
                            "expected": f"variants used elsewhere: {sorted(home_sets[s])[:6]}", "examples": ex(f.comp_ex[lbl])})
        for d in f.detached[:MAX_EX]:
            fnd.append({"type": "possibly-detached", "severity": "medium", "current": f"frame '{d['name']}'",
                        "expected": "an instance of the component with that name", "examples": ex([d["id"]])})
        if f.text_total and f.text_unstyled / f.text_total > 0.2:
            fnd.append({"type": "text-without-style", "severity": "medium",
                        "current": f"{f.text_unstyled}/{f.text_total} text layers have no text style or variable",
                        "expected": "use the file's text styles", "examples": ex(f.unstyled_ex)})
        if f.fill_total and f.fill_raw / max(f.fill_total, 1) > 0.3:
            fnd.append({"type": "raw-colors", "severity": "low",
                        "current": f"{f.fill_raw} raw (unstyled, unbound) solid fills",
                        "expected": "use colour styles or variables", "examples": ex(f.raw_ex)})
        # Layout: content width / left edge
        if f is not home and home.sections and f.sections:
            # Left text edge per section; the homepage's most common edge is the container margin.
            hx = Counter(s["content_x"] for s in home.sections if s["content_x"] is not None)
            if hx:
                std_x = hx.most_common(1)[0][0]
                allowed = {x for x, c in hx.items() if c >= 2} | {std_x}
                for s in f.sections:
                    if s["content_x"] is None or any(abs(s["content_x"] - x) <= 4 for x in allowed):
                        continue
                    if s["content_x"] > f.width * 0.3:   # centred or right-side content: not a margin
                        continue
                    fnd.append({"type": "container", "severity": "medium",
                                "current": f"section '{s['name']}' text starts at x={s['content_x']}",
                                "expected": f"homepage content margin x={std_x} (also used: {sorted(allowed)})",
                                "examples": ex([s["id"]])})
        out.append({"frame": f.name, "id": f.id, "page": f.page, "is_home": f is home, "link": link(key, f.id),
                    "findings": fnd})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url"); ap.add_argument("--file")
    ap.add_argument("--home", help="homepage frame id")
    ap.add_argument("--frames", default="", help="comma-separated frame ids to compare")
    ap.add_argument("--pages", default="", help="comma-separated page names: every top-level frame >=1000px wide")
    ap.add_argument("--list", action="store_true", help="list pages and top-level frames, then exit")
    ap.add_argument("--out")
    a = ap.parse_args()

    key, url_node = parse_url(a.url) if a.url else (a.file, None)
    if not key:
        sys.exit("Pass --url or --file")
    tok = token()
    meta = get(f"/files/{key}?depth=2", tok)
    pages = meta["document"]["children"]

    if a.list:
        print(f"# {meta['name']} ({key})")
        for p in pages:
            frames = [c for c in p.get("children", []) if c["type"] in ("FRAME", "SECTION", "COMPONENT")]
            print(f"\n## page {p['id']} {p['name']}  ({len(frames)} top-level)")
            for c in frames[:40]:
                print(f"  {c['type'][:4]} {c['id']}  {c['name']}")
        return

    if not a.home or not a.out:
        sys.exit("Pass --home <frameId> and --out <dir> (use --list first to find ids)")
    page_of = {}
    for p in pages:
        for c in p.get("children", []):
            page_of[c["id"]] = p["name"]
    ids = [i.strip() for i in a.frames.split(",") if i.strip()]
    if url_node and url_node != a.home:
        ids.append(url_node)
    if a.pages:
        wanted = {x.strip().lower() for x in a.pages.split(",")}
        for p in pages:
            if p["name"].strip().lower() in wanted:
                for c in p.get("children", []):
                    if c["type"] == "FRAME" and c.get("absoluteBoundingBox", {}).get("width", 0) >= 1000:
                        ids.append(c["id"])
    ids = [i for i in dict.fromkeys(ids) if i != a.home]
    if not ids:
        sys.exit("Nothing to compare: pass --frames, --pages or a --url with a node-id")

    docs, ctx = {}, {"components": {}, "sets": {}, "component_names": set()}
    for chunk in [[a.home] + ids[i:i + 3] for i in range(0, len(ids), 3)]:
        res = get(f"/files/{key}/nodes?ids={urllib.parse.quote(','.join(chunk), safe=',:')}", tok)["nodes"]
        for nid, v in res.items():
            if not v:
                continue
            docs[nid] = v["document"]
            ctx["components"].update(v.get("components", {}))
            ctx["sets"].update({k: s.get("name", "") for k, s in v.get("componentSets", {}).items()})
    for c in ctx["components"].values():
        ctx["component_names"].add(c.get("name", "").strip().lower())
    for s in ctx["sets"].values():
        ctx["component_names"].add(s.strip().lower())
    if a.home not in docs:
        sys.exit(f"Homepage frame {a.home} not found")

    home = fingerprint(docs[a.home], page_of.get(a.home, "?"), ctx)
    fps = [fingerprint(docs[i], page_of.get(i, "?"), ctx) for i in ids if i in docs]
    result = diff(home, fps, key)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    tokens = {f.name: {"text": {tkey(k): v for k, v in f.text.most_common()}, "colors": dict(f.fill.most_common()),
                       "radius": dict(f.radius), "shadows": dict(f.shadow), "components": dict(f.comp.most_common(40)),
                       "sections": f.sections, "header": f.header, "footer": f.footer}
              for f in [home] + fps}
    (out / "audit.json").write_text(json.dumps({"file": key, "home": a.home, "frames": result, "tokens": tokens}, indent=2, default=str))

    md = [f"# Consistency evidence — {meta['name']}", f"Homepage: {home.name} `{home.id}` ({home.page}). Compared: {len(fps)} frame(s).",
          "Automated evidence only — verify each item visually and judge intent before reporting."]
    md.append("\n## Homepage standard")
    md.append("- Type: " + "; ".join(f"{tkey(k)} ×{v}" for k, v in home.text.most_common(12)))
    md.append("- Colours: " + ", ".join(f"{h} ×{v}" for h, v in home.fill.most_common(14)))
    md.append("- Radius: " + ", ".join(f"{r} ×{v}" for r, v in home.radius.most_common(8)))
    md.append("- Shadows: " + "; ".join(f"{s} ×{v}" for s, v in home.shadow.most_common(5)))
    md.append(f"- Header: {home.header}\n- Footer: {home.footer}")
    for r in result:
        md.append(f"\n## {'[HOME] ' if r['is_home'] else ''}{r['frame']} `{r['id']}` ({r['page']}) — {len(r['findings'])} finding(s)")
        for f in sorted(r["findings"], key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]]):
            md.append(f"- [{f['severity']}] {f['type']}: {f['current']} → expected {f['expected']}  " + " ".join(f["examples"]))
    (out / "audit.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
