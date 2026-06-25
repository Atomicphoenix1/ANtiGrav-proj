"""
build_srt_from_json.py — Time-based SRT Reconstruction from JSON + original SRT

Uses the original SRT's time ranges to anchor each subtitle block and overlays
the JSON word-level timestamps for precise, gap-free timing.

Usage:
    python build_srt_from_json.py [timestamps.json] [orig_subtitles.srt] [output.srt]

All paths default to files inside SRT/ alongside this script.
"""

import json
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRT_DIR = os.path.join(SCRIPT_DIR, "SRT")

# ---------------------------------------------------------------------------
# Time conversion helpers
# ---------------------------------------------------------------------------

def secs_to_srt(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    ms = max(0, min(ms, 999))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ---------------------------------------------------------------------------
# Core alignment
# ---------------------------------------------------------------------------

SRT_BLOCK = re.compile(
    r"(\d+)\s*\n"
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
    r"(.*?)(?:\n\n|\Z)",
    re.DOTALL,
)
SRT_TS = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")

def _ts(s: str) -> float:
    m = SRT_TS.fullmatch(s.strip())
    if not m:
        return 0.0
    return int(m[1])*3600 + int(m[2])*60 + int(m[3]) + int(m[4])/1000

def parse_orig_srt(path: str) -> list[tuple[str, float, float]]:
    with open(path, encoding="utf-8-sig") as f:
        raw = f.read()
    out = []
    for m in SRT_BLOCK.finditer(raw):
        text = m.group(4).strip().replace("\n", " ")
        start = _ts(m.group(2))
        end = _ts(m.group(3))
        out.append((text, start, end))
    return out

def build_srt(json_path: str, orig_srt_path: str) -> list[tuple[str, float, float]]:
    with open(json_path, encoding="utf-8") as f:
        word_entries: list[list] = json.load(f)

    blocks_raw = parse_orig_srt(orig_srt_path)

    out: list[tuple[str, float, float]] = []
    ji = 0
    TOLERANCE_END = 0.15  # seconds — allow JSON words slightly past SRT end to be included

    for text, block_start, block_end in blocks_raw:
        if ji >= len(word_entries):
            break

        # Find first unconsumed JSON word within the block's time range
        start_idx = None
        for idx in range(ji, len(word_entries)):
            tw = word_entries[idx]
            if tw[2] < block_start:
                continue  # JSON word ends before block starts, skip it
            if tw[1] > block_end:
                break  # JSON word starts after block ends, stop searching
            start_idx = idx
            break

        if start_idx is None:
            continue  # no JSON words in this block's range

        # Consume JSON words from start_idx while still in range
        end_idx = start_idx
        for idx in range(start_idx, len(word_entries)):
            tw = word_entries[idx]
            if tw[1] > block_end + TOLERANCE_END:
                break
            end_idx = idx

        # Update cursor — skip to one past end_idx
        ji = end_idx + 1

        new_start = word_entries[start_idx][1]
        new_end = word_entries[end_idx][2]

        if out and new_start < out[-1][2]:
            new_start = out[-1][2]

        out.append((text, new_start, new_end))

    remaining = len(word_entries) - ji
    if remaining:
        msg = f"  [WARN] {remaining}/{len(word_entries)} unconsumed (stopped at {ji})"
        sys.stderr.write(msg + "\n")

    return out


# ---------------------------------------------------------------------------
# Write SRT
# ---------------------------------------------------------------------------

def write_srt(blocks: list[tuple[str, float, float]], output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for i, (text, start, end) in enumerate(blocks, 1):
            f.write(f"{i}\n")
            f.write(f"{secs_to_srt(start)} --> {secs_to_srt(end)}\n")
            f.write(f"{text}\n\n")
    msg = f"  Wrote {len(blocks)} subtitle blocks -> {os.path.basename(output_path)}"
    sys.stderr.write(msg + "\n")


# ---------------------------------------------------------------------------
# Database ingestion
# ---------------------------------------------------------------------------

def run_import(audio_path: str, srt_path: str) -> bool:
    import_script = os.path.join(SCRIPT_DIR, "Baheth", "import_lecture.py")
    if not os.path.isfile(import_script):
        print(f"  [SKIP] import_lecture.py not found at {import_script}")
        return False

    result = subprocess.run(
        [sys.executable, import_script,
         os.path.abspath(audio_path), os.path.abspath(srt_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        sys.stderr.write(result.stdout + "\n")
    return result.returncode == 0


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    base = SRT_DIR

    json_path = os.path.abspath(
        sys.argv[1] if len(sys.argv) > 1 else
        os.path.join(base, "03 الرسالة التبوكية لابن القيم_Timestamps.json")
    )
    orig_srt_path = os.path.abspath(
        sys.argv[2] if len(sys.argv) > 2 else
        os.path.join(base, "03 الرسالة التبوكية لابن القيم_Total.srt")
    )
    output_srt = os.path.abspath(
        sys.argv[3] if len(sys.argv) > 3 else
        os.path.join(base, "03_الرسالة_التبوكية_Pris_Clean.srt")
    )
    audio_path = os.path.join(base, "03 الرسالة التبوكية لابن القيم.mp3")

    for path, label in [(json_path, "JSON timestamps"),
                        (orig_srt_path, "Original SRT")]:
        if not os.path.isfile(path):
            msg = f"ERROR: {label} not found -> {os.path.basename(path)}"
            sys.stderr.write(msg + "\n")
            sys.exit(1)

    sys.stderr.write("=== SRT Reconstruction via Time Overlay ===\n\n")

    blocks = build_srt(json_path, orig_srt_path)

    if not blocks:
        sys.stderr.write("ERROR: no blocks produced\n")
        sys.exit(1)

    write_srt(blocks, output_srt)

    if os.path.isfile(audio_path):
        sys.stderr.write("\n--- Database ingestion ---\n")
        run_import(audio_path, output_srt)
    else:
        sys.stderr.write(f"\n  [SKIP] Audio not found at {os.path.basename(audio_path)}\n")

    sys.stderr.write(f"\n  Done.  {len(blocks)} sentences -> {os.path.basename(output_srt)}\n")


if __name__ == "__main__":
    main()
