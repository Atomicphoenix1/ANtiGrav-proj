"""
import_lecture.py — Parse an SRT file + MP3 path and bulk-insert into the
Arabic search FTS5 database.

Usage:
    python import_lecture.py <audio.mp3> <subtitles.srt> [book_title] [sheikh_name] [year_date]

Each SRT block becomes one row in lectures with its time bounds,
the MP3 file path, and metadata tags.  Text is normalized for FTS5 via normalizer.normalize().
"""

import sqlite3
import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from normalizer import normalize

SRT_TIMESTAMP = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)
SRT_BLOCK = re.compile(
    r"(?P<index>\d+)\s*\n"
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
    r"(?P<text>.+?)(?:\n\n|\Z)",
    re.DOTALL,
)


def _ts_to_seconds(ts: str) -> float:
    m = SRT_TIMESTAMP.fullmatch(ts.strip())
    if not m:
        raise ValueError(f"Invalid SRT timestamp: {ts!r}")
    h, mi, s, ms = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return h * 3600 + mi * 60 + s + ms / 1000


def parse_srt(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()

    blocks = []
    for match in SRT_BLOCK.finditer(raw):
        blocks.append(
            {
                "index": int(match["index"]),
                "start": _ts_to_seconds(match["start"]),
                "end": _ts_to_seconds(match["end"]),
                "text": match["text"].strip().replace("\n", " "),
            }
        )
    return blocks


def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python import_lecture.py <audio.mp3> <subtitles.srt> [book_title] [sheikh_name] [year_date] [youtube_url]\n")
        sys.exit(1)

    audio_path = os.path.abspath(sys.argv[1])
    srt_path = os.path.abspath(sys.argv[2])
    book_title = sys.argv[3] if len(sys.argv) > 3 else ""
    sheikh_name = sys.argv[4] if len(sys.argv) > 4 else ""
    year_date = sys.argv[5] if len(sys.argv) > 5 else ""
    youtube_url = sys.argv[6] if len(sys.argv) > 6 else None

    if not os.path.isfile(audio_path):
        msg = f"ERROR: audio file not found — {os.path.basename(audio_path)}"
        sys.stderr.write(msg + "\n")
        sys.exit(1)
    if not os.path.isfile(srt_path):
        msg = f"ERROR: SRT file not found — {os.path.basename(srt_path)}"
        sys.stderr.write(msg + "\n")
        sys.exit(1)

    blocks = parse_srt(srt_path)
    if not blocks:
        sys.stderr.write("ERROR: no SRT blocks parsed\n")
        sys.exit(1)

    db_path = os.path.join(os.path.dirname(__file__), "arabic_search.db")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")

    # Store only the filename; the file is served from the /media/ mount
    audio_filename = os.path.basename(audio_path)

    rows = []
    for b in blocks:
        rows.append(
            (
                b["text"],
                normalize(b["text"]),
                audio_filename,
                b["start"],
                b["end"],
                book_title,
                sheikh_name,
                year_date,
                youtube_url,
            )
        )

    conn.execute("BEGIN TRANSACTION")
    conn.executemany(
        """INSERT INTO lectures
           (text_content, normalized_text, audio_url, start_time, end_time,
            book_title, sheikh_name, year_date, youtube_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    conn.close()

    msg = (
        f"  Import: {len(rows)} blocks from {os.path.basename(audio_path)} ["
        f"{blocks[0]['start']:.2f}s -> {blocks[-1]['end']:.2f}s]"
        + (f" | {book_title}" if book_title else "")
    )
    sys.stderr.write(msg + "\n")


if __name__ == "__main__":
    main()
