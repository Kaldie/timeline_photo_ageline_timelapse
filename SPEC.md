# Timelinephoto v1 Spec

Oct 27, 2026 · @Ruud

## Overview

Timelinephoto finds one child across years of a family photo library and turns those photos into an aging timelapse video for a birthday.

- **User:** parents making a birthday video.
- **Input:** the family's Google Photos library.
- **Output:** an MP4 showing the child growing up, roughly one frame per 2 months, ideally against a similar background.
- **v1 scope:** a weekend prototype running in a Docker container on the user's own GPU machine. Video only; GIF and editing extras come later.

## Ingest

Photos come in through a broad Google Takeout export, because the Google Photos API can no longer read a whole library and Google's own People face-grouping is unreliable with two kids (mixes them up, especially as babies).

Since March 31, 2025 the Library API's read-only scope is gone; apps can only see photos the user picks by hand in the Picker API ([Google](https://developers.google.com/photos/support/updates)). Takeout also has no lower-quality option, so we shrink what is exported rather than its resolution.

1. Export a **broad slice** with Google Takeout — not a hand-curated live album, just everything likely to contain the kids (whole library, or per-year folders if that's too big) — and unzip it into a folder mounted into the container (`/data/takeout`).
2. Index every photo: path, capture time (Takeout JSON sidecar first, then EXIF, then file date), dimensions.
3. Make a **downscaled copy** (about 1024 px long edge) for all analysis. Full-resolution originals are only touched when rendering selected frames.

We don't rely on Google to pre-filter by child at all; that's what the clustering + seed step below is for. Fallback if a full export is too large: Takeout's per-year folders, processed one year at a time.

## Pipeline

Cluster first, then let the user pick which cluster is which kid, instead of trying to match a single child's face directly against the whole broad export — this is the part Google's People view gets wrong with two kids.

1. **Detect + embed.** Run face detection and embeddings on every face in the broad export's downscaled copies.
2. **Cluster.** Group faces by embedding similarity (background being roughly consistent across the family's photos helps separate real clusters from noise). Expect clusters to be messy, split across ages, and to include adults and false positives — that's fine.
3. **Seed-select clusters.** The user picks 3–5 photos of the child, ideally at different ages, and clicks the right face in each, same as before — but now those seeds are used to pick which cluster(s) belong to that kid, and to pull in matches the clustering missed or split off (e.g. baby photos that clustered separately from toddler photos of the same kid).
4. **Match.** Walk through time from the seeds outward, keeping faces close to the nearest seeds/cluster and adding confident matches as new seeds, so the model follows the child as they age and across the two-kid split.
5. **Bucket.** Split the matched photos into 2-month buckets across the full date range.
6. **Select.** Pick one frame per bucket by combined score:
   - face quality: sharpness, frontal pose, eyes open, face size
   - background similarity to the neighbouring frames (scene embedding of the image with the person masked out)
7. **Align.** Use face landmarks to rotate, scale and crop each full-resolution frame so the eyes land in the same spot.
8. **Render.** Output MP4 with a **smoothness slider**: hard cut → crossfade → full frame interpolation between photos. Frame duration and an optional date stamp are adjustable.

## Review loop

After the first render the user fixes the result frame by frame and re-renders, instead of tuning the matcher.

- **Missing slots:** buckets with no usable photo are left empty, and the UI lists them ("no photo for Mar–Apr 2019").
- **Throw out:** the user rejects a frame (wrong kid — e.g. sibling bled in from a bad cluster match — or just a bad shot); the slot refills with the next-best candidate from that bucket, or goes empty.
- **Add photos:** the user can drop extra photos into any slot, including empty ones; they get aligned like the rest.
- **Re-render:** one button rebuilds the video with the current frames and slider setting. Rejections and additions are saved, so they survive re-renders.

## Tech stack

One Python Docker image with GPU access, a local SQLite index and a Gradio web UI.

| Part | Choice |
| --- | --- |
| Container | Docker with NVIDIA runtime (`--gpus all`), CUDA base image |
| Face detection + embeddings | InsightFace (detector, landmarks, ArcFace embeddings) |
| Background similarity | CLIP image embeddings on the person-masked frame |
| Frame interpolation | RIFE |
| Video encoding | ffmpeg |
| Storage | SQLite for the index, scores and user choices; volumes for `/data/takeout` and `/data/cache` |
| UI | Gradio: seed picker, frame grid, slider, render button |

Open question: which GPU and how much VRAM? That decides batch sizes and how fast interpolation renders.

## First features: weekend build order

The first milestone is an ugly but real video by Saturday night; smoothness and the review loop come Sunday.

**Saturday**

- [ ] Docker image with GPU working, Takeout folder mounted
- [ ] Indexer: dates from sidecars/EXIF, downscaled copies
- [ ] Face detection + embeddings for the whole export, cached
- [ ] Clustering + seed picker to select/merge clusters per kid, matching with re-seeding
- [ ] 2-month buckets, best frame per bucket, eye alignment
- [ ] First render: hard cuts to MP4

**Sunday**

- [ ] Background similarity in the frame score
- [ ] Smoothness slider: crossfade, then RIFE interpolation
- [ ] Frame grid: missing-slot list, throw out, add photos, re-render

**Out of scope for v1:** GIF export, music and titles, multiple children per run, Picker API or direct Google login, cloud hosting.
