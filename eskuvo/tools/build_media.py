#!/usr/bin/env python3
"""
Esküvői galéria építő.

Az eredeti fájlokat az originals/ mappába kell tenni (ez NEM kerül a repóba).
Almappák = csoportok a galériában, pl. originals/Szertartás, originals/Buli.

A szkript elkészíti:
  media/photos/   webes méretű JPEG (2400 px hosszabbik oldal, GPS adat nélkül)
  media/thumbs/   kis WebP előnézetek
  media/videos/   H.264 MP4, 1080p, gyors indítással
  media/posters/  videó borítóképek
  media.json      a galéria adatai (az "info" és a meglévő képaláírások megmaradnak)

Futtatás:  python3 tools/build_media.py
"""
import json
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "originals"
OUT = ROOT / "media"
MANIFEST = ROOT / "media.json"

PHOTO_EXT = {".jpg", ".jpeg", ".png", ".heic", ".webp", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".mts"}

FULL_EDGE = 2400
THUMB_EDGE = 700
GITHUB_LIMIT_MB = 95  # a GitHub 100 MB felett nem fogad el fájlt

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    PHOTO_EXT.discard(".heic")


def slug(path: Path) -> str:
    rel = path.relative_to(SRC).with_suffix("")
    s = unicodedata.normalize("NFKD", str(rel)).encode("ascii", "ignore").decode()
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return s or "item"


def group_of(path: Path) -> str:
    rel = path.relative_to(SRC)
    return rel.parts[0] if len(rel.parts) > 1 else ""


def taken_at(img: Image.Image, path: Path) -> str:
    try:
        exif = img.getexif()
        raw = exif.get_ifd(0x8769).get(36867) or exif.get(306)
        if raw:
            return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").isoformat()
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).isoformat()


def build_photo(path: Path, old: dict) -> dict:
    name = slug(path)
    full = OUT / "photos" / f"{name}.jpg"
    thumb = OUT / "thumbs" / f"{name}.webp"
    with Image.open(path) as im:
        when = taken_at(im, path)
        im = ImageOps.exif_transpose(im).convert("RGB")
        if not full.exists():
            big = im.copy()
            big.thumbnail((FULL_EDGE, FULL_EDGE), Image.LANCZOS)
            big.save(full, "JPEG", quality=84, optimize=True, progressive=True)
        if not thumb.exists():
            small = im.copy()
            small.thumbnail((THUMB_EDGE, THUMB_EDGE), Image.LANCZOS)
            small.save(thumb, "WEBP", quality=78, method=6)
    with Image.open(thumb) as t:
        w, h = t.size
    src = f"media/photos/{name}.jpg"
    prev = old.get(src, {})
    return {
        "src": src,
        "thumb": f"media/thumbs/{name}.webp",
        "w": w,
        "h": h,
        "group": group_of(path),
        "caption": prev.get("caption", ""),
        "taken": when,
    }


def probe_duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def build_video(path: Path, old: dict) -> dict:
    name = slug(path)
    out = OUT / "videos" / f"{name}.mp4"
    poster = OUT / "posters" / f"{name}.jpg"
    dur = probe_duration(path)

    if not out.exists():
        # A bitrátát úgy választjuk, hogy a fájl beférjen a GitHub korlátba
        budget_kbit = (GITHUB_LIMIT_MB * 8 * 1024 * 0.92) / max(dur, 1)
        video_kbit = int(min(5000, budget_kbit - 128))
        if video_kbit < 600:
            print(f"  ! {path.name}: túl hosszú ({dur/60:.0f} perc) egyetlen fájlnak, "
                  "érdemes részekre vágni vagy YouTube-ra tenni.", file=sys.stderr)
            video_kbit = 600
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(path),
            "-vf", "scale='min(1920,iw)':-2",
            "-c:v", "libx264", "-preset", "slow",
            "-b:v", f"{video_kbit}k", "-maxrate", f"{int(video_kbit*1.4)}k",
            "-bufsize", f"{video_kbit*2}k",
            "-pix_fmt", "yuv420p", "-profile:v", "high",
            "-c:a", "aac", "-b:a", "128k",
            "-movflags", "+faststart", str(out)], check=True)

    if not poster.exists():
        at = min(5.0, dur / 3) if dur else 0
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error", "-ss", f"{at:.2f}", "-i", str(path),
            "-frames:v", "1", "-vf", "scale='min(1600,iw)':-2", "-q:v", "3",
            str(poster)], check=True)

    size_mb = out.stat().st_size / 1024 / 1024
    if size_mb > GITHUB_LIMIT_MB:
        print(f"  ! {out.name} {size_mb:.0f} MB, ez nem fog felmenni a GitHubra.", file=sys.stderr)

    src = f"media/videos/{name}.mp4"
    prev = old.get(src, {})
    m, s = divmod(int(round(dur)), 60)
    return {
        "src": src,
        "poster": f"media/posters/{name}.jpg",
        "title": prev.get("title") or path.stem.replace("_", " "),
        "duration": f"{m}:{s:02d}",
    }


def main():
    for sub in ("photos", "thumbs", "videos", "posters"):
        (OUT / sub).mkdir(parents=True, exist_ok=True)

    existing = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else {}
    old = {x["src"]: x for x in existing.get("photos", []) + existing.get("videos", [])}

    files = sorted(p for p in SRC.rglob("*") if p.is_file() and not p.name.startswith("."))
    photos, videos = [], []
    for p in files:
        ext = p.suffix.lower()
        try:
            if ext in PHOTO_EXT:
                print("fotó  ", p.relative_to(SRC))
                photos.append(build_photo(p, old))
            elif ext in VIDEO_EXT:
                print("videó ", p.relative_to(SRC))
                videos.append(build_video(p, old))
        except Exception as e:
            print(f"  ! kihagyva: {p.name} ({e})", file=sys.stderr)

    photos.sort(key=lambda x: x["taken"])
    manifest = {
        "info": existing.get("info", {"date": "", "place": ""}),
        "photos": photos,
        "videos": videos,
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")

    total = sum(f.stat().st_size for f in OUT.rglob("*") if f.is_file()) / 1024 / 1024
    print(f"\n{len(photos)} fotó, {len(videos)} videó, összesen {total:.0f} MB a media/ mappában.")
    if total > 900:
        print("! A GitHub Pages ~1 GB-os oldalméretet javasol, ez már a határon van.", file=sys.stderr)


if __name__ == "__main__":
    main()
