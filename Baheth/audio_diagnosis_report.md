==============================================================================
  AUDIO PIPELINE DIAGNOSTIC — Phase 2
  Target: http://127.0.0.1:8000
  CWD:    C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Baheth
==============================================================================

[1] DATABASE PAYLOAD — what is actually stored in audio_url?
    (probing with a SAMPLE_QUERY against /search)
    Raw value (Python repr):  'C:\\Users\\saif_\\Desktop\\downs\\Currently\\Daily\\Lectures\\ANtiGrav\\Baheth\\media\\03 الرسالة التبوكية لابن القيم.mp3'
    Length: 110 chars
    Contains backslashes? False
    Contains spaces?       True
    Contains non-ASCII?    True
    Starts with C:\ ?      True

[2] URL PERCENT-ENCODING CHECK — what the frontend sees vs what it should see
    Raw from /search JSON (copy into <audio src> verbatim):
      C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Baheth\media\03 الرسالة التبوكية لابن القيم.mp3

    After proper URL-encoding (what <audio src> needs):
      C%3A%5CUsers%5Csaif_%5CDesktop%5Cdowns%5CCurrently%5CDaily%5CLectures%5CANtiGrav%5CBaheth%5Cmedia%5C03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3

    The raw value contains:
      - backslashes:    False
      - spaces:         True
      - non-ASCII:      True
    None of which are URL-safe.

[3] LIVE SERVER PROBE — what FastAPI actually returns
    [server up pid=5032]

    [3a] NAIVE: base + raw audio_url (client auto-encodes spaces)
      URL sent: http://127.0.0.1:8000/C:%5CUsers%5Csaif_%5CDesktop%5Cdowns%5CCurrently%5CDaily%5CLectures%5CANtiGrav%5CBaheth%5Cmedia%5C03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3
      HTTP:     404
      CType:    application/json
      Body:     '{"detail":"Not Found"}'

    [3b] FULL-ENCODE absolute path
      URL sent: http://127.0.0.1:8000/C%3A%5CUsers%5Csaif_%5CDesktop%5Cdowns%5CCurrently%5CDaily%5CLectures%5CANtiGrav%5CBaheth%5Cmedia%5C03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3
      HTTP:     404
      CType:    application/json
      Body:     '{"detail":"Not Found"}'

    [3c] CORRECT: /media/<URL-encoded basename>
      URL sent: http://127.0.0.1:8000/media/03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3
      HTTP:     200
      CType:    audio/mpeg
      Body:     '<12392594 bytes of audio/mpeg>'
      HEAD:     200  Content-Length: 12392594  CType: audio/mpeg

    [server torn down]

[4] FILESYSTEM RESOLUTION — where the file actually lives
    audio_url as given:                  C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Baheth\media\03 الرسالة التبوكية لابن القيم.mp3
    os.path.isfile(audio_url):           True

==============================================================================
  DEVELOPER BUG REPORT — for Opencode Zen
==============================================================================

## 🚨 AUDIO PIPELINE BREAKDOWN REPORT (For Opencode Zen)

### 1. Core Root Cause

**The `audio_url` column stores an absolute Windows filesystem path,
not a URL.** That value is doubly broken: FastAPI's
`StaticFiles(directory="media")` mount at `/media` serves paths
**relative to the `media/` directory** under CWD — it cannot resolve
an absolute path like `C:\Users\...\file.mp3`. The path also contains
backslashes, spaces, and Arabic letters, none of which are URL-safe,
so even if the static mount were able to resolve it, the browser/HTTP
client would mangle it on the wire.

The frontend is presumably doing one of:
- `<audio src={result.audio_url}>` — the browser strips the backslashes
  and either 404s or refuses to send the request.
- `axios.get(\`/media/${audio_url}\`)` — same 404, because the absolute
  path is prepended to the mount's URL prefix.

