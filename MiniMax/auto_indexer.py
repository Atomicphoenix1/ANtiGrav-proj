"""
auto_indexer.py
Auto-updates the daily-index.json for Mavis folder-index skill.
Run once or schedule with cron/scheduler.
"""

import json
import os
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────
ROOT_DIR   = Path(r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav")
INDEX_PATH = Path(r"C:\Users\saif_\.mavis\agents\mavis\workspace\daily-index.json")
# Only index these top-level subfolders (skip huge nested builds/node_modules etc.)
SKIP_NAMES = {".git", "node_modules", ".venv", ".python-version", "__pycache__",
              "assets", ".expo", ".claude"}
SKIP_PREFIXES = ("Unconfirmed", "Thumbs.db", ".DS_Store")
MAX_DEPTH = 20        # safety cap to avoid runaway scans
# ─────────────────────────────────────────────────────────────────────


def should_skip(path: Path) -> bool:
    name = path.name
    if name in SKIP_NAMES:
        return True
    if any(name.startswith(p) for p in SKIP_PREFIXES):
        return True
    # skip files > 2 GB (likely a corrupt installer or download)
    try:
        if path.stat().st_size > 2 * 1024**3:
            return True
    except OSError:
        pass
    return False


def scan(root: Path, depth: int = 0) -> list[dict]:
    entries = []
    if depth > MAX_DEPTH:
        return entries

    try:
        items = root.iterdir()
    except PermissionError:
        return entries

    for item in items:
        try:
            if item.is_file():
                if should_skip(item):
                    continue
                stat = item.stat()
                entries.append({
                    "Name": item.name,
                    "FullName": str(item.resolve()),
                    "Length": stat.st_size,
                    "LastWriteTime": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                })
            elif item.is_dir():
                if should_skip(item):
                    continue
                entries.extend(scan(item, depth + 1))
        except (PermissionError, OSError):
            continue

    return entries


def main() -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning {ROOT_DIR} ...")
    files = scan(ROOT_DIR)
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  [OK]  {len(files):,} files indexed -> {INDEX_PATH}")


if __name__ == "__main__":
    main()