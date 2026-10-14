"""Shared helpers for the read-only Figma audit scripts (REST API only)."""
import json, os, re, sys, urllib.error, urllib.parse, urllib.request
from pathlib import Path

API = "https://api.figma.com/v1"


def token():
    t = os.environ.get("FIGMA_TOKEN", "").strip()
    if t:
        return t
    try:  # macOS Keychain (preferred over plain-text files): security add-generic-password -s figma-maintainer -a FIGMA_TOKEN -w
        import subprocess
        r = subprocess.run(["security", "find-generic-password", "-s", "figma-maintainer", "-a", "FIGMA_TOKEN", "-w"],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    home = Path.home()
    f = home / ".claude/figma-maintainer/figma-token"
    if f.is_file() and f.read_text().strip():
        return f.read_text().strip()
    for rc in (".zshrc", ".zprofile", ".bashrc", ".bash_profile"):
        p = home / rc
        if p.is_file():
            for line in p.read_text(errors="ignore").splitlines():
                m = re.match(r"""\s*export\s+FIGMA_TOKEN=["']?([^"'\s#]+)""", line)
                if m:
                    t = m.group(1)
    if t:
        return t
    sys.exit("No Figma token found. Set FIGMA_TOKEN (Figma > Settings > Security > Personal access tokens; read access to File content).")


def get(path, tok):
    req = urllib.request.Request(API + path, headers={"X-Figma-Token": tok})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Figma API {e.code} for {path.split('?')[0]}: {e.read()[:200].decode(errors='ignore')}")


def parse_url(url):
    m = re.search(r"figma\.com/(?:design|file)/([A-Za-z0-9]+)(?:/branch/([A-Za-z0-9]+))?", url)
    if not m:
        sys.exit("Not a figma.com/design URL")
    q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    node = q.get("node-id", [None])[0]
    return m.group(2) or m.group(1), (node.replace("-", ":") if node else None)


def link(key, nid):
    return f"https://www.figma.com/design/{key}/?node-id={nid.replace(':', '-')}"


def fetch_frames(key, ids, tok, chunk=3):
    """Return {id: document} for the given node ids (full depth)."""
    docs = {}
    for i in range(0, len(ids), chunk):
        part = ids[i:i + chunk]
        res = get(f"/files/{key}/nodes?ids={urllib.parse.quote(','.join(part), safe=',:')}", tok)["nodes"]
        for nid, v in res.items():
            if v and v.get("document"):
                docs[nid] = v["document"]
    return docs


def resolve_targets(a):
    """Common CLI handling: --url / --file, --frames, --pages. Returns key, ids, tok, page_of."""
    key, url_node = parse_url(a.url) if a.url else (a.file, None)
    if not key:
        sys.exit("Pass --url or --file")
    tok = token()
    meta = get(f"/files/{key}?depth=2", tok)
    page_of, ids = {}, [i.strip() for i in (a.frames or "").split(",") if i.strip()]
    for p in meta["document"]["children"]:
        for c in p.get("children", []):
            page_of[c["id"]] = p["name"]
    if url_node:
        ids.insert(0, url_node)
    if a.pages:
        wanted = {x.strip().lower() for x in a.pages.split(",")}
        for p in meta["document"]["children"]:
            if p["name"].strip().lower() in wanted:
                ids += [c["id"] for c in p.get("children", []) if c["type"] == "FRAME"
                        and c.get("absoluteBoundingBox", {}).get("width", 0) >= 360]
    ids = list(dict.fromkeys(ids))
    if not ids:
        sys.exit("Nothing to audit: pass --url with a node-id, --frames or --pages")
    return key, ids, tok, page_of, meta["name"]


def visible_walk(n, fn, path=()):
    if n.get("visible", True) is False:
        return
    fn(n, path)
    for c in n.get("children", []) or []:
        visible_walk(c, fn, path + (n,))
