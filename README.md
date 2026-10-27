# Timelinephoto

Turns years of photos of one child into an aging timelapse video for a birthday. See [SPEC.md](SPEC.md).

## Quick start

1. In Google Photos, make a live album of your child; export only that album with Google Takeout.
2. Unzip the export into `data/takeout/`.
3. Run `docker compose up --build` (needs the NVIDIA Container Toolkit).
4. Open http://localhost:7860.

## Layout

| File | Job | Status |
| --- | --- | --- |
| `app/config.py` | paths and tunables | done |
| `app/db.py` | SQLite schema | done |
| `app/indexer.py` | find photos, read dates, downscale | done |
| `app/faces.py` | InsightFace detect + embed | stub |
| `app/matcher.py` | seed-based matching with re-seeding | stub |
| `app/select.py` | 2-month buckets, frame scoring | partly done |
| `app/align.py` | eye alignment | done |
| `app/render.py` | MP4 render (hard cut / crossfade) | done; RIFE is TODO |
| `app/ui.py` | Gradio UI | skeleton |
