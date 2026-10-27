from pathlib import Path

TAKEOUT_DIR = Path("/data/takeout")
CACHE_DIR = Path("/data/cache")
THUMB_DIR = CACHE_DIR / "thumbs"
RENDER_DIR = CACHE_DIR / "renders"
DB_PATH = CACHE_DIR / "index.sqlite"

THUMB_LONG_EDGE = 1024          # analysis resolution
BUCKET_MONTHS = 2               # one frame per 2 months
MATCH_THRESHOLD = 0.45          # cosine similarity to nearest seed (tune!)
RESEED_THRESHOLD = 0.60         # matches above this become new seeds
OUTPUT_SIZE = 1080              # square output, px
EYE_Y = 0.40                    # eyes at 40% from top
EYE_DISTANCE = 0.22             # eye distance as fraction of width
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".heic", ".webp"}

for d in (CACHE_DIR, THUMB_DIR, RENDER_DIR):
    d.mkdir(parents=True, exist_ok=True)
