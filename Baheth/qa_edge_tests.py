"""
qa_edge_tests.py — Self-contained edge-case QA suite for Baheth Arabic Search.

Lifecycle (all inside this script — no PowerShell process wrangling):
  1. Spawn uvicorn as a child process.
  2. Wait for /docs to respond (server ready).
  3. Seed the DB with a sentinel row (كتاب, un-vocalized).
  4. Run three test groups against GET /search?q=...
  5. Print pass/fail matrix.
  6. Terminate the child, exit with code 0 on full pass / 1 on any fail.

Test groups:
  A. Empty / junk / FTS5-injection inputs  ->  expect 200 OK + empty results
  B. Diacritic cross-matching               ->  vocalized query hits un-vocalized row
  C. Payload limit                          ->  query > 200 chars -> 422

Stdlib only. No pytest, no requests.

Usage:
  python qa_edge_tests.py

Assumes a clean arabic_search.db (this script's setup creates the schema via
uvicorn's lifespan handler). The script does NOT delete the DB itself; the
operator controls that. A pre-existing DB with extra rows is fine — the
sentinel uses a unique token and assertions are tolerant.
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
from dataclasses import dataclass, field
from typing import Any, Callable

# Force UTF-8 on Windows so print() of Arabic strings doesn't trip cp1252
# when this script is run from PowerShell (which defaults to OEM codepage).
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
READINESS_URL = f"{BASE_URL}/docs"   # 404 on /docs is fine; we just need a TCP+HTTP reply

SERVER_BOOT_TIMEOUT_S = 30.0
SERVER_POLL_INTERVAL_S = 0.5

# Sentinel tokens for cross-matching tests. Unique enough to avoid
# collision with whatever else is in the DB.
SENTINEL_BASE = "كتاب"            # un-vocalized base
SENTINEL_VOCALIZED = "كِتَاب"     # same word with tashkeel
SENTINEL_FULL_TASHKEEL = "كِتَابٌ"  # with tanwin

# ----------------------------------------------------------------------
# HTTP helpers
# ----------------------------------------------------------------------


def _request(
    method: str,
    url: str,
    body: dict[str, Any] | None = None,
    timeout: float = 10.0,
) -> tuple[int, Any]:
    data = None
    headers: dict[str, str] = {}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
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


def _index(text: str) -> tuple[int, Any]:
    return _request("POST", INDEX_URL, {"shards": [{"text": text}]})


# ----------------------------------------------------------------------
# Server lifecycle (the part Opencode got stuck on)
# ----------------------------------------------------------------------


def start_server() -> subprocess.Popen:
    """Spawn uvicorn, wait until HTTP responds. Returns the Popen handle.

    Critical detail that hangs naive PowerShell wrappers: we must redirect
    stdout/stderr to DEVNULL (or pipes we drain), otherwise the child holds
    the parent's stdio and shell process tracking gets confused. We use
    DEVNULL here so the parent never blocks on a child stdout fill.
    """
    creationflags = 0
    if os.name == "nt":
        # CREATE_NO_WINDOW so no console flashes; uvicorn still works.
        creationflags = 0x08000000

    # Pass UTF-8 down to uvicorn so its own Arabic log lines are safe.
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
            # 404 on /docs still means the server is up.
            return proc
        except Exception:
            time.sleep(SERVER_POLL_INTERVAL_S)

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


# ----------------------------------------------------------------------
# Test runner
# ----------------------------------------------------------------------


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
        except AssertionError as e:
            ok, detail = False, f"assertion: {e}"
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
        total_ms = sum(r.duration_ms for r in self.results)

        print()
        print("=" * 72)
        print(f"  RESULTS:  {passed}/{total} passed   |   {failed} failed   |   total {total_ms:.1f} ms")
        print("=" * 72)
        if failed:
            print("  Failures:")
            for r in self.results:
                if not r.passed:
                    print(f"    - {r.name}")
                    print(f"        {r.detail}")
        print()
        print("  Matrix:")
        groups: dict[str, list[CaseResult]] = {}
        for r in self.results:
            group = r.name.split("::", 1)[0] if "::" in r.name else "misc"
            groups.setdefault(group, []).append(r)
        for g, items in groups.items():
            print(f"    {g}:")
            for r in items:
                mark = "PASS" if r.passed else "FAIL"
                print(f"      [{mark}] {r.name}  ({r.duration_ms:.1f} ms)")
        print()
        return 0 if failed == 0 else 1


# ----------------------------------------------------------------------
# Group A — Empty / junk / FTS5-injection inputs
# ----------------------------------------------------------------------

EMPTY_INPUTS = [
    ("whitespace_only",         "   "),
    ("tabs_and_newlines",       "\t\n  \r\n"),
    ("arabic_comma_only",       "،"),
    ("arabic_question_only",    "؟"),
    ("mixed_arabic_punct",      "،؛؟!."),
    ("unicode_zero_width",      "​​‌"),
]

INJECTION_INPUTS = [
    ("fts5_star",               "*"),
    ("fts5_caret",              "^"),
    ("fts5_quote_break",        '"; DROP TABLE arabic_text_shards; --'),
    ("sql_or_1_eq_1",           "OR 1=1"),
    ("sql_union_select",        "' UNION SELECT * FROM arabic_text_shards --"),
    ("fts5_column_filter",      "id:1"),
    ("fts5_near_op",            "NEAR(foo bar, 5)"),
    ("fts5_asterisk_wildcard",  "كتاب*"),
    ("fts5_minus_negation",     "كتاب -مدرسة"),
]


def _expect_empty_results(q: str) -> tuple[bool, str]:
    status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(q)}")
    if status == 0:
        return False, f"connection error: {body}"
    if status != 200:
        return False, f"expected 200 OK, got {status}; body={body}"
    if not isinstance(body, dict) or "results" not in body:
        return False, f"malformed response (no 'results' key): {body}"
    if body["results"] != []:
        return False, f"expected results=[], got {len(body['results'])} hits: {body['results'][:3]}"
    return True, ""


def test_group_A(runner: TestRunner) -> None:
    print("\n[A] Empty / junk / FTS5-injection inputs")
    print("    Expectation: 200 OK + empty results, no crash, no operator abuse.")
    for name, q in EMPTY_INPUTS:
        runner.case(f"junk::{name}", lambda q=q: _expect_empty_results(q))
    for name, q in INJECTION_INPUTS:
        runner.case(f"injection::{name}", lambda q=q: _expect_empty_results(q))


# ----------------------------------------------------------------------
# Group B — Diacritic cross-matching
# ----------------------------------------------------------------------


def _hits_contain_sentinel(body: Any) -> bool:
    if not isinstance(body, dict) or not isinstance(body.get("results"), list):
        return False
    return any(
        isinstance(r, dict) and SENTINEL_BASE in (r.get("normalized_text") or "")
        for r in body["results"]
    )


def test_group_B(runner: TestRunner) -> None:
    print("\n[B] Diacritic cross-matching")
    print("    Index base form (كتاب), query with tashkeel, expect hit.")

    # Setup: index the un-vocalized sentinel.
    idx_status, idx_body = _index(SENTINEL_BASE)
    runner.case(
        "setup::index_sentinel_base",
        lambda: (idx_status == 201, f"index returned {idx_status}: {idx_body}"),
    )
    if idx_status != 201:
        return  # can't continue without the seed row

    def vocalized_query_hits_base() -> tuple[bool, str]:
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(SENTINEL_VOCALIZED)}")
        if status != 200:
            return False, f"expected 200, got {status}; body={body}"
        if not _hits_contain_sentinel(body):
            return False, f"vocalized query {SENTINEL_VOCALIZED!r} did not match base row; body={body}"
        return True, ""

    def full_tashkeel_query_hits_base() -> tuple[bool, str]:
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(SENTINEL_FULL_TASHKEEL)}")
        if status != 200:
            return False, f"expected 200, got {status}; body={body}"
        if not _hits_contain_sentinel(body):
            return False, f"full-tashkeel query {SENTINEL_FULL_TASHKEEL!r} did not match base row; body={body}"
        return True, ""

    def reverse_direction_vocalized_indexed() -> tuple[bool, str]:
        # Index the vocalized form too; base query should still match (at least one of the two rows).
        st, bd = _index(SENTINEL_VOCALIZED)
        if st != 201:
            return False, f"index(vocalized) returned {st}: {bd}"
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(SENTINEL_BASE)}")
        if status != 200:
            return False, f"expected 200, got {status}; body={body}"
        if not _hits_contain_sentinel(body):
            return False, f"reverse direction failed (un-vocalized query did not match vocalized row); body={body}"
        return True, ""

    runner.case("diacritics::vocalized_query_hits_base_row", vocalized_query_hits_base)
    runner.case("diacritics::full_tashkeel_query_hits_base_row", full_tashkeel_query_hits_base)
    runner.case("diacritics::reverse_vocalized_indexed_matches_base_query", reverse_direction_vocalized_indexed)


# ----------------------------------------------------------------------
# Group C — Payload limits
# ----------------------------------------------------------------------

LONG_QUERY = "ا" * 250       # > max_length=200
BOUNDARY_QUERY = "ك" * 200   # exactly max_length=200, should pass


def test_group_C(runner: TestRunner) -> None:
    print("\n[C] Payload limits")
    print("    Expectation: 422 Unprocessable Entity for over-long input.")

    def long_query_422() -> tuple[bool, str]:
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(LONG_QUERY)}")
        if status != 422:
            return False, f"expected 422 for {len(LONG_QUERY)}-char query, got {status}; body={body}"
        if not isinstance(body, dict) or "detail" not in body:
            return False, f"expected FastAPI validation error body, got {body}"
        return True, ""

    def empty_query_422() -> tuple[bool, str]:
        # min_length=1 should reject empty string
        status, body = _request("GET", f"{SEARCH_URL}?q=")
        if status != 422:
            return False, f"expected 422 for empty query, got {status}; body={body}"
        if not isinstance(body, dict) or "detail" not in body:
            return False, f"expected FastAPI validation error body, got {body}"
        return True, ""

    def boundary_200_accepted() -> tuple[bool, str]:
        # exactly 200 chars should be accepted (within max_length=200).
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(BOUNDARY_QUERY)}")
        if status != 200:
            return False, f"expected 200 for boundary-length query, got {status}; body={body}"
        return True, ""

    def over_boundary_by_1_422() -> tuple[bool, str]:
        q = "ك" * 201
        status, body = _request("GET", f"{SEARCH_URL}?q={urllib.parse.quote(q)}")
        if status != 422:
            return False, f"expected 422 for 201-char query, got {status}; body={body}"
        return True, ""

    runner.case("limits::long_query_250chars_422", long_query_422)
    runner.case("limits::empty_query_422", empty_query_422)
    runner.case("limits::boundary_200chars_200", boundary_200_accepted)
    runner.case("limits::over_boundary_201chars_422", over_boundary_by_1_422)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------


def main() -> int:
    print("=" * 72)
    print("  Baheth Search API — Edge-Case QA Suite")
    print(f"  Target: {BASE_URL}")
    print(f"  Python: {PYTHON}")
    print(f"  CWD:    {HERE}")
    print("=" * 72)

    server = None
    try:
        print("\n[setup] spawning uvicorn...")
        server = start_server()
        print(f"[setup] server up (pid={server.pid})")

        runner = TestRunner()
        test_group_A(runner)
        test_group_B(runner)
        test_group_C(runner)
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
