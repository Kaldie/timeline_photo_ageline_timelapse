# Timelinephoto v1 Spec

Oct 27, 2026 · @Ruud

## Overview

Timelinephoto finds one child across years of a family photo library and turns those photos into an aging timelapse video for a birthday.

- **User:** parents making a birthday video.
- **Input:** the family's Google Photos library.
- **Output:** an MP4 showing the child growing up, roughly one frame per 2 months, ideally against a similar background.
- **v1 scope:** a weekend prototype running in a Docker container on the user's own GPU machine. Video only; GIF and editing extras come later.

## Ingest

Photos come in through a Google Takeout export of one live album, because the Google Photos API can no longer read a whole library.

Since March 31, 2025 the Library API's read-only scope is gone; apps can only see photos the user picks by hand in the Picker API ([Google](https://developers.google.com/photos/support/updates)). Takeout also has no lower-quality option, so we shrink what is exported rather than its resolution.

1. In Google Photos, create a **live album** that auto-adds the child's face group.
2. Export only that album with **Google Takeout** and unzip it into a folder mounted into the container (`/data/takeout`).
3. Index every photo: path, capture time (Takeout JSON sidecar first, then EXIF, then file date), dimensions.
4. Make a **downscaled copy** (about 1024 px long edge) for all analysis. Full-resolution originals are only touched when rendering selected frames.

Fallback if the live album is incomplete: Takeout's per-year folders, processed one year at a time.

## Pipeline

A two-stage match (user seeds, then automatic) feeds a per-bucket frame picker, eye alignment and a GPU render.

1. **Seed.** The user picks 3–5 photos of the child, ideally at different ages, and clicks the right face in each.
2. **Match.** Detect and embed every face on the downscaled copies. Walk through time from the seeds outward, keeping faces close to the nearest seeds and adding confident matches as new seeds, so the model follows the child as they age.
3. **Bucket.** Split the matched photos into 2-month buckets across the full date range.
4. **Select.** Pick one frame per bucket by combined score:
   - face quality: sharpness, frontal pose, eyes open, face size
   - background similarity to the neighbouring frames (scene embedding of the image with the person masked out)
5. **Align.** Use face landmarks to rotate, scale and crop each full-resolution frame so the eyes land in the same spot.
6. **Render.** Output MP4 with a **smoothness slider**: hard cut → crossfade → full frame interpolation between photos. Frame duration and an optional date stamp are adjustable.

## Review loop

After the first render the user fixes the result frame by frame and re-renders, instead of tuning the matcher.

- **Missing slots:** buckets with no usable photo are left empty, and the UI lists them ("no photo for Mar–Apr 2019").
- **Throw out:** the user rejects a frame (wrong kid, bad shot); the slot refills with the next-best candidate from that bucket, or goes empty.
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
- [ ] Face detection + embeddings for the whole album, cached
- [ ] Seed picker + matching with re-seeding
- [ ] 2-month buckets, best frame per bucket, eye alignment
- [ ] First render: hard cuts to MP4

**Sunday**

- [ ] Background similarity in the frame score
- [ ] Smoothness slider: crossfade, then RIFE interpolation
- [ ] Frame grid: missing-slot list, throw out, add photos, re-render

**Out of scope for v1:** GIF export, music and titles, multiple children per run, Picker API or direct Google login, cloud hosting.
