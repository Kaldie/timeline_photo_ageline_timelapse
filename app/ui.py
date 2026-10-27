"""Gradio UI skeleton: index -> seed -> match -> review -> render."""
import json

import cv2
import gradio as gr

from . import indexer, embed, gmatcher, gselect
from .db import connect
from .render import render


def do_index():
    n = indexer.run()
    return f"Indexed {n} files."


def do_embed():
    n = embed.run()
    return f"Embedded {n} new photos."


def load_gallery():
    con = connect()
    rows = con.execute("SELECT id, thumb FROM photos ORDER BY taken_at").fetchall()
    return [(r["thumb"], str(r["id"])) for r in rows]


def toggle_seed(seeds: list[int], evt: gr.SelectData):
    pid = int(evt.value["caption"]) if isinstance(evt.value, dict) else int(evt.value[1])
    seeds = list(seeds)
    if pid in seeds:
        seeds.remove(pid)
    else:
        seeds.append(pid)
    return seeds, f"Seeds: {seeds}"


def do_match(seeds: list[int]):
    if not seeds:
        return "Pick at least one seed photo first."
    n = gmatcher.run(seeds)
    return f"{n} photos matched."


def do_bucket():
    n = gselect.run()
    return f"{n} buckets filled (some may be empty — see review tab)."


def load_buckets():
    con = connect()
    rows = con.execute(
        "SELECT g.bucket, g.photo_id, g.manual_path, p.thumb "
        "FROM gchoices g LEFT JOIN photos p ON p.id = g.photo_id "
        "ORDER BY g.bucket"
    ).fetchall()
    gallery = [
        (r["manual_path"] or r["thumb"] or "", f"{r['bucket']}"
         + ("" if (r["photo_id"] or r["manual_path"]) else " (empty)"))
        for r in rows
    ]
    missing = [r["bucket"] for r in rows if not r["photo_id"] and not r["manual_path"]]
    return gallery, ("Missing: " + ", ".join(missing) if missing else "All buckets filled.")


def reject_bucket(bucket: str):
    con = connect()
    row = con.execute("SELECT photo_id, rejected FROM gchoices WHERE bucket=?", (bucket,)).fetchone()
    if not row or not row["photo_id"]:
        return "Nothing to reject in that bucket."
    rejected = json.loads(row["rejected"])
    rejected.append(row["photo_id"])
    con.execute("UPDATE gchoices SET rejected=? WHERE bucket=?", (json.dumps(rejected), bucket))
    con.commit()
    gselect.run()
    return f"Rejected, refilled bucket {bucket}."


def add_manual_photo(bucket: str, path: str):
    con = connect()
    con.execute(
        "INSERT INTO gchoices(bucket, manual_path) VALUES (?,?) "
        "ON CONFLICT(bucket) DO UPDATE SET manual_path=excluded.manual_path",
        (bucket, path),
    )
    con.commit()
    return f"Added {path} to {bucket}."


def do_render(smoothness: float):
    con = connect()
    rows = con.execute(
        "SELECT g.manual_path, p.path FROM gchoices g "
        "LEFT JOIN photos p ON p.id = g.photo_id "
        "ORDER BY g.bucket"
    ).fetchall()
    frames = []
    for r in rows:
        src = r["manual_path"] or r["path"]
        if not src:
            continue
        img = cv2.imread(src)
        if img is not None:
            frames.append(img)
    if not frames:
        return None, "No frames to render yet — run match + bucket first."
    out = render(frames, smoothness=smoothness)
    return str(out), f"Rendered {len(frames)} frames."


with gr.Blocks(title="Timelinephoto") as demo:
    gr.Markdown("# Timelinephoto")
    mode = gr.Radio(["Similarity match", "Face match"], value="Similarity match", label="Mode")

    with gr.Tab("1. Index"):
        gr.Markdown("Point `/data/takeout` at a folder of photos (face mode) "
                    "or a local folder of example photos (similarity mode).")
        btn = gr.Button("Scan folder")
        status = gr.Textbox(label="Status")
        btn.click(do_index, outputs=status)

    with gr.Tab("2. Seed (Similarity match)"):
        gr.Markdown("Click 3-5 photos that show what you want (sunsets, a pet, "
                    "a place, ...). Click again to unselect.")
        embed_btn = gr.Button("Embed all photos (CLIP)")
        embed_status = gr.Textbox(label="Status")
        embed_btn.click(do_embed, outputs=embed_status)

        seed_state = gr.State([])
        gallery = gr.Gallery(label="All photos", columns=6, height=400)
        refresh_btn = gr.Button("Refresh gallery")
        refresh_btn.click(load_gallery, outputs=gallery)
        seed_status = gr.Textbox(label="Selected seeds")
        gallery.select(toggle_seed, inputs=seed_state, outputs=[seed_state, seed_status])

        match_btn = gr.Button("Match")
        match_status = gr.Textbox(label="Match status")
        match_btn.click(do_match, inputs=seed_state, outputs=match_status)

    with gr.Tab("2. Seed (Face match)"):
        gr.Markdown("TODO: gallery of faces; pick 3-5 of your child.")

    with gr.Tab("3. Review & render"):
        bucket_btn = gr.Button("Bucket + pick best frame per slot")
        bucket_status = gr.Textbox(label="Status")
        bucket_gallery = gr.Gallery(label="One frame per bucket", columns=6, height=400)
        bucket_btn.click(do_bucket, outputs=bucket_status).then(
            load_buckets, outputs=[bucket_gallery, bucket_status]
        )

        with gr.Row():
            reject_bucket_box = gr.Textbox(label="Bucket to reject (e.g. 2019-03)")
            reject_btn = gr.Button("Throw out current frame")
        reject_btn.click(reject_bucket, inputs=reject_bucket_box, outputs=bucket_status).then(
            load_buckets, outputs=[bucket_gallery, bucket_status]
        )

        with gr.Row():
            manual_bucket_box = gr.Textbox(label="Bucket")
            manual_path_box = gr.Textbox(label="Full path to replacement photo")
            add_btn = gr.Button("Add photo to slot")
        add_btn.click(add_manual_photo, inputs=[manual_bucket_box, manual_path_box],
                      outputs=bucket_status).then(
            load_buckets, outputs=[bucket_gallery, bucket_status]
        )

        smooth = gr.Slider(0, 1, value=0, step=0.05,
                           label="Smoothness (cut -> crossfade -> interpolate)")
        render_btn = gr.Button("Render")
        video_out = gr.Video(label="Result")
        render_status = gr.Textbox(label="Render status")
        render_btn.click(do_render, inputs=smooth, outputs=[video_out, render_status])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
