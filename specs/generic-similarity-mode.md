# Feature: Generic similarity mode

Status: in progress · first cut implementation

## What

Seed photos + CLIP similarity search over a local folder, no face detection.
Reuses the index/bucket/select/render/review pieces already built for the
kid pipeline; swaps face-embedding matching for whole-image CLIP matching
and skips eye alignment.

## Scope (this pass)

- `app/embed.py`: CLIP model load + whole-image embedding, cached in a new
  `photo_embeddings` table.
- `app/gmatcher.py`: seed -> nearest-seed walk over photo embeddings
  (same algorithm shape as `matcher.py`, no per-face loop, one embedding
  per photo instead of one per face).
- `app/gselect.py`: bucket matched photos by `taken_at`, pick best per
  bucket by sharpness only for now (no face quality, no background-sim
  yet — that's the Sunday-equivalent follow-up).
- `app/db.py`: add `photo_embeddings(photo_id PK, vector BLOB)` and
  `gchoices(bucket PK, photo_id, rejected TEXT, manual_path TEXT)` —
  separate from the face pipeline's `faces`/`choices` tables so neither
  mode has to fake rows for the other.
- `app/ui.py`: mode toggle (Face match / Similarity match), wired end to
  end for Similarity match: index -> seed gallery (whole photos, multi-select)
  -> match -> bucket grid -> render. Face match tab stays TODO as before.
- `app/config.py`: `SIM_MATCH_THRESHOLD`, `SIM_RESEED_THRESHOLD`,
  `CLIP_MODEL` name.

## Out of scope (this pass)

- Background-similarity scoring in `gselect` (face pipeline doesn't have
  it wired up yet either — do both together later).
- Center-crop to common aspect ratio for render (render takes frames
  as-is for now; sunset photos are already consistent landscape).
- Anything in the face/kid pipeline (`faces.py`, `matcher.py`, `select.py`,
  `align.py` untouched).

## Test data

`data/takeout/sunset/*.jpg` (already in repo) — point the indexer at it
via existing `TAKEOUT_DIR`, no Takeout-specific parsing needed since
there are no `.json` sidecars for this set (falls back to EXIF/file
date, already handled by `indexer.py`).

## GPU

Target: consumer 8–12GB card. CLIP ViT-B/32 easily fits; batch embedding
in chunks of ~64 photos.