**The fix is in the data model, not the frontend:** `audio_url` should
hold a path that is (a) portable across machines, (b) URL-safe, and
(c) directly servable by the existing `/media` mount. The simplest
representation is the **basename** of the audio file (e.g.
`03 الرسالة التبوكية لابن القيم.mp3`), which the API exposes as
`/media/<URL-encoded basename>` and FastAPI's static mount serves
verbatim.

### 2. Runtime Diagnostic Evidence

- **Database Payload Value:** `C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Baheth\media\03 الرسالة التبوكية لابن القيم.mp3`
- **Constructed Frontend URL (naive, the bug):** `http://127.0.0.1:8000/C:%5CUsers%5Csaif_%5CDesktop%5Cdowns%5CCurrently%5CDaily%5CLectures%5CANtiGrav%5CBaheth%5Cmedia%5C03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3`
- **Constructed Frontend URL (correct, after fix):** `http://127.0.0.1:8000/media/03%20%D8%A7%D9%84%D8%B1%D8%B3%D8%A7%D9%84%D8%A9%20%D8%A7%D9%84%D8%AA%D8%A8%D9%88%D9%83%D9%8A%D8%A9%20%D9%84%D8%A7%D8%A8%D9%86%20%D8%A7%D9%84%D9%82%D9%8A%D9%85.mp3`
- **FastAPI HTTP Server Response Code (naive):** 404
- **Content-Type Header Checked (naive):** `application/json`
- **FastAPI HTTP Server Response Code (correct URL):** 200
- **Content-Type Header Checked (correct URL):** `audio/mpeg`
- **Content-Length on correct URL:** `Content-Length=12392594`

**Probe matrix (HTTP / Content-Type / verdict):**

| Construction                                | HTTP | Content-Type    | Serves file? |
|---------------------------------------------|------|-----------------|--------------|
| `base + raw audio_url` (no encoding)        | 404   | `application/json` | No — 404    |
| `base + full-URL-encoded abs path`          | 404   | `application/json` | No — 404    |
| `/media/<URL-encoded basename>` (correct)   | 200   | `audio/mpeg` | **Yes** ✅ |

### 3. Exact Code Fix Instructions

**Fix in `import_lecture.py` — store the basename, not the absolute path:**

```python
# BEFORE (lines 62, 87):
audio_path = os.path.abspath(sys.argv[1])   # full Windows path stored in DB
...
rows.append((b["text"], normalize(b["text"]), audio_path, b["start"], b["end"]))
```

```python
# AFTER:
audio_path = os.path.abspath(sys.argv[1])
audio_ref = os.path.basename(audio_path)   # <-- ADD: portable, URL-safe ref
...
rows.append((b["text"], normalize(b["text"]), audio_ref, b["start"], b["end"]))
```

**Fix in `main.py` `/search` handler — build a real URL the frontend can use:**

```python
# BEFORE (line ~123 in main.py):
audio_url=row["audio_url"],   # passes raw DB value straight to the client
```

```python
# AFTER:
# audio_url is now the basename; build a real, URL-safe URL the
# browser can fetch directly. Filename is percent-encoded so spaces
# and Arabic letters are safe in <audio src> and HTTP requests.
from urllib.parse import quote
raw = row["audio_url"] or ""
audio_url = f"/media/{quote(raw)}" if raw else None,
```

**Migration for existing rows (run once, then drop):**

```sql
UPDATE arabic_text_shards
   SET audio_url = SUBSTR(audio_url, LENGTH(audio_url) - INSTR(REVERSE(audio_url), '\') + 2)
 WHERE audio_url LIKE 'C:%' AND audio_url LIKE '%.mp3';
```

(Or in Python: `audio_url = os.path.basename(audio_url)` for each row.)

**Why this is the right fix:**
- Portable — `03 الرسالة التبوكية لابن القيم.mp3` is the same on every machine.
- URL-safe — when the API wraps it in `/media/<quote(basename)>`, browsers and
  HTTP clients can request it without ambiguity.
- Served directly by the existing `app.mount("/media", StaticFiles(...))` —
  no new endpoints, no new mount configuration.
- One-line change in each of two files; one SQL update for the existing 1817 rows.
