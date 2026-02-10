import sqlite3

from rewind.config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    uuid TEXT PRIMARY KEY,
    creation_date TEXT NOT NULL,
    modified_date TEXT,
    timezone TEXT,
    text TEXT,
    snippet TEXT,
    starred INTEGER DEFAULT 0,
    latitude REAL,
    longitude REAL,
    place_name TEXT,
    locality TEXT,
    admin_area TEXT,
    country TEXT,
    weather_description TEXT,
    weather_temp_c REAL,
    duration INTEGER,
    word_count INTEGER
);

CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    uuid UNINDEXED,
    text,
    snippet,
    place_name,
    locality,
    country,
    content='entries',
    content_rowid='rowid',
    tokenize='porter'
);

CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(uuid, text, snippet, place_name, locality, country)
    VALUES (new.uuid, new.text, new.snippet, new.place_name, new.locality, new.country);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, uuid, text, snippet, place_name, locality, country)
    VALUES ('delete', old.uuid, old.text, old.snippet, old.place_name, old.locality, old.country);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, uuid, text, snippet, place_name, locality, country)
    VALUES ('delete', old.uuid, old.text, old.snippet, old.place_name, old.locality, old.country);
    INSERT INTO entries_fts(uuid, text, snippet, place_name, locality, country)
    VALUES (new.uuid, new.text, new.snippet, new.place_name, new.locality, new.country);
END;

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    tag_type TEXT DEFAULT 'topic',
    ai_suggested_type TEXT,
    user_confirmed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS entry_tags (
    entry_uuid TEXT NOT NULL REFERENCES entries(uuid),
    tag_id INTEGER NOT NULL REFERENCES tags(id),
    PRIMARY KEY (entry_uuid, tag_id)
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_uuid TEXT NOT NULL REFERENCES entries(uuid),
    identifier TEXT NOT NULL,
    md5 TEXT,
    file_type TEXT,
    width INTEGER,
    height INTEGER,
    has_thumbnail INTEGER DEFAULT 0,
    UNIQUE(entry_uuid, identifier)
);

CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    weight INTEGER DEFAULT 1,
    first_date TEXT,
    last_date TEXT,
    UNIQUE(source_type, source_id, target_type, target_id)
);

CREATE TABLE IF NOT EXISTS graph_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_type TEXT NOT NULL,
    node_id TEXT NOT NULL,
    label TEXT NOT NULL,
    entry_count INTEGER DEFAULT 0,
    first_date TEXT,
    last_date TEXT,
    UNIQUE(node_type, node_id)
);

CREATE TABLE IF NOT EXISTS import_meta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    imported_at TEXT NOT NULL,
    entry_count INTEGER,
    tag_count INTEGER,
    photo_count INTEGER,
    filename TEXT,
    duration_seconds REAL
);

CREATE INDEX IF NOT EXISTS idx_entries_creation ON entries(creation_date);
CREATE INDEX IF NOT EXISTS idx_entries_place ON entries(place_name);
CREATE INDEX IF NOT EXISTS idx_entry_tags_entry ON entry_tags(entry_uuid);
CREATE INDEX IF NOT EXISTS idx_entry_tags_tag ON entry_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_photos_entry ON photos(entry_uuid);
"""


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(settings.DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=wal")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_db()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
