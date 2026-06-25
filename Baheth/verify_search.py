import sqlite3
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Import the normalize function from our app
sys.path.insert(0, HERE)
from normalizer import normalize

DB = os.path.join(HERE, "arabic_search.db")

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Queries that match exact tokens in the normalized text
tests = [
    "الحمد",        # exact token in shards 1, 37, 3, 39
    "سيبويه",       # exact token in shard 17, 53
    "العالمين",     # exact token in shard 1, 37
    "إبراهيم",      # normalizes to ابراهيم — is in shard 8, 44
    "آدم",          # normalizes to ادم — is in shard 9, 45
    "مالكا",        # exact token in shard 42 (مالكًا → مالكا)
    "أحمد",         # normalizes to احمد — is in shard 7, 43
    "الأعمال",      # normalizes to الاعمال — is in shard 2, 38
    "الإمام",       # normalizes to الامام — is in shard 42
    "اللغة",        # exact token in shard 27, 63
]

results = {}
for q in tests:
    nq = normalize(q)
    rows = conn.execute(
        """SELECT arabic_text_shards.id,
                  arabic_text_shards.original_text,
                  arabic_text_shards.normalized_text,
                  arabic_text_shards_fts.rank
        FROM arabic_text_shards JOIN arabic_text_shards_fts
          ON arabic_text_shards.id = arabic_text_shards_fts.rowid
        WHERE arabic_text_shards_fts MATCH ?
        ORDER BY rank""",
        (nq,),
    ).fetchall()
    results[q] = {"normalized_query": nq, "matches": [dict(r) for r in rows]}

total = sum(len(v["matches"]) for v in results.values())

# Write full results
out_path = os.path.join(HERE, "search_verify.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Tested {len(tests)} queries, total {total} matches.")
print(f"Full JSON at: {out_path}")

conn.close()
