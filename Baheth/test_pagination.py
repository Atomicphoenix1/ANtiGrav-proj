import subprocess
import urllib.request
import urllib.parse
import json
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = r"C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe"
OUT = os.path.join(HERE, "pagination_verify.json")

server = subprocess.Popen(
    [PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=HERE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(4)

def req(url):
    return json.loads(urllib.request.urlopen(url).read())

results = {}

# 1 — default page=1, page_size=50 (should return everything)
r = req("http://127.0.0.1:8000/search?q=%D8%A7%D9%84%D9%84%D9%87")
results["default_pagination"] = {
    "total_results": r["total_results"],
    "page": r["page"],
    "page_size": r["page_size"],
    "returned": len(r["results"]),
}

# 2 — page=1, page_size=2
r = req("http://127.0.0.1:8000/search?q=%D8%A7%D9%84%D9%84%D9%87&page=1&page_size=2")
results["page1_size2"] = {
    "total_results": r["total_results"],
    "page": r["page"],
    "page_size": r["page_size"],
    "returned": len(r["results"]),
    "ids": [res["id"] for res in r["results"]],
}

# 3 — page=2, page_size=2
r = req("http://127.0.0.1:8000/search?q=%D8%A7%D9%84%D9%84%D9%87&page=2&page_size=2")
results["page2_size2"] = {
    "total_results": r["total_results"],
    "page": r["page"],
    "page_size": r["page_size"],
    "returned": len(r["results"]),
    "ids": [res["id"] for res in r["results"]],
}

# 4 — audio fields present
r = req("http://127.0.0.1:8000/search?q=%D8%A7%D9%84%D9%84%D9%87&page_size=1")
if r["results"]:
    res = r["results"][0]
    results["audio_fields"] = {
        "has_audio_url": res["audio_url"] is not None,
        "has_start_time": res["start_time"] is not None,
        "has_end_time": res["end_time"] is not None,
    }

server.terminate()
server.wait(timeout=5)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Results written to:", OUT)
