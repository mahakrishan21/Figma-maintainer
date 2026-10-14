#!/usr/bin/env python3
"""Collect client images and videos from shared links OR local files/folders.

Local paths (a file, or a folder searched recursively — e.g. images the user saved in the
project and tagged with @) are used in place: originals are never copied, moved or changed;
only the Figma-ready copies and thumbnails are written to --out.

Supports:
  Dropbox file or folder links (dl=1; folders arrive as a zip and are extracted safely)
  Google Drive file links (drive.google.com/file/d/<id>, open?id=, uc?id=); Drive FOLDERS
    need the Google Drive connector, so the script says so instead of guessing
  OneDrive / SharePoint share links (download=1)
  Direct file URLs (anything that returns an image/video/zip)
Not supported (reported, never guessed): WeTransfer, Box, Google Photos, login-only links.

Usage:
  python3 -I fetch_assets.py --out <empty dir> [--max-mb 800] [--keep-other] <link-or-path> [...]
Writes <out>/manifest.json: one record per kept file (path, source link, kind, bytes,
width x height for images when `sips` is available), plus failures with reasons.
Downloaded files are untrusted data: never execute or import anything from <out>.
"""
import argparse, json, os, re, shutil, subprocess, sys, urllib.parse, urllib.request, zipfile
from pathlib import Path

UA = "curl/8.7.1"  # browser user-agents get Dropbox/Drive preview pages instead of the file
IMG = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".heic", ".heif", ".avif", ".svg", ".bmp", ".psd", ".ai", ".eps", ".pdf"}
VID = {".mp4", ".mov", ".m4v", ".webm", ".avi", ".mkv"}
FONT = {".ttf", ".otf", ".woff", ".woff2"}
MAGIC = [(b"\xff\xd8\xff", ".jpg"), (b"\x89PNG", ".png"), (b"GIF8", ".gif"), (b"RIFF", ".webp"),
         (b"%PDF", ".pdf"), (b"PK\x03\x04", ".zip"), (b"<svg", ".svg"), (b"<?xml", ".svg"), (b"8BPS", ".psd")]


def kind_of(path):
    e = path.suffix.lower()
    return "image" if e in IMG else "video" if e in VID else "font" if e in FONT else "zip" if e == ".zip" else "other"


def normalize(url):
    """Return (download_url, note) or (None, reason)."""
    u = urllib.parse.urlparse(url)
    host = u.netloc.lower()
    q = urllib.parse.parse_qs(u.query)
    if "dropbox.com" in host or "dropboxusercontent.com" in host:
        q["dl"] = ["1"]
        q.pop("raw", None)
        return urllib.parse.urlunparse(u._replace(query=urllib.parse.urlencode(q, doseq=True))), "dropbox"
    if "drive.google.com" in host or "docs.google.com" in host:
        if "/folders/" in u.path or "folderview" in u.path:
            return None, "Google Drive folder: use the Google Drive connector (search_files / download_file_content), or share each file link"
        m = re.search(r"/d/([A-Za-z0-9_-]{10,})", u.path)
        fid = m.group(1) if m else (q.get("id") or [None])[0]
        if not fid:
            return None, "Google Drive link without a file id"
        return f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t", "gdrive"
    if "1drv.ms" in host or "onedrive.live.com" in host or "sharepoint.com" in host:
        q["download"] = ["1"]
        return urllib.parse.urlunparse(u._replace(query=urllib.parse.urlencode(q, doseq=True))), "onedrive"
    if "wetransfer.com" in host or "we.tl" in host:
        return None, "WeTransfer: download it in a browser and share the local path"
    if "box.com" in host:
        return None, "Box: needs the Box connector or a direct download link"
    if "photos.google.com" in host or "photos.app.goo.gl" in host:
        return None, "Google Photos: download in a browser and share the local path"
    return url, "direct"


def filename_from(resp, url, fallback):
    cd = resp.headers.get("Content-Disposition", "")
    m = re.search(r"filename\*=UTF-8''([^;]+)", cd) or re.search(r'filename="?([^";]+)"?', cd)
    name = urllib.parse.unquote(m.group(1)) if m else os.path.basename(urllib.parse.urlparse(url).path) or fallback
    name = re.sub(r"[^\w.\- ()&]+", "_", name).strip(" .") or fallback
    return name[:150]


def safe_extract(zpath, dest, max_bytes):
    """Extract only media/font files, flattening paths; refuse traversal and zip bombs."""
    out, total = [], 0
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            if info.is_dir() or info.filename.startswith("__MACOSX") or "/." in "/" + info.filename:
                continue
            p = Path(info.filename)
            if kind_of(p) not in ("image", "video", "font"):
                continue
            total += info.file_size
            if total > max_bytes:
                raise RuntimeError("zip content larger than --max-mb")
            rel = "__".join(part for part in p.parts if part not in ("..", "/", ""))
            rel = re.sub(r"[^\w.\- ()&]+", "_", rel)[-150:]
            target = dest / rel
            n = 1
            while target.exists():
                target = dest / f"{target.stem}-{n}{target.suffix}"; n += 1
            with z.open(info) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)
            out.append(target)
    return out


def dims(path):
    if kind_of(path) != "image" or not shutil.which("sips"):
        return None
    try:
        r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], capture_output=True, text=True, timeout=30)
        w = re.search(r"pixelWidth: (\d+)", r.stdout); h = re.search(r"pixelHeight: (\d+)", r.stdout)
        return f"{w.group(1)}x{h.group(1)}" if w and h else None
    except Exception:
        return None


