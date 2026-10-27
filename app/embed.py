"""Whole-image CLIP embeddings for generic (similarity) mode."""
import numpy as np
from PIL import Image

from .config import CLIP_MODEL, CLIP_PRETRAINED, CLIP_BATCH_SIZE
from .db import connect

_model = None
_preprocess = None
_device = None


def model():
    global _model, _preprocess, _device
    if _model is None:
        import torch
        import open_clip
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _model, _, _preprocess = open_clip.create_model_and_transforms(
            CLIP_MODEL, pretrained=CLIP_PRETRAINED
        )
        _model = _model.to(_device).eval()
    return _model, _preprocess, _device


def embed_images(paths: list[str]) -> np.ndarray:
    """L2-normalised float32[len(paths), dim] CLIP embeddings."""
    import torch

    m, preprocess, device = model()
    tensors = [preprocess(Image.open(p).convert("RGB")) for p in paths]
    batch = torch.stack(tensors).to(device)
    with torch.no_grad():
        feats = m.encode_image(batch)
        feats = feats / feats.norm(dim=-1, keepdim=True)
    return feats.cpu().numpy().astype(np.float32)


def run(progress=print):
    """Embed every thumbnail that doesn't have a photo_embeddings row yet."""
    con = connect()
    rows = con.execute(
        "SELECT p.id, p.thumb FROM photos p "
        "LEFT JOIN photo_embeddings e ON e.photo_id = p.id "
        "WHERE e.photo_id IS NULL"
    ).fetchall()
    for i in range(0, len(rows), CLIP_BATCH_SIZE):
        chunk = rows[i:i + CLIP_BATCH_SIZE]
        vecs = embed_images([r["thumb"] for r in chunk])
        con.executemany(
            "INSERT INTO photo_embeddings(photo_id, vector) VALUES (?,?)",
            [(r["id"], v.tobytes()) for r, v in zip(chunk, vecs)],
        )
        con.commit()
        progress(f"embedded {min(i + CLIP_BATCH_SIZE, len(rows))}/{len(rows)}")
    return len(rows)


if __name__ == "__main__":
    run()
