import re
from urllib.parse import quote
from fastapi import FastAPI, Query
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware


class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        return response

from database import init_db, get_connection
from normalizer import normalize
from models import IndexShardsRequest, IndexShardsResponse, SearchResult, SearchResponse, FiltersResponse
from admin_routes import router as admin_router

_FTS_SAFE = re.compile(r"[^\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]")


def _sanitize_fts_query(q: str) -> str:
    cleaned = _FTS_SAFE.sub(" ", q).strip()
    if not cleaned:
        return ""
    return '"' + cleaned.replace('"', ' ') + '"'


def get_youtube_embed_url(url: str | None, start_seconds: float | None) -> str:
    if not url:
        return ""
    # Default to 0 start seconds if none provided
    start_val = start_seconds if start_seconds is not None else 0.0
    video_id = ""
    match = re.search(r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/)([^#\&\?]{11})', url)
    if match:
        video_id = match.group(1)
    if video_id:
        start_int = int(float(start_val))
        return f"https://www.youtube.com/embed/{video_id}?start={start_int}&autoplay=1"
    return ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Fusha Arabic Search Engine", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", CORSStaticFiles(directory="media"), name="media")
app.include_router(admin_router)


@app.get("/api/filters", response_model=FiltersResponse)
def get_filters():
    conn = get_connection()
    try:
        book_titles = [
            row["book_title"]
            for row in conn.execute(
                "SELECT DISTINCT book_title FROM lectures WHERE book_title IS NOT NULL AND book_title != '' ORDER BY book_title"
            ).fetchall()
        ]
        sheikh_names = [
            row["sheikh_name"]
            for row in conn.execute(
                "SELECT DISTINCT sheikh_name FROM lectures WHERE sheikh_name IS NOT NULL AND sheikh_name != '' ORDER BY sheikh_name"
            ).fetchall()
        ]
        year_dates = [
            row["year_date"]
            for row in conn.execute(
                "SELECT DISTINCT year_date FROM lectures WHERE year_date IS NOT NULL AND year_date != '' ORDER BY year_date"
            ).fetchall()
        ]
        return FiltersResponse(
            book_titles=book_titles,
            sheikh_names=sheikh_names,
            year_dates=year_dates,
        )
    finally:
        conn.close()


@app.post("/index-shards", response_model=IndexShardsResponse, status_code=201)
def index_shards(payload: IndexShardsRequest):
    conn = get_connection()
    try:
        ids = []
        for shard in payload.shards:
            original = shard.text
            normalized = normalize(original)
            cur = conn.execute(
                "INSERT INTO lectures (text_content, normalized_text) VALUES (?, ?)",
                (original, normalized),
            )
            ids.append(cur.lastrowid)
        conn.commit()
        return IndexShardsResponse(
            status="success",
            indexed_count=len(ids),
            ids=ids,
        )
    finally:
        conn.close()


@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    book_title: str | None = Query(None),
    sheikh_name: str | None = Query(None),
    year_date: str | None = Query(None),
):
    normalized_query = normalize(q)
    clean_q = re.sub(r'[\u064B-\u065F\u0670]', '', q)
    safe_query = _sanitize_fts_query(normalized_query)
    if not safe_query:
        return SearchResponse(
            query=q,
            normalized_query=normalized_query,
            page=page,
            page_size=page_size,
            total_results=0,
            results=[],
        )

    conn = get_connection()
    try:
        # 1. Build dynamic filter clause and params array
        query_params = [f'{safe_query}*']
        filter_clause = ""

        if book_title:
            filter_clause += " AND lectures.book_title = ?"
            query_params.append(book_title)
        if sheikh_name:
            filter_clause += " AND lectures.sheikh_name = ?"
            query_params.append(sheikh_name)
        if year_date:
            filter_clause += " AND lectures.year_date = ?"
            query_params.append(year_date)

        offset = (page - 1) * page_size

        # 2. Execute COUNT query
        count_query = f"""
            SELECT count(*)
            FROM lectures
            JOIN arabic_text_shards_fts ON lectures.id = arabic_text_shards_fts.rowid
            WHERE arabic_text_shards_fts MATCH ? {filter_clause}
        """
        count_row = conn.execute(count_query, query_params).fetchone()
        total_results = count_row[0] if count_row else 0

        # 3. Execute DATA query
        data_query = f"""
            SELECT lectures.*, arabic_text_shards_fts.rank
            FROM lectures
            JOIN arabic_text_shards_fts ON lectures.id = arabic_text_shards_fts.rowid
            WHERE arabic_text_shards_fts MATCH ? {filter_clause}
            ORDER BY arabic_text_shards_fts.rank
            LIMIT ? OFFSET ?
        """
        data_params = query_params.copy()
        data_params.extend([page_size, offset])

        rows = conn.execute(data_query, data_params).fetchall()

        def _encode_audio_url(raw: str | None) -> str | None:
            if not raw:
                return None
            filename = raw.replace("\\", "/").rstrip("/").split("/")[-1]
            if not filename:
                return None
            return "/media/" + quote(filename, safe="")

        results = [
            SearchResult(
                id=row["id"],
                original_text=row["text_content"],
                normalized_text=row["normalized_text"],
                rank=round(row["rank"], 4),
                audio_url=_encode_audio_url(row["audio_url"]),
                start_time=row["start_time"],
                end_time=row["end_time"],
                book_title=row["book_title"],
                sheikh_name=row["sheikh_name"],
                year_date=row["year_date"],
                youtube_url=row["youtube_url"],
                youtube_embed_url=get_youtube_embed_url(row["youtube_url"], row["start_time"]),
            )
            for row in rows
        ]

        return SearchResponse(
            query=q,
            normalized_query=normalized_query,
            page=page,
            page_size=page_size,
            total_results=total_results,
            results=results,
        )
    finally:
        conn.close()
