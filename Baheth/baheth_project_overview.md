# Baheth (باحث) — Complete Project Reference Guide

This document is a comprehensive, self-contained technical specification and architecture guide for the **Baheth** project. It contains sufficient detail (schemas, routes, business logic, constraints) for an AI agent or developer to understand, maintain, or refactor the codebase without inspecting raw files.

---

## 1. Project Directory Structure

```text
Baheth/
├── main.py                     # Backend entry point, search router, CORS middleware
├── database.py                 # SQLite WAL connection, table schemas, FTS5 creation, triggers
├── normalizer.py               # Arabic text normalization mapping & rules
├── admin_routes.py             # Dual ingestion uploading, asset query/deletion, nuclear database reset
├── models.py                   # Pydantic schema declarations
├── import_lecture.py           # SRT parsing CLI subprocess utility
├── diagnose_audio_pipeline.py  # Diagnostic check for URL encoding and StaticFiles routes
├── arabic-search-interface/    # Next.js App Router root
│   ├── app/
│   │   ├── layout.tsx          # Font optimization (Cairo/Amiri), dir="rtl" setup
│   │   └── page.tsx            # Main Search UI, state machine, debounced search pipelines
│   ├── components/
│   │   ├── audio-player.tsx    # Audio control wrapper (fastSeek, time cushions, Webkit/Moz styling)
│   │   └── AdminControlPanel.tsx # Secret dashboard overlay
│   └── hooks/
│       └── useAdminCombo.ts    # Up+Left+Right simultaneous chord and Konami code sequence
├── qa_integrity_test.py        # Lifecycle integration tests
├── qa_edge_tests.py           # Input sanitization, SQL/FTS injection, and diacritic tests
└── qa_media_sync.py            # SRT timestamp translation and pagination tests
```

---

## 2. Database Layer (`database.py`)

### A. Connection Setup
- Uses SQLite 3.
- Runs in **WAL (Write-Ahead Logging)** mode (`PRAGMA journal_mode=WAL`) for concurrent reading and writing.
- Enforces foreign key constraints (`PRAGMA foreign_keys=ON`).

### B. Schemas

#### 1. Primary Table: `lectures`
```sql
CREATE TABLE lectures (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    text_content    TEXT    NOT NULL,     -- Original Arabic text (contains diacritics / formatting HTML)
    normalized_text TEXT    NOT NULL,     -- Normalized text stripped of diacritics (for FTS5 lookup)
    audio_url       TEXT    DEFAULT NULL, -- Basename of the audio file (e.g. "lecture.mp3")
    start_time      REAL    DEFAULT NULL, -- Start timestamp in seconds (float)
    end_time        REAL    DEFAULT NULL, -- End timestamp in seconds (float)
    book_title      TEXT    DEFAULT NULL, -- Book/source metadata filter
    sheikh_name     TEXT    DEFAULT NULL, -- Sheikh/speaker metadata filter
    year_date       TEXT    DEFAULT NULL  -- Date/year metadata filter
);
```

#### 2. Virtual Index Table: `arabic_text_shards_fts`
```sql
CREATE VIRTUAL TABLE arabic_text_shards_fts USING fts5(
    normalized_text,
    book_title,
    sheikh_name
);
```

### C. Synchronization Triggers
Automatic synchronization between tables is enforced by three database triggers:

1. **Insert**:
   ```sql
   CREATE TRIGGER after_lectures_insert AFTER INSERT ON lectures
   BEGIN
       INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
       VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
   END;
   ```
2. **Delete**:
   ```sql
   CREATE TRIGGER after_lectures_delete AFTER DELETE ON lectures
   BEGIN
       INSERT INTO arabic_text_shards_fts(arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name)
       VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
   END;
   ```
3. **Update**:
   ```sql
   CREATE TRIGGER after_lectures_update AFTER UPDATE ON lectures
   BEGIN
       INSERT INTO arabic_text_shards_fts(arabic_text_shards_fts, rowid, normalized_text, book_title, sheikh_name)
       VALUES('delete', old.id, old.normalized_text, old.book_title, old.sheikh_name);
       INSERT INTO arabic_text_shards_fts(rowid, normalized_text, book_title, sheikh_name)
       VALUES (new.id, new.normalized_text, new.book_title, new.sheikh_name);
   END;
   ```

---

## 3. Arabic Normalization Pipeline (`normalizer.py`)

To ensure robust search matches regardless of diacritics or alternate spelling variants, both search queries and incoming text shards are normalized using the following sequence:

1. **HTML Unescape**: Converts HTML entities (e.g. `&amp;` → `&`, `&lt;` → `<`).
2. **HTML Tag Stripping**: Removes structural HTML markup.
3. **Tatweel (Kashida) Removal**: Strips instances of `\u0640` (`ـ`).
4. **Diacritics (Tashkeel) Removal**: Translates the following unicode characters to `None`:
   - Fathatayn (`\u064B` / `ً`), Dammatayn (`\u064C` / `ٌ`), Kasratayn (`\u064D` / `ٍ`)
   - Fatha (`\u064E` / `َ`), Damma (`\u064F` / `ُ`), Kasra (`\u0650` / `ِ`)
   - Shadda (`\u0651` / `ّ`), Sukun (`\u0652` / `ْ`)
