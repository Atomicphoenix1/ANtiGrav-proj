"""
run_aeneas_alignment.py — Automated Arabic Media Realignment via Aeneas Engine

Extracts plain text from a broken SRT, runs aeneas forced alignment,
then imports the clean SRT into the FTS5 database.

Usage:
    python run_aeneas_alignment.py [audio.mp3] [input.srt] [output.srt]

Defaults (all relative to the SRT/ directory beside this script):
    audio:  03 الرسالة التبوكية لابن القيم.mp3
    input:  03 الرسالة التبوكية لابن القيم_Total.srt
    output: 03_الرسالة_التبوكية_Pris_Clean.srt
"""

import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SRT_DIR = os.path.join(SCRIPT_DIR, "SRT")


# ---------------------------------------------------------------------------
# Step 1 — Extract plain text stream from the broken SRT
# ---------------------------------------------------------------------------

def extract_text_from_srt(srt_path: str, output_path: str) -> list[str]:
    """Strip index/timestamp lines; write one phrase per line."""
    with open(srt_path, encoding="utf-8-sig") as f:
        raw = f.read()

    blocks = re.split(r"\n\n+", raw.strip())
    phrases: list[str] = []
    for block in blocks:
        parts = block.strip().split("\n")
        if len(parts) >= 3:
            text = " ".join(parts[2:]).strip()
            if text:
                phrases.append(text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(phrases) + "\n")

    print(f"[1/3] Extracted {len(phrases)} phrases -> {output_path}")
    return phrases


# ---------------------------------------------------------------------------
# Step 2 — Install aeneas and run forced alignment
# ---------------------------------------------------------------------------

def _ensure_aeneas() -> bool:
    try:
        import aeneas  # noqa: F401
        return True
    except ImportError:
        print("aeneas not found. Installing...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", "aeneas"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            import aeneas  # noqa: F401
            return True
        except Exception:
            print("ERROR: pip install aeneas failed.")
            print("On Windows, aeneas requires espeak + ffmpeg.")
            print("  winget install espeak ffmpeg")
            print("  pip install aeneas")
            return False


def run_alignment(audio_path: str, text_path: str, output_srt: str) -> None:
    from aeneas.executetask import ExecuteTask
    from aeneas.task import Task

    config_string = (
        "task_language=ara|"
        "is_text_type=plain|"
        "os_task_file_format=srt"
    )

    task = Task(config_string=config_string)
    task.audio_file_path_absolute = os.path.abspath(audio_path)
    task.text_file_path_absolute = os.path.abspath(text_path)
    task.sync_map_file_path_absolute = os.path.abspath(output_srt)

    ExecuteTask(task).execute()
    print(f"[2/3] Aeneas wrote aligned SRT -> {output_srt}")


# ---------------------------------------------------------------------------
# Step 3 — Import clean SRT into FTS5 database
# ---------------------------------------------------------------------------

def run_import(audio_path: str, srt_path: str) -> bool:
    import_script = os.path.join(SCRIPT_DIR, "Baheth", "import_lecture.py")
    if not os.path.isfile(import_script):
        print(f"[3/3] SKIP — import_lecture.py not found at {import_script}")
        return False

    result = subprocess.run(
        [sys.executable, import_script, os.path.abspath(audio_path), os.path.abspath(srt_path)],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode == 0


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------

def main() -> None:
    base = SRT_DIR

    audio_path = os.path.abspath(
        sys.argv[1] if len(sys.argv) > 1 else
        os.path.join(base, "03 الرسالة التبوكية لابن القيم.mp3")
    )
    input_srt = os.path.abspath(
        sys.argv[2] if len(sys.argv) > 2 else
        os.path.join(base, "03 الرسالة التبوكية لابن القيم_Total.srt")
    )
    output_srt = os.path.abspath(
        sys.argv[3] if len(sys.argv) > 3 else
        os.path.join(base, "03_الرسالة_التبوكية_Pris_Clean.srt")
    )
    text_path = os.path.join(base, "lecture_text.txt")

    # Validate inputs
    for path, label in [(audio_path, "Audio"), (input_srt, "Input SRT")]:
        if not os.path.isfile(path):
            print(f"ERROR: {label} not found -> {path}")
            sys.exit(1)

    os.makedirs(base, exist_ok=True)

    # Pipeline
    extract_text_from_srt(input_srt, text_path)

    if not _ensure_aeneas():
        sys.exit(1)

    run_alignment(audio_path, text_path, output_srt)

    run_import(audio_path, output_srt)

    print("\n=== Pipeline complete ===")
    print(f"  Text dump : {text_path}")
    print(f"  Clean SRT : {output_srt}")


if __name__ == "__main__":
    main()
