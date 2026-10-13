#!/usr/bin/env python3
"""Read Figma comments and match each one to the layer it points at.

Pulls a file's comments through the Figma REST API, keeps the ones pinned to the
given frame (or every frame), and for each top-level comment lists the nearest
text layers and image layers to the pin, plus replies. Read-only: it never posts,
resolves or deletes comments.

Token: FIGMA_TOKEN env var, else ~/.claude/figma-maintainer/figma-token, else an
`export FIGMA_TOKEN=...` line in ~/.zshrc / ~/.zprofile / ~/.bashrc / ~/.bash_profile.
Create one in Figma > Settings > Security > Personal access tokens with read access
to File content and Comments.

Usage:
  python3 -I figma_comments.py --url "<figma url with node-id>" --out <dir>
  python3 -I figma_comments.py --file <fileKey> [--node 12421:2541] [--all-frames] \
      [--include-resolved] [--author "Jesse Brede"] --out <dir>
Writes <dir>/comments.json (structured) and <dir>/comments.md (readable), and
prints the markdown.
"""
import argparse, json, os, re, sys, urllib.parse, urllib.request
from pathlib import Path

API = "https://api.figma.com/v1"


def token():
    t = os.environ.get("FIGMA_TOKEN", "").strip()
    if t:
        return t
    home = Path.home()
    f = home / ".claude/figma-maintainer/figma-token"
    if f.is_file():
        t = f.read_text().strip()
        if t:
            return t
    for rc in (".zshrc", ".zprofile", ".bashrc", ".bash_profile"):
        p = home / rc
        if not p.is_file():
            continue
        for line in p.read_text(errors="ignore").splitlines():
            m = re.match(r"""\s*export\s+FIGMA_TOKEN=["']?([^"'\s#]+)""", line)
            if m:
                t = m.group(1)
    if t:
        return t
    sys.exit("No Figma token found. Set FIGMA_TOKEN (see the header of this script).")


def get(path, tok):
    req = urllib.request.Request(API + path, headers={"X-Figma-Token": tok})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Figma API {e.code} for {path.split('?')[0]}: {e.read()[:200].decode(errors='ignore')}")


def parse_url(url):
    m = re.search(r"figma\.com/(?:design|file)/([A-Za-z0-9]+)(?:/branch/([A-Za-z0-9]+))?", url)
    if not m:
        sys.exit("Not a figma.com/design URL")
    key = m.group(2) or m.group(1)
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    node = q.get("node-id", [None])[0]
    return key, node.replace("-", ":") if node else None


def has_image(n):
    return any(f.get("type") == "IMAGE" and f.get("visible", True) for f in n.get("fills", []) or [])


def collect(frame):
    """Visible TEXT and image-fill layers with frame-relative boxes, plus all descendant ids."""
    ox, oy = frame["absoluteBoundingBox"]["x"], frame["absoluteBoundingBox"]["y"]
    texts, images, ids = [], [], set()

    def walk(n, hidden):
        ids.add(n["id"])
        hidden = hidden or n.get("visible", True) is False
        b = n.get("absoluteBoundingBox")
        if not hidden and b:
            box = (b["x"] - ox, b["y"] - oy, b["width"], b["height"])
            if n["type"] == "TEXT":
                texts.append({"id": n["id"], "box": box, "text": n.get("characters", "")})
            elif has_image(n):
                images.append({"id": n["id"], "box": box, "name": n.get("name", "")})
        for c in n.get("children", []):
            walk(c, hidden)

    walk(frame, False)
    return texts, images, ids


def dist(box, x, y):
    bx, by, w, h = box
    dx = max(bx - x, 0, x - (bx + w))
    dy = max(by - y, 0, y - (by + h))
    return round(dx + dy * 1.5)  # vertical distance matters more on long pages


def nearest(items, x, y, k):
    out = sorted(items, key=lambda i: dist(i["box"], x, y))[:k]
    return [dict(i, distance=dist(i["box"], x, y)) for i in out]


