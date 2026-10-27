"""Generic mode: bucket matched photos per 2 months, pick best frame per bucket."""
import json

import cv2

from .select import bucket_key  # same bucketing rule as face mode
from .db import connect


def sharpness(path: str) -> float:
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    return float(cv2.Laplacian(img, cv2.CV_64F).var()) if img is not None else 0.0


def run():
    con = connect()
    rows = con.execute(
        "SELECT p.id, p.thumb, p.taken_at, e.match_score "
        "FROM photo_embeddings e JOIN photos p ON p.id = e.photo_id "
        "WHERE e.match_score IS NOT NULL"
    ).fetchall()

    existing = {
        r["bucket"]: json.loads(r["rejected"])
        for r in con.execute("SELECT bucket, rejected FROM gchoices").fetchall()
    }

    buckets: dict[str, list] = {}
    for r in rows:
        buckets.setdefault(bucket_key(r["taken_at"]), []).append(r)

    for bucket, candidates in buckets.items():
        rejected = existing.get(bucket, [])
        pool = [c for c in candidates if c["id"] not in rejected]
        best = max(pool, key=lambda c: sharpness(c["thumb"]), default=None)
        con.execute(
            "INSERT INTO gchoices(bucket, photo_id, rejected) VALUES (?,?,?) "
            "ON CONFLICT(bucket) DO UPDATE SET photo_id=excluded.photo_id",
            (bucket, best["id"] if best else None, json.dumps(rejected)),
        )
    con.commit()
    return len(buckets)
