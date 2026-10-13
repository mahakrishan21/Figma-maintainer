#!/usr/bin/env python3
"""Fetch watermarked iStock comp images as layout placeholders.

Searches iStock filtered to the Basic plan (Essentials collection), ranks
Editorial-use results first, and downloads each pick's 2048px watermarked comp
plus a candidates.json record. Comps are for client review only; the purchased
file replaces them after approval.

Usage:
  python3 -I istock_fetch.py --query "couple meeting financial advisor" \
      --orientation horizontal --count 4 --out assets/stock/<slot-id>
  --orientation: horizontal | vertical | square | panoramicHorizontal (optional)
  --creative-only / --editorial-only: override the default editorial-first mix
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
BASE = "https://www.istockphoto.com"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def search(query, orientation):
    params = {"phrase": query, "mediatype": "photography",
              "istockcollection": "main"}  # main = Essentials = Basic plan
    if orientation:
        params["orientations"] = orientation
    html = get(f"{BASE}/search/2/image?{urllib.parse.urlencode(params)}").decode("utf-8", "ignore")
    m = re.search(r"data-component='Search'>\s*(.*?)\s*</script>", html, re.S)
    if not m:
        sys.exit("iStock search page format changed: no Search JSON found")
    assets = json.loads(m.group(1))["search"]["gallery"]["assets"]
    # Belt and braces: the collection filter should already drop Signature.
    return [a for a in assets if not a.get("isIstockSignature") and a.get("assetType") == "image"]


def comp_url(asset):
    """Largest watermarked comp on the asset page (w=is), else the 612 thumb."""
    html = get(BASE + asset["landingUrl"]).decode("utf-8", "ignore").replace("\\u0026", "&").replace("&amp;", "&")
    pat = rf"https://media\.istockphoto\.com/id/{asset['id']}/[^\"' ]+?\.jpg\?s=(\d+)x\d+&w=is&k=20&c=[^\"' ]+"
    found = sorted({(int(m.group(1)), m.group(0)) for m in re.finditer(pat, html)}, reverse=True)
    return found[0][1] if found else asset["thumbUrl"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--count", type=int, default=4)
    ap.add_argument("--orientation")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--editorial-only", action="store_true")
    g.add_argument("--creative-only", action="store_true")
    a = ap.parse_args()

    assets = search(a.query, a.orientation)
    editorial = [x for x in assets if x.get("editorialOnly")]
    creative = [x for x in assets if not x.get("editorialOnly")]
    picks = editorial if a.editorial_only else creative if a.creative_only else editorial + creative
    picks = picks[: a.count]
    if not picks:
        sys.exit(f"no Essentials results for '{a.query}'")

    os.makedirs(a.out, exist_ok=True)
    records = []
    for n, x in enumerate(picks, 1):
        url = comp_url(x)
        data = get(url)
        if data[:3] != b"\xff\xd8\xff":
            print(f"skip {x['id']}: not a JPEG", file=sys.stderr)
            continue
        fn = f"cand-{n}.jpg"
        with open(os.path.join(a.out, fn), "wb") as f:
            f.write(data)
        records.append({
            "file": fn, "source": "istock", "istock_id": x["id"],
            "title": x.get("title"), "collection": x.get("istockCollection"),
            "editorial_only": bool(x.get("editorialOnly")),
            "usage_info": x.get("usageInfo"),
            "landing_url": BASE + x["landingUrl"], "comp_url": url,
            "status": "placeholder-comp (watermarked, not licensed)",
            "query": a.query,
        })
        print(f"{fn}  {x['id']}  {'EDITORIAL' if x.get('editorialOnly') else 'creative'}  {x.get('title')}")
    with open(os.path.join(a.out, "candidates.json"), "w") as f:
        json.dump(records, f, indent=2)
    print(f"{len(records)} comps -> {a.out} ({len(editorial)} editorial / {len(creative)} creative Essentials results)")


if __name__ == "__main__":
    main()
