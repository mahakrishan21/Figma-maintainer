#!/usr/bin/env python3
"""Build Figma PROTOTYPE links (figma.com/proto/...) for frames you changed — read-only (REST API).

The client message must link to the prototype, never the design/page link.
For each node it finds the page and the screen frame (the outermost frame under the page or
section that contains the node) and prints:
  <frame name>  https://www.figma.com/proto/<fileKey>/<File-Name>?page-id=..&node-id=..&starting-point-node-id=..&scaling=scale-down-width&content-scaling=fixed

Usage:
  proto_link.py --url "<any figma design/proto link with node-id>" [--url ...]
  proto_link.py --file <fileKey> --node 22170:1642 [--node 22170:1904]
  add --json for machine-readable output
"""
import argparse, json, os, re, sys, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figma_common import get, parse_url, token  # noqa: E402

SCREEN_TYPES = ("FRAME", "COMPONENT", "COMPONENT_SET", "INSTANCE")


def path_to(node, nid, path=()):
    if node.get("id") == nid:
        return list(path) + [node]
    for c in node.get("children", []) or []:
        r = path_to(c, nid, path + (node,))
        if r:
            return r
    return None


def slug(name):
    return re.sub(r"-+", "-", re.sub(r"[^A-Za-z0-9]+", "-", name or "Figma")).strip("-") or "Figma"


def proto_url(key, fname, page_id, frame_id):
    sid = frame_id.replace(":", "-")
    q = {"page-id": page_id or "", "node-id": sid, "starting-point-node-id": sid,
         "scaling": "scale-down-width", "content-scaling": "fixed"}
    return f"https://www.figma.com/proto/{key}/{slug(fname)}?" + urllib.parse.urlencode(q)


def proto_links(key, nids, tok):
    res = get(f"/files/{key}?ids={urllib.parse.quote(','.join(nids), safe=',:')}", tok)
    fname = res.get("name", "Figma")
    out = []
    for nid in nids:
        p = path_to(res["document"], nid)
        if not p:
            out.append({"node": nid, "error": "node not found"}); continue
        page = next((x for x in p if x["type"] == "CANVAS"), None)
        below = p[p.index(page) + 1:] if page else p
        screen = next((x for x in below if x["type"] in SCREEN_TYPES), p[-1])
        url = proto_url(key, fname, page["id"] if page else "", screen["id"])
        out.append({"node": nid, "frame_id": screen["id"], "frame": screen.get("name"), "page": page.get("name") if page else None,
                    "page_id": page["id"] if page else None, "link": url})
    return fname, out


def locate(key, nids, tok):
    """Page and screen frame for each node: {node: {page, page_id, frame, frame_id, proto_link}}, plus the file name.
    Cheap first pass over pages and their top-level frames (depth=2); deeper nodes fall back to proto_links()."""
    meta = get(f"/files/{key}?depth=2", tok)
    fname = meta.get("name", "Figma")
    top = {}
    for page in meta["document"].get("children", []) or []:
        top[page["id"]] = (page, None)
        for c in page.get("children", []) or []:
            top[c["id"]] = (page, c)
    out, deep = {}, []
    for nid in dict.fromkeys(n for n in nids if n):
        page, fr = top.get(nid, (None, None))
        if page and fr is None:  # pinned to the page canvas itself
            out[nid] = {"page": page["name"], "page_id": page["id"], "frame": None, "frame_id": None, "proto_link": None}
        elif fr is not None and fr["type"] in SCREEN_TYPES:
            out[nid] = {"page": page["name"], "page_id": page["id"], "frame": fr["name"], "frame_id": fr["id"],
                        "proto_link": proto_url(key, fname, page["id"], fr["id"])}
        else:
            deep.append(nid)
    for i in range(0, len(deep), 20):
        for r in proto_links(key, deep[i:i + 20], tok)[1]:
            out[r["node"]] = ({"page": None, "page_id": None, "frame": None, "frame_id": None, "proto_link": None, "error": r["error"]}
                              if r.get("error") else {"page": r["page"], "page_id": r["page_id"], "frame": r["frame"],
                                                       "frame_id": r["frame_id"], "proto_link": r["link"]})
    return fname, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", action="append", default=[])
    ap.add_argument("--file"); ap.add_argument("--node", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    groups = {}
    for u in a.url:
        k, n = parse_url(u)
        if n:
            groups.setdefault(k, []).append(n)
    if a.file and a.node:
        groups.setdefault(a.file, []).extend(n.replace("-", ":") for n in a.node)
    if not groups:
        sys.exit("Pass --url with a node-id, or --file and --node")
    tok, allout = token(), []
    for k, nids in groups.items():
        _, out = proto_links(k, list(dict.fromkeys(nids)), tok)
        allout += out
    if a.json:
        print(json.dumps(allout, indent=2))
    else:
        for o in allout:
            print(f"{o.get('frame', o['node'])}\t{o.get('link') or o.get('error')}")


if __name__ == "__main__":
    main()
