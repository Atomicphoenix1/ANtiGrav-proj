# باحث (Baheth) — Arabic Search Engine: Complete Developer Guide

> A full-stack Arabic text search engine with synchronized audio playback,
> built with FastAPI + SQLite FTS5 + Next.js 16 + React 19 + Tailwind CSS v4.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Database Layer — SQLite + FTS5](#2-database-layer--sqlite--fts5)
3. [Arabic Text Normalizer](#3-arabic-text-normalizer)
4. [SRT Import Pipeline](#4-srt-import-pipeline)
5. [FastAPI Backend — API Layer](#5-fastapi-backend--api-layer)
6. [Admin Routes & Control Panel](#6-admin-routes--control-panel)
7. [Pydantic & SQLAlchemy Models](#7-pydantic--sqlalchemy-models)
8. [Frontend — Next.js Setup](#8-frontend--nextjs-setup)
9. [Search UI — Core Logic](#9-search-ui--core-logic)
10. [Audio Player Component](#10-audio-player-component)
11. [Admin Control Panel Frontend](#11-admin-control-panel-frontend)
12. [XSS Protection — DOMPurify](#12-xss-protection--dompurify)
13. [QA & Testing Infrastructure](#13-qa--testing-infrastructure)
14. [Audio Pipeline Bug Diagnosis](#14-audio-pipeline-bug-diagnosis)
15. [CORS & Integration](#15-cors--integration)
16. [End-to-End Flow](#16-end-to-end-flow)
17. [Glossary for Junior Devs](#17-glossary-for-junior-devs)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│              Frontend (Next.js 16 + React 19)             │
│  arabic-search-interface/app/page.tsx  ← Search UI       │
│  components/  ← SearchBar, ResultCard, AudioPlayer        │
│  hooks/       ← useDebounce, useAdminCombo                │
│  utils/       ← sanitizeHtml (DOMPurify)                  │
│        │  HTTP fetch → http://127.0.0.1:8000              │
└──────────────┬───────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│              Backend (FastAPI + Uvicorn)                   │
│  main.py          — App entry, CORS, search/filters/index │
│  admin_routes.py  — Upload, delete, nuclear flush         │
│  database.py      — SQLite schema, FTS5, triggers         │
│  models.py        — Pydantic & SQLAlchemy models          │
│  normalizer.py    — Arabic text normalization pipeline    │
│  import_lecture.py— SRT parser → DB bulk insert           │
└──────────────┬───────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│              Database Layer (SQLite + FTS5)                │
│  arabic_search.db                                          │
│    ├── lectures (9 columns: id, text_content, ...)         │
│    └── arabic_text_shards_fts (FTS5 virtual table)         │
│  Triggers: AFTER INSERT/DELETE/UPDATE → sync FTS           │
└──────────────┬───────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│              Media Assets (on disk)                        │
│  media/ — MP3 audio files + SRT subtitle files             │
│  FastAPI StaticFiles("/media") serves them                 │
└───────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend Language | Python 3.12 | Server-side logic |
| API Framework | FastAPI | REST endpoints with auto Swagger docs |
| ASGI Server | Uvicorn | High-performance async server |
| Database | SQLite 3 | Embedded, zero-config database |
| Search Engine | FTS5 (SQLite extension) | Full-text search with BM25 ranking |
| Frontend Framework | Next.js 16 (App Router) | React-based SSR/SPA |
| UI Language | TypeScript 5.7 | Type-safe JavaScript |
| Styling | Tailwind CSS v4 | Utility-first CSS |
| Components | shadcn/ui (base-nova style) | Pre-built, customizable components |
| Icons | lucide-react | Open-source icon library |
| HTML Sanitization | DOMPurify / isomorphic-dompurify | XSS prevention |
| Fonts | Google Fonts (Cairo + Amiri) | Arabic-optimized typography |
| Analytics | @vercel/analytics | Production usage tracking |

### Key Design Decisions

1. **Why SQLite instead of PostgreSQL/MySQL?**
   - Zero configuration — no server process to manage
   - FTS5 is built-in (no need for Elasticsearch)
   - Perfect for local/single-user or small-team deployment
   - File-based, easy to backup and transfer

2. **Why store both `text_content` AND `normalized_text`?**
   - `text_content`: Preserves original Arabic diacritics (tashkeel), HTML markup, formatting — what the user sees
   - `normalized_text`: Stripped of diacritics, unified alef/ya/ta — what FTS5 searches
   - This separation lets users see beautifully formatted text while the search engine matches flexibly

3. **Why two indexing paths (`POST /index-shards` vs `import_lecture.py`)?**
   - `/index-shards`: For programmatic/API-based indexing (testing, small snippets)
   - `import_lecture.py`: For bulk importing SRT+MP3 lecture pairs with timing metadata

---

## 2. Database Layer — SQLite + FTS5

**File:** `Baheth/database.py`

### 2.1 Connection Management

```python
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Rows behave like dicts
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
```

**PRAGMA journal_mode=WAL (Write-Ahead Logging):**
- Instead of writing changes directly to the main database file, SQLite writes them to a separate WAL file (`arabic_search.db-wal`)
- Readers can still read the old data while writers append to the WAL
- Periodically, the WAL is "checkpointed" (merged) back into the main file
- Result: **concurrent reads + writes without blocking** — critical for a search app

**PRAGMA foreign_keys=ON:**
- Enforces foreign key constraints at the database level
- ON by default in most databases, but OFF by default in SQLite

### 2.2 Schema (lectures table)

```sql
CREATE TABLE IF NOT EXISTS lectures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    text_content    TEXT    NOT NULL,     -- Original Arabic text (may contain HTML)
    normalized_text TEXT    NOT NULL,     -- Normalized version (for FTS5 search)
    audio_url       TEXT    DEFAULT NULL, -- Audio file path/basename
    start_time      REAL    DEFAULT NULL, -- Segment start time (seconds)
    end_time        REAL    DEFAULT NULL, -- Segment end time (seconds)
    book_title      TEXT    DEFAULT NULL, -- Book/course title (for filtering)
    sheikh_name     TEXT    DEFAULT NULL, -- Speaker/sheikh name (for filtering)
    year_date       TEXT    DEFAULT NULL  -- Year/date metadata
);
```

**Column-by-column explanation:**

| Column | Type | Purpose | Example |
|--------|------|---------|---------|
| `id` | INTEGER | Auto-incrementing primary key | 1, 2, 3... |
| `text_content` | TEXT | Raw text as imported (preserves diacritics, HTML) | `<p>الْحَمْدُ لِلَّهِ</p>` |
| `normalized_text` | TEXT | Text after normalization pipeline | `الحمد لله` |
| `audio_url` | TEXT | Basename of the MP3 file | `amr21.mp3` |
| `start_time` | REAL | When this subtitle segment starts (seconds) | `85.5` |
| `end_time` | REAL | When this subtitle segment ends (seconds) | `90.0` |
| `book_title` | TEXT | Book title filter value | `تقريب العلم` |
| `sheikh_name` | TEXT | Sheikh/speaker filter value | `الشيخ صالح العصيمي` |
| `year_date` | TEXT | Year/date filter value | `1445` |

### 2.3 FTS5 Virtual Table

```sql
CREATE VIRTUAL TABLE IF NOT EXISTS arabic_text_shards_fts USING fts5(
    normalized_text,   -- Searchable text content
    book_title,        -- Filterable metadata
    sheikh_name        -- Filterable metadata
);
```

**What is FTS5?**

FTS5 (Full-Text Search version 5) is a **virtual table** — it looks like a table but behaves like a search engine:

- **Tokenization**: Splits text into individual tokens (words). For Arabic, it handles right-to-left text natively
- **Inverted Index**: For each unique token, stores a list of all rows containing it — enables instant lookup
- **BM25 Ranking**: Built-in relevance scoring algorithm. Returns a `rank` value where lower = more relevant
- **Prefix Search**: `كتاب*` matches `كتاب`, `كتابة`, `كتابي`
- **Advanced Queries**: `NEAR`, `AND`, `OR`, `NOT`, phrase search
- **Auto-sync via rowid**: `rowid` in FTS5 corresponds to `id` in the source table

### 2.4 Triggers — Automatic FTS Synchronization

```sql
-- When a row is inserted into lectures, also insert into FTS
CREATE TRIGGER after_lectures_insert
AFTER INSERT ON lectures
BEGIN
    INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
    VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
END;

-- When a row is deleted, remove from FTS
CREATE TRIGGER after_lectures_delete
AFTER DELETE ON lectures
BEGIN
    INSERT INTO arabic_text_shards_fts(
        arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name
    ) VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
END;

-- When a row is updated, delete old FTS entry and insert new one
CREATE TRIGGER after_lectures_update
AFTER UPDATE ON lectures
BEGIN
    INSERT INTO arabic_text_shards_fts(
        arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name
    ) VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
    INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
    VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
END;
```

**Why triggers instead of application-level sync?**

- **Data integrity**: Even if a row is inserted via the SQLite CLI or another tool, FTS stays in sync
- **No forgotten sync calls**: The database enforces consistency
- **Simpler application code**: No need to remember to update FTS after every INSERT/UPDATE/DELETE

**Why `rowid = id`?** FTS5 uses `rowid` as its internal identifier. By setting `rowid = lectures.id`, we can JOIN both tables on matching IDs.

### 2.5 Initialization & Migration System

```python
def init_db() -> None:
    Base.metadata.create_all(bind=engine)  # Create ORM tables

    conn = get_connection()
    try:
        # Rename old table if it exists (migration from v1)
        old_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='arabic_text_shards'"
        ).fetchone()
        if old_exists:
            conn.execute("ALTER TABLE arabic_text_shards RENAME TO lectures")

        # Run full schema script
        conn.executescript(SCHEMA_SQL)

        # Run individual column migrations (safe to re-run)
        for migration in MIGRATIONS:
            try:
                conn.execute(migration)
            except sqlite3.OperationalError:
                pass  # Column already exists — skip

        # Rebuild FTS if it's empty but lectures have data
        # (happens after migrations or manual DB edits)
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
```

**Migration list — columns added incrementally:**
```python
MIGRATIONS = [
    "ALTER TABLE lectures ADD COLUMN normalized_text TEXT DEFAULT ''",
    "ALTER TABLE lectures ADD COLUMN audio_url TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN start_time REAL DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN end_time REAL DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN book_title TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN sheikh_name TEXT DEFAULT NULL",
    "ALTER TABLE lectures ADD COLUMN year_date TEXT DEFAULT NULL",
]
```

**Why `try/except OperationalError`?** SQLite's `ALTER TABLE ADD COLUMN` throws an error if the column already exists. By catching and ignoring it, we can run `init_db()` safely on every server start — new columns get added, existing ones are left untouched.

---

## 3. Arabic Text Normalizer

**File:** `Baheth/normalizer.py`

### 3.1 The Arabic Search Problem

Arabic orthography presents unique challenges for text search:

| Challenge | Example | Why It Breaks Search |
|-----------|---------|---------------------|
| **Diacritics (Tashkeel)** | `كِتَابٌ` vs `كتاب` | Fatha, Damma, Kasra, Shadda, Sukun are optional marks that don't change meaning |
| **Alef variants** | `أ`, `إ`, `آ`, `ٱ` | All represent the same sound `/aː/` but have different Unicode codepoints |
| **Ta Marbuta** | `مدرسة` (ة) vs `مدرسه` (ه) | Both are pronounced "h" at the end of a word in pausa |
| **Alef Maqsura** | `على` (ى) vs `علي` (ي) | Both are pronounced "aː" — a common spelling variation |
| **Tatweel (Kashida)** | `كتابـــة` | Horizontal elongation has no phonetic value |
| **HTML markup** | `<p>نص</p>` | Markup shouldn't be part of searchable text |

### 3.2 The Normalization Pipeline

```python
def normalize(text: str) -> str:
    # Step 1: Unescape HTML entities (&lt; → <, &amp; → &)
    text = html.unescape(text)

    # Step 2: Remove all HTML tags
    text = strip_html(text)

    # Step 3: Remove Tatweel (kashida) characters
    text = text.replace(TATWEEL, "")

    # Step 4: Remove Arabic diacritics (tashkeel)
    text = text.translate(DIACRITICS)

    # Step 5: Normalize variant letters to their base form
    text = text.translate(CHAR_MAP)

    # Step 6: Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text
```

### 3.3 Character Maps

**Diacritics removed (all are combining marks in Unicode):**

```python
DIACRITICS = str.maketrans({
    "\u064B": None,  # Fathatayn (ً)
    "\u064C": None,  # Dammatayn (ٌ)
    "\u064D": None,  # Kasratayn (ٍ)
    "\u064E": None,  # Fatha (َ)
    "\u064F": None,  # Damma (ُ)
    "\u0650": None,  # Kasra (ِ)
    "\u0651": None,  # Shadda (ّ)
    "\u0652": None,  # Sukun (ْ)
})
```

**Letter normalization map:**

```python
CHAR_MAP = str.maketrans({
    "\u0623": "\u0627",  # أ (alef with hamza above) → ا (alef)
    "\u0625": "\u0627",  # إ (alef with hamza below) → ا (alef)
    "\u0622": "\u0627",  # آ (alef with madda) → ا (alef)
    "\u0671": "\u0627",  # ٱ (alef wasla) → ا (alef)
    "\u0629": "\u0647",  # ة (ta marbuta) → ه (ha)
    "\u0649": "\u064A",  # ى (alef maqsura) → ي (ya)
})
```

### 3.4 Normalization Examples

| Original Text | After Normalization | Why This Helps |
|---------------|-------------------|----------------|
| `الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ` | `الحمد لله رب العالمين` | Search for `الحمد` finds it even with full tashkeel |
| `<p>إِيَّاكَ نَعْبُدُ</p>` | `اياك نعبد` | HTML stripped, alef unified, diacritics removed |
| `مدرسةُ الـعلمِ` | `مدرسه العلم` | Ta marbuta → ha |
| `عَلَىٰ صِرَاطٍ` | `علي صراط` | Alef maqsura → ya |
| `ٱسْمُ اللَّهِ` | `اسم الله` | Alef wasla → alef |

### 3.5 Critical Insight

The normalizer only runs on the **backend** — both when:
1. **Indexing**: `normalized_text = normalize(original_text)` ← stored in DB
2. **Searching**: `normalized_query = normalize(user_query)` ← used for FTS5 MATCH

This ensures that regardless of how the user types their query (with or without diacritics, with أ or ا), it will match the normalized version in FTS5.

---

## 4. SRT Import Pipeline

**File:** `Baheth/import_lecture.py`

### 4.1 What is SRT?

SRT (SubRip) is the most common subtitle format:

```
1
00:01:25,500 --> 00:01:30,000
بسم الله الرحمن الرحيم

2
00:02:00,000 --> 00:02:05,250
الحمد لله رب العالمين
```

Each block consists of:
1. **Sequence number** (1, 2, 3...)
2. **Timestamps**: `HH:MM:SS,mmm --> HH:MM:SS,mmm`
3. **Subtitle text** (one or more lines)
4. **Blank line** separating blocks

### 4.2 Timestamp Parsing

```python
SRT_TIMESTAMP = re.compile(r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})")

def _ts_to_seconds(ts: str) -> float:
    m = SRT_TIMESTAMP.fullmatch(ts.strip())
    h, mi, s, ms = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    return h * 3600 + mi * 60 + s + ms / 1000
```

**Examples:**

| Timestamp | Calculation | Result (seconds) |
|-----------|------------|------------------|
| `00:00:00,000` | 0+0+0+0 | 0.0 |
| `00:01:00,000` | 0+60+0+0 | 60.0 |
| `00:01:25,500` | 0+60+25+0.5 | 85.5 |
| `01:00:00,000` | 3600+0+0+0 | 3600.0 |
| `01:23:45,678` | 3600+1380+45+0.678 | 5025.678 |

### 4.3 Full SRT Block Parser

```python
SRT_BLOCK = re.compile(
    r"(?P<index>\d+)\s*\n"
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
    r"(?P<text>.+?)(?:\n\n|\Z)",
    re.DOTALL,
)
```

**Named capture groups:**
- `(?P<index>\d+)` — Block sequence number
- `(?P<start>...)` — Start timestamp
- `(?P<end>...)` — End timestamp
- `(?P<text>.+?)` — Text content (lazy match)
- `(?:\n\n|\Z)` — Terminated by blank line or end-of-file

**Why `re.DOTALL`?** Makes `.` match newlines too — subtitle text often spans multiple lines.

### 4.4 Main Import Function

```python
def main():
    audio_path = os.path.abspath(sys.argv[1])  # Full path to MP3
    srt_path = os.path.abspath(sys.argv[2])    # Full path to SRT
    book_title = sys.argv[3] if len(sys.argv) > 3 else ""
    sheikh_name = sys.argv[4] if len(sys.argv) > 4 else ""
    year_date = sys.argv[5] if len(sys.argv) > 5 else ""

    blocks = parse_srt(srt_path)

    # Use just the filename (not the full path)
    audio_filename = os.path.basename(audio_path)

    rows = []
    for b in blocks:
        rows.append((
            b["text"],                # text_content — original Arabic with diacritics
            normalize(b["text"]),     # normalized_text — cleaned for FTS5
            audio_filename,           # audio_url — portable filename
            b["start"],               # start_time — in seconds
            b["end"],                 # end_time — in seconds
            book_title,
            sheikh_name,
            year_date,
        ))

    conn.executemany("""INSERT INTO lectures
        (text_content, normalized_text, audio_url, start_time, end_time,
         book_title, sheikh_name, year_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", rows)
    conn.commit()
```

### 4.5 The Audio URL Bug (Fixed)

**Before fix:**
```python
audio_path = os.path.abspath(sys.argv[1])   # C:\Users\...\file.mp3
rows.append((..., audio_path, ...))          # Stored full Windows path
```

**After fix:**
```python
audio_path = os.path.abspath(sys.argv[1])
audio_ref = os.path.basename(audio_path)    # file.mp3 only
rows.append((..., audio_ref, ...))            # Stored portable basename
```

**Why the full path was broken:**
1. **Non-portable**: `C:\Users\saif_\...` only works on one machine
2. **Not URL-safe**: Contains backslashes (\), spaces, Arabic characters
3. **StaticFiles mismatch**: FastAPI's `/media` mount serves files **relative** to the `media/` directory — it can't resolve absolute paths

**The fix in `main.py` search handler:**
```python
from urllib.parse import quote
raw = row["audio_url"] or ""
audio_url = f"/media/{quote(raw)}" if raw else None
```

This builds a proper URL: `/media/03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20...mp3`

---

## 5. FastAPI Backend — API Layer

**File:** `Baheth/main.py`

### 5.1 Application Setup

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # Run DB initialization on every server start
    yield      # Server runs while in this "yield"

app = FastAPI(
    title="Fusha Arabic Search Engine",
    version="2.0.0",
    lifespan=lifespan   # ← Modern FastAPI lifecycle
)
```

**The `lifespan` pattern (FastAPI 2.0+):**
- Replaces the old `@app.on_event("startup")` decorator
- Code before `yield` runs on startup
- Code after `yield` runs on shutdown
- Type-safe and async-native

### 5.2 CORS Middleware

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

CORS (Cross-Origin Resource Sharing) is a browser security mechanism. When the Next.js frontend at `http://localhost:3000` makes a `fetch()` call to the backend at `http://127.0.0.1:8000`, the browser automatically sends a **preflight `OPTIONS` request**. The backend must respond with `Access-Control-Allow-Origin: http://localhost:3000` for the actual request to proceed.

**Security note:** `"*"` allows any origin and should only be used in development. In production, restrict to your actual frontend domain.

### 5.3 Custom StaticFiles with CORS

```python
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response

app.mount("/media", CORSStaticFiles(directory="media"), name="media")
```

**Why custom CORS for static files?** HTML `<audio>` elements also make CORS requests. Without CORS headers on the media responses, the browser blocks audio playback even from the same origin in some configurations.

### 5.4 FTS5 Query Sanitization

```python
_FTS_SAFE = re.compile(r"[^\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]")

def _sanitize_fts_query(q: str) -> str:
    cleaned = _FTS_SAFE.sub(" ", q).strip()
    if not cleaned:
        return ""
    return '"' + cleaned.replace('"', ' ') + '"'
```

**What this does:**
1. Removes any character that's NOT:
   - `\w` (alphanumeric + underscore)
   - `\u0600-\u06FF` (Arabic block)
   - `\u0750-\u077F` (Arabic Supplement)
   - `\u08A0-\u08FF` (Arabic Extended-A)
   - whitespace
2. Wraps the result in double quotes to prevent FTS5 operator injection

**Examples:**

| User Input | After Sanitization | Safe? |
|-----------|-------------------|-------|
| `الرحمن` | `"الرحمن"*` | Yes |
| `*` | (empty) → returns empty results | Yes — no crash |
| `"; DROP TABLE ...` | `"   drop table   "` | Yes — SQL syntax neutralized |
| `كتاب*` | `"كتاب "` | Yes — `*` removed, prefix search still works via FTS5 |

### 5.5 Search Endpoint

```python
@app.get("/search", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, max_length=200),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    book_title: str | None = Query(None),
    sheikh_name: str | None = Query(None),
    year_date: str | None = Query(None),
):
```

**Algorithm (step by step):**

```
1. Normalize the query (strip diacritics, unify letters)
2. Sanitize for FTS5 (remove dangerous chars, wrap in quotes)
3. Build filter clause using the optional parameters
4. COUNT query: number of matching rows
5. DATA query: matching rows with BM25 ranking, LIMIT/OFFSET for pagination
6. Transform audio_url: raw filename → /media/<URL-encoded basename>
7. Return SearchResponse
```

**The JOIN pattern:**
```sql
SELECT lectures.*, arabic_text_shards_fts.rank
FROM lectures
JOIN arabic_text_shards_fts ON lectures.id = arabic_text_shards_fts.rowid
WHERE arabic_text_shards_fts MATCH ?
  AND lectures.book_title = ?   -- optional filter
ORDER BY arabic_text_shards_fts.rank
LIMIT ? OFFSET ?
```

**Why JOIN with FTS5?** The `lectures` table has the full data (original text, audio times, metadata). FTS5 only stores normalized text. By JOINing on `id = rowid`, we get the best of both: FTS5's fast search + the lectures table's rich data.

**BM25 Ranking:**
- `rank` is a float — lower values mean better matches
- Negative values are typical (BM25 produces negative scores)
- The `ORDER BY rank` sorts by relevance (best match first)

### 5.6 Index Shards Endpoint

```python
@app.post("/index-shards", response_model=IndexShardsResponse, status_code=201)
def index_shards(payload: IndexShardsRequest):
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
    return IndexShardsResponse(status="success", indexed_count=len(ids), ids=ids)
```

**Purpose:** Allows quick, programmatic insertion of text snippets. Unlike `import_lecture.py`, this endpoint:
- Operates via HTTP (not CLI)
- Only inserts text (no audio/timing metadata)
- Returns the generated IDs (useful for verification)

### 5.7 Filters Endpoint

```python
@app.get("/api/filters", response_model=FiltersResponse)
def get_filters():
    book_titles = conn.execute(
        "SELECT DISTINCT book_title FROM lectures WHERE book_title IS NOT NULL AND book_title != '' ORDER BY book_title"
    ).fetchall()
    sheikh_names = ...  # same pattern
    year_dates = ...     # same pattern
    return FiltersResponse(book_titles=book_titles, sheikh_names=sheikh_names, year_dates=year_dates)
```

**Why `DISTINCT` + `ORDER BY`?** Returns each unique value once, sorted alphabetically — perfect for building dropdown selectors in the frontend. The `WHERE ... IS NOT NULL AND != ''` filters out empty metadata.

---

## 6. Admin Routes & Control Panel

**File:** `Baheth/admin_routes.py`

### 6.1 Endpoint Overview

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/admin/assets` | List all MP3/SRT files in media/ |
| POST | `/api/admin/upload` | Upload MP3+SRT + metadata → import to DB |
| DELETE | `/api/admin/assets/{type}/{filename}` | Delete a specific file |
| POST | `/api/admin/flush` | Wipe DB + media, reinitialize |

### 6.2 Asset Inventory

```python
@router.get("/assets")
async def get_inventory_assets():
    if not os.path.exists(MEDIA_DIR):
        return {"mp3s": [], "srts": []}
    files = os.listdir(MEDIA_DIR)
    return {
        "mp3s": [f for f in files if f.endswith(".mp3")],
        "srts": [f for f in files if f.endswith(".srt")],
    }
```

Simply reads the `media/` directory and separates files by extension. Used by the frontend admin panel to display current assets.

### 6.3 Dual Ingestion Pipeline

```python
@router.post("/upload")
async def process_dual_ingestion_pipeline(
    mp3: UploadFile = File(...),
    srt: UploadFile = File(...),
    book_title: str = Form(""),
    sheikh_name: str = Form(""),
    year_date: str = Form(""),
    overwrite: bool = Form(False)
):
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # Check for existing files
    if (os.path.exists(mp3_target) or os.path.exists(srt_target)) and not overwrite:
        raise HTTPException(status_code=409, detail="File conflict")

    # Save uploaded files to disk
    with open(mp3_target, "wb") as buffer:
        shutil.copyfileobj(mp3.file, buffer)
    with open(srt_target, "wb") as buffer:
        shutil.copyfileobj(srt.file, buffer)

    # Launch import_lecture.py as subprocess
    result = subprocess.run(
        [sys.executable, import_script, mp3_target, srt_target,
         book_title, sheikh_name, year_date],
        capture_output=True, text=True, timeout=120,
    )
```

**Why `subprocess` instead of calling the function directly?** The `import_lecture.py` script was written as a standalone CLI tool. Using `subprocess` was expedient but introduces:
- Process overhead (spawning a new Python process)
- Error handling complexity (stdout/stderr parsing)
- Timeout management (120s hard limit)

**A better design** would be to refactor `import_lecture.py` into a callable module.

**`shutil.copyfileobj()`**: Efficiently copies file data in chunks — uses a buffer internally, so large MP3 files don't consume excessive memory.

### 6.4 Nuclear Flush

```python
@router.post("/flush")
async def execute_nuclear_database_flush():
    # 1. Drop ALL tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")

    # 2. Nuke media directory
    if os.path.exists(MEDIA_DIR):
        shutil.rmtree(MEDIA_DIR)
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # 3. Reinitialize (creates tables, FTS, triggers)
    init_db()
```

**Use cases:**
- Testing/reset during development
- Complete re-import of all content
- Recovery from corrupted state

**Safety in frontend:** Requires double confirmation (first a `window.confirm`, then typing "FLUSH").

---

## 7. Pydantic & SQLAlchemy Models

**File:** `Baheth/models.py`

### 7.1 SQLAlchemy ORM Model

```python
class Base(DeclarativeBase):
    pass

class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text_content = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    book_title = Column(String, nullable=True)
    sheikh_name = Column(String, nullable=True)
    year_date = Column(String, nullable=True)
```

**Why SQLAlchemy if we use raw SQL everywhere else?** `Base.metadata.create_all(bind=engine)` is the lazy way to ensure the table exists. Raw SQL (`database.py`'s `SCHEMA_SQL`) does the actual work. The ORM model is essentially documentation and a safety net.

**`DeclarativeBase`**: The modern SQLAlchemy 2.0 way to define ORM models (replaces the old `declarative_base()`).

### 7.2 Pydantic Request/Response Models

```python
class ShardItem(BaseModel):
    text: str = Field(..., max_length=10_000)

class IndexShardsRequest(BaseModel):
    shards: list[ShardItem] = Field(..., max_length=10_000)

class IndexShardsResponse(BaseModel):
    status: str
    indexed_count: int
    ids: list[int]

class FiltersResponse(BaseModel):
    book_titles: list[str]
    sheikh_names: list[str]
    year_dates: list[str]

class SearchResult(BaseModel):
    id: int
    original_text: str
    normalized_text: str
    rank: float
    audio_url: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    book_title: str | None = None
    sheikh_name: str | None = None
    year_date: str | None = None

class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    page: int
    page_size: int
    total_results: int
    results: list[SearchResult]
```

**Pydantic v2 features used here:**
- **Type validation**: `str | None = None` — auto-coercion, nullable fields
- **`Field(...)` constraints**: `max_length`, `ge` (greater than or equal)
- **Automatic JSON Schema**: Powers the Swagger UI documentation
- **`response_model` parameter**: FastAPI uses this to:
  1. Validate the response data
  2. Filter out extra fields (security)
  3. Generate OpenAPI docs

---

## 8. Frontend — Next.js Setup

**Directory:** `arabic-search-interface/`

### 8.1 Package Highlights

```json
{
  "next": "16.2.6",
  "react": "19.2.4",
  "dompurify": "^3.4.10",
  "isomorphic-dompurify": "^3.17.0",
  "lucide-react": "^1.16.0",
  "class-variance-authority": "^0.7.1",
  "tailwind-merge": "^3.3.1"
}
```

**Why `isomorphic-dompurify` instead of just `dompurify`?**
- Next.js uses Server-Side Rendering (SSR)
- `dompurify` is browser-only (needs `window`)
- `isomorphic-dompurify` wraps DOMpurify to work in both Node.js (server) and browser environments

### 8.2 next.config.mjs

```js
const nextConfig = {
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
}
```

- **`ignoreBuildErrors: true`**: Expedient during rapid development. Should be removed in CI/CD to catch type errors before deployment.
- **`images.unoptimized: true`**: Bypasses Next.js image optimization. Acceptable for a search app (few images), but would be wasteful for an image-heavy site.

### 8.3 tsconfig.json

```json
{
  "compilerOptions": {
    "strict": true,
    "moduleResolution": "bundler",
    "paths": { "@/*": ["./*"] }
  }
}
```

**`paths: { "@/*": ["./*"] }`** — The `@` alias means:
- `import { Button } from "@/components/ui/button"` instead of
- `import { Button } from "../../../components/ui/button"`

Much cleaner for deep imports.

### 8.4 Root Layout (layout.tsx)

```tsx
import { Cairo, Amiri } from 'next/font/google'

const cairo = Cairo({ variable: '--font-cairo', subsets: ['arabic', 'latin'] })
const amiri = Amiri({ variable: '--font-amiri', subsets: ['arabic', 'latin'] })

export const metadata: Metadata = {
  title: 'باحث — محرك البحث في النصوص العربية',
  description: 'محرك بحث عربي حديث للنصوص والمتون التراثية',
}

export const viewport: Viewport = {
  colorScheme: 'light dark',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: 'white' },
    { media: '(prefers-color-scheme: dark)', color: 'black' },
  ],
}

export default function RootLayout({ children }) {
  return (
    <html lang="ar" dir="rtl" className={`${cairo.variable} ${amiri.variable} bg-background`}>
      <body className="font-sans antialiased">
        {children}
        <AdminControlPanel />
      </body>
    </html>
  )
}
```

**`next/font/google`**: Loads fonts at build time (not runtime). Font files are hosted on your own server — no external requests, no CLS (Cumulative Layout Shift).

**RTL setup:**
- `lang="ar"` — tells screen readers, translation tools, and search engines this is Arabic
- `dir="rtl"` — sets text direction to right-to-left
- `Cairo` variable font — for UI elements (sans-serif)
- `Amiri` — classical Arabic typeface, perfect for religious/poetic texts (serif)

---

## 9. Search UI — Core Logic

**File:** `app/page.tsx`

### 9.1 State Management

```typescript
const [query, setQuery] = useState("")             // Current input value
const [submitted, setSubmitted] = useState("")      // Last successfully searched query
const [loading, setLoading] = useState(false)        // Loading indicator
const [results, setResults] = useState<SearchResult[]>([])     // Search results
const [activeResult, setActiveResult] = useState<SearchResult | null>(null)  // Selected result
const [durationMs, setDurationMs] = useState(0)      // Search response time
const [error, setError] = useState<string | null>(null)      // Error message
const [page, setPage] = useState(1)                  // Pagination
const [filters, setFilters] = useState<FilterOptions>({...})  // Available filter values
const [selectedBook, setSelectedBook] = useState("")
const [selectedSheikh, setSelectedSheikh] = useState("")
const [selectedYear, setSelectedYear] = useState("")
```

### 9.2 Debouncing

```typescript
const debouncedQuery = useDebounce(query, 300)

// Hook implementation:
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);  // Cleanup: cancel on every value change
  }, [value, delay]);

  return debouncedValue;
}
```

**Timeline of debouncing:**

```
User types:        "ا" -- "ال" -- "الر" -- "الرح" -- "الرحم" -- "الرحمن" (final)
                    │       │        │         │          │          │
Debounce (300ms):   └───X───┘───X────┘───X─────┘───X──────┘───X──────┘══════▶ fires!
                    Each keystroke cancels the previous 300ms timer.
                    Only the FINAL stable value triggers the search.
```

### 9.3 Search URL Builder

```typescript
const buildSearchUrl = useCallback(() => {
    const params = new URLSearchParams()
    params.set("q", debouncedQuery.trim())
    params.set("page", String(page))
    params.set("page_size", "10")
    if (selectedBook) params.set("book_title", selectedBook)
    if (selectedSheikh) params.set("sheikh_name", selectedSheikh)
    if (selectedYear) params.set("year_date", selectedYear)
    return `${BACKEND_URL}/search?${params.toString()}`
}, [debouncedQuery, page, selectedBook, selectedSheikh, selectedYear])
```

**`useCallback`:** Memoizes the function. It only recreates when its dependencies change. Prevents infinite loops in `useEffect`.

**`URLSearchParams.toString()`:** Automatically encodes Arabic characters:
- `q = "الرحمن"` → `q=%D8%A7%D9%84%D8%B1%D8%AD%D9%85%D9%86`
- `sheikh_name = "ابن القيم"` → `sheikh_name=%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85`

### 9.4 Search Effect

```typescript
useEffect(() => {
    const runSearchPipeline = async () => {
        const trimmed = debouncedQuery.trim()
        if (!trimmed) {
            setResults([])
            setActiveResult(null)
            setSubmitted("")
            setError(null)
            return
        }

        setLoading(true)
        setError(null)
        const start = performance.now()

        try {
            const url = buildSearchUrl()
            const response = await fetch(url)
            if (!response.ok) throw new Error(`Server returned error code: ${response.status}`)

            const data = await response.json()

            if (page === 1) {
                setResults(data.results)
                setActiveResult(data.results.length > 0 ? data.results[0] : null)
            } else {
                setResults(prev => [...prev, ...data.results])  // Append for "load more"
            }

            setSubmitted(trimmed)
            setDurationMs(Math.round(performance.now() - start))
        } catch (err: any) {
            setError("تعذر الاتصال بالخادم الرئيسي. يرجى التحقق من تشغيل الواجهة البرمجية (FastAPI).")
            setResults([])
            setActiveResult(null)
        } finally {
            setLoading(false)
        }
    }

    runSearchPipeline()
}, [debouncedQuery, page, buildSearchUrl])
```

**Smart behaviors:**
- **Empty query**: Clears everything gracefully
- **Page 1**: Replaces results and auto-selects the first result
- **Page > 1**: Appends to existing results ("infinite scroll" / "load more" pattern)
- **Auto-select**: `setActiveResult(data.results[0]` — the first result is immediately shown in the reading pane
- **Performance measurement**: `performance.now()` tracks how long the search takes

### 9.5 Audio Auto-Play

```typescript
useEffect(() => {
    if (activeResult && activeResult.audio_url && audioRef.current) {
        audioRef.current.src = `${BACKEND_URL}${activeResult.audio_url}`
        audioRef.current.load()
        audioRef.current.currentTime = activeResult.start_time || 0
        audioRef.current.play().catch(err => console.log("Audio autoplay interrupted:", err))
    }
}, [activeResult])
```

**What happens when the user clicks a result:**
1. `activeResult` changes → this effect fires
2. Sets `<audio>` source to the full URL: `http://127.0.0.1:8000/media/03%20...mp3`
3. Calls `.load()` to begin fetching the audio metadata
4. Seeks to `start_time` — the exact moment this text segment begins
5. Calls `.play()` — starts playing immediately

**.catch() is essential**: Browsers block autoplay unless the user has interacted with the page. The catch silently handles this (logged, not thrown).

### 9.6 UI Layout

```
┌──────────────────────────────────────────────────────────┐
│  ██ باحِث — محرك البحث في النصوص العربية     [بحث دلالي] │
│  [ابحث في النصوص والمتون..._________] [بحث] [⚙ filters] │
├────────────────────────────────────┬─────────────────────┤
│                                    │                     │
│  READING VIEWPORT (2/3 width)      │  RESULTS (1/3 width)│
│                                    │                     │
│  ┌──────────────────────────┐      │  ┌───────────────┐  │
│  │ شظية نصية #42            │      │  │ نتائج (10)    │  │
│  │ درجة المطابقة: -2.3      │      │  │ لـ "الرحمن"   │  │
│  │━━━━━━━━━━━━━━━━━━━━━━━━━ │      │  │ 0.42 ثانية    │  │
│  │                          │      │  └───────────────┘  │
│  │ النص الأصلي بالتشكيل     │      │                     │
│  │ مع HTML markup محفوظ     │      │  ┌───────────────┐  │
│  │                          │      │  │ شظية #42     │  │
│  │ بسم الله الرحمن الرحيم   │      │  │ الْحَمْدُ...  │  │←active
│  │                          │      │  ├───────────────┤  │
│  │━━━━━━━━━━━━━━━━━━━━━━━━━ │      │  │ شظية #43     │  │
│  │ ▶ التشغيل  [=========>]  │      │  │ الحمد لله...  │  │
│  │ 1:25              1:30  │      │  ├───────────────┤  │
│  │                          │      │  │ شظية #44     │  │
│  │ الكتاب: تقريب العلم       │      │  │ رب العالمين.. │  │
│  │ الشيخ: صالح العصيمي      │      │  ├───────────────┤  │
│  └──────────────────────────┘      │  │ [تحميل المزيد]│  │
│                                    │  └───────────────┘  │
│                                    │                     │
│                                    │  ┌───────────────┐  │
│                                    │  │ عمليات بحث    │  │
│                                    │  │ [طلب العلم]   │  │
│                                    │  │ [الإخلاص]     │  │
│                                    │  └───────────────┘  │
└────────────────────────────────────┴─────────────────────┘
```

---

## 10. Audio Player Component

**File:** `components/audio-player.tsx`

### 10.1 Component Interface

```typescript
interface AudioPlayerProps {
  src: string        // Audio file URL
  startTime?: number // Starting position in seconds
  isPlaying?: boolean// Auto-play flag
}
```

### 10.2 State & Refs

```typescript
const audioRef = useRef<HTMLAudioElement>(null)
const [playing, setPlaying] = useState(isPlaying)
const [currentTime, setCurrentTime] = useState(startTime)
const [duration, setDuration] = useState(0)
const [isMetadataLoaded, setIsMetadataLoaded] = useState(false)
```

### 10.3 Seeking to Start Position

```typescript
useEffect(() => {
    const audio = audioRef.current
    if (audio && isMetadataLoaded) {
        const cushionedTime = Math.max(0, startTime - 2)  // 2s cushion
        if ('fastSeek' in audio) {
            audio.fastSeek(cushionedTime)
        } else {
            audio.currentTime = cushionedTime
        }
        setCurrentTime(cushionedTime)
    }
}, [startTime, isMetadataLoaded])
```

**`fastSeek` vs `currentTime`:**
- `fastSeek()` is a newer API that seeks to a position before the audio file is fully downloaded
- `currentTime = value` works everywhere but may need the file to be loaded first
- The code uses `fastSeek` if available (modern browsers), falls back to `currentTime`

**Why `startTime - 2` (2-second cushion)?** Gives the listener context — they hear the phrase immediately before the matched segment. Without it, starting exactly at the word boundary sounds jarring.

### 10.4 Formatting Time

```typescript
function formatTime(seconds: number) {
    if (!Number.isFinite(seconds) || seconds < 0) seconds = 0
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, "0")}`
}
```

**`Number.isFinite` guard:** Prevents `NaN` or `Infinity` from crashing the UI. In CSS, `tabular-nums` ensures digits have uniform width so the display doesn't jitter during playback.

### 10.5 Progress Bar (Custom Range Input)

```tsx
<input type="range"
    min={0} max={duration || 0} step={0.1}
    value={currentTime} onChange={handleSeek}
    aria-label="شريط التقدم"
    className="[&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5
               [&::-webkit-slider-thumb]:appearance-none
               [&::-webkit-slider-thumb]:rounded-full
               [&::-webkit-slider-thumb]:bg-primary
               [&::-webkit-slider-thumb]:shadow-sm
               [&::-webkit-slider-thumb]:hover:scale-125
               [&::-moz-range-thumb]:h-3.5 ..."
/>
```

**`type="range"` customization:** Native range inputs have different shadow DOM structures per browser. The `[&::-webkit-slider-thumb]` and `[&::-moz-range-thumb]` selectors target WebKit (Chrome, Edge, Safari) and Firefox respectively.

---

## 11. Admin Control Panel Frontend

**File:** `components/AdminControlPanel.tsx`

### 11.1 Secret Activation — Konami Code + Chord

```typescript
export function useAdminCombo(onTrigger: () => void) {
    const TARGET_SEQUENCE = ["ArrowUp", "ArrowUp", "ArrowDown", "ArrowDown", "ArrowLeft", "ArrowRight"];

    // Phase 1: Chord detection — hold ↑ + ← + → simultaneously
    if (keys.has("ArrowUp") && keys.has("ArrowLeft") && keys.has("ArrowRight")) {
        setIsChordActive(true);  // Shows "SECURE ACCESS SIGNAL" indicator
    }

    // Phase 2: Konami Code sequence — ↑↑↓↓←→
    if (isChordActive) {
        inputSequence.push(key);
        if (endsWith(TARGET_SEQUENCE)) {
            onTrigger();  // Opens the admin panel overlay
        }
    }
}
```

**Two-factor authentication (client-side):**
- Factor 1: Three simultaneous arrow keys (chord) — proves deliberate intent
- Factor 2: Classic Konami Code sequence — proves knowledge of the secret

### 11.2 Upload with Overwrite Confirmation

```typescript
const handleUpload = async (overwriteConfirmed = false) => {
    if (!mp3File || !srtFile) return alert("Both MP3 and SRT must be selected.");

    const formData = new FormData();
    formData.append("mp3", mp3File);
    formData.append("srt", srtFile);
    formData.append("book_title", metadata.bookTitle);
    formData.append("sheikh_name", metadata.sheikhName);
    formData.append("year_date", metadata.yearDate);
    formData.append("overwrite", String(overwriteConfirmed));

    const res = await fetch("http://127.0.0.1:8000/api/admin/upload", { method: "POST", body: formData });

    if (res.status === 409) {
        const confirmOverwrite = window.confirm("File collision detected! Confirm overwrite?");
        if (confirmOverwrite) handleUpload(true);  // Recursive call with overwrite=true
    }
};
```

**Recursive retry pattern:** If the server returns `409 Conflict` (file exists), the frontend asks the user to confirm, then retries with `overwrite=true`. No state management needed — the recursion handles the retry.

### 11.3 Nuclear Flush — Double Confirmation

```typescript
const handleNuclearFlush = async () => {
    // Confirmation 1: Simple OK/Cancel dialog
    const firstVerify = window.confirm("WARNING: This deletes all data. Proceed?");
    if (!firstVerify) return;

    // Confirmation 2: Must type "FLUSH" exactly
    const finalVerify = window.prompt("Type 'FLUSH' to confirm:");
    if (finalVerify !== "FLUSH") return alert("Mismatch. Aborted.");

    const res = await fetch("http://127.0.0.1:8000/api/admin/flush", { method: "POST" });
    if (res.ok) alert("Database wiped clean.");
    window.location.reload();
};
```

**Why `prompt()` for confirmation?** `window.confirm` is too easy to accidentally click. Requiring the user to type "FLUSH" ensures they've read the warning and deliberately intend to destroy data.

---

## 12. XSS Protection — DOMPurify

**File:** `utils/sanitizeHtml.ts`

### 12.1 The Problem

Arabic text content contains structural HTML:

```html
<p>قَالَ <strong>سِيبَوَيْهِ</strong>:
الْكَلَامُ مَا اجْتَمَعَ فِيهِ
<span style="color:red">ثَلَاثَةُ أَشْيَاءَ</span>:
الِاسْمُ وَالْفِعْلُ وَالْحَرْفُ</p>
```

React's `dangerouslySetInnerHTML` renders raw HTML — but if a malicious user managed to inject `<script>alert('xss')</script>`, it would execute JavaScript in the context of your app.

### 12.2 The Solution

```typescript
import DOMPurify from "isomorphic-dompurify";

export function sanitizeHtml(rawHtml: string): string {
    return DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: [
            "p", "span", "strong", "em", "matn", "br", "div", "b", "i",
            "section", "h2", "h3", "article"
        ],
        ALLOWED_ATTR: ["class", "id", "dir"],
    });
}
```

**What DOMPurify removes:**
- `<script>`, `<iframe>`, `<object>`, `<embed>` — all executable content
- `onclick`, `onerror`, `onload`, `onmouseover` — all event handlers
- `javascript:` URLs in `href`/`src`
- Any tag not in `ALLOWED_TAGS`
- Any attribute not in `ALLOWED_ATTR`

**Why `isomorphic-dompurify`?** Next.js renders on the server first (SSR). The regular `dompurify` library requires `window` and `document`, which don't exist in Node.js. `isomorphic-dompurify` provides a fallback implementation for server-side rendering.

**Note:** The `ALLOWED_TAGS` list was extended to include `<matn>` — a non-standard tag commonly used in Arabic Islamic texts to denote the core text (متن).

### 12.3 SafeHtml Component

```typescript
export function SafeHtml({ html, className }: SafeHtmlProps) {
    const clean = sanitizeHtml(html);
    return (
        <p className={cn("arabic-content text-pretty", className)}
            dangerouslySetInnerHTML={{ __html: clean }}
        />
    );
}
```

**Usage in result cards:**
```tsx
<SafeHtml html={result.original_text} className="text-xl leading-loose" />
```

---

## 13. QA & Testing Infrastructure

### 13.1 Test Suite Overview

| File | Type | What It Tests |
|------|------|---------------|
| `test_api.py` | Integration | Basic index + search round-trip |
| `test_pagination.py` | Integration | Pagination parameters, audio field presence |
| `verify_search.py` | Unit (offline) | FTS5 query matching against normalized text |
| `qa_edge_tests.py` | E2E | Empty/injection inputs, diacritic matching, payload limits |
| `qa_integrity_test.py` | E2E | Full lifecycle: flush → upload → search → nuke |
| `qa_media_sync.py` | E2E + Unit | SRT parsing, pagination correctness, boundary cases |
| `diagnose_audio_pipeline.py` | Diagnostic | Audio URL encoding, static file serving investigation |

### 13.2 qa_edge_tests.py — Edge Cases

**Group A — Empty / Junk / FTS5 Injection Inputs:**
```python
EMPTY_INPUTS = [
    ("whitespace_only",      "   "),
    ("tabs_and_newlines",    "\t\n  \r\n"),
    ("mixed_arabic_punct",   "،؛؟!."),
]

INJECTION_INPUTS = [
    ("fts5_star",            "*"),
    ("sql_or_1_eq_1",        "OR 1=1"),
    ("fts5_near_op",         "NEAR(foo bar, 5)"),
    ("fts5_quote_break",     '"; DROP TABLE ... --'),
]
```

**Expected: All return `200 OK` with `results: []`** — not crashes, not SQL errors, not FTS5 errors.

**Group B — Diacritic Cross-Matching:**
```
1. Index "كتاب" (bare, no diacritics)
2. Search "كِتَاب" (with diacritics) → MUST find the row
3. Search "كِتَابٌ" (full tashkeel) → MUST find the row
4. Index "كِتَاب" then search "كتاب" → MUST find the row (reverse direction)
```

**Group C — Payload Limits:**
| Input | Expected Status | Why |
|-------|----------------|-----|
| 250-character query | `422` | Exceeds `max_length=200` |
| Empty query (`q=`) | `422` | Violates `min_length=1` |
| 200-character query | `200` | At the boundary — should work |
| 201-character query | `422` | One character over the limit |
| `page=0` | `422` | Violates `ge=1` |
| `page_size=0` | `422` | Violates `ge=1` |
| `page_size=201` | `422` | Violates `le=200` |

### 13.3 qa_integrity_test.py — Full System Audit

**Part 1: Schema Verification**
- Check `lectures` table exists
- Check `arabic_text_shards_fts` FTS5 table exists
- Check all 3 triggers exist (`after_lectures_insert/delete/update`)
- Check all 9 columns present in `lectures`
- Verify FTS row count = lectures row count (synced)

**Part 2: Arabic Truth Test**
```python
# The key test:
diacritized = "الْحَمْدُ لِلَّهِ"
# Search for: الحمد → MUST find it
# Search for: لله → MUST find it (handles alef variants)
# Search for: الْحَمْدُ → MUST find it (diacritized query)
# Verify: original_text preserves الْحَمْدُ (diacritics NOT stripped)
```

**Part 3: Full-Cycle QA**
```
FLUSH → verify 0 rows
UPLOAD amr21 (تقريب العلم, الشيخ صالح العصيمي, 1445)
UPLOAD الرسالة التبوكية لابن القيم
VERIFY assets count (≥2 MP3s, ≥2 SRTs)
VERIFY DB row count (hundreds for 2 SRTs)
SEARCH "الله" → has results
SEARCH "الحمد" → has results
SEARCH "التبوكية" → has results
VERIFY audio_url values exist
VERIFY original_text contains diacritics
```

**Part 4: URL Encoding Round-Trip**
```
"السلام عليكم" → URL encode → search → response.query == "السلام عليكم" ✓
"آية (الكرسي) + كتاب؟" → 200 OK ✓ (special characters work)
audio_url starts with "/media/" → properly encoded ✓
```

**Stress Nuke Test:**
```
1. FLUSH again
2. SEARCH immediately → 200 OK, 0 results (doesn't crash)
3. Verify tables and triggers survived
4. INDEX a new shard → SEARCH → finds it (FTS still works after flush)
```

### 13.4 qa_media_sync.py — SRT + Pagination

**Group A — SRT Timestamp Conversion (pure unit tests):**
```python
SRT_CASES = [
    ("00:00:00,000",      0.0),
    ("00:00:01,000",      1.0),
    ("00:01:25,500",     85.5),      # Canonical example
    ("01:23:45,678",   5025.678),
    ("23:59:59,999",  86399.999),
]

SRT_BAD_CASES = [
    ("",                    "empty string"),
    ("not a timestamp",     "garbage"),
    ("00:00:00",            "missing milliseconds"),
    ("00:00:00,00",         "2-digit ms"),
]
```

**Group B — Pagination:**
```
1. Seed 16 synthetic shards
2. page=1, page_size=5 → 5 results, page=1, page_size=5
3. page=2, page_size=5 → 5 results, page=2, page_size=5
4. Page 1 and Page 2 share NO IDs (disjoint)
5. total_results is consistent across pages (≥16)
6. page=999 → 200 OK, results=[]
7. page=0 → 422
8. page_size=0 → 422
9. page_size=201 → 422
10. page_size=200 (boundary) → 200
```

### 13.5 Testing Philosophy

All E2E tests follow the same pattern:
```
1. Spawn uvicorn as subprocess
2. Poll /docs until ready (or timeout)
3. Run test cases against the live server
4. Terminate uvicorn
5. Exit 0 (all pass) or 1 (any fail)
```

**Why self-contained (no pytest/requests)?**
- Zero dependencies — runs with Python stdlib
- Portable — works on any machine with Python
- CI-friendly — no package installation needed

---

## 14. Audio Pipeline Bug Diagnosis

**Files:** `diagnose_audio_pipeline.py` + `audio_diagnosis_report.md`

### 14.1 The Bug

The database stored absolute Windows paths for `audio_url`:

```
C:\Users\saif_\Desktop\...\Baheth\media\03 الرسالة التبوكية لابن القيم.mp3
```

**Three distinct problems:**

1. **Non-portable path**: Works only on the original machine
2. **Not URL-safe**: Contains spaces, Arabic characters, backslashes
3. **StaticFiles resolution failure**: FastAPI's `/media` mount serves files relative to the `media/` directory — it can't resolve absolute paths

### 14.2 The Diagnosis Script

```python
# The script:
# 1. Queries /search for a result with audio_url
# 2. Constructs three different URLs and tests each against the live server

# Probe 1: Naive — base URL + raw audio_url
#   → http://127.0.0.1:8000/C:\Users\...\file.mp3
#   → 404 Not Found

# Probe 2: Full URL-encoded absolute path
#   → http://127.0.0.1:8000/C%3A%5CUsers%5C...%5Cfile.mp3
#   → 404 Not Found

# Probe 3: Correct — /media/<URL-encoded basename>
#   → http://127.0.0.1:8000/media/03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20...mp3
#   → 200 OK, Content-Type: audio/mpeg, Content-Length: 12392594 ✓
```

### 14.3 The Fix (Applied)

**In `import_lecture.py`:**
```python
# BEFORE:
audio_path = os.path.abspath(sys.argv[1])  # Full path stored
rows.append((..., audio_path, ...))

# AFTER:
audio_path = os.path.abspath(sys.argv[1])
audio_ref = os.path.basename(audio_path)    # Just the filename
rows.append((..., audio_ref, ...))
```

**In `main.py` (search handler):**
```python
# BEFORE:
audio_url=row["audio_url"],  # Raw DB value passed to frontend

# AFTER:
from urllib.parse import quote
raw = row["audio_url"] or ""
audio_url = f"/media/{quote(raw)}" if raw else None,
```

---

## 15. CORS & Integration

**Files:** `main.py` + `integration_guide.md`

### 15.1 What is CORS?

```
Browser at localhost:3000
    │
    ├── fetch("http://127.0.0.1:8000/search?q=الله")
    │   │
    │   └── Browser checks: "Is localhost:3000 allowed to talk to 127.0.0.1:8000?"
    │       │
    │       └── Request headers include: Origin: http://localhost:3000
    │           │
    │           Server responds with:
    │           Access-Control-Allow-Origin: http://localhost:3000  ✓
    │           or
    │           No CORS header → Blocked! 🚫
    │
    └── Only if CORS header matches does the browser allow JavaScript to read the response
```

**The preflight request:** For non-simple requests (POST with JSON, or requests with custom headers), the browser first sends an `OPTIONS` request to check permissions before sending the actual request.

### 15.2 Backend CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- **`allow_origins`**: Which frontend origins are allowed
- **`allow_credentials`**: Whether cookies/auth headers can be sent cross-origin
- **`allow_methods`**: Which HTTP methods are permitted (GET, POST, DELETE, etc.)
- **`allow_headers`**: Which HTTP headers are permitted in the actual request

### 15.3 Static Files CORS

```python
class CORSStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
```

**Why separate CORS for static files?** HTML5 `<audio>` elements also make CORS requests. If the server doesn't respond with the correct `Access-Control-Allow-Origin` header, the browser refuses to play the audio — even for same-origin requests in strict configurations.

### 15.4 Frontend Integration (from integration_guide.md)

**Debounce Hook — `useDebounce.ts`:**
```typescript
export function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState<T>(value);
    useEffect(() => {
        const handler = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(handler);
    }, [value, delay]);
    return debouncedValue;
}
```

**Error handling strategy:**
```typescript
try {
    const response = await fetch(`${backendUrl}/search?q=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error(`Server returned status: ${response.status}`);
    const data: SearchResponse = await response.json();
    setResults(data.results);
} catch (err: any) {
    // "تعذر الاتصال بالخادم الرئيسي. يرجى التحقق من تشغيل الواجهة البرمجية (FastAPI)."
    setError("Server unreachable. Please verify the FastAPI backend is running.");
    setResults([]);
}
```

**DOMPurify Sanitization:**
```typescript
export function sanitizeHtml(rawHtml: string): string {
    return DOMPurify.sanitize(rawHtml, {
        ALLOWED_TAGS: ["p", "span", "strong", "em", "matn", "br", "div", "b", "i"],
        ALLOWED_ATTR: ["class", "id", "dir"],
    });
}
```

---

## 16. End-to-End Flow

### Scenario 1: User Search

```
User types "الرحمن" in search box
    │
    ├── 300ms debounce timer starts
    │   (each keystroke resets the timer)
    │
    ├── debouncedQuery = "الرحمن"
    │
    ├── useEffect triggers runSearchPipeline()
    │
    ├── buildSearchUrl() constructs:
    │   http://127.0.0.1:8000/search
    │   ?q=%D8%A7%D9%84%D8%B1%D8%AD%D9%85%D9%86
    │   &page=1&page_size=10
    │
    ├── fetch() → FastAPI backend
    │
    ├── FastAPI handler:
    │   │
    │   ├── normalize("الرحمن") → "الرحمن"
    │   ├── _sanitize_fts_query("الرحمن") → '"الرحمن"*'
    │   │
    │   ├── COUNT query:
    │   │   SELECT COUNT(*) FROM lectures
    │   │   JOIN arabic_text_shards_fts ON lectures.id = fts.rowid
    │   │   WHERE arabic_text_shards_fts MATCH '"الرحمن"*'
    │   │
    │   ├── DATA query:
    │   │   SELECT lectures.*, fts.rank
    │   │   FROM lectures JOIN fts ON lectures.id = fts.rowid
    │   │   WHERE fts MATCH '"الرحمن"*'
    │   │   ORDER BY fts.rank
    │   │   LIMIT 10 OFFSET 0
    │   │
    │   ├── For each row: transform audio_url
    │   │   "03 الرسالة التبوكية لابن القيم.mp3"
    │   │   → "/media/03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20...mp3"
    │   │
    │   └── Return SearchResponse JSON
    │
    ├── React receives response
    │   ├── setResults(data.results)
    │   ├── setActiveResult(data.results[0])
    │   ├── setDurationMs(...)
    │   └── setSubmitted("الرحمن")
    │
    ├── Audio effect fires:
    │   audioRef.current.src = "http://127.0.0.1:8000/media/03%20...mp3"
    │   audioRef.current.currentTime = result.start_time
    │   audioRef.current.play()
    │
    └── Rendering:
        ├── LEFT PANE: Active result text (with diacritics, HTML preserved)
        ├── RIGHT PANE: Result list with rankings
        ├── BOTTOM LEFT: Audio player at correct timestamp
        └── METADATA: Book title, sheikh name, year
```

### Scenario 2: Admin Upload

```
Admin activates panel (Konami Code: ↑↑↓↓←→)
    │
    ├── Panel renders as full-screen overlay
    │
    ├── Admin selects MP3 file + SRT file
    │
    ├── Admin fills metadata:
    │   Book Title: "تقريب العلم"
    │   Sheikh Name: "الشيخ صالح العصيمي"
    │   Year: "1445"
    │
    ├── Admin clicks "ENGAGE INGESTION PIPE"
    │
    ├── Frontend builds FormData with files + metadata
    │
    ├── POST to http://127.0.0.1:8000/api/admin/upload
    │
    ├── FastAPI handler:
    │   │
    │   ├── Saves MP3 to media/amr21.mp3
    │   ├── Saves SRT to media/amr21_TokenAnchored_DryRun.srt
    │   │
    │   ├── Spawns subprocess:
    │   │   python import_lecture.py media/amr21.mp3 media/amr21_TokenAnchored_DryRun.srt \
    │   │       "تقريب العلم" "الشيخ صالح العصيمي" "1445"
    │   │
    │   ├── import_lecture.py:
    │   │   │
    │   │   ├── Parses SRT → 150+ blocks
    │   │   ├── Each block: normalize(text) → create DB row
    │   │   ├── INSERT 150+ rows → lectures table
    │   │   ├── Triggers fire → FTS5 synced
    │   │   └── Success message to stderr
    │   │
    │   ├── Captures output
    │   │   "Import: 150 blocks from amr21.mp3 [0.00s → 3600.00s] | تقريب العلم"
    │   │
    │   └── Returns {"status": "SUCCESS", "detail": "..."}
    │
    └── Frontend shows "Injected successfully!"
        ├── Refreshes asset list
        └── New files visible in inventory
```

### Scenario 3: Filtered Search

```
User selects "ابن القيم" from sheikh dropdown
    │
    ├── setSelectedSheikh("ابن القيم")
    ├── setPage(1)  // Reset to first page when filters change
    │
    ├── buildSearchUrl() includes:
    │   sheikh_name=%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85
    │
    ├── FastAPI adds WHERE clause:
    │   AND lectures.sheikh_name = 'ابن القيم'
    │
    └── Results limited to lectures by Ibn al-Qayyim
```

### Scenario 4: Nuclear Reset

```
Admin clicks "NUCLEAR FLUSH DATABASE"
    │
    ├── window.confirm: "WARNING: This deletes all data. Proceed?"
    │   No → Abort
    │   Yes →
    │       ├── window.prompt: "Type 'FLUSH' to confirm:"
    │       │   Wrong input → "Mismatch. Aborted."
    │       │   "FLUSH" →
    │       │       ├── POST http://127.0.0.1:8000/api/admin/flush
    │       │       │
    │       │       ├── FastAPI handler:
    │       │       │   ├── Drop ALL tables
    │       │       │   ├── Delete entire media/ directory
    │       │       │   ├── Recreate media/ empty
    │       │       │   ├── Run init_db() → new tables, FTS, triggers
    │       │       │   └── Return {"status": "CLEARED", "detail": "..."}
    │       │       │
    │       │       └── window.location.reload()
    │       │
    │       └── Back to clean slate
```

---

## 17. Glossary for Junior Devs

### Backend Concepts

| Term | Definition | Why It Matters |
|------|-----------|----------------|
| **ASGI** | Async Server Gateway Interface — the modern Python standard for async web apps | FastAPI is an ASGI framework. Uvicorn is an ASGI server. Together they handle thousands of concurrent connections. |
| **BM25** | Okapi BM25 — the ranking function used by FTS5 to score search results | Lower rank = better match. Negative values are normal. `ORDER BY rank` sorts most relevant first. |
| **CORS** | Cross-Origin Resource Sharing — browser security mechanism | Without it, `localhost:3000` can't fetch from `127.0.0.1:8000` |
| **FTS5** | Full-Text Search v5 — SQLite's built-in search engine | Tokenizes text, builds inverted index, supports prefix search, BM25 ranking |
| **Inverted Index** | A data structure mapping each word to the list of documents containing it | Enables instant lookup: `الرحمن` → [row 42, row 87, row 103] |
| **Normalization** | Converting text to a canonical form | Makes search diacritic- and spelling-agnostic |
| **Pydantic** | Python library for data validation using type annotations | Auto-validates API inputs/outputs, generates Swagger docs |
| **PRAGMA** | SQLite-specific configuration directives | `WAL` for performance, `foreign_keys=ON` for integrity |
| **Subprocess** | Spawning a new OS-level process | Used to run `import_lecture.py` as a separate Python process |
| **WAL** | Write-Ahead Logging — SQLite journal mode | Enables concurrent reads while writing, much faster than default |
| **Virtual Table** | A table that behaves like a real table but computes its data on-the-fly | FTS5 is a virtual table — it doesn't store data like a normal table |

### Frontend Concepts

| Term | Definition | Why It Matters |
|------|-----------|----------------|
| **App Router** | Next.js 13+ routing system based on file system | `app/page.tsx` = route `/`, `app/about/page.tsx` = route `/about` |
| **CLS** | Cumulative Layout Shift — Core Web Vital | Fixed by pre-loading fonts with `next/font` |
| **Debouncing** | Delaying execution until after input stops | Prevents spamming the backend on every keystroke |
| **DOMPurify** | HTML sanitization library | Prevents XSS attacks when rendering user-generated HTML |
| **Fast Refresh** | Next.js dev feature preserving state during edits | Instant feedback when editing React components |
| **isomorphic-dompurify** | Server-compatible version of DOMPurify | Works in Node.js (SSR) and browsers |
| **Konami Code** | ↑↑↓↓←→ — classic video game cheat code | Used as a fun "secret" to access the admin panel |
| **Lucide** | Open-source icon library | Consistent, clean icons throughout the UI |
| **Memoization** | Caching function results based on inputs | `useCallback`, `useMemo` prevent unnecessary re-renders |
| **Preflight Request** | OPTIONS HTTP request sent before cross-origin requests | Browser checks CORS permissions before sending the actual request |
| **RTL** | Right-to-Left text direction | Essential for Arabic UI layout |
| **SSR** | Server-Side Rendering — pages rendered on the server | Better SEO, faster initial load, works without JavaScript |
| **Tailwind CSS** | Utility-first CSS framework | Rapid styling without writing custom CSS |
| **URLSearchParams** | Browser API for building query strings | Auto-encodes Arabic characters, handles `?` and `&` correctly |
| **XSS** | Cross-Site Scripting — injecting malicious JavaScript | Prevented by DOMPurify sanitization |

### Arabic Text Concepts

| Term | Arabic | Meaning | Example |
|------|--------|---------|---------|
| **Tashkeel** | تشكيل | Diacritic marks indicating short vowels | `كِتَابٌ` (the marks are tashkeel) |
| **Fatha** | فتحة | /a/ vowel mark | َ |
| **Damma** | ضمة | /u/ vowel mark | ُ |
| **Kasra** | كسرة | /i/ vowel mark | ِ |
| **Shadda** | شدة | Consonant gemination (doubling) | ّ |
| **Sukun** | سكون | No vowel | ْ |
| **Alef Maqsura** | ألف مقصورة | Final ya-shaped alef | ى |
| **Alef Wasla** | ألف الوصل | Connecting alef | ٱ |
| **Ta Marbuta** | تاء مربوطة | Feminine ending (sounds like "h" in pausa) | ة |
| **Tatweel** | تطويل | Horizontal letter elongation | ـ |
| **Matn** | متن | Core text (in Islamic scholarly works) | `<matn>...</matn>` |

---

*This guide was generated from the complete source code analysis of the Baheth (باحث) project — a full-stack Arabic search engine with synchronized audio playback, built with FastAPI + SQLite FTS5 + Next.js 16 + React 19 + Tailwind CSS v4.*
