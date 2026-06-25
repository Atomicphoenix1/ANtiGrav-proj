import os
import sys
import subprocess
import shutil
import sqlite3
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional

router = APIRouter(prefix="/api/admin", tags=["admin"])

from database import init_db

MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "media")
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "arabic_search.db")


@router.get("/assets")
async def get_inventory_assets():
    if not os.path.exists(MEDIA_DIR):
        return {"mp3s": [], "srts": []}
    files = os.listdir(MEDIA_DIR)
    return {
        "mp3s": [f for f in files if f.endswith(".mp3")],
        "srts": [f for f in files if f.endswith(".srt")],
    }


@router.post("/upload")
async def process_dual_ingestion_pipeline(
    mp3: UploadFile = File(...),
    srt: UploadFile = File(...),
    book_title: Optional[str] = Form(""),  # Changed from Form(...)
    sheikh_name: Optional[str] = Form(""), # Changed from Form(...)
    year_date: Optional[str] = Form(""),   # Changed from Form(...)
    youtube_url: Optional[str] = Form(None),
    overwrite: bool = Form(False)
):
    os.makedirs(MEDIA_DIR, exist_ok=True)
    mp3_target = os.path.join(MEDIA_DIR, mp3.filename or "audio.mp3")
    srt_target = os.path.join(MEDIA_DIR, srt.filename or "subs.srt")

    if (os.path.exists(mp3_target) or os.path.exists(srt_target)) and not overwrite:
        raise HTTPException(status_code=409, detail="File infrastructure configuration clash.")

    with open(mp3_target, "wb") as buffer:
        shutil.copyfileobj(mp3.file, buffer)
    with open(srt_target, "wb") as buffer:
        shutil.copyfileobj(srt.file, buffer)

    try:
        import_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "import_lecture.py")
        args = [sys.executable, import_script, mp3_target, srt_target, book_title or "", sheikh_name or "", year_date or ""]
        if youtube_url:
            args.append(youtube_url)
        result = subprocess.run(
            args,
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            detail = result.stderr.strip() or f"exit code {result.returncode}"
            raise HTTPException(status_code=500, detail=detail)
        return {"status": "SUCCESS", "detail": result.stderr.strip() or "Media file array correctly indexed."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/assets/{file_type}/{filename:path}")
async def delete_storage_asset(file_type: str, filename: str):
    if file_type not in ["mp3", "srt"]:
        raise HTTPException(status_code=400, detail="Invalid target classification type.")

    target_path = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(target_path):
        os.remove(target_path)
        return {"status": "DELETED"}
    raise HTTPException(status_code=404, detail="File asset reference lost.")


@router.post("/flush")
async def execute_nuclear_database_flush():
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail="Target tracking engine db missing.")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")

        conn.commit()
        conn.close()

        if os.path.exists(MEDIA_DIR):
            shutil.rmtree(MEDIA_DIR)
        os.makedirs(MEDIA_DIR, exist_ok=True)

        # Recreate all tables immediately so the next request never sees "no such table"
        init_db()

        return {"status": "CLEARED", "detail": "FTS5 structures, index caches, and media files atomized."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
