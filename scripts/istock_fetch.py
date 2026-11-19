#!/usr/bin/env python3
"""Fetch watermarked iStock comp images as layout placeholders.

Searches iStock filtered to the Basic plan (Essentials collection, never Signature), ranks
Editorial-use results first, and downloads each pick's 2048px watermarked comp
plus a candidates.json record. Comps are for client review only; the purchased
file replaces them after approval. No iStock account, API key or extra software is needed:
it uses Python's HTTPS and falls back to macOS's own curl when Python can't connect
(missing certificates, a blocked TLS client).

Usage:
  python3 -I istock_fetch.py --query "couple meeting financial advisor" \
      --orientation horizontal --count 4 --out assets/stock/<slot-id>
  --orientation: horizontal | vertical | square | panoramicHorizontal (optional)
  --creative-only / --editorial-only: override the default editorial-first mix
  python3 -I istock_fetch.py --check   # is iStock reachable from this Mac? prints READY or SETUP NEEDED + the fix

Anything that stops the fetch prints "iStock setup needed: <reason>" and "Fix: <what to do>" and exits 3.
"""
import argparse, json, os, re, shutil, ssl, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
BASE = "https://www.istockphoto.com"
FM = Path(os.environ.get("FIGMA_MAINTAINER_HOME") or Path.home() / ".claude" / "figma-maintainer")
CACHE = FM / "istock-check.json"
CURL = shutil.which("curl") or "/usr/bin/curl"
STATE = {"via": "python"}


class SetupNeeded(Exception):
    def __init__(self, reason, fix):
        super().__init__(reason)
        self.reason, self.fix = reason, fix


def _curl(url):
    if not os.path.exists(CURL):
        raise SetupNeeded("Python can't reach iStock and curl isn't available", "Install Apple's Command Line Tools: xcode-select --install")
    r = subprocess.run([CURL, "-sSL", "--compressed", "--max-time", "40", "-A", UA, "-H", "Accept-Language: en-US",
                        "-w", "\n%{http_code}", url], capture_output=True, timeout=60)
    body, _, code = r.stdout.rpartition(b"\n")
    if r.returncode != 0:
        err = r.stderr.decode("utf-8", "ignore").strip()
        if "certificate" in err.lower() or "SSL" in err:
            raise SetupNeeded(f"this Mac can't verify istockphoto.com's HTTPS certificate ({err[:120]})",
                              "Check the Mac's date and time are correct, and turn off any VPN or web filter that intercepts HTTPS, then try again.")
        raise SetupNeeded(f"can't connect to istockphoto.com ({err[:120] or 'curl error ' + str(r.returncode)})",
                          "Check the internet connection, and turn off any VPN or firewall that blocks istockphoto.com, then try again.")
    code = int(code or 0)
    if code in (403, 429):
        raise SetupNeeded(f"iStock refused the request (HTTP {code}): it is blocking automated searches from this network",
                          "Turn off VPN or try another network (e.g. a phone hotspot), wait a few minutes, then try again. "
                          "Opening istockphoto.com once in the browser can help.")
    if code >= 400:
        raise SetupNeeded(f"iStock returned HTTP {code}", "Try again in a few minutes.")
    return body


def get(url):
    """HTTPS GET: Python first; on certificate, connection or block errors, macOS curl (system certificates)."""
    if STATE["via"] == "python":
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except (ssl.SSLError, urllib.error.URLError, OSError) as e:
            # HTTPError (403 etc.) is a URLError too: python's TLS client is sometimes blocked where curl's isn't
            STATE["via"] = "curl"
            STATE["python_error"] = str(getattr(e, "reason", e))[:160]
    return _curl(url)


def search(query, orientation):
    params = {"phrase": query, "mediatype": "photography",
              "istockcollection": "main"}  # main = Essentials = Basic plan
    if orientation:
        params["orientations"] = orientation
    html = get(f"{BASE}/search/2/image?{urllib.parse.urlencode(params)}").decode("utf-8", "ignore")
    m = re.search(r"data-component='Search'>\s*(.*?)\s*</script>", html, re.S)
    if not m:
        if re.search(r"captcha|access denied|are you a robot|px-captcha|_Incapsula_", html, re.I):
            raise SetupNeeded("iStock showed a robot check (captcha) instead of results: it is blocking automated searches from this network",
                              "Turn off VPN or try another network (e.g. a phone hotspot), wait a few minutes, then try again.")
        raise SetupNeeded("iStock's search page has changed, so results can't be read",
                          "Tell the SOP manager: istock_fetch.py needs an update. Meanwhile, pick images on istockphoto.com by hand.")
    assets = json.loads(m.group(1))["search"]["gallery"]["assets"]
    # Belt and braces: the collection filter should already drop Signature.
    return [a for a in assets if not a.get("isIstockSignature") and a.get("assetType") == "image"]


