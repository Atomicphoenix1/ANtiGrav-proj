import os
import sys
import time
import re
import gc
import shutil
import subprocess
import torch
import json
import gradio as gr
import tkinter as tk
from tkinter import filedialog
from faster_whisper import WhisperModel
from google import genai
import concurrent.futures
import warnings

warnings.filterwarnings("ignore", message="torchcodec")



# =========================================================================
# ⚙️ PORTABILITY CONFIGURATION
# =========================================================================
GEMINI_API_KEY = "AQ.Ab8RN6L0epbx7yKIz0sl_M-hZPdTc_GH-0m9tiQuJg4J1APKVA"
V2_FORMATTER_DIR = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload"
WORD_TEMPLATE_PATH = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload\template.docx"

# 📡 n8n LOGGING BRIDGE
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "n8n_live_logs.txt")

def update_log(current_logs, new_msg):
    """Appends to Gradio log and writes to disk for n8n to read."""
    current_logs += new_msg + "\n"
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write(current_logs)
    except Exception:
        pass
    return current_logs

def resolve_original_path(file_path):
    """If the file is in a temp directory, try to find a matching file in the workspace or parent directories."""
    if not file_path:
        return None
    filename = os.path.basename(file_path)
    if "temp" in file_path.lower() or "appdata" in file_path.lower():
        parent_workspace = os.path.dirname(SCRIPT_DIR)
        for root, dirs, files in os.walk(parent_workspace):
            if filename in files:
                resolved = os.path.join(root, filename)
                if SCRIPT_DIR not in resolved:
                    return resolved
    return file_path

def write_file_with_log(file_path, content, current_logs):
    """Writes text to a file, calculates its character count, and prints to Gradio terminal."""
    try:
        abs_path = os.path.abspath(file_path)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        char_count = len(content)
        msg = f"💾 Saved file: {abs_path} | Character count: {char_count} chars."
        current_logs = update_log(current_logs, msg)
    except Exception as e:
        current_logs = update_log(current_logs, f"❌ Failed to save file {file_path}: {str(e)}")
    return current_logs

# =========================================================================
# ⚡️ NVIDIA DLL PATH INJECTOR & FORMATTER IMPORTS
# =========================================================================
python_base = os.path.dirname(sys.executable)
site_packages = os.path.join(python_base, "Lib", "site-packages")
nvidia_paths = [
    os.path.join(site_packages, "nvidia", "cublas", "bin"),
    os.path.join(site_packages, "nvidia", "cudnn", "bin"),
    os.path.join(site_packages, "nvidia", "cuda_nvrtc", "bin")
]
for path in nvidia_paths:
    if os.path.exists(path):
        os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
        if sys.version_info >= (3, 8):
            os.add_dll_directory(path)

sys.path.append(V2_FORMATTER_DIR)
try:
    from v2_formatter import format_document
    HAS_FORMATTER = True
except ImportError:
    HAS_FORMATTER = False

client = genai.Client(api_key=GEMINI_API_KEY)

ALL_AVAILABLE_MODELS = [
    "gemini-3-flash-preview", "gemini-3.5-flash", "gemini-3.1-pro-preview",
    "gemini-2.5-flash"
]

# =========================================================================
# SYSTEM PROMPT (SIMPLIFIED FOR NOW TO PREVENT BREAKING)
# =========================================================================
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
Example:
<speaker>قَالَ الْمُصَنِّفُ رَحِمَهُ اللَّهُ:</speaker>
<matn>
[نص الكتاب المشروح هنا مشكلاً بالكامل]
</matn>

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
مثال: <quran>﴿إِنَّ اللَّهَ وَمَلَائِكَتَهُ يُصَلُّونَ عَلَى النَّبِيِّ﴾</quran>

5. الأحاديث النبوية — `<hadith>`
توضع الأحاديث النبوية (سواء كانت حديثًا كاملاً أو جزءًا من حديث يستشهد به الشيخ) داخل وسم `<hadith>` محاطة بأقواس مربعة [...].
مثال: وَفِي قَوْلِهِ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ: <hadith>[فَهُوَ رَدٌّ]</hadith>

6. أسماء الكتب وأقوال العلماء والشعر — الأقواس المربعة فقط [...]
ضع أسماء الكتب والاقباسات المباشرة من العلماء أو أبيات الشعر داخل أقواس مربعة بدون أي وسوم إضافية.
- كتاب: فِي [مُغْنِي اللَّبِيبِ]
- قول عالم: قَالَ ابْنُ تَيْمِيَّةَ: [الْقَلْبُ مَعَ طُمَأْنِينَةِ السُّكُونِ يَرْجُو...]

7. التقسيمات والتصنيفات — `<strong>` و العناوين النقاطية
- لتنسيق التقسيمات (مثل: أحدهما، الآخر، أولها، ثانيها)، ضع الكلمة الدالة داخل وسم `<strong>`.
مثال الهيئة: وَهُوَ نَوْعَانِ: <strong>أَحَدُهُمَا:</strong> ..... <strong>وَالآخَرُ:</strong> .....
(تطبق هذه الطريقة بغض النظر عن عدد الأقسام المذكورة).
- عند وجود قائمة نقاطية أو تعداد، ابدأ كل عنصر بواصلة مسافة `- ` (Dash).

8. الألفاظ التعبدية والصلوات (Honorifics)
تُترك كلمات مثل "صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ"، "تَعَالَى"، "رَحِمَهُ اللَّهُ" كنص عادي مشكل تمامًا، ولا تضع حولها أي وسوم أو أقواس.

# رابعًا: علامات الترقيم وتقسيم الفقرات
1. تقسيم النص: قسّم الشرح والنص إلى فقرات واضحة ومستقلة حسب اكتمال المعنى وسياق الفكرة، حتى لو كان ذلك أثناء استرسال المتحدث نفسه.
2. قاعدة النقطة الصارمة: لا تضع علامة النقطة (.) مطلقًا في نص الشرح أو المتن إلا عند نهاية الفقرة التامة فقط. استخدم الفواصل (،) والفواصل المنقوطة (؛) والنقطتان (:) للفصل بين الجمل الداخلية لضمان استمرارية النص السليمة في خط المعالجة.

