"""Stage 1 seeds -> stage 2 automatic matching with re-seeding (Saturday task)."""
import numpy as np


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return b @ a  # embeddings are L2-normalised


def run(seed_face_ids: list[int]):
    """TODO:
    1. mark seed faces (is_seed=1)
    2. sort all faces by photo taken_at
    3. walk outward in time from each seed; score each face against the seeds
       nearest in time (MATCH_THRESHOLD); faces above RESEED_THRESHOLD become seeds
    4. keep at most one matched face per photo (highest score) -> match_score
    """
    raise NotImplementedError
