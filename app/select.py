"""Bucket matched faces per 2 months and pick the best frame per bucket."""
from datetime import datetime
import cv2

from .config import BUCKET_MONTHS


def bucket_key(ts: float) -> str:
    d = datetime.fromtimestamp(ts)
    m = ((d.month - 1) // BUCKET_MONTHS) * BUCKET_MONTHS + 1
    return f"{d.year}-{m:02d}"


def sharpness(img_bgr, bbox) -> float:
    x1, y1, x2, y2 = map(int, bbox)
    crop = cv2.cvtColor(img_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(crop, cv2.CV_64F).var()) if crop.size else 0.0


def score(face_row, img_bgr) -> float:
    """TODO: weigh sharpness, frontal pose (kps symmetry), face size, det_score.
    Sunday: + background similarity to neighbouring buckets (CLIP)."""
    raise NotImplementedError


def run():
    """TODO: group matched faces by bucket_key(taken_at), skip rejected ids,
    write best face per bucket into `choices` (NULL face_id = missing slot)."""
    raise NotImplementedError