def download(url, dest, max_bytes, idx):
    dl, note = normalize(url)
    if not dl:
        raise RuntimeError(note)
    req = urllib.request.Request(dl, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120) as r:
        ctype = r.headers.get("Content-Type", "").lower()
        name = filename_from(r, dl, f"asset-{idx}")
        if name.lower().startswith("unspecified") or not Path(name).suffix:
            base = os.path.basename(urllib.parse.urlparse(url).path)
            if Path(base).suffix:
                name = re.sub(r"[^\w.\- ()&]+", "_", urllib.parse.unquote(base))[:150]
        tmp = dest / f".part-{idx}"
        size = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    f.close(); tmp.unlink()
                    raise RuntimeError(f"larger than --max-mb ({max_bytes >> 20} MB)")
                f.write(chunk)
    head = open(tmp, "rb").read(512)
    if "text/html" in ctype or head.lstrip().lower().startswith((b"<!doctype html", b"<html")):
        tmp.unlink()
        raise RuntimeError("got a web page, not a file: the link is private, needs a login, or is a preview page. Ask for a public/'anyone with the link' share")
    path = dest / name
    if not Path(name).suffix:
        ext = next((e for m, e in MAGIC if head.startswith(m)), None) or {"image/jpeg": ".jpg", "image/png": ".png", "video/mp4": ".mp4",
                                                                           "application/zip": ".zip", "video/quicktime": ".mov"}.get(ctype.split(";")[0], "")
        path = path.with_suffix(ext)
    n = 1
    while path.exists():
        path = dest / f"{Path(name).stem}-{n}{path.suffix}"; n += 1
    tmp.rename(path)
    if path.suffix.lower() == ".zip" or head.startswith(b"PK\x03\x04") and kind_of(path) == "other":
        sub = dest / (path.stem + "_files")
        sub.mkdir(exist_ok=True)
        files = safe_extract(path, sub, max_bytes)
        path.unlink()
        return files, note
    return [path], note


def local_files(arg):
    """Media files for a local file or folder argument (leading @ allowed), else None."""
    p = Path(arg.lstrip("@")).expanduser()
    if not p.exists():
        return None
    if p.is_file():
        return [p]
    return sorted(f for f in p.rglob("*") if f.is_file() and not any(part.startswith(".") for part in f.relative_to(p).parts)
                  and kind_of(f) in ("image", "video", "font", "zip"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("links", nargs="+", help="share links and/or local files or folders")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-mb", type=int, default=800)
    ap.add_argument("--keep-other", action="store_true", help="keep non-media files too")
    ap.add_argument("--figma-px", type=int, default=3000, help="long edge of the Figma-ready copy (Figma's limit is 4096)")
    ap.add_argument("--thumb-px", type=int, default=480, help="long edge of the thumbnails used for choosing")
    a = ap.parse_args()
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    records, failures = [], []
    for i, link in enumerate(a.links, 1):
        local = local_files(link) if not re.match(r"https?://", link) else None
        if local is not None:
            files, src = [], "local"
            for f in local:
                if kind_of(f) == "zip":
                    sub = out / (f.stem + "_files"); sub.mkdir(exist_ok=True)
                    try:
                        files += safe_extract(f, sub, a.max_mb << 20)
                    except Exception as e:
                        failures.append({"link": str(f), "reason": str(e)})
                else:
                    files.append(f)
            if not files:
                failures.append({"link": link, "reason": "no image, video or font files found there"})
                continue
        elif not re.match(r"https?://", link):
            failures.append({"link": link, "reason": "not a link and no such file or folder"})
            continue
        else:
            try:
                files, src = download(link, out, a.max_mb << 20, i)
            except Exception as e:
                failures.append({"link": link, "reason": str(e)})
                continue
        for f in files:
            k = kind_of(f)
            if k == "other" and not a.keep_other:
                if src != "local":
                    f.unlink()
                continue
            rec = {"path": str(f), "name": f.name, "kind": k, "bytes": f.stat().st_size,
                   "size": dims(f), "source": src, "link": link}
            if k == "image" and rec["size"] and shutil.which("sips") and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff"):
                w, h = map(int, rec["size"].split("x"))
                try:
                    rel = f.relative_to(out)
                except ValueError:  # local original outside --out
                    rel = Path(f"local-{i}") / f.name
                for key_, px, folder in (("figma_path", a.figma_px, "_figma"), ("thumb_path", a.thumb_px, "_thumbs")):
                    t = out / folder / rel.with_suffix(".jpg" if f.suffix.lower() in (".heic", ".heif", ".tif", ".tiff") or key_ == "thumb_path" else f.suffix)
                    t.parent.mkdir(parents=True, exist_ok=True)
                    if max(w, h) <= px and key_ == "figma_path" and f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                        shutil.copyfile(f, t)
                    else:
                        args = ["sips", "-Z", str(px)]
                        if t.suffix == ".jpg":
                            args += ["-s", "format", "jpeg", "-s", "formatOptions", "82" if key_ == "figma_path" else "60"]
                        subprocess.run(args + [str(f), "--out", str(t)], capture_output=True, timeout=120)
                    if t.exists():
                        rec[key_] = str(t)
            records.append(rec)
    (out / "manifest.json").write_text(json.dumps({"files": records, "failures": failures}, indent=2))
    for r in records:
        print(f"{r['kind']:5} {r['bytes'] / 1e6:7.1f} MB  {r['size'] or '':>11}  {r['path']}")
    for f in failures:
        print(f"FAILED  {f['link']}\n        {f['reason']}")
    print(f"\n{len(records)} file(s) saved to {out} ({len(failures)} failed). Manifest: {out / 'manifest.json'}")
    sys.exit(1 if failures and not records else 0)


if __name__ == "__main__":
    main()