def comp_url(asset):
    """Largest watermarked comp on the asset page (w=is), else the 612 thumb."""
    html = get(BASE + asset["landingUrl"]).decode("utf-8", "ignore").replace("\\u0026", "&").replace("&amp;", "&")
    pat = rf"https://media\.istockphoto\.com/id/{asset['id']}/[^\"' ]+?\.jpg\?s=(\d+)x\d+&w=is&k=20&c=[^\"' ]+"
    found = sorted({(int(m.group(1)), m.group(0)) for m in re.finditer(pat, html)}, reverse=True)
    return found[0][1] if found else asset["thumbUrl"]


def check():
    """Is iStock usable from this Mac? Returns a dict and caches it in the session folder."""
    t0 = time.time()
    res = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "python": sys.version.split()[0]}
    try:
        n = len(search("office", None))
        res.update(ok=n > 0, via=STATE["via"], results=n,
                   reason="" if n else "iStock returned no Essentials results for a test search",
                   fix="" if n else "Try again in a few minutes.")
        if STATE.get("python_error"):
            res["python_error"] = STATE["python_error"]
    except SetupNeeded as e:
        res.update(ok=False, via=STATE["via"], reason=e.reason, fix=e.fix)
    except Exception as e:  # never crash a hook or the doctor
        res.update(ok=False, via=STATE["via"], reason=f"unexpected error: {e}"[:200], fix="Run /figma-maintainer:doctor and send its output to the SOP manager.")
    res["seconds"] = round(time.time() - t0, 1)
    try:
        FM.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(res, indent=1))
    except OSError:
        pass
    return res


def cached_check(max_ok_hours=24, max_fail_minutes=10):
    """The last check if it's fresh (a pass for a day, a failure for 10 minutes), else a new one."""
    try:
        c = json.loads(CACHE.read_text())
        age = time.time() - time.mktime(time.strptime(c["at"], "%Y-%m-%dT%H:%M:%S"))
        if age < (max_ok_hours * 3600 if c.get("ok") else max_fail_minutes * 60):
            return c
    except Exception:
        pass
    return check()


def setup_needed(reason, fix):
    print(f"iStock setup needed: {reason}\nFix: {fix}")
    sys.exit(3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="test iStock access from this Mac and exit")
    ap.add_argument("--query")
    ap.add_argument("--out")
    ap.add_argument("--count", type=int, default=4)
    ap.add_argument("--orientation")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--editorial-only", action="store_true")
    g.add_argument("--creative-only", action="store_true")
    a = ap.parse_args()

    if a.check:
        r = check()
        if r["ok"]:
            print(f"iStock READY: {r['results']} Essentials results in a test search ({r['seconds']}s via {r['via']}).")
            return
        setup_needed(r["reason"], r["fix"])
    if not a.query or not a.out:
        ap.error("--query and --out are required (or use --check)")

    try:
        assets = search(a.query, a.orientation)
        editorial = [x for x in assets if x.get("editorialOnly")]
        creative = [x for x in assets if not x.get("editorialOnly")]
        picks = editorial if a.editorial_only else creative if a.creative_only else editorial + creative
        picks = picks[: a.count]
        if not picks:
            sys.exit(f"no Essentials results for '{a.query}': try simpler search words")

        try:
            os.makedirs(a.out, exist_ok=True)
        except OSError as e:
            setup_needed(f"can't create the output folder {a.out} ({e.strerror})", "Use a folder inside the project or job folder.")
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
    except SetupNeeded as e:
        setup_needed(e.reason, e.fix)
    with open(os.path.join(a.out, "candidates.json"), "w") as f:
        json.dump(records, f, indent=2)
    print(f"{len(records)} comps -> {a.out} ({len(editorial)} editorial / {len(creative)} creative Essentials results)")


if __name__ == "__main__":
    main()
