"""Generic mode: seed photos -> automatic similarity matching with re-seeding."""
import numpy as np

from .config import SIM_MATCH_THRESHOLD, SIM_RESEED_THRESHOLD
from .db import connect


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return b @ a  # embeddings are L2-normalised


def run(seed_photo_ids: list[int], progress=print):
    con = connect()
    con.execute("UPDATE photo_embeddings SET is_seed=0, match_score=NULL")
    con.executemany(
        "UPDATE photo_embeddings SET is_seed=1, match_score=1.0 WHERE photo_id=?",
        [(pid,) for pid in seed_photo_ids],
    )
    con.commit()

    rows = con.execute(
        "SELECT e.photo_id, e.vector, e.is_seed, p.taken_at "
        "FROM photo_embeddings e JOIN photos p ON p.id = e.photo_id "
        "ORDER BY p.taken_at"
    ).fetchall()

    vectors = {r["photo_id"]: np.frombuffer(r["vector"], dtype=np.float32) for r in rows}
    seeds = {r["photo_id"] for r in rows if r["is_seed"]}

    changed = True
    while changed:
        changed = False
        seed_matrix = np.stack([vectors[pid] for pid in seeds])
        seed_ids = list(seeds)
        for r in rows:
            pid = r["photo_id"]
            if pid in seeds:
                continue
            sims = cosine(vectors[pid], seed_matrix)
            best = float(sims.max())
            if best >= SIM_MATCH_THRESHOLD:
                con.execute(
                    "UPDATE photo_embeddings SET match_score=? WHERE photo_id=?",
                    (best, pid),
                )
                if best >= SIM_RESEED_THRESHOLD:
                    seeds.add(pid)
                    changed = True
        con.commit()
        progress(f"{len(seeds)} seeds so far")

    matched = con.execute(
        "SELECT COUNT(*) FROM photo_embeddings WHERE match_score IS NOT NULL"
    ).fetchone()[0]
    return matched
