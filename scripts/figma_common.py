"""Shared helpers for the Figma REST scripts (read-only).

get() retries rate limits (429, honouring Retry-After), Figma server errors (5xx) and network errors with
backoff, and fails with a FigmaError (a SystemExit, so scripts stop with a clear message) that says why.
Test hooks: FIGMA_FIXTURES=<dir> serves responses from <dir>/index.json (API path → file) without network;
FIGMA_RECORD=<dir> saves live responses there. FIGMA_MAINTAINER_HOME overrides ~/.claude/figma-maintainer.
"""
import hashlib, json, os, re, socket, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

API = "https://api.figma.com/v1"
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
RETRY_STATUS = (429, 500, 502, 503, 504)
WHY = {
    400: "Figma rejected the request (bad node id or parameter)",
    401: "the Figma token is invalid or expired: make a new one and store it in the Keychain",
    403: "no access: the token lacks the scope this needs, or the file isn't shared with the token's Figma account",
    404: "not found, or not shared with the token's Figma account",
    429: "Figma's rate limit: wait a few minutes and try again",
}


class FigmaError(SystemExit):
    """A Figma API failure. Subclasses SystemExit, so an uncaught one stops the script with this message."""

    def __init__(self, status, path, detail=""):
        self.status, self.path = status, path
        why = WHY.get(status) or ("a Figma server problem: try again shortly" if status >= 500 else
                                  "network problem: check the connection" if status == 0 else "unexpected error")
        super().__init__(f"Figma API {status or 'network error'} for {path.split('?')[0]}: {why}." + (f" ({detail[:160]})" if detail else ""))


def _fixture(path):
    d = Path(os.environ["FIGMA_FIXTURES"])
    idx = json.loads((d / "index.json").read_text()) if (d / "index.json").exists() else {}
    hit = idx.get(path)
    if hit is None:  # tolerate query order: match on the path plus sorted query
        u = urllib.parse.urlparse(path)
        key = u.path + "?" + "&".join(sorted(u.query.split("&"))) if u.query else u.path
        for k, v in idx.items():
            ku = urllib.parse.urlparse(k)
            if (ku.path + "?" + "&".join(sorted(ku.query.split("&"))) if ku.query else ku.path) == key:
                hit = v
                break
    if hit is None:
        raise FigmaError(404, path, "no fixture")
    if isinstance(hit, dict) and "status" in hit:
        raise FigmaError(hit["status"], path, "fixture error")
    return json.loads((d / hit).read_text())


def _record(path, data):
    d = Path(os.environ["FIGMA_RECORD"]); d.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha1(path.encode()).hexdigest()[:16] + ".json"
    (d / name).write_text(json.dumps(data))
    idx = json.loads((d / "index.json").read_text()) if (d / "index.json").exists() else {}
    idx[path] = name
    (d / "index.json").write_text(json.dumps(idx, indent=1))


def token():
    if os.environ.get("FIGMA_FIXTURES"):
        return "fixture-token"
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
    f = FM / "figma-token"
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


def get(path, tok, retries=4, timeout=180):
    """GET a Figma REST path ('/files/…'). Retries 429/5xx/network errors with backoff; raises FigmaError."""
    if os.environ.get("FIGMA_FIXTURES"):
        return _fixture(path)
    url = path if path.startswith("http") else API + path
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"X-Figma-Token": tok})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = json.load(r)
            if os.environ.get("FIGMA_RECORD"):
                _record(path, data)
            return data
        except urllib.error.HTTPError as e:
            body = e.read()[:300].decode(errors="ignore")
            if e.code in RETRY_STATUS and attempt < retries:
                ra = (e.headers or {}).get("Retry-After") if hasattr(e, "headers") else None
                wait = int(ra) if ra and str(ra).isdigit() else 2 ** (attempt + 1)
                time.sleep(min(wait, 60))
                continue
            raise FigmaError(e.code, path, body)
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            if attempt < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise FigmaError(0, path, str(getattr(e, "reason", e)))


def wait_saved(key, after_iso, tok, max_wait=30):
    """Wait until Figma reports the file saved at or after `after_iso` (REST reads lag edits slightly).
    Returns True when saved, False on timeout."""
    def ts(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    target = ts(after_iso)
    end = time.time() + max_wait
    while True:
        try:
            lt = get(f"/files/{key}/meta", tok, retries=1, timeout=15)["file"].get("last_touched_at")
            if lt and ts(lt) >= target:
                return True
        except FigmaError:
            return False
        if time.time() >= end:
            return False
        time.sleep(3)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


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
