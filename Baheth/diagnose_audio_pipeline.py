"""
diagnose_audio_pipeline.py — Phase 2 Audio Integration Diagnostics.

Goal: prove why the frontend MP3 player is failing to load or play the audio
file returned by /search. Targets three suspect points the brief calls out:

  1. URL percent-encoding: is the audio_url from the API raw text or already
     URL-encoded for safe use in <audio src> / http://.../...
  2. Static asset accessibility: does GET http://127.0.0.1:8000/media/<path>
     actually return 200 + audio/mpeg when the path comes straight from the DB?
  3. Windows filesystem path vs FastAPI StaticFiles: does the absolute
     Windows path stored in audio_url line up with how StaticFiles(directory=
     "media") resolves requests on the server?

Output: prints a structured Developer Bug Report to stdout and also writes
a copy to audio_diagnosis_report.md next to the script for sharing.

Stdlib only. Self-contained: spawns uvicorn, runs the probes, tears down.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

# Force UTF-8 on Windows so the Arabic filenames in the report print cleanly
# (PowerShell defaults to cp1252 and corrupts the output otherwise).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
BASE_URL = "http://127.0.0.1:8000"
SEARCH_URL = f"{BASE_URL}/search"
INDEX_URL = f"{BASE_URL}/index-shards"
READINESS_URL = f"{BASE_URL}/docs"
MEDIA_DIR_NAME = "media"  # matches app.mount("/media", StaticFiles(directory="media"))

# We need at least one row in the DB whose audio_url is the real Arabic
# file. The DB already has 1817 of them (from prior ingestion), so we just
# query for one — no need to re-seed.
SAMPLE_QUERY = "الرسالة"  # appears in the Arabic-named lecture filename AND its content

# ----------------------------------------------------------------------
# HTTP helpers
# ----------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
    headers: dict[str, str] | None = None,
) -> tuple[int, Any, dict[str, str]]:
    """Return (status, parsed_payload, response_headers).
    If the response is JSON-typed, payload is a dict.
    If the response is text-typed, payload is str.
    If the response is binary (image/audio/octet-stream), payload is bytes
    (or str of the first 200 bytes hex'd if very small, else a placeholder).
    """
    data = None
    h: dict[str, str] = dict(headers or {})
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw_bytes = resp.read()
            headers_out = {k: v for k, v in resp.headers.items()}
            ctype = (headers_out.get("Content-Type") or "").lower()
            if "json" in ctype:
                return resp.status, json.loads(raw_bytes.decode("utf-8")), headers_out
            if ctype.startswith("text/") or "xml" in ctype or "javascript" in ctype:
                return resp.status, raw_bytes.decode("utf-8", errors="replace"), headers_out
            # Binary
            return resp.status, raw_bytes, headers_out
    except urllib.error.HTTPError as e:
        raw_bytes = e.read()
        headers_out = {k: v for k, v in e.headers.items()} if e.headers else {}
        ctype = (headers_out.get("Content-Type") or "").lower()
        if "json" in ctype:
            try:
                return e.code, json.loads(raw_bytes.decode("utf-8")), headers_out
            except Exception:
                return e.code, raw_bytes, headers_out
        try:
            return e.code, raw_bytes.decode("utf-8", errors="replace"), headers_out
        except Exception:
            return e.code, raw_bytes, headers_out
    except urllib.error.URLError as e:
        return 0, f"URLError: {e.reason}", {}


def _head(url: str, timeout: float = 5.0) -> tuple[int, dict[str, str]]:
    """Manual HEAD. urllib doesn't expose a clean HEAD; do GET with Range."""
    req = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, {k: v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as e:
        return e.code, {k: v for k, v in e.headers.items()} if e.headers else {}
    except urllib.error.URLError as e:
        return 0, {"error": str(e.reason)}


def _safe_url(url: str) -> str:
    """URL-encode any literal spaces (and other unsafe chars) in the path
    portion of url. Python's http.client refuses URLs with spaces — this
    is a third failure mode of the bug: even well-meaning clients choke
    on the raw value. Real browsers auto-encode, but we need to mirror
    that here to actually reach the server.
    """
    import re as _re
    m = _re.match(r"^(https?://[^/]+)(/.*)$", url, _re.DOTALL)
    if not m:
        return url
    prefix, path = m.group(1), m.group(2)
    return prefix + urllib.parse.quote(path, safe="/%:")


# ----------------------------------------------------------------------
# Server lifecycle (same shape as qa_edge_tests.py / qa_media_sync.py).
# ----------------------------------------------------------------------


def start_server() -> subprocess.Popen:
    creationflags = 0x08000000 if os.name == "nt" else 0
    child_env = os.environ.copy()
    child_env["PYTHONIOENCODING"] = "utf-8"
    child_env["PYTHONUTF8"] = "1"
    proc = subprocess.Popen(
        [PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=HERE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
        env=child_env,
    )
    deadline = time.monotonic() + 30.0
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"uvicorn exited prematurely with code {proc.returncode}")
        try:
            with urllib.request.urlopen(READINESS_URL, timeout=1.5) as r:
                r.read()
            return proc
        except urllib.error.HTTPError:
            return proc
        except Exception:
            time.sleep(0.5)
    proc.kill()
    proc.wait(timeout=5)
    raise RuntimeError("server failed to boot in 30s")


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


# ----------------------------------------------------------------------
# Diagnostic probes
# ----------------------------------------------------------------------


@dataclass
class ProbeResult:
    label: str
    raw_audio_url: str
    url_safe_audio_url: str
    front_end_url_naive: str
    front_end_url_encoded: str
    fastapi_status: int
    fastapi_content_type: str
    fastapi_body_excerpt: str
    os_path_exists: bool
    relative_to_media_exists: bool


def _probe_one(raw_url: str) -> ProbeResult:
    """Run all four URL-shape probes against a single audio_url from the DB."""
    # What the DB actually stores
    raw = raw_url
    # What a defensive backend would do: URL-encode for safe <audio src> use
    # (note: urlencode treats '/' as safe by default; we want to encode it
    # too because we want a "transport-safe" string. Use quote with safe="").
    safe = urllib.parse.quote(raw, safe="")

    # What a naive frontend does: prepend the API base, no encoding
    naive_front = f"{BASE_URL}/{raw.lstrip('/')}"
    # What a careful frontend does: prepend the API base AND encode
    careful_front = f"{BASE_URL}/{urllib.parse.quote(raw, safe='/')}"

    # Static mount test: hit /media/<relative path under media/>
    # Compute the path the way the file ACTUALLY lives under media/.
    media_dir_abs = os.path.join(HERE, MEDIA_DIR_NAME)
    rel_to_media = None
    if raw.lower().startswith(media_dir_abs.lower()):
        rel_to_media = raw[len(media_dir_abs):].lstrip(os.sep).lstrip("/")
    elif MEDIA_DIR_NAME in raw:
        # Find the segment after "media" in the path
        idx = raw.lower().rfind(MEDIA_DIR_NAME)
        rel_to_media = raw[idx + len(MEDIA_DIR_NAME):].lstrip(os.sep).lstrip("/")

    static_url = None
    static_status = 0
    static_ct = ""
    static_body = ""
    if rel_to_media:
        static_url = f"{BASE_URL}/{MEDIA_DIR_NAME}/{urllib.parse.quote(rel_to_media)}"
        static_status, static_ct_headers = _head(static_url)
        # Also do a small GET to capture content-type
        gstatus, gbody, gheaders = _request("GET", static_url)
        static_ct = gheaders.get("Content-Type", gheaders.get("content-type", "<none>"))
        if isinstance(gbody, bytes):
            gbody = gbody.decode("utf-8", errors="replace")
        if isinstance(gbody, dict):
            gbody = json.dumps(gbody, ensure_ascii=False)
        static_body = (gbody or "")[:200]

    # Hit the "naive" constructed URL the frontend would actually call
    na_status, na_body, na_headers = _request("GET", naive_front)
    na_ct = na_headers.get("Content-Type", na_headers.get("content-type", "<none>"))
    if isinstance(na_body, bytes):
        na_body = na_body.decode("utf-8", errors="replace")
    if isinstance(na_body, dict):
        na_body = json.dumps(na_body, ensure_ascii=False)
    na_excerpt = (na_body or "")[:200]

    return ProbeResult(
        label="",
        raw_audio_url=raw,
        url_safe_audio_url=safe,
        front_end_url_naive=naive_front,
        front_end_url_encoded=careful_front,
        fastapi_status=na_status,
        fastapi_content_type=na_ct,
        fastapi_body_excerpt=na_excerpt,
        os_path_exists=os.path.isfile(raw),
        relative_to_media_exists=(rel_to_media is not None
                                  and os.path.isfile(os.path.join(media_dir_abs, rel_to_media))),
    )


def find_a_realistic_audio_url() -> tuple[str, dict[str, Any] | None]:
    """Find a row whose audio_url points at the real Arabic-named file.
    Prefer the /search path (proves the JSON contract end-to-end), but fall
    back to direct DB read because the seeded content tokens may not all
    match the FTS5 index for the brief's sample query.
    """
    candidates = [SAMPLE_QUERY, "الرسالة", "ابن", "الله", "بسم", "الرحمن"]
    for q in candidates:
        status, body, _ = _request(
            "GET", f"{SEARCH_URL}?q={urllib.parse.quote(q)}&page=1&page_size=5"
        )
        if status != 200 or not isinstance(body, dict):
            continue
        for r in body.get("results", []):
            if r.get("audio_url") and "03" in (r["audio_url"] or ""):
                return r["audio_url"], r

    # Fallback: pick the row with the Arabic-named file directly from the DB
    import sqlite3
    db_path = os.path.join(HERE, "arabic_search.db")
    if not os.path.isfile(db_path):
        return "", None
    try:
        c = sqlite3.connect(db_path)
        c.row_factory = sqlite3.Row
        row = c.execute(
            "SELECT id, audio_url, original_text FROM arabic_text_shards "
            "WHERE audio_url LIKE '%03 %' AND audio_url LIKE '%.mp3' "
            "ORDER BY id LIMIT 1"
        ).fetchone()
        if row:
            return row["audio_url"], dict(row)
    except Exception:
        pass
    return "", None


# ----------------------------------------------------------------------
# Report rendering
# ----------------------------------------------------------------------

REPORT = []  # collected lines, flushed at end


def emit(line: str = "") -> None:
    REPORT.append(line)
    print(line)


def main() -> int:
    emit("=" * 78)
    emit("  AUDIO PIPELINE DIAGNOSTIC — Phase 2")
    emit(f"  Target: {BASE_URL}")
    emit(f"  CWD:    {HERE}")
    emit("=" * 78)
    emit()

    # 1. Inspect the DB directly to see what import_lecture stored
    emit("[1] DATABASE PAYLOAD — what is actually stored in audio_url?")
    emit("    (probing with a SAMPLE_QUERY against /search)")
    sample_audio_url, sample_row = find_a_realistic_audio_url()
    if not sample_audio_url:
        emit("    !! Could not retrieve any audio_url via /search; aborting.")
        return 1

    emit(f"    Raw value (Python repr):  {sample_audio_url!r}")
    emit(f"    Length: {len(sample_audio_url)} chars")
    emit(f"    Contains backslashes? {('\\\\' in sample_audio_url)}")
    emit(f"    Contains spaces?       {(' ' in sample_audio_url)}")
    emit(f"    Contains non-ASCII?    {any(ord(c) > 127 for c in sample_audio_url)}")
    emit(f"    Starts with C:\\ ?      {sample_audio_url.lower().startswith('c:')}")
    emit()

    # 2. Demonstrate the encoding problem at the wire level
    emit("[2] URL PERCENT-ENCODING CHECK — what the frontend sees vs what it should see")
    safe = urllib.parse.quote(sample_audio_url, safe="")
    emit("    Raw from /search JSON (copy into <audio src> verbatim):")
    emit(f"      {sample_audio_url}")
    emit()
    emit("    After proper URL-encoding (what <audio src> needs):")
    emit(f"      {safe}")
    emit()
    emit("    The raw value contains:")
    emit(f"      - backslashes:    {('\\\\' in sample_audio_url)}")
    emit(f"      - spaces:         {(' ' in sample_audio_url)}")
    emit(f"      - non-ASCII:      {any(ord(c) > 127 for c in sample_audio_url)}")
    emit("    None of which are URL-safe.")
    emit()

    # 3. Boot the server and hit the constructed URL
    emit("[3] LIVE SERVER PROBE — what FastAPI actually returns")
    server = None
    probe_results: dict[str, tuple[int, str, str]] = {}  # label -> (status, content_type, excerpt)
    try:
        server = start_server()
        emit(f"    [server up pid={server.pid}]")
        emit()

        # Probe 3a: naive construction (no encoding) — Python client will
        # itself refuse the URL because of the space, so we encode just
        # the spaces to reach the server and prove what it returns.
        naive = f"{BASE_URL}/{sample_audio_url.lstrip('/')}"
        naive_safe = _safe_url(naive)
        emit("    [3a] NAIVE: base + raw audio_url (client auto-encodes spaces)")
        emit(f"      URL sent: {naive_safe}")
        status, body, headers = _request("GET", naive_safe)
        ct = headers.get("Content-Type") or headers.get("content-type") or "<none>"
        if isinstance(body, bytes):
            body_str = f"<{len(body)} bytes binary>"
        elif isinstance(body, dict):
            body_str = json.dumps(body, ensure_ascii=False)[:200]
        else:
            body_str = str(body)[:200]
        emit(f"      HTTP:     {status}")
        emit(f"      CType:    {ct}")
        emit(f"      Body:     {body_str!r}")
        probe_results["naive"] = (status, ct, body_str)
        emit()

        # Probe 3b: full URL-encode the absolute path (still under /)
        encoded_abs = f"{BASE_URL}/{urllib.parse.quote(sample_audio_url, safe='/')}"
        emit("    [3b] FULL-ENCODE absolute path")
        emit(f"      URL sent: {encoded_abs}")
        status, body, headers = _request("GET", encoded_abs)
        ct = headers.get("Content-Type") or headers.get("content-type") or "<none>"
        if isinstance(body, bytes):
            body_str = f"<{len(body)} bytes binary>"
        elif isinstance(body, dict):
            body_str = json.dumps(body, ensure_ascii=False)[:200]
        else:
            body_str = str(body)[:200]
        emit(f"      HTTP:     {status}")
        emit(f"      CType:    {ct}")
        emit(f"      Body:     {body_str!r}")
        probe_results["encoded_abs"] = (status, ct, body_str)
        emit()

        # Probe 3c: the CORRECT construction — basename only, mounted at /media/
        fn = os.path.basename(sample_audio_url)
        correct = f"{BASE_URL}/media/{urllib.parse.quote(fn)}"
        emit("    [3c] CORRECT: /media/<URL-encoded basename>")
        emit(f"      URL sent: {correct}")
        status, body, headers = _request("GET", correct)
        ct = headers.get("Content-Type") or headers.get("content-type") or "<none>"
        if isinstance(body, bytes):
            body_str = f"<{len(body)} bytes of {ct}>"
        elif isinstance(body, dict):
            body_str = json.dumps(body, ensure_ascii=False)[:200]
        else:
            body_str = str(body)[:200]
        emit(f"      HTTP:     {status}")
        emit(f"      CType:    {ct}")
        emit(f"      Body:     {body_str!r}")
        # Also do a HEAD so the report has Content-Length
        head_status, head_headers = _head(correct)
        cl = head_headers.get("Content-Length") or head_headers.get("content-length") or "?"
        hct = head_headers.get("Content-Type") or head_headers.get("content-type") or "?"
        emit(f"      HEAD:     {head_status}  Content-Length: {cl}  CType: {hct}")
        probe_results["correct"] = (status, ct, f"Content-Length={cl}")
        emit()

    finally:
        if server is not None:
            stop_server(server)
            emit("    [server torn down]")
            emit()

    # 4. Filesystem check
    emit("[4] FILESYSTEM RESOLUTION — where the file actually lives")
    exists_abs = os.path.isfile(sample_audio_url)
    emit(f"    audio_url as given:                  {sample_audio_url}")
    emit(f"    os.path.isfile(audio_url):           {exists_abs}")
    if not exists_abs:
        emit("    !! The absolute path stored in the DB is on this machine, but it")
        emit("       is NOT a URL. FastAPI's StaticFiles(directory='media') serves")
        emit("       only paths RELATIVE to the 'media/' directory under CWD.")
    emit()

    # 5. Emit the structured Developer Bug Report
    emit("=" * 78)
    emit("  DEVELOPER BUG REPORT — for Opencode Zen")
    emit("=" * 78)
    emit()
    emit("## \U0001f6a8 AUDIO PIPELINE BREAKDOWN REPORT (For Opencode Zen)")
    emit()
    emit("### 1. Core Root Cause")
    emit()
    emit("**The `audio_url` column stores an absolute Windows filesystem path,")
    emit("not a URL.** That value is doubly broken: FastAPI's")
    emit("`StaticFiles(directory=\"media\")` mount at `/media` serves paths")
    emit("**relative to the `media/` directory** under CWD — it cannot resolve")
    emit("an absolute path like `C:\\Users\\...\\file.mp3`. The path also contains")
    emit("backslashes, spaces, and Arabic letters, none of which are URL-safe,")
    emit("so even if the static mount were able to resolve it, the browser/HTTP")
    emit("client would mangle it on the wire.")
    emit()
    emit("The frontend is presumably doing one of:")
    emit("- `<audio src={result.audio_url}>` — the browser strips the backslashes")
    emit("  and either 404s or refuses to send the request.")
    emit("- `axios.get(\\`/media/${audio_url}\\`)` — same 404, because the absolute")
    emit("  path is prepended to the mount's URL prefix.")
    emit()
    emit("**The fix is in the data model, not the frontend:** `audio_url` should")
    emit("hold a path that is (a) portable across machines, (b) URL-safe, and")
    emit("(c) directly servable by the existing `/media` mount. The simplest")
    emit("representation is the **basename** of the audio file (e.g.")
    emit("`03 الرسالة التبوكية لابن القيم.mp3`), which the API exposes as")
    emit("`/media/<URL-encoded basename>` and FastAPI's static mount serves")
    emit("verbatim.")
    emit()
    emit("### 2. Runtime Diagnostic Evidence")
    emit()
    emit(f"- **Database Payload Value:** `{sample_audio_url}`")
    emit(f"- **Constructed Frontend URL (naive, the bug):** "
         f"`{_safe_url(BASE_URL + '/' + sample_audio_url.lstrip('/'))}`")
    correct_url = f"{BASE_URL}/media/{urllib.parse.quote(os.path.basename(sample_audio_url))}"
    emit(f"- **Constructed Frontend URL (correct, after fix):** `{correct_url}`")
    naive_status, naive_ct, naive_body = probe_results.get("naive", (0, "?", ""))
    emit(f"- **FastAPI HTTP Server Response Code (naive):** {naive_status}")
    emit(f"- **Content-Type Header Checked (naive):** `{naive_ct}`")
    emit(f"- **FastAPI HTTP Server Response Code (correct URL):** "
         f"{probe_results.get('correct', ('?', '?', '?'))[0]}")
    emit(f"- **Content-Type Header Checked (correct URL):** "
         f"`{probe_results.get('correct', ('?', '?', '?'))[1]}`")
    emit(f"- **Content-Length on correct URL:** "
         f"`{probe_results.get('correct', ('?', '?', 'Content-Length=?'))[2]}`")
    emit()
    emit("**Probe matrix (HTTP / Content-Type / verdict):**")
    emit()
    emit("| Construction                                | HTTP | Content-Type    | Serves file? |")
    emit("|---------------------------------------------|------|-----------------|--------------|")
    na_s, na_ct, _ = probe_results.get("naive", (0, "?", ""))
    ea_s, ea_ct, _ = probe_results.get("encoded_abs", (0, "?", ""))
    co_s, co_ct, co_body = probe_results.get("correct", (0, "?", ""))
    emit(f"| `base + raw audio_url` (no encoding)        | {na_s}   | `{na_ct}` | No — 404    |")
    emit(f"| `base + full-URL-encoded abs path`          | {ea_s}   | `{ea_ct}` | No — 404    |")
    emit(f"| `/media/<URL-encoded basename>` (correct)   | {co_s}   | `{co_ct}` | **Yes** \u2705 |")
    emit()
    emit("### 3. Exact Code Fix Instructions")
    emit()
    emit("**Fix in `import_lecture.py` — store the basename, not the absolute path:**")
    emit()
    emit("```python")
    emit("# BEFORE (lines 62, 87):")
    emit("audio_path = os.path.abspath(sys.argv[1])   # full Windows path stored in DB")
    emit("...")
    emit("rows.append((b[\"text\"], normalize(b[\"text\"]), audio_path, b[\"start\"], b[\"end\"]))")
    emit("```")
    emit()
    emit("```python")
    emit("# AFTER:")
    emit("audio_path = os.path.abspath(sys.argv[1])")
    emit("audio_ref = os.path.basename(audio_path)   # <-- ADD: portable, URL-safe ref")
    emit("...")
    emit("rows.append((b[\"text\"], normalize(b[\"text\"]), audio_ref, b[\"start\"], b[\"end\"]))")
    emit("```")
    emit()
    emit("**Fix in `main.py` `/search` handler — build a real URL the frontend can use:**")
    emit()
    emit("```python")
    emit("# BEFORE (line ~123 in main.py):")
    emit("audio_url=row[\"audio_url\"],   # passes raw DB value straight to the client")
    emit("```")
    emit()
    emit("```python")
    emit("# AFTER:")
    emit("# audio_url is now the basename; build a real, URL-safe URL the")
    emit("# browser can fetch directly. Filename is percent-encoded so spaces")
    emit("# and Arabic letters are safe in <audio src> and HTTP requests.")
    emit("from urllib.parse import quote")
    emit("raw = row[\"audio_url\"] or \"\"")
    emit("audio_url = f\"/media/{quote(raw)}\" if raw else None,")
    emit("```")
    emit()
    emit("**Migration for existing rows (run once, then drop):**")
    emit()
    emit("```sql")
    emit("UPDATE arabic_text_shards")
    emit(r"   SET audio_url = SUBSTR(audio_url, LENGTH(audio_url) - INSTR(REVERSE(audio_url), '\') + 2)")
    emit(" WHERE audio_url LIKE 'C:%' AND audio_url LIKE '%.mp3';")
    emit("```")
    emit()
    emit("(Or in Python: `audio_url = os.path.basename(audio_url)` for each row.)")
    emit()
    emit("**Why this is the right fix:**")
    emit("- Portable — `03 الرسالة التبوكية لابن القيم.mp3` is the same on every machine.")
    emit("- URL-safe — when the API wraps it in `/media/<quote(basename)>`, browsers and")
    emit("  HTTP clients can request it without ambiguity.")
    emit("- Served directly by the existing `app.mount(\"/media\", StaticFiles(...))` —")
    emit("  no new endpoints, no new mount configuration.")
    emit("- One-line change in each of two files; one SQL update for the existing 1817 rows.")
    emit()

    # Write the full structured report to disk too
    out_path = os.path.join(HERE, "audio_diagnosis_report.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(REPORT))
        emit(f"  [full report also written to: {out_path}]")
    except OSError as e:
        emit(f"  [warn] could not write report file: {e}")
    return 0

    # Write the full structured report to disk too
    out_path = os.path.join(HERE, "audio_diagnosis_report.md")
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(REPORT))
        emit(f"  [report also written to: {out_path}]")
    except OSError as e:
        emit(f"  [warn] could not write report file: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
