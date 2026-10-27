"""Warp a full-res photo so the eyes land at a fixed spot."""
import cv2
import numpy as np

from .config import OUTPUT_SIZE, EYE_Y, EYE_DISTANCE


def align(img_bgr: np.ndarray, left_eye, right_eye) -> np.ndarray:
    """left_eye/right_eye in img_bgr pixel coords (scale thumb kps up first)."""
    le, re = np.array(left_eye, float), np.array(right_eye, float)
    S = OUTPUT_SIZE
    dst_l = np.array([S * (0.5 - EYE_DISTANCE / 2), S * EYE_Y])
    dst_r = np.array([S * (0.5 + EYE_DISTANCE / 2), S * EYE_Y])
    M, _ = cv2.estimateAffinePartial2D(np.stack([le, re]), np.stack([dst_l, dst_r]))
    return cv2.warpAffine(img_bgr, M, (S, S), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REFLECT)
