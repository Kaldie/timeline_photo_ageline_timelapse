"""Frames -> MP4. smoothness: 0 = hard cut, 0..1 = crossfade length, 1 = RIFE (TODO)."""
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from .config import RENDER_DIR

FPS = 30


def render(frames: list[np.ndarray], smoothness: float = 0.0,
           seconds_per_photo: float = 0.4, out_name: str = "timelapse.mp4") -> Path:
    hold = max(1, int(seconds_per_photo * FPS))
    fade = int(hold * min(smoothness, 0.99))
    out = RENDER_DIR / out_name
    with tempfile.TemporaryDirectory() as tmp:
        n = 0
        def write(img):
            nonlocal n
            cv2.imwrite(f"{tmp}/{n:06d}.png", img)
            n += 1
        for i, f in enumerate(frames):
            for _ in range(hold - fade):
                write(f)
            if fade and i + 1 < len(frames):
                nxt = frames[i + 1]
                for k in range(fade):
                    a = (k + 1) / (fade + 1)
                    write(cv2.addWeighted(f, 1 - a, nxt, a, 0))
        subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS), "-i", f"{tmp}/%06d.png",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", str(out)],
                       check=True, capture_output=True)
    return out
