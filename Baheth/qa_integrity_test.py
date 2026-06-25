"""
qa_integrity_test.py — Full-System Integrity Audit for Baheth Arabic Search Engine.

Phases:
  1. Flush & Reset
  2. Upload Integrity (amr21 + 03 الرسالة التبوكية)
  3. Search Response Test (Arabic diacritic-agnostic)
  4. Stress Nuke Test (flush + immediate search)

Stdlib only. Spawns uvicorn, runs tests, kills server, reports PASS/FAIL.
Exit code 0 = all pass, 1 = any fail.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
MEDIA_DIR = os.path.join(HERE, "media")
DB_PATH = os.path.join(HERE, "arabic_search.db")
PYTHON = sys.executable
BASE_URL = "http://127.0.0.1:8000"
SEARCH_URL = f"{BASE_URL}/search"
FLUSH_URL = f"{BASE_URL}/api/admin/flush"
ASSETS_URL = f"{BASE_URL}/api/admin/assets"
UPLOAD_URL = f"{BASE_URL}/api/admin/upload"
INDEX_URL = f"{BASE_URL}/index-shards"
READINESS_URL = f"{BASE_URL}/docs"

SERVER_BOOT_TIMEOUT_S = 30.0

# Source files from outside media/ (flush nukes MEDIA_DIR entirely)
AU_DIR = os.path.join(HERE, "..", "AutoUpload")
SRT_DIR = os.path.join(HERE, "..", "SRT")
SAMPLE1_MP3 = os.path.join(AU_DIR, "amr21", "amr21.mp3")
SAMPLE1_SRT = os.path.join(AU_DIR, "amr21", "amr21_TokenAnchored_DryRun.srt")
SAMPLE2_MP3 = os.path.join(SRT_DIR, "03 الرسالة التبوكية لابن القيم.mp3")
SAMPLE2_SRT = os.path.join(SRT_DIR, "03 الرسالة التبوكية لابن القيم_Total.srt")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def _request(
    method: str,
    url: str,
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> tuple[int, Any]:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw
    except urllib.error.URLError as e:
        return 0, f"URLError: {e.reason}"


def _get(url: str) -> tuple[int, Any]:
    return _request("GET", url)


def _post(url: str, data: bytes | None = None, headers: dict | None = None) -> tuple[int, Any]:
    return _request("POST", url, data, headers)


def _build_multipart(fields: dict[str, tuple[str, bytes] | str]) -> tuple[bytes, str]:
    boundary = "----QAIntegrityTestBoundary" + str(int(time.time() * 1e6))
    body_parts = []
    for name, value in fields.items():
        body_parts.append(f"--{boundary}\r\n".encode())
        if isinstance(value, tuple):
            filename, data = value
            body_parts.append(
                f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
            )
            body_parts.append(b"Content-Type: application/octet-stream\r\n\r\n")
            body_parts.append(data)
            body_parts.append(b"\r\n")
        else:
            body_parts.append(
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
            )
            body_parts.append(value.encode("utf-8"))
            body_parts.append(b"\r\n")
    body_parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(body_parts)
    return body, boundary


def _upload_lecture(mp3_path: str, srt_path: str, book_title: str = "", sheikh_name: str = "", year_date: str = "", youtube_url: str | None = None) -> tuple[int, Any]:
    with open(mp3_path, "rb") as f:
        mp3_data = f.read()
    with open(srt_path, "rb") as f:
        srt_data = f.read()
    fields = {
        "mp3": (os.path.basename(mp3_path), mp3_data),
        "srt": (os.path.basename(srt_path), srt_data),
        "book_title": book_title,
        "sheikh_name": sheikh_name,
        "year_date": year_date,
        "overwrite": "true",
    }
    if youtube_url:
        fields["youtube_url"] = youtube_url
    body, boundary = _build_multipart(fields)
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    return _post(UPLOAD_URL, body, headers)


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def start_server() -> subprocess.Popen:
    creationflags = 0
    if os.name == "nt":
        creationflags = 0x08000000
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
    deadline = time.monotonic() + SERVER_BOOT_TIMEOUT_S
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
    raise RuntimeError(f"Server did not respond within {SERVER_BOOT_TIMEOUT_S}s")


def stop_server(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

@dataclass
class CaseResult:
    name: str
    passed: bool
    detail: str = ""
    duration_ms: float = 0.0


@dataclass
class TestRunner:
    results: list[CaseResult] = field(default_factory=list)

    def case(self, name: str, fn: Callable[[], tuple[bool, str]]) -> None:
        t0 = time.perf_counter()
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, f"exception: {type(e).__name__}: {e}"
        dt = (time.perf_counter() - t0) * 1000
        marker = "PASS" if ok else "FAIL"
        suffix = f"  ({dt:.1f} ms)" if ok else f"  -- {detail}"
        print(f"  [{marker}] {name}{suffix}")
        self.results.append(CaseResult(name=name, passed=ok, detail=detail, duration_ms=dt))

    def report(self) -> int:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        print()
        print("=" * 72)
        print(f"  RESULTS:  {passed}/{total} passed   |   {failed} failed")
        print("=" * 72)
        if failed:
            print("  Failures:")
            for r in self.results:
                if not r.passed:
                    print(f"    - {r.name}")
                    print(f"        {r.detail}")
        print()
        return 0 if failed == 0 else 1


# ---------------------------------------------------------------------------
# PART 1: Schema & Integrity Verification
# ---------------------------------------------------------------------------

def direct_db_row_count() -> int:
    if not os.path.exists(DB_PATH):
        return 0
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT COUNT(*) FROM lectures").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def direct_fts_row_count() -> int:
    if not os.path.exists(DB_PATH):
        return 0
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute("SELECT COUNT(*) FROM arabic_text_shards_fts").fetchone()
        return row[0] if row else 0
    finally:
        conn.close()


def table_exists(name: str) -> bool:
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def trigger_exists(name: str) -> bool:
    if not os.path.exists(DB_PATH):
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND name=?", (name,)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def test_part1(runner: TestRunner) -> None:
    print("\n" + "=" * 72)
    print("PART 1: Schema & Integrity Verification")
    print("=" * 72)

    # Check tables exist
    runner.case("schema::lectures_table_exists", lambda: (table_exists("lectures"), ""))
    runner.case("schema::fts5_table_exists", lambda: (table_exists("arabic_text_shards_fts"), ""))

    # Check triggers exist
    for trig in ["after_lectures_insert", "after_lectures_delete", "after_lectures_update"]:
        runner.case(f"schema::trigger_{trig}", lambda t=trig: (trigger_exists(t), ""))

    # Check column count
    def check_columns():
        conn = sqlite3.connect(DB_PATH)
        try:
            cols = [r[1] for r in conn.execute("PRAGMA table_info(lectures)").fetchall()]
            expected = ["id", "text_content", "normalized_text", "audio_url", "start_time", "end_time", "book_title", "sheikh_name", "year_date", "youtube_url"]
            for c in expected:
                if c not in cols:
                    return False, f"missing column: {c}"
            return True, f"columns: {len(cols)}"
        finally:
            conn.close()
    runner.case("schema::lectures_columns", check_columns)

    # Persistence check: FTS row count should match lectures row count
    def fts_sync():
        lc = direct_db_row_count()
        fc = direct_fts_row_count()
        if lc != fc:
            return False, f"lectures={lc} != fts={fc}"
        return True, f"both={lc}"
    runner.case("schema::fts_lectures_sync", fts_sync)


# ---------------------------------------------------------------------------
# PART 2: Arabic Diacritic Truth Test
# ---------------------------------------------------------------------------

def test_part2(runner: TestRunner) -> None:
    print("\n" + "=" * 72)
    print('PART 2: The "Arabic Truth" Test (Diacritic Problem)')
    print("=" * 72)

    # Index a diacritized string via /index-shards
    diacritized = "الْحَمْدُ لِلَّهِ"
    # Search for undiacritized "الحمد"

    def index_diacritized():
        st, body = _post(INDEX_URL, json.dumps({"shards": [{"text": diacritized}]}, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})
        if st != 201:
            return False, f"index returned {st}: {body}"
        return True, body.get("status", "")
    runner.case("diacritic::index_diacritized", index_diacritized)

    def search_undiacritized_hits():
        st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الحمد')}")
        if st != 200:
            return False, f"expected 200, got {st}: {body}"
        if not isinstance(body, dict) or "results" not in body:
            return False, f"malformed: {body}"
        hits = [r for r in body["results"] if "الحمد" in r.get("normalized_text", "")]
        if not hits:
            return False, f"no hits for الحمد in normalized_text. results={body['results'][:3]}"
        # Check that original diacritized text is preserved
        first = hits[0].get("original_text", "")
        if "الْحَمْدُ" not in first and "لِلَّهِ" not in first:
            return False, f"original_text missing diacritization: {first[:100]}"
        return True, f"found {len(hits)} hits, original preserved"
    runner.case("diacritic::undiacritized_search_hits", search_undiacritized_hits)

    def search_alef_variant():
        st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('لله')}")
        if st != 200:
            return False, f"expected 200, got {st}: {body}"
        hits = [r for r in body.get("results", []) if "لله" in r.get("normalized_text", "")]
        if not hits:
            return False, f"no hits for لله (should match لله, لَلَّهِ, etc.)"
        return True, f"found {len(hits)} hits"
    runner.case("diacritic::alef_variant_search", search_alef_variant)

    def diacritized_query_search():
        # Search with full tashkeel should also work
        st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الْحَمْدُ')}")
        if st != 200:
            return False, f"expected 200, got {st}: {body}"
        hits = [r for r in body.get("results", []) if "الحمد" in r.get("normalized_text", "")]
        if not hits:
            return False, f"diacritized query الْحَمْدُ should match normalized الحمد"
        return True, f"found {len(hits)} hits"
    runner.case("diacritic::diacritized_query_matches", diacritized_query_search)


# ---------------------------------------------------------------------------
# PART 3: Full-Cycle QA — Upload, Verify, Search, Stress Nuke
# ---------------------------------------------------------------------------

def test_part3(runner: TestRunner) -> None:
    print("\n" + "=" * 72)
    print("PART 3: Full-Cycle Automated QA")
    print("=" * 72)

    # --- 3A: Flush & Reset ---
    def flush_db():
        st, body = _post(FLUSH_URL)
        if st != 200:
            return False, f"flush returned {st}: {body}"
        if not isinstance(body, dict) or body.get("status") != "CLEARED":
            return False, f"unexpected flush response: {body}"
        return True, body.get("detail", "")
    runner.case("flush::nuke_and_reset", flush_db)

    def after_flush_tables_exist():
        if not table_exists("lectures"):
            return False, "lectures table missing after flush+init_db"
        if not table_exists("arabic_text_shards_fts"):
            return False, "FTS5 table missing after flush+init_db"
        if not trigger_exists("after_lectures_insert"):
            return False, "insert trigger missing after flush+init_db"
        return True, "all tables + triggers present"
    runner.case("flush::tables_exist_after_nuke", after_flush_tables_exist)

    def after_flush_zero_rows():
        lc = direct_db_row_count()
        fc = direct_fts_row_count()
        if lc != 0 or fc != 0:
            return False, f"lectures={lc}, fts={fc} (expected 0)"
        return True, "lectures=0, fts=0"
    runner.case("flush::zero_rows_after_nuke", after_flush_zero_rows)

    def after_flush_no_assets():
        st, body = _get(ASSETS_URL)
        if st != 200:
            return False, f"assets endpoint returned {st}: {body}"
        mp3_count = len(body.get("mp3s", []))
        srt_count = len(body.get("srts", []))
        if mp3_count != 0 or srt_count != 0:
            return False, f"expected 0 assets, got mp3s={mp3_count}, srts={srt_count}"
        return True, "0 assets"
    runner.case("flush::media_cleared", after_flush_no_assets)

    # --- 3B: Upload Integrity ---
    def upload_amr21():
        if not os.path.exists(SAMPLE1_MP3):
            return False, f"MP3 not found: {SAMPLE1_MP3}"
        if not os.path.exists(SAMPLE1_SRT):
            return False, f"SRT not found: {SAMPLE1_SRT}"
        st, body = _upload_lecture(SAMPLE1_MP3, SAMPLE1_SRT, "تقريب العلم", "الشيخ صالح العصيمي", "1445", "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        if st != 200:
            return False, f"upload returned {st}: {body}"
        return True, body.get("detail", "")
    runner.case("upload::amr21", upload_amr21)

    def upload_risala():
        if not os.path.exists(SAMPLE2_MP3):
            return False, f"MP3 not found: {SAMPLE2_MP3}"
        if not os.path.exists(SAMPLE2_SRT):
            return False, f"SRT not found: {SAMPLE2_SRT}"
        st, body = _upload_lecture(SAMPLE2_MP3, SAMPLE2_SRT)
        if st != 200:
            return False, f"upload returned {st}: {body}"
        return True, body.get("detail", "")
    runner.case("upload::risala_tabukia", upload_risala)

    # --- 3C: Verify file counts and DB row counts ---

    def assets_count_after_upload():
        st, body = _get(ASSETS_URL)
        if st != 200:
            return False, f"assets returned {st}: {body}"
        mp3s = body.get("mp3s", [])
        srts = body.get("srts", [])
        if len(mp3s) < 2:
            return False, f"expected >=2 mp3s, got {len(mp3s)}: {mp3s}"
        if len(srts) < 2:
            return False, f"expected >=2 srts, got {len(srts)}: {srts}"
        return True, f"mp3s={len(mp3s)}, srts={len(srts)}"
    runner.case("verify::assets_count", assets_count_after_upload)

    def db_row_count_after_upload():
        lc = direct_db_row_count()
        fc = direct_fts_row_count()
        if lc < 10:
            return False, f"too few lectures rows: {lc} (expected hundreds from 2 SRTs)"
        if lc == 0:
            return False, "lectures row count is 0 after upload"
        if lc != fc:
            return False, f"mismatch: lectures={lc}, fts={fc}"
        return True, f"lectures={lc}, fts={fc}"
    runner.case("verify::db_row_counts", db_row_count_after_upload)

    # Check audio_url values in DB
    def check_audio_urls():
        try:
            conn = sqlite3.connect(DB_PATH)
            urls = conn.execute("SELECT DISTINCT audio_url FROM lectures ORDER BY audio_url").fetchall()
            conn.close()
            if not urls:
                return False, "no rows in lectures"
            url_list = [u[0] for u in urls]
            if any(u and u != "" for u in url_list):
                return True, f"audio_url values: {url_list}"
            return False, f"all audio_url are empty/null: {url_list}"
        except Exception as e:
            return False, f"query error: {e}"
    runner.case("verify::audio_url_values", check_audio_urls)

    # Check youtube_url values in DB & API
    def check_youtube_urls():
        try:
            conn = sqlite3.connect(DB_PATH)
            urls = conn.execute("SELECT DISTINCT youtube_url FROM lectures ORDER BY youtube_url").fetchall()
            conn.close()
            url_list = [u[0] for u in urls if u[0]]
            if not url_list:
                return False, "no youtube_url found in DB"
            if "https://www.youtube.com/watch?v=dQw4w9WgXcQ" not in url_list:
                return False, f"expected youtube_url not in DB: {url_list}"
            
            # Now verify through API
            st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الله')}&book_title={urllib.parse.quote('تقريب العلم')}")
            if st != 200:
                return False, f"search returned {st}: {body}"
            
            youtube_found = False
            for r in body.get("results", []):
                y_url = r.get("youtube_url")
                ye_url = r.get("youtube_embed_url")
                if y_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ":
                    youtube_found = True
                    if not ye_url or "https://www.youtube.com/embed/dQw4w9WgXcQ?start=" not in ye_url:
                        return False, f"invalid embed URL: {ye_url}"
            if not youtube_found:
                return False, "youtube_url not found in search api response results"
            return True, "youtube_url and youtube_embed_url verified successfully"
        except Exception as e:
            return False, f"query error: {e}"
    runner.case("verify::youtube_url_values", check_youtube_urls)

    # --- 3D: Search Response Tests ---

    def search_then_check(q: str, expected_substring: str, label: str):
        def fn():
            st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote(q)}")
            if st != 200:
                return False, f"expected 200 for '{q}', got {st}"
            if not isinstance(body, dict):
                return False, f"not JSON: {type(body)}"
            if "results" not in body:
                return False, f"no results key: {list(body.keys())}"
            total = body.get("total_results", 0)
            if total == 0:
                return False, f"0 results for '{q}'"
            if "original_text" not in body["results"][0]:
                return False, f"result missing original_text key"
            return True, f"{total} results for '{q}'"
        runner.case(f"search::{label}", fn)

    search_then_check("الله", "الله", "allah_search")
    search_then_check("الحمد", "الحمد", "hamd_search")
    search_then_check("التبوكية", "التبوكية", "tabukia_search")

    def search_returns_diacritized_text(q: str, label: str):
        def fn():
            st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote(q)}")
            if st != 200:
                return False, f"expected 200, got {st}"
            for r in body.get("results", []):
                original = r.get("original_text", "")
                # original should have tashkeel diacritics in it
                if any(c in original for c in "\u064E\u064F\u0650\u0651"):
                    return True, "has diacritized text"
            return False, "no result contains diacritized original_text"
        runner.case(f"diacritic_original::{label}", fn)

    search_returns_diacritized_text("الله", "preserves_diacritics")


# ---------------------------------------------------------------------------
# PART 4: Frontend-to-Backend Sync (URL encoding check)
# ---------------------------------------------------------------------------

def test_part4(runner: TestRunner) -> None:
    print("\n" + "=" * 72)
    print("PART 4: Frontend-to-Backend Sync (URL Encoding)")
    print("=" * 72)

    # Frontend uses URLSearchParams which auto-encodes.
    # Backend uses FastAPI Query() which auto-decodes.
    # Test: send special characters that need URL encoding.

    def url_encode_arabic():
        q = "السلام عليكم"
        encoded = urllib.parse.quote(q)
        st, body = _get(f"{SEARCH_URL}?q={encoded}")
        if st != 200:
            return False, f"encoded search returned {st}: {body}"
        if not isinstance(body, dict) or "query" not in body:
            return False, f"no query key: {body}"
        if body["query"] != q:
            return False, f"query round-trip failed: sent '{q}', got '{body['query']}'"
        return True, f"round-trip OK: '{body['query']}'"
    runner.case("encoding::arabic_roundtrip", url_encode_arabic)

    def url_encode_special_chars():
        q = "آية (الكرسي) + كتاب؟"
        encoded = urllib.parse.quote(q)
        st, body = _get(f"{SEARCH_URL}?q={encoded}")
        if st != 200:
            return False, f"returned {st}: {body}"
        return True, f"status={st}"
    runner.case("encoding::special_chars", url_encode_special_chars)

    def audio_url_encode():
        # After uploads, audio_url should be a relative /media/foo.mp3 URL
        st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الله')}")
        if st != 200:
            return False, f"search returned {st}"
        for r in body.get("results", []):
            au = r.get("audio_url")
            if au and au.startswith("/media/"):
                filename = au.split("/")[-1]
                decoded = urllib.parse.unquote(filename)
                if decoded:
                    return True, f"audio_url OK: {au}"
        return False, "no result with properly encoded audio_url"
    runner.case("encoding::audio_url", audio_url_encode)


# ---------------------------------------------------------------------------
# PART 4b: Stress Nuke Test
# ---------------------------------------------------------------------------

def test_stress_nuke(runner: TestRunner) -> None:
    print("\n" + "=" * 72)
    print("STRESS: Nuclear Flush + Immediate Search")
    print("=" * 72)

    def second_flush():
        st, body = _post(FLUSH_URL)
        if st != 200:
            return False, f"flush returned {st}: {body}"
        return True, "flushed"
    runner.case("stress::second_flush", second_flush)

    def immediate_search_post_flush():
        # Must return 200 with 0 results (not crash with "no such table")
        st, body = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الله')}")
        if st != 200:
            return False, f"expected 200, got {st}: {body}"
        total = body.get("total_results", -1)
        if total != 0:
            return False, f"expected 0 results after flush, got {total}"
        return True, f"200 OK, {total} results, table ready"
    runner.case("stress::search_after_flush", immediate_search_post_flush)

    def tables_still_exist_after_stress():
        if not table_exists("lectures"):
            return False, "lectures table missing"
        if not table_exists("arabic_text_shards_fts"):
            return False, "FTS5 table missing"
        if not trigger_exists("after_lectures_insert"):
            return False, "insert trigger missing"
        return True, "all tables and triggers survived flush"
    runner.case("stress::tables_survive_nuke", tables_still_exist_after_stress)

    def fts_ready_for_new_data():
        # After flush, index a new shard, verify it's searchable
        st, body = _post(INDEX_URL, json.dumps({"shards": [{"text": "بسم الله الرحمن الرحيم"}]}, ensure_ascii=False).encode("utf-8"), {"Content-Type": "application/json"})
        if st != 201:
            return False, f"index returned {st}: {body}"
        st2, body2 = _get(f"{SEARCH_URL}?q={urllib.parse.quote('الرحمن')}")
        if st2 != 200:
            return False, f"search returned {st2}: {body2}"
        if body2.get("total_results", 0) == 0:
            return False, "post-flush index not searchable"
        return True, f"indexed+searchable, {body2['total_results']} results"
    runner.case("stress::index_after_flush_works", fts_ready_for_new_data)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 72)
    print("  Baheth Search API — Full-System Integrity Audit")
    print(f"  Target: {BASE_URL}")
    print(f"  Python: {PYTHON}")
    print(f"  CWD:    {HERE}")
    print("=" * 72)

    # Pre-flight checks
    if not os.path.exists(SAMPLE1_MP3):
        print(f"\n  [PREFLIGHT FAIL] {SAMPLE1_MP3} not found")
        return 1
    if not os.path.exists(SAMPLE1_SRT):
        print(f"\n  [PREFLIGHT FAIL] {SAMPLE1_SRT} not found")
        return 1
    if not os.path.exists(SAMPLE2_MP3):
        print(f"\n  [PREFLIGHT FAIL] {SAMPLE2_MP3} not found")
        return 1
    if not os.path.exists(SAMPLE2_SRT):
        print(f"\n  [PREFLIGHT FAIL] {SAMPLE2_SRT} not found")
        return 1

    server = None
    try:
        print("\n[setup] spawning uvicorn...")
        server = start_server()
        print(f"[setup] server up (pid={server.pid})")

        runner = TestRunner()

        test_part1(runner)
        test_part2(runner)
        test_part3(runner)
        test_part4(runner)
        test_stress_nuke(runner)

        return runner.report()
    except RuntimeError as e:
        print(f"\n[FATAL] {e}")
        return 2
    finally:
        if server is not None:
            print("[teardown] stopping uvicorn...")
            stop_server(server)
            print("[teardown] done.")


if __name__ == "__main__":
    sys.exit(main())
