"""
testgem.py  --  Gemini-Only Formatter with SRT/JSON timestamp alignment.

Adapted from Super-Uploader_BACKUP.py (do_gemini_format, process_gemini,
token_anchored_alignment, build_srt_from_aligned_words).

Usage (CLI):
    python testgem.py --file <path.txt>
    python testgem.py --files <path1.txt> <path2.txt> ...
    python testgem.py --file <path.txt> --api-key <key> --model <name>

Usage (GUI):
    python testgem.py
"""

import os
import sys
import json
import re
import time
import gc
import argparse
import tkinter as tk
from tkinter import filedialog
import gradio as gr

try:
    from google import genai
except ImportError:
    genai = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "n8n_live_logs.txt")

GEMINI_API_KEY = ""
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3-flash-preview")


# ═══════════════════════════════════════════════════════════════
# Utility Functions  (same logging/browsing pattern as testwhisp.py)
# ═══════════════════════════════════════════════════════════════

def update_log(msg):
    try:
        print(msg)
    except UnicodeEncodeError:
        sanitized = msg.encode("ascii", "replace").decode("ascii")
        print(sanitized)
    try:
        with open(LOG_FILE_PATH, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    return msg


def tail_logs():
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_file_with_log(file_path, content):
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        char_count = len(content)
        msg = f"  \U0001f4be Saved file: {abs_path} | {char_count} chars."
        update_log(msg)
    except Exception as e:
        update_log(f"  \u274c Failed to save file {file_path}: {str(e)}")


def browse_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory()
    root.destroy()
    return folder


# ═══════════════════════════════════════════════════════════════
# Gemini Prompt  (from Super-Uploader_BACKUP.py get_gemini_prompt)
# ═══════════════════════════════════════════════════════════════

def get_gemini_prompt(raw_text):
    return f"""أنت خبير لغوي ومصحح شرعي محترف متخصص في تحرير وتنسيق وتشكيل تفريغات المحاضرات الإسلامية. مهمتك هي معالجة النص الخام {raw_text} بدقة متناهية وتحويله إلى نص منسق ومشكل بالكامل مع إضافة الوسوم الدلالية (Semantic Tags) لتمريرها عبر خط معالجة تلقائي. يجب عليك الالتزام بالقواعد التالية بدقة هندسية ودون أي تغيير أو تعليق خارج النص المخرَج.

# أولًا: قواعد الحفاظ على النص ومنع التلخيص (صارم جدًا)
1. الأمانة الحرفية المطلقة: ممنوع منعًا باتًا حذف أو تلخيص أو دمج أو تعديل أي كلمة أو جملة.
2. الحفاظ على التكرار: إذا كرر الشيخ لفظًا أو جملة (مثل: "أحدهما، أحدهما" أو "والدليل والدليل")، يجب الإبقاء عليها كاملة وتشكيلها كما هي دون أي اختصار أو حذف.
3. عدم الإكمال التلقائي: لا تكمل من عندك أي آية أو حديث أو جملة بترها الشيخ في الكلام، بل التزم بما نطق به حرفيًا.

# ثانيًا: التشكيل الكامل والنحو الصحيح (التشكيل الدلالي)
1. تشكيل بنيوي شامل: يجب ضبط كل حرف في كل كلمة بالتشكيل الكامل (Tashkeel)، بما في ذلك الحركات الإعرابية وأواخر الكلم.
2. دقة الفتحة والضمة والكسرة: يجب مراعاة السياق النحوي بدقة؛ التفريق بين الفاعل والمفعول، وبين المبني للمعلوم والمبني للمجهول أمر حتمي (مثل التفريق بين التشكيل الذي يغير المعنى الشرعي تمامًا). لا تضع حركات عشوائية بناءً على الحروف فقط، بل بناءً على الإعراب الصحيح للجملة.

# ثالثًا: منظومة الوسوم والتنسيق الهيكلي (Tagging Rules)
لا تقم بدمج أو تداخل الوسوم أبدًا، والتزم بالهيكل الآتي:

1. وسوم المتحدثين — `<speaker>`
يتم وضع سطر تقديم المتحدث داخل وسم `<speaker>` على النحو التالي:
- عند كلام الشيخ (الشارح): `<speaker>قَالَ الشَّارِحُ هَدَاهُ اللَّهُ:</speaker>`
- عند انتقال الكلام لقراءة كتاب المصنف: `<speaker>قَالَ الْمُصَنِّفُ حَفِظَهُ اللَّهُ:</speaker>` (أو رَحِمَهُ اللَّهُ حسب سياق المتن المشروح).
*تنبيه حاسم لفصل المتن عن الشرح:* التقط بدقة لحظة انتقال القارئ لقراءة نص الكتاب؛ غالبًا ما تبدأ بكلمة "نعم" تليها قراءة مباشرة، أو عبارة "قال المصنف". يجب إنهاء الشرح فورًا وفتح وسم المصنف لضمان عدم التداخل.

2. وسم المتن — `<matn>`
كل النص الذي يقرأه القارئ من كتاب المصنف الأصلي يجب أن يُغلف بالكامل داخل وسم `<matn>`، ويكون متبوعًا بسطر المتحدث الخاص به.

3. الحوار والنقاش (الشيخ والطلاب)
إذا سأل الشارح سؤالاً فأجاب أحد الطلاب أو جرى نقاش، قم بصياغة الهيئة هكذا وبخط عادي مشكل:
الشيخ:
[نص السؤال]
طالب:
[نص الإجابة]
الشيخ:
[تعقيب الشيخ]
ثم عد إلى التنسيق الطبيعي (الشارح أو المصنف) فور انتهاء المناقشة.

4. الآيات القرآنية — `<quran>`
توضع الآيات الكريمة داخل وسم `<quran>` محاطة بالأقواس المزهرة ﴿...﴾.

5. الأحاديث النبوية — `<hadith>`
توضع الأحاديث النبوية داخل وسم `<hadith>` محاطة بأقواس مربعة [...].

6. أسماء الكتب وأقوال العلماء والشعر — الأقواس المربعة فقط [...]

7. التقسيمات والتصنيفات — `<strong>` و العناوين النقاطية
لتنسيق التقسيمات (مثل: أحدهما، الآخر، أولها، ثانيها)، ضع الكلمة الدالة داخل وسم `<strong>`.

8. الألفاظ التعبدية والصلوات (Honorifics)
تُترك كلمات مثل "صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ"، "تَعَالَى"، "رَحِمَهُ اللَّهُ" كنص عادي مشكل تمامًا، ولا تضع حولها أي وسوم أو أقواس.

# رابعًا: علامات الترقيم وتقسيم الفقرات
1. تقسيم النص: قسّم الشرح والنص إلى فقرات واضحة ومستقلة حسب اكتمال المعنى وسياق الفكرة، حتى لو كان ذلك أثناء استرسال المتحدث نفسه.
2. قاعدة النقطة الصارمة: لا تضع علامة النقطة (.) مطلقًا في نص الشرح أو المتن إلا عند نهاية الفقرة التامة فقط. استخدم الفواصل (،) والفواصل المنقوطة (؛) والنقطتان (:) للفصل بين الجمل الداخلية لضمان استمرارية النص السليمة في خط المعالجة.

ملاحظة نهائية: ابدأ في إخراج النص مباشرة بناءً على هذه القواعد، ولا تضف أي مقدمات أو مؤخرات أو اعتذارات أو تعليقات جانبية.
"""


# ═══════════════════════════════════════════════════════════════
# Chunking Logic
# ═══════════════════════════════════════════════════════════════

def chunk_text_15k(text, chunk_size=15000):
    chunks = []
    start = 0
    total_len = len(text)

    while start < total_len:
        if start + chunk_size >= total_len:
            chunks.append(text[start:])
            break

        end = text.rfind('\n', start, start + chunk_size)
        if end == -1 or end <= start:
            end = text.rfind(' ', start, start + chunk_size)
            if end == -1 or end <= start:
                end = start + chunk_size

        chunks.append(text[start:end].strip())
        start = end

    return chunks


# ═══════════════════════════════════════════════════════════════
# SRT / Time Utilities
# ═══════════════════════════════════════════════════════════════

def format_srt_time(seconds):
    ms = int(round((seconds % 1) * 1000))
    s = int(seconds)
    if ms >= 1000:
        ms -= 1000
        s += 1
    m, s_remaining = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s_remaining:02d},{ms:03d}"


