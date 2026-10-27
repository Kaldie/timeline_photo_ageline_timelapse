"""Walk the Takeout folder, read capture times, write downscaled copies."""
import json
from datetime import datetime
from pathlib import Path
from PIL import Image, ExifTags

from .config import TAKEOUT_DIR, THUMB_DIR, THUMB_LONG_EDGE, IMAGE_EXTS
from .db import connect

DATETIME_ORIGINAL = 36867


def sidecar_time(p: Path):
    # Takeout names vary: IMG_1.jpg.json, IMG_1.jpg.supplemental-metadata.json, ...
    for cand in p.parent.glob(p.name[:40] + "*.json"):
        try:
            ts = json.loads(cand.read_text())["photoTakenTime"]["timestamp"]
            return float(ts)
        except Exception:
            continue
    return None


def exif_time(img: Image.Image):
    try:
        raw = img.getexif().get_ifd(ExifTags.IFD.Exif).get(DATETIME_ORIGINAL)
        return datetime.strptime(raw, "%Y:%m:%d %H:%M:%S").timestamp() if raw else None
    except Exception:
        return None


def run(progress=print):
    con = connect()
    files = [p for p in TAKEOUT_DIR.rglob("*") if p.suffix.lower() in IMAGE_EXTS]
    for i, p in enumerate(files):
        if con.execute("SELECT 1 FROM photos WHERE path=?", (str(p),)).fetchone():
            continue
        try:
            img = Image.open(p)
            taken = sidecar_time(p) or exif_time(img) or p.stat().st_mtime
            w, h = img.size
            img = img.convert("RGB")
            img.thumbnail((THUMB_LONG_EDGE, THUMB_LONG_EDGE))
            thumb = THUMB_DIR / f"{i:07d}.jpg"
            img.save(thumb, quality=90)
            con.execute(
                "INSERT INTO photos(path, thumb, taken_at, width, height) VALUES (?,?,?,?,?)",
                (str(p), str(thumb), taken, w, h),
            )
        except Exception as e:
            progress(f"skip {p.name}: {e}")
        if i % 200 == 0:
            con.commit()
            progress(f"indexed {i}/{len(files)}")
    con.commit()
    return len(files)


if __name__ == "__main__":
    run()
