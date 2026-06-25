"""
generate_srt_directly_from_json.py — Pure JSON-to-SRT Linear Subtitle Generator

Chunks the raw word timeline from Timestamps.json into fixed-size phrase blocks,
strips Arabic diacritics, formats into standard sequential SRT, and auto-ingests
into the FTS5 database.

Usage:
    python generate_srt_directly_from_json.py [chunk_size]

The chunk_size argument (default 10) controls how many words per subtitle block.
"""

import json
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRT_DIR = os.path.join(SCRIPT_DIR, "SRT")
CHUNK_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 10

ARABIC_DIACRITICS = re.compile(r"[\u064B-\u0652]")
SRT_TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")


def strip_diacritics(text: str) -> str:
    return ARABIC_DIACRITICS.sub("", text).strip()


def secs_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    ms = max(0, min(ms, 999))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main() -> None:
    src = os.path.join(SRT_DIR, "03 الرسالة التبوكية لابن القيم_Timestamps.json")
    dst = os.path.join(SRT_DIR, "03_الرسالة_التبوكية_Direct_Clean.srt")
    audio = os.path.join(SRT_DIR, "03 الرسالة التبوكية لابن القيم.mp3")

    if not os.path.isfile(src):
        sys.stderr.write(f"ERROR: Timestamps file not found -> {os.path.basename(src)}\n")
        sys.exit(1)

    with open(src, encoding="utf-8") as f:
        words: list[list] = json.load(f)

    total = len(words)
    blocks: list[tuple[str, float, float]] = []

    for i in range(0, total, CHUNK_SIZE):
        chunk = words[i : i + CHUNK_SIZE]
        raw_text = " ".join(w[0] for w in chunk)
        clean_text = strip_diacritics(raw_text)
        start = chunk[0][1]
        end = chunk[-1][2]
        blocks.append((clean_text, start, end))

    with open(dst, "w", encoding="utf-8") as f:
        for idx, (text, start, end) in enumerate(blocks, 1):
            f.write(f"{idx}\n")
            f.write(f"{secs_to_srt(start)} --> {secs_to_srt(end)}\n")
            f.write(f"{text}\n\n")

    msg = (
        f"  Wrote {len(blocks)} blocks ({CHUNK_SIZE} words/block) "
        f"-> {os.path.basename(dst)}"
    )
    sys.stderr.write(msg + "\n")

    # ---- Database ingestion ----
    import_script = os.path.join(SCRIPT_DIR, "Baheth", "import_lecture.py")
    if not os.path.isfile(import_script):
        sys.stderr.write("  [SKIP] import_lecture.py not found\n")
        sys.exit(1)

    if not os.path.isfile(audio):
        sys.stderr.write(f"  [SKIP] Audio not found -> {os.path.basename(audio)}\n")
        sys.exit(1)

    result = os.system(
        f'python "{import_script}" "{audio}" "{dst}"'
    )
    if result == 0:
        sys.stderr.write("SUCCESS: Pristine direct SRT created and fully ingested.\n")
    else:
        sys.stderr.write(f"ERROR: ingestion failed (exit code {result})\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
