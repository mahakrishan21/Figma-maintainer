#!/usr/bin/env python3
"""Read-only content extractor + mechanical copy checks for Figma frames (REST API).

Dumps every visible text layer per frame in reading order (grouped by top-level section,
with role guessed from size/weight: heading / body / button / label), then flags:
placeholder/lorem text, double spaces, leading/trailing spaces, repeated words, trailing
period mismatch within the same heading level, mixed title/sentence case within a level,
straight vs curly quotes and dash mixing, the same CTA worded differently, inconsistent
copyright years / phone / email formats, banned words (--banned) and very long headings.
Spelling, grammar, tone and accuracy are judged by the content-auditor agent from the dump.

Usage:
  python3 -I figma_content.py --url "<figma url with node-id>" [--frames id,id] [--pages "A,B"] \
      [--banned "call,schedule"] --out <dir>
Writes <dir>/content.json, <dir>/content.md (checks) and <dir>/copy-dump.md (all text).
"""
import argparse, json, os, re, sys
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figma_common import fetch_frames, link, resolve_targets, visible_walk  # noqa: E402

PLACEHOLDER = re.compile(r"lorem|ipsum|dolor sit|placeholder|\btbd\b|\btbc\b|xxx+|\[insert|\{.*\}|sample text|your text here|heading goes here|button text|label text|text goes here", re.I)
SMALL = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "at", "by", "in", "of", "on", "to", "up", "as", "is", "it", "vs", "via", "with", "from", "into", "&"}


def role(n, in_button):
    s = n.get("style", {}) or {}
    size, weight = s.get("fontSize", 16) or 16, s.get("fontWeight", 400) or 400
    if in_button:
        return "button"
    if size >= 28 or (size >= 22 and weight >= 600):
        return f"heading-{int(round(size))}"
    if size <= 13 or (s.get("textCase") == "UPPER"):
        return "label"
    return "body"


