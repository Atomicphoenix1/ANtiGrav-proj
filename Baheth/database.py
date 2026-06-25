import sqlite3
import os
from sqlalchemy import create_engine
from models import Base

DB_PATH = os.path.join(os.path.dirname(__file__), "arabic_search.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL, echo=False)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS lectures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text_content TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    audio_url TEXT DEFAULT NULL,
    start_time REAL DEFAULT NULL,
    end_time REAL DEFAULT NULL,
    book_title TEXT DEFAULT NULL,
    sheikh_name TEXT DEFAULT NULL,
    year_date TEXT DEFAULT NULL,
    youtube_url TEXT DEFAULT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS arabic_text_shards_fts USING fts5(
    normalized_text,
    book_title,
    sheikh_name
);

CREATE TRIGGER IF NOT EXISTS after_lectures_insert AFTER INSERT ON lectures BEGIN
    INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
    VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
END;

CREATE TRIGGER IF NOT EXISTS after_lectures_delete AFTER DELETE ON lectures BEGIN
    INSERT INTO arabic_text_shards_fts(arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name)
    VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
END;

CREATE TRIGGER IF NOT EXISTS after_lectures_update AFTER UPDATE ON lectures BEGIN
    INSERT INTO arabic_text_shards_fts(arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name)
    VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
    INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
    VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
END;
"""

MIGRATIONS = [
    "ALTER TABLE lectures ADD COLUMN normalized_text TEXT DEFAULT ''",
    "ALTER TABLE lectures ADD COLUMN audio_url TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN start_time REAL DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN end_time REAL DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN book_title TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN sheikh_name TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN year_date TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN youtube_url TEXT DEFAULT NULL",
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    # Recreate all ORM-mapped tables via SQLAlchemy
    Base.metadata.create_all(bind=engine)

    # Apply raw SQL for FTS5 virtual table and triggers (not supported by SQLAlchemy)
    conn = get_connection()
    try:
        # Migrate from legacy table name if needed
        old_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='arabic_text_shards'"
        ).fetchone()
        if old_exists:
            conn.execute("ALTER TABLE arabic_text_shards RENAME TO lectures")

        conn.executescript(SCHEMA_SQL)
        for migration in MIGRATIONS:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass

        # Backfill FTS index if data already exists in the source table
        count = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
        fts_count = conn.execute("SELECT COUNT(*) FROM arabic_text_shards_fts").fetchone()[0]
        if count > 0 and fts_count == 0:
            conn.execute("""
                INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
                SELECT id, normalized_text, book_title, sheikh_name FROM lectures
            """)

        conn.commit()
    finally:
        conn.close()
