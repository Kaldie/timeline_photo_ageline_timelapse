import sqlite3
from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS photos (
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE NOT NULL,
  thumb TEXT,
  taken_at REAL,          -- unix seconds
  width INTEGER, height INTEGER
);
CREATE TABLE IF NOT EXISTS faces (
  id INTEGER PRIMARY KEY,
  photo_id INTEGER REFERENCES photos(id),
  bbox TEXT,              -- json [x1,y1,x2,y2] in thumb coords
  landmarks TEXT,         -- json 5-point kps in thumb coords
  det_score REAL,
  embedding BLOB,         -- float32[512]
  is_seed INTEGER DEFAULT 0,
  match_score REAL
);
CREATE TABLE IF NOT EXISTS choices (     -- survives re-renders
  bucket TEXT PRIMARY KEY,               -- e.g. '2019-03'
  face_id INTEGER,                       -- chosen face, NULL = empty slot
  rejected TEXT DEFAULT '[]',            -- json list of rejected face ids
  manual_path TEXT                       -- user-added photo
);
CREATE TABLE IF NOT EXISTS photo_embeddings (  -- generic (similarity) mode
  photo_id INTEGER PRIMARY KEY REFERENCES photos(id),
  vector BLOB,             -- float32[512] CLIP embedding, whole image
  is_seed INTEGER DEFAULT 0,
  match_score REAL
);
CREATE TABLE IF NOT EXISTS gchoices (     -- generic mode's choices, survives re-renders
  bucket TEXT PRIMARY KEY,
  photo_id INTEGER,                      -- chosen photo, NULL = empty slot
  rejected TEXT DEFAULT '[]',            -- json list of rejected photo ids
  manual_path TEXT                       -- user-added photo
);
"""

def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con