ملاحظة نهائية: ابدأ في إخراج النص مباشرة بناءً على هذه القواعد، ولا تضف أي مقدمات أو مؤخرات أو اعتذارات أو تعليقات جانبية.
"""

# =========================================================================
# CORE WORKER FUNCTIONS
# =========================================================================

# =========================================================================
# CORE WORKER FUNCTIONS
# =========================================================================

def chunk_text_15k(text, chunk_size=15000):
    """Chunks text into segments of ~15,000 characters, splitting cleanly at newlines."""
    chunks = []
    start = 0
    total_len = len(text)
    
    while start < total_len:
        if start + chunk_size >= total_len:
            chunks.append(text[start:])
            break
        
        # Look for the last newline before the chunk_size limit
        end = text.rfind('\n', start, start + chunk_size)
        if end == -1 or end <= start:
            # Fallback to the last space before the limit
            end = text.rfind(' ', start, start + chunk_size)
            if end == -1 or end <= start:
                # If neither is found, split at exact chunk_size
                end = start + chunk_size
        
        chunks.append(text[start:end].strip())
        start = end
        
    return chunks

def generate_srt_content(segments, offset=0):
    srt_lines = []
    for idx, seg in enumerate(segments, start=1):
        start = format_srt_time(seg["start"] + offset)
        end = format_srt_time(seg["end"] + offset)
        text = seg["text"].strip()
        srt_lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_lines), len(srt_lines)

def format_srt_time(seconds):
    ms = int(round((seconds % 1) * 1000))
    s = int(seconds)
    if ms >= 1000:
        ms -= 1000
        s += 1
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def clean_arabic_word(w):
    w = re.sub(r"[\u064B-\u065F\u0670]", "", w)
    w = re.sub(r"[إأآا]", "ا", w)
    w = re.sub(r"ى", "ي", w)
    w = re.sub(r"ة", "ه", w)
    w = re.sub(r"[^\w]", "", w)
    return w.lower()

def strip_html_tags(text):
    return re.sub(r"<[^>]+>", "", text)

def align_words(g_raw_words, all_W_words):
    G_clean = [clean_arabic_word(w) for w in g_raw_words]
    W_clean = [clean_arabic_word(w) for w, _, _ in all_W_words]
    
    aligned = []
    w_idx = 0
    w_len = len(all_W_words)
    
    for g_idx, g_word in enumerate(g_raw_words):
        g_c = G_clean[g_idx]
        if not g_c:
            prev_time = aligned[-1] if aligned else (0.0, 0.0)
            aligned.append((g_word, prev_time[1], prev_time[2]))
            continue
            
        matched_idx = -1
        for offset in range(50):
            test_idx = w_idx + offset
            if test_idx < w_len:
                if W_clean[test_idx] == g_c:
                    matched_idx = test_idx
                    break
        
        if matched_idx != -1:
            w_idx = matched_idx
            start, end = all_W_words[w_idx][1], all_W_words[w_idx][2]
            aligned.append((g_word, start, end))
            w_idx += 1
        else:
            curr_idx = min(w_idx, w_len - 1)
            if curr_idx >= 0:
                start, end = all_W_words[curr_idx][1], all_W_words[curr_idx][2]
            else:
                start, end = 0.0, 0.0
            aligned.append((g_word, start, end))
            
    return aligned

def build_srt_from_aligned_words(aligned_words):
    srt_lines = []
    idx = 1
    
    current_chunk = []
    max_words_per_seg = 10
    max_duration = 3.5
    
    for word, start, end in aligned_words:
        if not current_chunk:
            current_chunk.append((word, start, end))
        else:
            chunk_start = current_chunk[0][1]
            duration = end - chunk_start
            
            has_punctuation = any(char in word for char in [".", "،", "؟", "!"])
            if len(current_chunk) >= max_words_per_seg or duration > max_duration or has_punctuation:
                if has_punctuation and len(current_chunk) < max_words_per_seg:
                    current_chunk.append((word, start, end))
                    words_text = " ".join([w for w, _, _ in current_chunk])
                    c_start = current_chunk[0][1]
                    c_end = current_chunk[-1][2]
                    srt_lines.append(f"{idx}\n{format_srt_time(c_start)} --> {format_srt_time(c_end)}\n{words_text}\n")
                    idx += 1
                    current_chunk = []
                else:
                    words_text = " ".join([w for w, _, _ in current_chunk])
                    c_start = current_chunk[0][1]
                    c_end = current_chunk[-1][2]
                    srt_lines.append(f"{idx}\n{format_srt_time(c_start)} --> {format_srt_time(c_end)}\n{words_text}\n")
                    idx += 1
                    current_chunk = [(word, start, end)]
            else:
                current_chunk.append((word, start, end))
                
    if current_chunk:
        words_text = " ".join([w for w, _, _ in current_chunk])
        c_start = current_chunk[0][1]
        c_end = current_chunk[-1][2]
        srt_lines.append(f"{idx}\n{format_srt_time(c_start)} --> {format_srt_time(c_end)}\n{words_text}\n")
        
    return "\n".join(srt_lines)

def do_ffmpeg_split(file_path, base_logs, split_mode="10 min", custom_seconds=600):
    """Splits or moves a single MP3 into part folders based on the split_mode selection."""
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    parent_dir = os.path.dirname(file_path)
    
    base_logs = update_log(base_logs, f"📁 Preparing master folder for: {filename}")
    
    if "temp" in file_path.lower() or "appdata" in file_path.lower():
        target_folder = os.path.join(SCRIPT_DIR, base_name)
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        new_file_path = os.path.join(target_folder, filename)
        shutil.copy2(file_path, new_file_path)
        base_logs = update_log(base_logs, f"   ➡️ Copied temp file to workspace: {os.path.abspath(new_file_path)}")
    else:
        if os.path.basename(parent_dir) == base_name:
            target_folder = parent_dir
            new_file_path = file_path
        else:
            target_folder = os.path.join(parent_dir, base_name)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            new_file_path = os.path.join(target_folder, filename)
            shutil.move(file_path, new_file_path)
            base_logs = update_log(base_logs, f"   ➡️ Moved to folder: {os.path.abspath(new_file_path)}")

    if split_mode == "Full (No Split)":
        # Create a single part folder and place the whole MP3 there as seg001
        part_dir = os.path.join(target_folder, "part001")
        if not os.path.exists(part_dir):
            os.makedirs(part_dir)
        dest_path = os.path.join(part_dir, "part001_seg001.mp3")
        shutil.copy2(new_file_path, dest_path)
        base_logs = update_log(base_logs, "   ✅ Full mode selected (No Split). Created part001/part001_seg001.mp3.")
        return base_logs, target_folder

    # Determine segment time
    if split_mode == "10 min":
        seg_time = 600
    elif split_mode == "30 min":
        seg_time = 1800
    else:
        try:
            seg_time = int(custom_seconds)
        except ValueError:
            seg_time = 600

    # Split into temp files
    temp_pattern = os.path.join(target_folder, "temp_seg_%03d.mp3")
    cmd = [
        "ffmpeg", "-y", "-i", new_file_path,
        "-f", "segment", "-segment_time", str(seg_time),
        "-segment_start_number", "1", "-c", "copy",
        temp_pattern
    ]
    try:
        base_logs = update_log(base_logs, f"   ✂️ Slicing into {seg_time // 60}m {seg_time % 60}s segments...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Organize segments into part folders (pile up to 3 segments per folder)
        segments = sorted([f for f in os.listdir(target_folder) if f.startswith("temp_seg_") and f.endswith(".mp3")])
        for idx, seg_file in enumerate(segments, start=1):
            part_idx = (idx - 1) // 3 + 1
            seg_idx = (idx - 1) % 3 + 1
            part_dir = os.path.join(target_folder, f"part{part_idx:03d}")
            if not os.path.exists(part_dir):
                os.makedirs(part_dir)
            new_seg_name = f"part{part_idx:03d}_seg{seg_idx:03d}.mp3"
            shutil.move(os.path.join(target_folder, seg_file), os.path.join(part_dir, new_seg_name))
            
        base_logs = update_log(base_logs, f"   ✅ Segmentation complete! Organized into {(len(segments)-1)//3 + 1} part folder(s) (each containing up to 3 segments).")
    except Exception as e:
        base_logs = update_log(base_logs, f"   ❌ FFmpeg Error: {str(e)}")
    
    return base_logs, target_folder

def do_whisper_transcribe(audio_file_path, device, ft_model_ref, base_logs):
    """Transcribes a single audio file and returns (joined_text, segments_list, logs)."""
    filename = os.path.basename(audio_file_path)
    try:
        seg_start_time = time.time()
        segments_iter, info = ft_model_ref.transcribe(
            audio_file_path, beam_size=3, vad_filter=True, language="ar"
        )
        
        segments_list = []
        segment_text_list = []
        for segment in segments_iter:
            segment_text_list.append(segment.text.strip())
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            
        joined_segment_text = " ".join(segment_text_list)
        seg_time = time.time() - seg_start_time
        base_logs = update_log(base_logs, f"✅ Transcribed in {seg_time:.2f} seconds.")
        return joined_segment_text, segments_list, base_logs
    except Exception as e:
        base_logs = update_log(base_logs, f"❌ Whisper Error on {filename}: {str(e)}")
        return None, None, base_logs

def get_target_lesson_folder(file_path, default_base_name="Gemini"):
    if file_path:
        filename = os.path.basename(file_path)
        base_name = os.path.splitext(filename)[0]
        parent_dir = os.path.dirname(file_path)
        if "temp" in file_path.lower() or "appdata" in file_path.lower():
            target_folder = os.path.join(SCRIPT_DIR, base_name)
        else:
            target_folder = os.path.join(parent_dir, base_name)
    else:
        target_folder = os.path.join(SCRIPT_DIR, f"{default_base_name}_{int(time.time())}")
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
    return target_folder

def do_gemini_format(raw_text, gemini_model, base_logs, output_folder=None, chunk_idx=1, result_holder=None):
    """Sends text to Gemini with strict timeout, verifies >1.65x char count, and yields logs. Stores result in result_holder."""
    fallback_matrix = [gemini_model] + [m for m in ALL_AVAILABLE_MODELS if m != gemini_model]
    formatted_text = None
    prompt = get_gemini_prompt(raw_text)
    len_input = len(raw_text)

    for model_name in fallback_matrix:
        base_logs = update_log(base_logs, f"🔄 Engaging Model: {model_name}...")
        yield base_logs
        for attempt in range(1, 3): 
            try:
                base_logs = update_log(base_logs, f"   ⏳ [Attempt {attempt}/2] Strict Time-Bomb Active (3.5 Mins)...")
                yield base_logs
                # Configure low temperature to force strict instruction adherence and reduce laziness
                chat = client.chats.create(model=model_name, config={'temperature': 0.1})
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(chat.send_message, prompt)
                    response = future.result(timeout=210)
                
                temp_text = response.text
                if temp_text:
                    len_output = len(temp_text)
                    if len_output > 1.65 * len_input:
                        base_logs = update_log(base_logs, f"   ✅ SUCCESS! Character count check PASSED: output ({len_output}) > 1.65x input ({len_input}).")
                        formatted_text = temp_text
                        yield base_logs
                        break
                    else:
                        base_logs = update_log(base_logs, f"   ⚠️ SUCCESS but FAILED character count check: output ({len_output}) is NOT strictly above 1.65x input ({len_input}). harakat/tags might be incomplete. Saving failed output for inspection...")
                        yield base_logs
                        # Save failed trial output for user inspection inside output_folder as failed_chunkX.txt
                        target_dir = output_folder if output_folder else SCRIPT_DIR
                        failed_path = os.path.join(target_dir, f"failed_chunk{chunk_idx}.txt")
                        try:
                            with open(failed_path, "w", encoding="utf-8") as f_fail:
                                f_fail.write(temp_text)
                            base_logs = update_log(base_logs, f"   💾 Saved failed trial output to: {os.path.basename(failed_path)}")
                        except Exception as save_err:
                            base_logs = update_log(base_logs, f"   ❌ Failed to save trial output: {str(save_err)}")
                        yield base_logs
                else:
                    base_logs = update_log(base_logs, f"   ⚠️ Failed: Empty response received.")
                    yield base_logs
                
                if attempt < 2: time.sleep(3)
            except concurrent.futures.TimeoutError:
                base_logs = update_log(base_logs, f"   ⚠️ Failed: CONNECTION TIMED OUT.")
                yield base_logs
                if attempt < 2: time.sleep(3)
            except Exception as e:
                base_logs = update_log(base_logs, f"   ⚠️ Failed: {str(e)}")
                yield base_logs
                if attempt < 2: time.sleep(3)
                
        if formatted_text: 
            break
        else: 
            base_logs = update_log(base_logs, f"❌ {model_name} failed to deliver valid fully-diacritized output. Switching models...")
            yield base_logs

    if result_holder is not None:
        result_holder['formatted_text'] = formatted_text
    yield base_logs

# =========================================================================
# THE MASTER ROUTER
# =========================================================================
def execute_pipeline(op_mode, scope, single_audio, multi_audio, folder_input, 
                     single_txt, multi_txt, text_box, device, gemini_model,
                     split_mode="10 min", custom_seconds=600, srt_txt_file=None, srt_json_file=None):
    
    # Initialize Log
    logs = update_log("", f"🚀 PIPELINE STARTED\nOperation: {op_mode}\nMode: {scope}\n" + "="*40)
    yield logs

    # Calculate seg_time based on split choices
    if split_mode == "10 min":
        seg_time = 600
    elif split_mode == "30 min":
        seg_time = 1800
    elif split_mode == "Full (No Split)":
        seg_time = 0
    else:
        try:
            seg_time = int(custom_seconds)
        except ValueError:
            seg_time = 600

    # ---------------------------------------------------------
    # 0. SRT ALIGNMENT MODE
    # ---------------------------------------------------------
    if op_mode == "SRT Alignment":
        if srt_txt_file and srt_json_file:
            logs = update_log(logs, "📝 Initiating SRT Alignment mode...")
            yield logs
            try:
                # Read Formatted TXT
                with open(srt_txt_file.name, "r", encoding="utf-8") as f:
                    formatted_text = f.read()
                
                # Read Timestamps JSON
                with open(srt_json_file.name, "r", encoding="utf-8") as f:
                    all_W_words = json.load(f)
                
                logs = update_log(logs, f"📖 Loaded {len(formatted_text)} chars of text and {len(all_W_words)} word timestamps.")
                yield logs
                
                # Align words
                g_clean_text = strip_html_tags(formatted_text)
                g_raw_words = g_clean_text.strip().split()
                
                aligned_words = align_words(g_raw_words, all_W_words)
                
                # Build SRT
                final_srt_txt = build_srt_from_aligned_words(aligned_words)
                
                base_dir = os.path.dirname(srt_txt_file.name)
                base_name = os.path.splitext(os.path.basename(srt_txt_file.name))[0]
                out_srt_path = os.path.join(base_dir, f"{base_name}_Aligned.srt")
                
                logs = write_file_with_log(out_srt_path, final_srt_txt, logs)
                logs = update_log(logs, f"🎉 SRT Alignment completed successfully!")
            except Exception as e:
                logs = update_log(logs, f"❌ Failed SRT alignment: {str(e)}")
            yield logs
            return
        else:
            logs = update_log(logs, "❌ Error: SRT Alignment mode requires both formatted text and timestamps JSON file.")
            yield logs
            return

    # Helper function to process a single lesson folder
    def process_lesson_folder(lesson_folder, ft_model_ref, seg_time):
        nonlocal logs
        lesson_name = os.path.basename(lesson_folder)
        logs = update_log(logs, f"\n{'='*40}\n📁 Processing Lesson: {lesson_name}\n{'='*40}")
        yield logs

        # Find part subfolders
        part_dirs = sorted([
            os.path.join(lesson_folder, d)
            for d in os.listdir(lesson_folder)
            if os.path.isdir(os.path.join(lesson_folder, d)) and re.match(r"^part\d+$", d.lower())
        ])
        
        all_gemini_outputs = []
        all_whisper_segments = []
        
        for part_dir in part_dirs:
            part_name = os.path.basename(part_dir)
            part_idx = int(re.search(r"\d+", part_name).group())
            
            logs = update_log(logs, f"\n📂 Processing {part_name}...")
            yield logs
            
            # Find segment MP3s
            seg_mp3s = sorted([
                f for f in os.listdir(part_dir)
                if f.lower().endswith(".mp3") and "seg" in f.lower()
            ])
            
            part_raw_transcripts = []
            
            for seg_file in seg_mp3s:
                seg_idx = int(re.search(r"seg(\d+)", seg_file.lower()).group(1))
                global_seg_idx = (part_idx - 1) * 3 + seg_idx
                offset = (global_seg_idx - 1) * seg_time
                
                logs = update_log(logs, f"🎙️ Transcribing segment: {seg_file} (offset: {format_srt_time(offset)})...")
                yield logs
                
                txt, segments, logs = do_whisper_transcribe(os.path.join(part_dir, seg_file), device, ft_model_ref, logs)
                yield logs
                
                if txt:
                    # Save raw text segment
                    seg_base = os.path.splitext(seg_file)[0]
                    txt_name = f"{seg_base}.txt"
                    logs = write_file_with_log(os.path.join(part_dir, txt_name), txt, logs)
                    
                    part_raw_transcripts.append(txt)
                    
                    # Accumulate Whisper segments with offset
                    for seg in segments:
                        all_whisper_segments.append({
                            "start": seg["start"] + offset,
                            "end": seg["end"] + offset,
                            "text": seg["text"]
                        })
            
            # Write part level merged files
            if part_raw_transcripts:
                merged_raw_txt = " ".join(part_raw_transcripts)
                logs = write_file_with_log(os.path.join(part_dir, f"{part_name}_Merged_Raw.txt"), merged_raw_txt, logs)
                
                # Send chunked raw text to Gemini
                txt_chunks = chunk_text_15k(merged_raw_txt, chunk_size=15000)
                formatted_chunks = []
                
                logs = update_log(logs, f"⚙️ Chunked raw text into {len(txt_chunks)} part(s) (~15k chars each) for Gemini formatting.")
                yield logs
                
                for c_idx, chunk in enumerate(txt_chunks, start=1):
                    # Output chunk as text
                    chunk_raw_path = os.path.join(part_dir, f"{part_name}_Raw_Chunk_{c_idx:03d}.txt")
                    logs = write_file_with_log(chunk_raw_path, chunk, logs)
                    
                    logs = update_log(logs, f"🔄 Formatting chunk {c_idx}/{len(txt_chunks)} ({len(chunk)} chars)...")
                    yield logs
                    
                    res_holder = {}
                    for updated_logs in do_gemini_format(chunk, gemini_model, logs, output_folder=part_dir, chunk_idx=c_idx, result_holder=res_holder):
                        logs = updated_logs
                        yield logs
                    formatted_chunk = res_holder.get("formatted_text")
                    
                    if formatted_chunk:
                        # Output formatted chunk as text
                        chunk_formatted_path = os.path.join(part_dir, f"{part_name}_Formatted_Chunk_{c_idx:03d}.txt")
                        logs = write_file_with_log(chunk_formatted_path, formatted_chunk, logs)
                        formatted_chunks.append(formatted_chunk)
                
                if formatted_chunks:
                    formatted_txt = "\n\n".join(formatted_chunks)
                    logs = write_file_with_log(os.path.join(part_dir, f"{part_name}_Formatted.txt"), formatted_txt, logs)
                    all_gemini_outputs.append(formatted_txt)

        # Merge lesson-level files
        if all_gemini_outputs:
            final_formatted_txt = "\n\n".join(all_gemini_outputs)
            final_formatted_path = os.path.join(lesson_folder, f"{lesson_name}_Final_Merged_Formatted.txt")
            logs = write_file_with_log(final_formatted_path, final_formatted_txt, logs)
            
            # Programmatic alignment to generate Gemini-aligned Total SRT!
            logs = update_log(logs, f"📝 Aligning Gemini formatted text with Whisper timestamps to generate final SRT...")
            yield logs
            try:
                # Get word-level timestamps
                all_W_words = []
                for seg in all_whisper_segments:
                    seg_text = seg["text"].strip()
                    if not seg_text:
                        continue
                    words = seg_text.split()
                    num_words = len(words)
                    duration = seg["end"] - seg["start"]
                    for idx, w in enumerate(words):
                        w_start = seg["start"] + idx * (duration / num_words)
                        w_end = seg["start"] + (idx + 1) * (duration / num_words)
                        all_W_words.append((w, w_start, w_end))
                
                # Save word-level timestamps JSON (can be used for instant SRT Alignment later!)
                ts_path = os.path.join(lesson_folder, f"{lesson_name}_Timestamps.json")
                logs = write_file_with_log(ts_path, json.dumps(all_W_words, ensure_ascii=False), logs)
                
                # Tokenize Gemini output (strip HTML tags)
                g_clean_text = strip_html_tags(final_formatted_txt)
                g_raw_words = g_clean_text.strip().split()
                
                # Align words
                aligned_words = align_words(g_raw_words, all_W_words)
                
                # Build SRT
                final_srt_txt = build_srt_from_aligned_words(aligned_words)
                
                logs = write_file_with_log(os.path.join(lesson_folder, f"{lesson_name}_Total.srt"), final_srt_txt, logs)
                logs = update_log(logs, f"✅ Total SRT file generated successfully!")
            except Exception as e:
                logs = update_log(logs, f"❌ Failed to align SRT: {str(e)}")
            yield logs
                
            if HAS_FORMATTER:
                doc_path = os.path.join(lesson_folder, f"{lesson_name}_Final.docx")
                logs = update_log(logs, f"📄 Formatting Word Document & PDF...")
                yield logs
                try:
                    format_document(final_formatted_path, WORD_TEMPLATE_PATH, doc_path)
                    logs = update_log(logs, f"✅ Word Doc and PDF generated successfully!")
                except Exception as e:
                    logs = update_log(logs, f"❌ Formatter failed: {str(e)}")
                yield logs

        # Write permanent processing telemetry log
        try:
            with open(os.path.join(lesson_folder, f"{lesson_name}_Execution_Report.log"), "w", encoding="utf-8") as f:
                f.write(logs)
        except Exception:
            pass

    # ---------------------------------------------------------
    # 1. MP3 SPLITTER
    # ---------------------------------------------------------
    if op_mode == "MP3 Splitter":
        if scope == "Singular" and single_audio:
            logs = update_log(logs, f"🎬 Initiating split for single audio file...")
            yield logs
            logs, target_folder = do_ffmpeg_split(single_audio.name, logs, split_mode, custom_seconds)
            yield logs
            
        elif scope == "Bulk":
            if multi_audio:
                for f in multi_audio:
                    logs = update_log(logs, f"🎬 Initiating split for: {f.name}...")
                    yield logs
                    logs, target_folder = do_ffmpeg_split(f.name, logs, split_mode, custom_seconds)
                    yield logs
            if folder_input and os.path.exists(folder_input):
                for root, dirs, files in os.walk(folder_input):
                    for file in files:
                        if file.lower().endswith('.mp3') and not any(part in os.path.join(root, file).lower() for part in ["part", "seg"]):
                            logs = update_log(logs, f"🎬 Initiating split for: {file}...")
                            yield logs
                            logs, target_folder = do_ffmpeg_split(os.path.join(root, file), logs, split_mode, custom_seconds)
                            yield logs
        
        logs = update_log(logs, "\n🎉 All Audio Segmentation Finished!")
        yield logs
        return

    # ---------------------------------------------------------
    # 2. WHISPER ONLY
    # ---------------------------------------------------------
    elif op_mode == "Whisper Only":
        logs = update_log(logs, "🤖 Loading Whisper Model into VRAM...")
        yield logs
        compute_type = "int8_float16" if device == "cuda" else "int8"
        ft_model = WhisperModel("dev-ahmedhany/whisper-large-v3-arabic-ft-v3-ct2-int8", device=device, compute_type=compute_type)

        def process_whisper(file_path, current_logs):
            current_logs = update_log(current_logs, f"🎙️ Transcribing: {os.path.basename(file_path)}...")
            # Yielding here so UI updates
            return do_whisper_transcribe(file_path, device, ft_model, current_logs)

        if scope == "Singular" and single_audio:
            logs = update_log(logs, "🎙️ Starting singular Whisper transcription...")
            yield logs
            txt, segments, logs = process_whisper(single_audio.name, logs)
            if txt:
                base_name = os.path.splitext(single_audio.name)[0]
                out_path = f"{base_name}_Whisper.txt"
                logs = write_file_with_log(out_path, txt, logs)
                
                srt_path = f"{base_name}_Whisper.srt"
                srt_content, _ = generate_srt_content(segments, offset=0)
                logs = write_file_with_log(srt_path, srt_content, logs)
                
                # Save timestamps
                all_W_words = []
                for seg in segments:
                    seg_text = seg["text"].strip()
                    if not seg_text: continue
                    words = seg_text.split()
                    num_words = len(words)
                    duration = seg["end"] - seg["start"]
                    for idx, w in enumerate(words):
                        w_start = seg["start"] + idx * (duration / num_words)
                        w_end = seg["start"] + (idx + 1) * (duration / num_words)
                        all_W_words.append((w, w_start, w_end))
                ts_path = f"{base_name}_Timestamps.json"
                logs = write_file_with_log(ts_path, json.dumps(all_W_words, ensure_ascii=False), logs)
            yield logs
        elif scope == "Bulk" and multi_audio:
            for f in multi_audio:
                txt, segments, logs = process_whisper(f.name, logs)
                if txt:
                    base_name = os.path.splitext(f.name)[0]
                    out_path = f"{base_name}_Whisper.txt"
                    logs = write_file_with_log(out_path, txt, logs)
                    
                    srt_path = f"{base_name}_Whisper.srt"
                    srt_content, _ = generate_srt_content(segments, offset=0)
                    logs = write_file_with_log(srt_path, srt_content, logs)
                    
                    # Save timestamps
                    all_W_words = []
                    for seg in segments:
                        seg_text = seg["text"].strip()
                        if not seg_text: continue
                        words = seg_text.split()
                        num_words = len(words)
                        duration = seg["end"] - seg["start"]
                        for idx, w in enumerate(words):
                            w_start = seg["start"] + idx * (duration / num_words)
                            w_end = seg["start"] + (idx + 1) * (duration / num_words)
                            all_W_words.append((w, w_start, w_end))
                    ts_path = f"{base_name}_Timestamps.json"
                    logs = write_file_with_log(ts_path, json.dumps(all_W_words, ensure_ascii=False), logs)
                yield logs

        del ft_model
        gc.collect()
        if device == "cuda": torch.cuda.empty_cache()
        logs = update_log(logs, "\n🎉 Whisper Transcription Finished!")
        yield logs
        return

    # ---------------------------------------------------------
    # 3. GEMINI API ONLY
    # ---------------------------------------------------------
    elif op_mode == "Gemini Only":
        def get_gemini_folders(file_path):
            if file_path:
                resolved_path = resolve_original_path(file_path)
                parent_dir = os.path.dirname(resolved_path)
                parent_name = os.path.basename(parent_dir)
                if re.match(r"^part\d+$", parent_name.lower()):
                    part_dir = parent_dir
                    part_name = parent_name
                    lesson_folder = os.path.dirname(part_dir)
                    lesson_name = os.path.basename(lesson_folder)
                else:
                    lesson_name = os.path.splitext(os.path.basename(resolved_path))[0]
                    if "temp" in parent_dir.lower() or "appdata" in parent_dir.lower():
                        lesson_folder = os.path.join(SCRIPT_DIR, lesson_name)
                    else:
                        lesson_folder = os.path.join(parent_dir, lesson_name)
                    part_name = "part001"
                    part_dir = os.path.join(lesson_folder, part_name)
            else:
                lesson_name = f"Gemini_{int(time.time())}"
                lesson_folder = os.path.join(SCRIPT_DIR, lesson_name)
                part_name = "part001"
                part_dir = os.path.join(lesson_folder, part_name)
            
            if not os.path.exists(lesson_folder):
                os.makedirs(lesson_folder)
            if not os.path.exists(part_dir):
                os.makedirs(part_dir)
            return lesson_folder, lesson_name, part_dir, part_name

        def process_gemini(raw_text, lesson_folder, lesson_name, part_dir, part_name, current_logs):
            current_logs = update_log(current_logs, f"\n{'='*40}\n📁 Processing Gemini Lesson: {lesson_name}\n{'='*40}")
            yield current_logs

            txt_chunks = chunk_text_15k(raw_text, chunk_size=15000)
            formatted_chunks = []
            current_logs = update_log(current_logs, f"⚙️ Chunked raw text into {len(txt_chunks)} part(s) (~15k chars each) for Gemini formatting.")
            yield current_logs

            for idx, chunk in enumerate(txt_chunks, start=1):
                if len(txt_chunks) > 1:
                    chunk_raw_path = os.path.join(part_dir, f"{part_name}_Raw_Chunk_{idx:03d}.txt")
                    current_logs = write_file_with_log(chunk_raw_path, chunk, current_logs)
                    yield current_logs

                current_logs = update_log(current_logs, f"🔄 Formatting chunk {idx}/{len(txt_chunks)} ({len(chunk)} chars)...")
                yield current_logs

                res_holder = {}
                for updated_logs in do_gemini_format(chunk, gemini_model, current_logs, output_folder=part_dir, chunk_idx=idx, result_holder=res_holder):
                    current_logs = updated_logs
                    yield current_logs
                
                formatted_chunk = res_holder.get("formatted_text")
                if formatted_chunk:
                    if len(txt_chunks) > 1:
                        chunk_formatted_path = os.path.join(part_dir, f"{part_name}_Formatted_Chunk_{idx:03d}.txt")
                        current_logs = write_file_with_log(chunk_formatted_path, formatted_chunk, current_logs)
                    formatted_chunks.append(formatted_chunk)
                    yield current_logs
            
            if formatted_chunks:
                formatted_txt = "\n\n".join(formatted_chunks)
                part_formatted_path = os.path.join(part_dir, f"{part_name}_Formatted.txt")
                current_logs = write_file_with_log(part_formatted_path, formatted_txt, current_logs)

                final_formatted_txt = "\n\n".join(formatted_chunks)
                final_formatted_path = os.path.join(lesson_folder, f"{lesson_name}_Final_Merged_Formatted.txt")
                current_logs = write_file_with_log(final_formatted_path, final_formatted_txt, current_logs)
                yield current_logs
                
                if HAS_FORMATTER:
                    doc_path = os.path.join(lesson_folder, f"{lesson_name}_Final.docx")
                    current_logs = update_log(current_logs, f"📄 Formatting Word Document & PDF...")
                    yield current_logs
                    try:
                        format_document(final_formatted_path, WORD_TEMPLATE_PATH, doc_path)
                        current_logs = update_log(current_logs, f"✅ Word Doc and PDF generated successfully!")
                    except Exception as e:
                        current_logs = update_log(current_logs, f"❌ Formatter failed: {str(e)}")
                    yield current_logs
            else:
                current_logs = update_log(current_logs, f"❌ Formatting failed - no chunks formatted successfully.")
                yield current_logs

        if scope == "Singular":
            combined_text = (text_box.strip() + "\n\n") if text_box else ""
            if single_txt:
                with open(single_txt.name, "r", encoding="utf-8") as tf: combined_text += tf.read()
                file_to_resolve = single_txt.name
            else:
                file_to_resolve = None
            
            lesson_folder, lesson_name, part_dir, part_name = get_gemini_folders(file_to_resolve)
            
            if combined_text.strip():
                logs = update_log(logs, "⚙️ Processing Gemini singular text...")
                yield logs
                for updated_logs in process_gemini(combined_text, lesson_folder, lesson_name, part_dir, part_name, logs):
                    logs = updated_logs
                    yield logs
                
        elif scope == "Bulk" and multi_txt:
            for f in multi_txt:
                try:
                    with open(f.name, "r", encoding="utf-8") as tf: text_data = tf.read()
                    lesson_folder, lesson_name, part_dir, part_name = get_gemini_folders(f.name)
                    logs = update_log(logs, f"⚙️ Processing Gemini bulk file: {f.name}...")
                    yield logs
                    for updated_logs in process_gemini(text_data, lesson_folder, lesson_name, part_dir, part_name, logs):
                        logs = updated_logs
                        yield logs
                except Exception as e:
                    logs = update_log(logs, f"❌ Failed to read {f.name}: {e}\n")
                    yield logs

        logs = update_log(logs, "\n🎉 Gemini Formatting Finished!")
        yield logs
        return

    # ---------------------------------------------------------
    # 4. WHISPER + GEMINI
    # ---------------------------------------------------------
    elif op_mode == "Whisper + Gemini":
        logs = update_log(logs, "🤖 Loading Whisper Model into VRAM...")
        yield logs
        compute_type = "int8_float16" if device == "cuda" else "int8"
        ft_model = WhisperModel("dev-ahmedhany/whisper-large-v3-arabic-ft-v3-ct2-int8", device=device, compute_type=compute_type)

        # -- Singular Scope --
        if scope == "Singular" and single_audio:
            logs = update_log(logs, f"🎬 Splitting single audio file: {single_audio.name}...")
            yield logs
            logs, lesson_folder = do_ffmpeg_split(single_audio.name, logs, split_mode, custom_seconds)
            yield logs
            
            # Process the created folder hierarchy
            for log_chunk in process_lesson_folder(lesson_folder, ft_model, seg_time):
                yield log_chunk

        # -- Bulk Scope --
        elif scope == "Bulk" and folder_input and os.path.exists(folder_input):
            subfolders = [
                os.path.join(folder_input, d)
                for d in os.listdir(folder_input)
                if os.path.isdir(os.path.join(folder_input, d))
            ]
            for folder in subfolders:
                # If the folder doesn't have part subdirs yet, try splitting any base MP3 inside
                part_subdirs = [d for d in os.listdir(folder) if os.path.isdir(os.path.join(folder, d)) and re.match(r"^part\d+$", d.lower())]
                if not part_subdirs:
                    all_mp3s = [f for f in os.listdir(folder) if f.lower().endswith('.mp3')]
                    base_mp3 = None
                    for f in all_mp3s:
                        if not any(part in f.lower() for part in ["part", "seg"]):
                            base_mp3 = f
                            break
                    if base_mp3:
                        logs = update_log(logs, f"🎬 Splitting base audio inside folder: {base_mp3}...")
                        yield logs
                        logs, folder = do_ffmpeg_split(os.path.join(folder, base_mp3), logs, split_mode, custom_seconds)
                        yield logs
                
                for log_chunk in process_lesson_folder(folder, ft_model, seg_time):
                    yield log_chunk

        del ft_model
        gc.collect()
        if device == "cuda": torch.cuda.empty_cache()
        logs = update_log(logs, "\n🎉 Bulk Whisper + Gemini Finished!")
        yield logs


# =========================================================================
# TKINTER WINDOW FOR BROWSE FUNCTION
# =========================================================================
def browse_folder():
    root = tk.Tk()
    root.withdraw() 
    root.attributes('-topmost', True) 
    folder_selected = filedialog.askdirectory()
    root.destroy()
    return folder_selected


# =========================================================================
# GRADIO UI SETUP (UNIFIED)
# =========================================================================
def toggle_inputs(op, scope, split):
    """Dynamically shows/hides UI elements based on selection."""
    is_audio_sing = op in ["Whisper Only", "MP3 Splitter", "Whisper + Gemini"] and scope == "Singular"
    is_audio_bulk = op in ["Whisper Only", "MP3 Splitter"] and scope == "Bulk"
    is_gemini_sing = op == "Gemini Only" and scope == "Singular"
    is_gemini_bulk = op == "Gemini Only" and scope == "Bulk"
    is_folder_bulk = op in ["MP3 Splitter", "Whisper + Gemini"] and scope == "Bulk"
    is_splitter_op = op in ["MP3 Splitter", "Whisper + Gemini"]
    is_srt_align = op == "SRT Alignment"
    
    return [
        gr.update(visible=is_audio_sing),  # single_audio
        gr.update(visible=is_audio_bulk),  # multi_audio
        gr.update(visible=is_gemini_sing),  # single_txt
        gr.update(visible=is_gemini_bulk),  # multi_txt
        gr.update(visible=is_gemini_sing),  # text_box
        gr.update(visible=is_folder_bulk),  # folder_row
        gr.update(visible=is_splitter_op),  # split_mode
        gr.update(visible=(is_splitter_op and split == "Custom")), # custom_seconds
        gr.update(visible=is_srt_align),  # srt_txt_file
        gr.update(visible=is_srt_align)   # srt_json_file
    ]

with gr.Blocks(title="Super Uploader V8") as demo:
    gr.Markdown("# 🎙️ Ultimate Audio & Text Suite V8 (Unified Routing & Skippable Chunks)")
    
    with gr.Row():
        with gr.Column():
            op_mode = gr.Radio(["Whisper Only", "MP3 Splitter", "Gemini Only", "Whisper + Gemini", "SRT Alignment"], value="Whisper + Gemini", label="1. Select Operation")
            scope_mode = gr.Radio(["Singular", "Bulk"], value="Singular", label="2. Select Scope")
            
        with gr.Column():
            device_dd = gr.Dropdown(choices=["cuda", "cpu"], value="cuda", label="Hardware Acceleration")
            model_dd = gr.Dropdown(choices=ALL_AVAILABLE_MODELS, value="gemini-3-flash-preview", label="Gemini Model")

    gr.Markdown("---")
    
    with gr.Group():
        single_audio = gr.File(label="Upload MP3 File", file_count="single", visible=True)
        multi_audio = gr.File(label="Upload Multiple MP3 Files", file_count="multiple", visible=False)
        single_txt = gr.File(label="Upload Single Text File", file_count="single", visible=False)
        multi_txt = gr.File(label="Upload Multiple Text Files", file_count="multiple", visible=False)
        text_box = gr.Textbox(label="Or Paste Text/Markdown (Clipboard)", lines=5, visible=False)
        
        # New SRT Alignment Uploads
        srt_txt_file = gr.File(label="Upload Formatted Text (.txt)", file_count="single", visible=False)
        srt_json_file = gr.File(label="Upload Timestamps JSON (.json)", file_count="single", visible=False)
        
        # New Splitter Options
        with gr.Row():
            split_mode = gr.Radio(["10 min", "30 min", "Custom", "Full (No Split)"], value="10 min", label="MP3 Segment Slicing Mode", visible=True)
            custom_seconds = gr.Number(value=600, label="Custom Slicing Duration (seconds)", visible=False)
        

        with gr.Row(visible=False) as folder_row:
            folder_input = gr.Textbox(label="Master Folder Path", scale=4)
            folder_browse = gr.Button("📁 Browse Folder", scale=1)

    submit_btn = gr.Button("🚀 Run Pipeline", variant="primary")
    log_output = gr.Textbox(label="Live Terminal Output", interactive=False, lines=20)

    # Listeners
    folder_browse.click(fn=browse_folder, outputs=folder_input)
    
    inputs_list = [
        single_audio, multi_audio, single_txt, multi_txt, text_box, 
        folder_row, split_mode, custom_seconds, srt_txt_file, srt_json_file
    ]
    
    # Auto-update elements visibility based on operation, scope, and split settings
    op_mode.change(toggle_inputs, inputs=[op_mode, scope_mode, split_mode], outputs=inputs_list)
    scope_mode.change(toggle_inputs, inputs=[op_mode, scope_mode, split_mode], outputs=inputs_list)
    split_mode.change(toggle_inputs, inputs=[op_mode, scope_mode, split_mode], outputs=inputs_list)

    submit_btn.click(
        fn=execute_pipeline,
        inputs=[
            op_mode, scope_mode, single_audio, multi_audio, folder_input, 
            single_txt, multi_txt, text_box, device_dd, model_dd, 
            split_mode, custom_seconds, srt_txt_file, srt_json_file
        ],
        outputs=log_output
    )

if __name__ == "__main__":
    demo.queue().launch(inbrowser=True)