def case_style(t):
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z'’-]*", t)]
    if len(words) < 3:
        return None
    caps = [w[0].isupper() for i, w in enumerate(words) if i and w.lower() not in SMALL]
    if not caps:
        return None
    r = sum(caps) / len(caps)
    return "Title Case" if r >= 0.8 else "Sentence case" if r <= 0.25 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url"); ap.add_argument("--file")
    ap.add_argument("--frames", default=""); ap.add_argument("--pages", default="")
    ap.add_argument("--banned", default="", help="comma-separated words/phrases the client never uses")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    key, ids, tok, page_of, fname = resolve_targets(a)
    docs = fetch_frames(key, ids, tok)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    banned = [b.strip().lower() for b in a.banned.split(",") if b.strip()]

    all_items, dump = [], [f"# Copy dump — {fname}"]
    for fid in ids:
        doc = docs.get(fid)
        if not doc:
            continue
        fb = doc["absoluteBoundingBox"]
        items = []

        def collect(n, path):
            if n["type"] != "TEXT" or not n.get("absoluteBoundingBox"):
                return
            names = " ".join((p.get("name") or "") for p in path[-4:]).lower()
            in_btn = any(p["type"] in ("INSTANCE", "FRAME") and re.search(r"button|btn|cta", p.get("name") or "", re.I) for p in path[-3:])
            sec = path[1] if len(path) > 1 else doc
            b = n["absoluteBoundingBox"]
            items.append({"id": n["id"], "text": n.get("characters", ""), "role": role(n, in_btn),
                          "section": sec.get("name"), "section_id": sec["id"], "y": b["y"] - fb["y"], "x": b["x"] - fb["x"],
                          "frame": doc["name"], "frame_id": fid, "nav": "nav" in names or "header" in names, "footer": "footer" in names})
        visible_walk(doc, collect)
        items.sort(key=lambda i: (round(i["y"] / 8), i["x"]))
        dump.append(f"\n## {doc['name']} `{fid}` ({page_of.get(fid, '?')}) {link(key, fid)}")
        cur = None
        for i in items:
            if i["section"] != cur:
                cur = i["section"]; dump.append(f"\n### {cur}")
            t = i["text"].replace(" ", " / ").replace("\n", " / ")
            dump.append(f"- [{i['role']}] {t}  `{i['id']}`")
        all_items += items

    flags = []

    def flag(kind, sev, item, detail):
        flags.append({"type": kind, "severity": sev, "frame": item["frame"], "id": item["id"], "text": item["text"][:160],
                      "detail": detail, "link": link(key, item["id"])})

    for i in all_items:
        t = i["text"]
        if PLACEHOLDER.search(t):
            flag("placeholder", "high", i, "placeholder or unfinished text")
        if "  " in t.replace("\n", ""):
            flag("double-space", "low", i, "double space")
        if t != t.strip() and t.strip():
            flag("edge-space", "low", i, "leading/trailing space or line break")
        m = re.search(r"\b(\w+)\s+\1\b", t, re.I)
        if m and m.group(1).lower() not in ("that", "had", "is"):
            flag("repeated-word", "medium", i, f"repeated word '{m.group(0)}'")
        for b in banned:
            if re.search(r"\b" + re.escape(b) + r"\b", t, re.I):
                flag("banned-word", "high", i, f"client avoids '{b}'")
        if i["role"].startswith("heading") and len(t) > 90:
            flag("long-heading", "low", i, f"heading is {len(t)} characters")

    # Consistency within roles
    by_role = defaultdict(list)
    for i in all_items:
        if not i["nav"] and not i["footer"]:
            by_role[i["role"]].append(i)
    for r, items in by_role.items():
        if not (r.startswith("heading") or r == "button"):
            continue
        ends = Counter(it["text"].strip().endswith(".") for it in items if len(it["text"].split()) > 2)
        if ends[True] and ends[False]:
            minority = ends[True] < ends[False]
            for it in items:
                if len(it["text"].split()) > 2 and it["text"].strip().endswith(".") == minority:
                    flag("period-mismatch", "medium", it, f"{r}: {ends[False]} without a final period, {ends[True]} with one")
        cases = Counter(case_style(it["text"]) for it in items)
        cases.pop(None, None)
        if len(cases) == 2 and len(set(cases.values())) == 2:
            minority = min(cases, key=cases.get)
            for it in items:
                if case_style(it["text"]) == minority:
                    flag("case-mismatch", "medium", it, f"{r}: mostly {max(cases, key=cases.get)}, this is {minority}")
    # CTA variants
    btn = defaultdict(list)
    for i in all_items:
        if i["role"] == "button":
            norm = re.sub(r"[^a-z ]", "", i["text"].lower()).strip()
            btn[" ".join(sorted(set(norm.split()) - {"a", "an", "the", "my", "your", "free"}))].append(i)
    labels = Counter(i["text"].strip() for i in all_items if i["role"] == "button")
    groups = defaultdict(set)
    for k, items in btn.items():
        for it in items:
            groups[k].add(it["text"].strip())
    for k, variants in groups.items():
        if len(variants) > 1:
            it = btn[k][0]
            flag("cta-variants", "medium", it, "same CTA worded differently: " + " | ".join(sorted(variants)))
    # Quotes / dashes / years / contact formats
    alltext = " ".join(i["text"] for i in all_items)
    if re.search(r"[‘’“”]", alltext) and re.search(r"\w'\w|\"", alltext):
        it = next(i for i in all_items if re.search(r"\w'\w|\"", i["text"]))
        flag("quote-style", "low", it, "mix of straight and curly quotes/apostrophes")
    if "—" in alltext and " - " in alltext:
        it = next(i for i in all_items if " - " in i["text"])
        flag("dash-style", "low", it, "mix of em dash and spaced hyphen")
    years = Counter(m for i in all_items if re.search(r"©|copyright", i["text"], re.I) for m in re.findall(r"20\d\d", i["text"]))
    if len(years) > 1:
        it = next(i for i in all_items if re.search(r"©", i["text"]))
        flag("copyright-year", "medium", it, f"copyright years differ: {dict(years)}")
    phones = Counter(re.sub(r"\d", "0", m) for m in re.findall(r"\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}", alltext))
    if len(phones) > 1:
        flag("phone-format", "low", all_items[0], f"phone number formats differ: {list(phones)}")

    flags.sort(key=lambda f: ({"high": 0, "medium": 1, "low": 2}[f["severity"]], f["frame"]))
    (out / "copy-dump.md").write_text("\n".join(dump) + "\n")
    (out / "content.json").write_text(json.dumps({"file": key, "frames": ids, "flags": flags, "items": all_items}, indent=2, ensure_ascii=False))
    md = [f"# Content checks — {fname}", f"{len(all_items)} text layers in {len(ids)} frame(s). Mechanical checks only; read copy-dump.md for spelling, grammar, tone and accuracy.",
          f"CTA labels used: " + "; ".join(f"{k} ×{v}" for k, v in labels.most_common(20))]
    for f in flags:
        md.append(f"- [{f['severity']}] {f['type']} — {f['frame']}: “{f['text'][:90]}” — {f['detail']}  {f['link']}")
    (out / "content.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
    print(f"\nFull copy: {out / 'copy-dump.md'}")


if __name__ == "__main__":
    main()