def flat(s):
    return re.sub(r"\s+", " ", s).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    ap.add_argument("--file")
    ap.add_argument("--node", help="frame id like 12421:2541 (default: node-id from --url)")
    ap.add_argument("--all-frames", action="store_true", help="ignore the node filter")
    ap.add_argument("--include-resolved", action="store_true")
    ap.add_argument("--author", help="only top-level comments by this handle (case-insensitive)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    key, node = (parse_url(a.url) if a.url else (a.file, None))
    node = a.node or node
    if not key:
        sys.exit("Pass --url or --file")
    tok = token()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    comments = get(f"/files/{key}/comments?as_md=true", tok)["comments"]
    replies = {}
    for c in comments:
        if c.get("parent_id"):
            replies.setdefault(c["parent_id"], []).append(c)
    tops = [c for c in comments if not c.get("parent_id")]
    if not a.include_resolved:
        tops = [c for c in tops if not c.get("resolved_at")]
    if a.author:
        tops = [c for c in tops if c["user"]["handle"].lower() == a.author.lower()]

    pinned = {}
    for c in tops:
        nid = (c.get("client_meta") or {}).get("node_id")
        if nid:
            pinned.setdefault(nid, []).append(c)

    frames = {}
    want = sorted(pinned) if (a.all_frames or not node) else sorted(set(pinned) | {node})
    for i in range(0, len(want), 20):
        ids = ",".join(want[i:i + 20])
        for nid, v in get(f"/files/{key}/nodes?ids={urllib.parse.quote(ids, safe=',:')}", tok)["nodes"].items():
            if v and v.get("document"):
                frames[nid] = v["document"]

    groups = []
    target_ids = None
    if node and not a.all_frames:
        if node not in frames:
            sys.exit(f"Node {node} not found in file {key}")
        target_ids = collect(frames[node])[2]
    for fid, cs in pinned.items():
        if target_ids is not None and fid not in target_ids:
            continue
        frame = frames.get(fid)
        if not frame or not frame.get("absoluteBoundingBox"):
            continue
        texts, images, _ = collect(frame)
        items = []
        for c in sorted(cs, key=lambda c: (c["client_meta"].get("node_offset") or {}).get("y", 0)):
            off = c["client_meta"].get("node_offset") or {"x": 0, "y": 0}
            x, y = off["x"], off["y"]
            items.append({
                "comment_id": c["id"], "author": c["user"]["handle"], "created": c["created_at"][:10],
                "resolved": bool(c.get("resolved_at")), "message": c["message"],
                "pin": {"x": round(x), "y": round(y)},
                "replies": [{"author": r["user"]["handle"], "message": r["message"]}
                            for r in sorted(replies.get(c["id"], []), key=lambda r: r["created_at"])],
                "near_text": [{"id": t["id"], "distance": t["distance"], "text": t["text"]} for t in nearest(texts, x, y, 3)],
                "near_images": [{"id": t["id"], "distance": t["distance"], "name": t["name"]} for t in nearest(images, x, y, 2)],
            })
        groups.append({"frame_id": fid, "frame_name": frame["name"], "comments": items})

    data = {"file_key": key, "node": node, "groups": groups}
    (out / "comments.json").write_text(json.dumps(data, indent=2, ensure_ascii=False))

    md = [f"# Comments — file {key}" + (f", frame {node}" if node and not a.all_frames else "")]
    total = sum(len(g["comments"]) for g in groups)
    md.append(f"{total} comment(s){'' if a.include_resolved else ' (unresolved only)'}.")
    for g in groups:
        md.append(f"\n## {g['frame_name']} `{g['frame_id']}` — {len(g['comments'])}")
        for i, c in enumerate(g["comments"], 1):
            msg = flat(c["message"])
            md.append(f"\n{i}. **{msg}** — {c['author']}, {c['created']}, pin ({c['pin']['x']}, {c['pin']['y']})"
                      + (" [resolved]" if c["resolved"] else ""))
            for r in c["replies"]:
                md.append(f"   - reply, {r['author']}: {flat(r['message'])}")
            for t in c["near_text"]:
                txt = flat(t["text"])
                md.append(f"   - text `{t['id']}` ~{t['distance']}px: {txt[:140]!r}")
            for t in c["near_images"]:
                md.append(f"   - image `{t['id']}` ~{t['distance']}px: {t['name']}")
    (out / "comments.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
