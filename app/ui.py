"""Gradio UI skeleton: index -> seed -> match -> review -> render."""
import gradio as gr

from . import indexer


def do_index():
    n = indexer.run()
    return f"Indexed {n} files."


with gr.Blocks(title="Timelinephoto") as demo:
    gr.Markdown("# Timelinephoto")
    with gr.Tab("1. Index"):
        btn = gr.Button("Scan Takeout folder")
        status = gr.Textbox(label="Status")
        btn.click(do_index, outputs=status)
    with gr.Tab("2. Seed"):
        gr.Markdown("TODO: gallery of faces; pick 3-5 of your child.")
    with gr.Tab("3. Review & render"):
        gr.Markdown("TODO: frame grid per bucket, missing slots, reject / add photo.")
        smooth = gr.Slider(0, 1, value=0, step=0.05, label="Smoothness (cut -> crossfade -> interpolate)")
        gr.Button("Render")

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