5. **Character Unification**:
   - `أ`, `إ`, `آ`, `ٱ` (Hamzated Alefs) → `ا` (Bare Alef, `\u0627`)
   - `ة` (Ta Marbuta, `\u0629`) → `ه` (Ha, `\u0647`)
   - `ى` (Alef Maqsura, `\u0649`) → `ي` (Ya, `\u064A`)
6. **Whitespace Consolidation**: Collapses multiple whitespace characters into a single space and trims edges.

---

## 4. API Specification

### A. Core Search
- **Route**: `GET /search`
- **Query Params**:
  - `q`: String (min length 1, max length 200)
  - `page`: Integer (default 1, minimum 1)
  - `page_size`: Integer (default 50, ge 1, le 200)
  - `book_title` (Optional)
  - `sheikh_name` (Optional)
  - `year_date` (Optional)
- **Logic**:
  1. Normalizes `q`.
  2. Sanitizes the query against FTS injection via regex `[^\w\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s]`, then wraps in quotes: `"normalized_query"*` (prefix matching).
  3. Returns ranked matches based on BM25 scores (lower score is better).
  4. Audio URLs are transformed on the fly from simple basenames to safe `/media/<urlencoded_filename>` paths.

### B. Index Shards
- **Route**: `POST /index-shards`
- **Request Body**:
  ```json
  {
    "shards": [
      { "text": "Original text with diacritics" }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "indexed_count": 1,
    "ids": [123]
  }
  ```

### C. Dropdown Filters Options
- **Route**: `GET /api/filters`
- **Response**: Distinct lists of non-empty `book_titles`, `sheikh_names`, and `year_dates` ordered alphabetically.

### D. Admin Upload
- **Route**: `POST /api/admin/upload` (Form Data)
- **Fields**:
  - `mp3`: File (binary)
  - `srt`: File (binary)
  - `book_title`: String
  - `sheikh_name`: String
  - `year_date`: String
  - `overwrite`: Boolean (default `false`)
- **Processing**:
  1. Checks for file name collisions. Returns `409 Conflict` if target exists and `overwrite` is false.
  2. Saves files under `media/`.
  3. Launches subprocess `import_lecture.py` to parse SRT and insert data.

### E. Database Flush
- **Route**: `POST /api/admin/flush`
- **Logic**: Drops all tables, removes files in `media/`, and calls `init_db()` to restore default schemas, FTS tables, and triggers.

---

## 5. SRT Ingestion Pipeline (`import_lecture.py`)

- **SRT Timestamp Parsing**: Converts format `HH:MM:SS,mmm` or `HH:MM:SS.mmm` to raw float seconds.
  ```python
  # Equation: Hours * 3600 + Minutes * 60 + Seconds + Milliseconds / 1000
  ```
- **SRT Text Processing**: Uses `re.DOTALL` to parse sequence indices, timestamps, and multi-line subtitle texts:
  ```python
  SRT_BLOCK = re.compile(
      r"(?P<index>\d+)\s*\n"
      r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
      r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*\n"
      r"(?P<text>.+?)(?:\n\n|\Z)",
      re.DOTALL
  )
  ```
- **Ingestion Execution**: Reads parsed blocks, normalizes subtitle texts, constructs metadata, and does an `executemany` insert into the `lectures` table.

---

## 6. Critical Bugs and Design Decisions Resolved

### The Absolute Path Audio URL Bug
- **Issue**: Originally, the database stored absolute local Windows paths for the audio files (e.g. `C:\Users\...\media\file.mp3`). This made the database non-portable across machines and caused FastAPI static file routes `/media` to return `404 Not Found` because it was expecting filenames relative to the `media/` directory.
- **Solution**:
  1. `import_lecture.py` was fixed to write only the basename of the files (`os.path.basename(audio_path)`) to the database.
  2. `main.py` was updated to urlencode the filename basenames when building paths (e.g., converting spaces and Arabic characters to percent encoding) using `urllib.parse.quote()`.
  3. Added `CORSStaticFiles` to override FastAPI's `StaticFiles` response header, adding `Access-Control-Allow-Origin: *` to prevent CORS issues in browsers during audio play streams.

---

## 7. Frontend User Interface Layout & Logic

- **RTL Support**: Setup with `<html lang="ar" dir="rtl">` using optimized Google fonts (Cairo for UI elements, Amiri for Arabic script/text rendering).
- **Core Panels layout**:
  - **Right Panel (1/3 Width)**: Search bar, filter inputs, matching results cards showing snippet details and BM25 rank scores. Offers a "Load More" button which appends the next paginated items.
  - **Left Panel (2/3 Width)**: Reading pane displaying the active result's full diacritized text (rendered via a DOMPurify sanitization wrapper), and the custom audio player widget.
- **Audio Context Cushion**: When a user selects a search result, the audio player seeks to the matched start time but subtracts **2 seconds** (`Math.max(0, startTime - 2)`) to give the listener preceding verbal context.
- **Admin Combo Key Chord**: Admin control panel modal is opened by holding down `ArrowUp + ArrowLeft + ArrowRight` together (Secure Access Signal) followed by typing the Konami Code sequence: `Up, Up, Down, Down, Left, Right`.
