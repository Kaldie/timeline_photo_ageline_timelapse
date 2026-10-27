"""Detect + embed every face on the thumbnails (Saturday task)."""
from .db import connect

_app = None

def model():
    global _app
    if _app is None:
        from insightface.app import FaceAnalysis
        _app = FaceAnalysis(name="buffalo_l", providers=["CUDAExecutionProvider"])
        _app.prepare(ctx_id=0, det_size=(640, 640))
    return _app


def run(progress=print):
    """TODO: for each photo without faces rows:
    - cv2.imread(thumb) -> model().get(img)
    - store bbox, kps (landmarks), det_score, normed_embedding (float32 bytes)
    """
    raise NotImplementedError