# ═══════════════════════════════════════════════════════════════
# Arabic Text Normalizers  (for alignment comparison)
# ═══════════════════════════════════════════════════════════════

def clean_arabic_word(w):
    w = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", w)
    w = re.sub(r"[إأآٱا]", "ا", w)
    w = re.sub(r"ى", "ي", w)
    w = re.sub(r"ة", "ه", w)
    w = re.sub(r"ؤ", "و", w)
    w = re.sub(r"ئ", "ي", w)
    w = re.sub(r"ء", "", w)
    w = re.sub(r"[^0-9A-Za-z_\u0600-\u06FF]", "", w)
    return w.lower()


def strip_html_tags(text):
    return re.sub(r"<[^>]+>", " ", text)


def prepare_formatted_text_for_srt(text):
    text = re.sub(r"<speaker>.*?</speaker>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?(matn|strong|quran|hadith)>", " ", text, flags=re.IGNORECASE)
    text = strip_html_tags(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def tokenize_for_alignment(text):
    return text.strip().split()


# ═══════════════════════════════════════════════════════════════
# Distance / Similarity  (for DP alignment)
# ═══════════════════════════════════════════════════════════════

def levenshtein_distance(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (0 if ca == cb else 1)
            current.append(min(insert_cost, delete_cost, replace_cost))
        previous = current
    return previous[-1]


def token_similarity(a, b):
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    max_len = max(len(a), len(b))
    return 1.0 - (levenshtein_distance(a, b) / max_len)


def substitution_cost(g_token, w_token):
    if not g_token or not w_token:
        return 1.8
    sim = token_similarity(g_token, w_token)
    if sim >= 0.92:
        return 0.05
    if sim >= 0.78:
        return 0.25
    if sim >= 0.62:
        return 0.55
    return 1.65


# ═══════════════════════════════════════════════════════════════
# Token-Anchored DP Alignment  (ported from Super-Uploader_BACKUP.py)
# ═══════════════════════════════════════════════════════════════

def align_gap_dp(g_clean, w_clean, g_start, g_end, w_start, w_end):
    g_gap = g_clean[g_start:g_end]
    w_gap = w_clean[w_start:w_end]
    n = len(g_gap)
    m = len(w_gap)
    mapping = [None] * n
    if n == 0 or m == 0:
        return mapping
    if n * m > 300000:
        return align_gap_greedy(g_clean, w_clean, g_start, g_end, w_start, w_end)

    insert_cost = 0.95
    delete_cost = 0.75
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    back = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + insert_cost
        back[i][0] = "insert"
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + delete_cost
        back[0][j] = "delete"

    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sub = dp[i - 1][j - 1] + substitution_cost(g_gap[i - 1], w_gap[j - 1])
            ins = dp[i - 1][j] + insert_cost
            dele = dp[i][j - 1] + delete_cost
            best = min(sub, ins, dele)
            dp[i][j] = best
            if best == sub:
                back[i][j] = "sub"
            elif best == dele:
                back[i][j] = "delete"
            else:
                back[i][j] = "insert"

    i, j = n, m
    while i > 0 or j > 0:
        op = back[i][j]
        if op == "sub":
            sim = token_similarity(g_gap[i - 1], w_gap[j - 1])
            if sim >= 0.58:
                mapping[i - 1] = w_start + j - 1
            i -= 1
            j -= 1
        elif op == "delete":
            j -= 1
        else:
            i -= 1
    return mapping


def align_gap_greedy(g_clean, w_clean, g_start, g_end, w_start, w_end):
    mapping = [None] * (g_end - g_start)
    cursor = w_start
    for local_i, token in enumerate(g_clean[g_start:g_end]):
        best_idx = None
        best_sim = 0.0
        search_end = min(w_end, cursor + 90)
        for idx in range(cursor, search_end):
            sim = token_similarity(token, w_clean[idx])
            if sim > best_sim:
                best_sim = sim
                best_idx = idx
                if sim >= 0.92:
                    break
        if best_idx is not None and best_sim >= 0.62:
            mapping[local_i] = best_idx
            cursor = best_idx + 1
    return mapping


def token_anchored_alignment(g_raw_words, all_w_words):
    whisper_words = all_w_words
    g_clean = [clean_arabic_word(w) for w in g_raw_words]
    w_clean = [clean_arabic_word(w["word"]) for w in whisper_words]

    import difflib
    matcher = difflib.SequenceMatcher(None, g_clean, w_clean, autojunk=False)
    opcodes = matcher.get_opcodes()
    g_to_w = [None] * len(g_raw_words)

    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            for offset in range(i2 - i1):
                g_to_w[i1 + offset] = j1 + offset
        else:
            gap_mapping = align_gap_dp(g_clean, w_clean, i1, i2, j1, j2)
            for offset, w_idx in enumerate(gap_mapping):
                g_to_w[i1 + offset] = w_idx

    aligned = []
    anchor_positions = [idx for idx, w_idx in enumerate(g_to_w) if w_idx is not None]

    for g_idx, word in enumerate(g_raw_words):
        clean = g_clean[g_idx]
        if not clean:
            continue
        w_idx = g_to_w[g_idx]
        if w_idx is not None and 0 <= w_idx < len(whisper_words):
            w_item = whisper_words[w_idx]
            aligned.append({
                "word": word,
                "start": w_item["start"],
                "end": w_item["end"],
                "whisper_index": w_idx,
                "source": "anchor"
            })
            continue

        prev_anchor = None
        next_anchor = None
        for pos in reversed(anchor_positions):
            if pos < g_idx:
                prev_anchor = pos
                break
        for pos in anchor_positions:
            if pos > g_idx:
                next_anchor = pos
                break

        nearest = None
        if prev_anchor is not None and next_anchor is not None:
            nearest = prev_anchor if (g_idx - prev_anchor) <= (next_anchor - g_idx) else next_anchor
        elif prev_anchor is not None:
            nearest = prev_anchor
        elif next_anchor is not None:
            nearest = next_anchor

        if nearest is not None and g_to_w[nearest] is not None:
            w_item = whisper_words[g_to_w[nearest]]
            start, end = w_item["start"], w_item["end"]
        elif whisper_words:
            w_item = whisper_words[min(len(whisper_words) - 1, g_idx)]
            start, end = w_item["start"], w_item["end"]
        else:
            start, end = 0.0, 0.05

        aligned.append({
            "word": word,
            "start": start,
            "end": max(end, start + 0.05),
            "whisper_index": None,
            "source": "ghost"
        })

    return aligned


def align_words(g_raw_words, all_w_words):
    return token_anchored_alignment(g_raw_words, all_w_words)


# ═══════════════════════════════════════════════════════════════
# SRT Builder  (from aligned words)
# ═══════════════════════════════════════════════════════════════

def build_srt_blocks_from_aligned_words(aligned_words, max_words_per_seg=10, max_duration=3.5, min_duration=0.30):
    items = aligned_words
    blocks = []
    current = []

    def flush():
        if not current:
            return
        text = " ".join(item["word"] for item in current).strip()
        if not text:
            current.clear()
            return
        starts = [float(item["start"]) for item in current]
        ends = [float(item["end"]) for item in current]
        start = min(starts)
        end = max(ends)
        blocks.append({"start": start, "end": end, "text": text})
        current.clear()

    for item in items:
        if not current:
            current.append(item)
            continue
        candidate_start = min(float(current[0]["start"]), float(item["start"]))
        candidate_end = max(float(item["end"]), max(float(x["end"]) for x in current))
        candidate_duration = candidate_end - candidate_start
        has_punctuation = any(char in item["word"] for char in [".", "،", "؟", "!", ":", "؛"])
        if len(current) >= max_words_per_seg or candidate_duration > max_duration:
            flush()
            current.append(item)
        else:
            current.append(item)
            if has_punctuation and len(current) >= 3:
                flush()

    flush()

    for idx, block in enumerate(blocks):
        if block["end"] <= block["start"]:
            block["end"] = block["start"] + min_duration
        if idx > 0:
            previous = blocks[idx - 1]
            if block["start"] < previous["end"]:
                block["start"] = previous["end"] + 0.02
            if block["end"] <= block["start"]:
                block["end"] = block["start"] + min_duration

    return blocks


def blocks_to_srt(blocks):
    srt_lines = []
    for idx, block in enumerate(blocks, start=1):
        start = format_srt_time(block["start"])
        end = format_srt_time(block["end"])
        srt_lines.append(f"{idx}\n{start} --> {end}\n{block['text']}\n")
    return "\n".join(srt_lines)


def build_srt_from_aligned_words(aligned_words):
    return blocks_to_srt(build_srt_blocks_from_aligned_words(aligned_words))


# ═══════════════════════════════════════════════════════════════
# Gemini API Call
# ═══════════════════════════════════════════════════════════════

def do_gemini_format(raw_text, api_key, model_name, chunk_idx=1):
    update_log(f"    \U0001f680 Engaging Gemini model: {model_name} (chunk {chunk_idx})...")
    client = genai.Client(api_key=api_key)
    prompt = get_gemini_prompt(raw_text)
    len_input = len(raw_text)

    for attempt in range(1, 3):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            temp_text = response.text
            if temp_text:
                len_output = len(temp_text)
                if len_output > 1.65 * len_input:
                    update_log(
                        f"    \u2705 Chunk {chunk_idx}: char count check PASSED "
                        f"({len_output} > {1.65 * len_input:.0f})"
                    )
                    return temp_text
                else:
                    update_log(
                        f"    \u26a0\ufe0f Chunk {chunk_idx}: char count check FAILED "
                        f"({len_output} <= {1.65 * len_input:.0f}), saving anyway."
                    )
                    return temp_text
            else:
                update_log(f"    \u26a0\ufe0f Chunk {chunk_idx}: Empty response on attempt {attempt}.")
        except Exception as e:
            update_log(f"    \u26a0\ufe0f Chunk {chunk_idx}: Attempt {attempt} failed: {str(e)}")
        if attempt < 2:
            time.sleep(3)

    update_log(f"    \u274c Chunk {chunk_idx}: All attempts failed.")
    return None


# ═══════════════════════════════════════════════════════════════
# 4-Layer Hierarchy Helper
# ═══════════════════════════════════════════════════════════════

def _get_hierarchy_paths(file_path):
    base_dir = os.path.dirname(file_path)
    parent_name = os.path.basename(base_dir)
    grandparent_dir = os.path.dirname(base_dir)
    grandparent_name = os.path.basename(grandparent_dir)

    if re.match(r"^part\d+$", parent_name.lower()):
        part_dir = base_dir
        part_name = parent_name
        lesson_dir = grandparent_dir
        lesson_name = grandparent_name
    else:
        lesson_dir = base_dir
        lesson_name = parent_name
        part_dir = None
        part_name = None

    return lesson_dir, lesson_name, part_dir, part_name


# ═══════════════════════════════════════════════════════════════
# Core Processing Function
# ═══════════════════════════════════════════════════════════════

def process_gemini(txt_path, srt_path, json_path, api_key, model_name):
    logs = ""
    base_dir = os.path.dirname(txt_path)
    base_name = os.path.splitext(os.path.basename(txt_path))[0]

    logs += update_log("=" * 52)
    logs += update_log(f"  \U0001f4c4 File: {base_name}")
    logs += update_log("=" * 52)

    # ── Load raw text and word timestamps ──
    with open(txt_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    logs += update_log(f"  \U0001f4d6 Loaded {len(raw_text)} chars of raw text")

    with open(json_path, "r", encoding="utf-8") as f:
        word_timestamps = json.load(f)
    logs += update_log(f"  \U0001f4d6 Loaded {len(word_timestamps)} word timestamps")

    if not raw_text.strip():
        logs += update_log(f"  \u274c Raw text is empty, skipping.")
        return

    # ── Chunk text at 15k boundaries ──
    txt_chunks = chunk_text_15k(raw_text)
    logs += update_log(f"  \u2702\ufe0f Split into {len(txt_chunks)} chunk(s) (max 15k chars each)")

    formatted_chunks = []

    if len(txt_chunks) > 1:
        chunks_dir = os.path.join(base_dir, f"{base_name}_whisper_chunks")
        os.makedirs(chunks_dir, exist_ok=True)
        logs += update_log(f"  \U0001f4c1 Created chunks directory: {chunks_dir}")

        # Split word timestamps to match chunk boundaries
        word_pos = 0
        for idx, chunk_text in enumerate(txt_chunks, start=1):
            chunk_word_count = len(chunk_text.split())
            end_pos = min(word_pos + chunk_word_count, len(word_timestamps))
            chunk_words = word_timestamps[word_pos:end_pos]
            word_pos = end_pos

            # Save chunk raw text
            chunk_raw_path = os.path.join(chunks_dir, f"chunk{idx:03d}.txt")
            write_file_with_log(chunk_raw_path, chunk_text)

            # Save chunk JSON
            chunk_json_path = os.path.join(chunks_dir, f"chunk{idx:03d}.json")
            write_file_with_log(
                chunk_json_path, json.dumps(chunk_words, ensure_ascii=False)
            )

            # Send to Gemini
            logs += update_log(
                f"  \U0001f504 Formatting chunk {idx}/{len(txt_chunks)} "
                f"({len(chunk_text)} chars, {len(chunk_words)} words)..."
            )
            formatted = do_gemini_format(chunk_text, api_key, model_name, chunk_idx=idx)

            if formatted:
                chunk_formed_path = os.path.join(chunks_dir, f"chunk{idx:03d}_formatted.txt")
                write_file_with_log(chunk_formed_path, formatted)
                formatted_chunks.append(formatted)
            else:
                logs += update_log(f"    \u274c Chunk {idx} formatting failed.")
    else:
        logs += update_log(f"  \U0001f504 Sending to Gemini for formatting...")
        formatted = do_gemini_format(raw_text, api_key, model_name, chunk_idx=1)
        if formatted:
            formatted_chunks.append(formatted)
        else:
            logs += update_log(f"  \u274c Formatting failed.")

    if not formatted_chunks:
        logs += update_log(f"  \u274c No chunks were successfully formatted.")
        return

    # ── Merge formatted chunks ──
    merged_formatted = "\n\n".join(formatted_chunks)
    merged_txt_path = os.path.join(base_dir, f"merged_formatted_{base_name}.txt")
    write_file_with_log(merged_txt_path, merged_formatted)
    logs += update_log(f"  \U0001f4dd Merged formatted text saved ({len(merged_formatted)} chars)")

    # ── Token-Anchored Alignment ──
    logs += update_log(f"  \U0001f517 Aligning formatted text against original timestamps...")
    try:
        g_clean_text = prepare_formatted_text_for_srt(merged_formatted)
        g_raw_words = tokenize_for_alignment(g_clean_text)
        logs += update_log(f"  \U0001f517 {len(g_raw_words)} Gemini words to align")

        aligned_words = align_words(g_raw_words, word_timestamps)
        logs += update_log(
            f"  \U0001f517 Alignment complete: {len(aligned_words)} aligned words "
            f"({sum(1 for a in aligned_words if a.get('source') == 'anchor')} anchors, "
            f"{sum(1 for a in aligned_words if a.get('source') == 'ghost')} ghosts)"
        )

        # ── 1.65x Duration Compensation (Harakat/voweling readability) ──
        for aw in aligned_words:
            duration = aw["end"] - aw["start"]
            aw["end"] = aw["start"] + duration * 1.65

        # ── Timebomb: drift detection ──
        original_total_end = max(w["end"] for w in word_timestamps) if word_timestamps else 0.0
        aligned_total_end = max(a["end"] for a in aligned_words) if aligned_words else 0.0
        drift = abs(aligned_total_end - original_total_end)
        threshold = max(5.0, original_total_end * 0.10)

        if drift > threshold:
            logs += update_log(
                f"  \u26a0\ufe0f TIMING DRIFT DETECTED: {drift:.1f}s "
                f"(threshold: {threshold:.1f}s) - ABORTING"
            )
            logs += update_log(
                "  \u274c Final .srt and .json not saved to prevent data corruption."
            )
            return

        logs += update_log(f"  \u2705 Alignment successful (Drift: {drift:.1f}s)")

        # Build final SRT
        final_srt = build_srt_from_aligned_words(aligned_words)
        final_srt_path = os.path.join(base_dir, f"merged_formatted_{base_name}.srt")
        write_file_with_log(final_srt_path, final_srt)

        # Build final aligned JSON
        final_json = []
        for aw in aligned_words:
            final_json.append({
                "word": aw["word"],
                "start": aw["start"],
                "end": aw["end"],
                "source": aw.get("source", "anchor"),
            })
        final_json_path = os.path.join(base_dir, f"merged_formatted_{base_name}.json")
        write_file_with_log(
            final_json_path, json.dumps(final_json, ensure_ascii=False)
        )

        # ── 4-Layer Hierarchy Output ──
        lesson_dir, lesson_name, part_dir, part_name = _get_hierarchy_paths(txt_path)

        # Layer 3: part-merged files (if input is inside a part folder)
        if part_dir and part_name:
            part_merged_srt = os.path.join(part_dir, f"{part_name}-merged.srt")
            write_file_with_log(part_merged_srt, final_srt)

            part_merged_json = os.path.join(part_dir, f"{part_name}-merged.json")
            write_file_with_log(
                part_merged_json, json.dumps(final_json, ensure_ascii=False)
            )

            part_merged_txt = os.path.join(part_dir, f"{part_name}-merged.txt")
            write_file_with_log(part_merged_txt, merged_formatted)

        # Layer 2: lesson total files
        lesson_total_srt = os.path.join(lesson_dir, f"{lesson_name}_total.srt")
        write_file_with_log(lesson_total_srt, final_srt)

        lesson_total_json = os.path.join(lesson_dir, f"{lesson_name}_total.json")
        write_file_with_log(
            lesson_total_json, json.dumps(final_json, ensure_ascii=False)
        )

        lesson_total_txt = os.path.join(lesson_dir, f"{lesson_name}_total.txt")
        write_file_with_log(lesson_total_txt, merged_formatted)

        logs += update_log(
            f"  \U0001f4c2 4-Layer output: "
            f"Layer2({lesson_name}_total) Layer3({part_name or '-'}-merged) "
            f"Layer4(segment files in chunks/)"
        )
        logs += update_log(f"  \u2705 Gemini formatting + alignment complete!")
    except Exception as e:
        logs += update_log(f"  \u274c Alignment failed: {str(e)}")


# ═══════════════════════════════════════════════════════════════
# Gradio Wrapper
# ═══════════════════════════════════════════════════════════════

def _resolve_upload(item):
    if item is None:
        return None
    if isinstance(item, dict):
        return item.get("path") or item.get("name")
    return getattr(item, "name", None)


def gradio_wrapper(single_file, multi_files, single_srt, single_json, multi_srt, multi_json, api_key_input, gemini_model):
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

    update_log("\U0001f680 Gemini-Only Formatter")
    update_log("=" * 52)

    api_key = api_key_input.strip() or GEMINI_API_KEY
    if not api_key:
        update_log("\u274c No Gemini API key. Set GEMINI_API_KEY env var or enter in UI.")
        return tail_logs()

    model_name = gemini_model or GEMINI_MODEL

    if not genai:
        update_log("\u274c google-genai package not installed.")
        return tail_logs()

    # ── Single file path ──
    if single_file:
        txt_path = _resolve_upload(single_file)
        srt_path = _resolve_upload(single_srt)
        json_path = _resolve_upload(single_json)

        if not txt_path:
            update_log("\u274c No .txt file provided.")
            return tail_logs()
        if not srt_path:
            update_log("\u274c No .srt file provided. Upload a matching .srt file.")
            return tail_logs()
        if not json_path:
            update_log("\u274c No .json file provided. Upload a matching .json file.")
            return tail_logs()

        process_gemini(txt_path, srt_path, json_path, api_key, model_name)
        gc.collect()
        update_log("\n\U0001f389 Single file processed!")
        return tail_logs()

    # ── Multi file path ──
    if multi_files:
        txt_list = [_resolve_upload(f) for f in multi_files if _resolve_upload(f)]
        srt_list = [_resolve_upload(f) for f in multi_srt if _resolve_upload(f)] if multi_srt else []
        json_list = [_resolve_upload(f) for f in multi_json if _resolve_upload(f)] if multi_json else []

        if not txt_list:
            update_log("\u274c No .txt files provided.")
            return tail_logs()

        if len(srt_list) != len(txt_list) or len(json_list) != len(txt_list):
            update_log(
                f"\u274c Mismatch: {len(txt_list)} txt, {len(srt_list)} srt, {len(json_list)} json. "
                "Upload equal numbers of each."
            )
            return tail_logs()

        for txt_path, srt_path, json_path in zip(txt_list, srt_list, json_list):
            process_gemini(txt_path, srt_path, json_path, api_key, model_name)
            gc.collect()

        update_log("\n\U0001f389 All files processed!")
        return tail_logs()

    update_log("\u274c No files selected.")
    return tail_logs()


# ═══════════════════════════════════════════════════════════════
# Gradio UI
# ═══════════════════════════════════════════════════════════════

with gr.Blocks(title="Gemini-Only Formatter") as demo:
    gr.Markdown("# \U0001f9ea Gemini-Only Formatter")
    gr.Markdown(
        "Format raw Whisper transcript text through Gemini with automatic "
        "SRT/JSON timestamp alignment."
    )

    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("### \U0001f4c1 Single File Mode")
                single_file = gr.File(
                    label="Upload .txt File",
                    file_types=[".txt"],
                    file_count="single",
                )
                single_srt = gr.File(
                    label="Upload Matching .srt File",
                    file_types=[".srt"],
                    file_count="single",
                )
                single_json = gr.File(
                    label="Upload Matching .json File",
                    file_types=[".json"],
                    file_count="single",
                )

            with gr.Group():
                gr.Markdown("### \U0001f4c1 Multiple File Mode")
                multi_files = gr.File(
                    label="Upload .txt Files (in order)",
                    file_types=[".txt"],
                    file_count="multiple",
                )
                multi_srt = gr.File(
                    label="Upload Matching .srt Files (same order)",
                    file_types=[".srt"],
                    file_count="multiple",
                )
                multi_json = gr.File(
                    label="Upload Matching .json Files (same order)",
                    file_types=[".json"],
                    file_count="multiple",
                )

            with gr.Group():
                gr.Markdown("### \u2699\ufe0f Gemini Settings")
                api_key_input = gr.Textbox(
                    label="API Key (or set GEMINI_API_KEY env var)",
                    placeholder="sk-...",
                    type="password",
                )
                gemini_model = gr.Dropdown(
                    choices=[
                        "gemini-3-flash-preview",
                        "gemini-3.5-flash",
                        "gemini-3.1-pro-preview",
                        "gemini-2.5-flash",
                    ],
                    value="gemini-3-flash-preview",
                    label="Select Gemini Model",
                )

            run_btn = gr.Button("\U0001f680 Run Gemini Formatting", variant="primary")

        with gr.Column(scale=2):
            log_box = gr.Textbox(
                label="Live Terminal Log",
                interactive=False,
                lines=25,
            )

    run_btn.click(
        fn=gradio_wrapper,
        inputs=[
            single_file, multi_files,
            single_srt, single_json,
            multi_srt, multi_json,
            api_key_input, gemini_model,
        ],
        outputs=log_box,
    )

    gr.Timer(1).tick(fn=tail_logs, outputs=log_box)


# ═══════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Gemini-Only Formatter")
        parser.add_argument("--file", help="Path to a single .txt file")
        parser.add_argument("--files", nargs="+", help="Paths to multiple .txt files")
        parser.add_argument("--api-key", help="Gemini API key (overrides GEMINI_API_KEY env var)")
        parser.add_argument("--model", default=GEMINI_MODEL, help="Gemini model name")
        args = parser.parse_args()

        api_key = args.api_key or GEMINI_API_KEY
        if not api_key:
            print("\u274c No Gemini API key. Set GEMINI_API_KEY or pass --api-key")
            sys.exit(1)

        targets = []
        if args.file:
            targets.append(args.file)
        if args.files:
            targets.extend(args.files)

        if not targets:
            parser.print_help()
            sys.exit(1)

        for t in targets:
            process_gemini(t, api_key, args.model)
    else:
        demo.launch(inbrowser=True)
