import subprocess
import urllib.request
import urllib.parse
import json
import sys
import time
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = r"C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe"

server = subprocess.Popen(
    [PYTHON, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
    cwd=HERE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
time.sleep(4)

def req(method, path, body=None):
    url = f"http://127.0.0.1:8000{path}"
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body else None
    headers = {"Content-Type": "application/json"} if body else {}
    r = urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers, method=method))
    return json.loads(r.read())

results = {}

# 1. index Arabic
res = req("POST", "/index-shards", {
    "shards": [{"text": "<p>الْحَمْدُ للَّهِ رَبِّ الْعَالَمِينَ</p>"}]
})
results["index"] = res

# 2. search bare word
q = "العالمين"
res = req("GET", f"/search?q={urllib.parse.quote(q)}")
results["search_bare"] = res

# 3. search with diacritics (should match same)
q2 = "الْعَالَمِينَ"
res2 = req("GET", f"/search?q={urllib.parse.quote(q2)}")
results["search_tashkeel"] = res2

# 4. search partial
q3 = "الحمد"
res3 = req("GET", f"/search?q={urllib.parse.quote(q3)}")
results["search_partial"] = res3

out = json.dumps(results, ensure_ascii=False, indent=2)
outpath = os.path.join(HERE, "test_results.json")
with open(outpath, "w", encoding="utf-8") as f:
    f.write(out)
print("Results written to:", outpath)

server.terminate()
server.wait(timeout=5)
