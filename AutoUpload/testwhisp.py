"""
testwhisp.py  --  Standalone Whisper transcription utility.

Extracted from Super-Uploader.py (do_whisper_transcribe, master-folder merge)
for independent CLI/GUI use.  Fully self-contained.

Usage (CLI):
    python testwhisp.py --file <path>
    python testwhisp.py --files <path1> <path2> ...
    python testwhisp.py --folder <dir>
    python testwhisp.py --file <path> --device cpu

Usage (GUI):
    python testwhisp.py
"""

import os
import sys
import json
import time
import re
import gc
import shutil
import argparse
import tkinter as tk
from tkinter import filedialog
import gradio as gr

try:
    import torch
except ImportError:
    torch = None

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

python_base = os.path.dirname(sys.executable)
site_packages = os.path.join(python_base, "Lib", "site-packages")
nvidia_paths = [
    os.path.join(site_packages, "nvidia", "cublas", "bin"),
    os.path.join(site_packages, "nvidia", "cudnn", "bin"),
    os.path.join(site_packages, "nvidia", "cuda_nvrtc", "bin"),
]
for p in nvidia_paths:
    if os.path.exists(p):
        os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]
        if sys.version_info >= (3, 8):
            os.add_dll_directory(p)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(SCRIPT_DIR, "n8n_live_logs.txt")
WORKSPACE = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Split-Vault"

WHISPER_MODEL_ID = "dev-ahmedhany/whisper-large-v3-arabic-ft-v3-ct2-int8"

_model_cache = {"model": None, "device": None}


def get_device():
    if torch is not None and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def get_whisper_model(device):
    if _model_cache["model"] is not None and _model_cache["device"] == device:
        return _model_cache["model"]
    compute_type = "int8_float16" if device == "cuda" else "int8"
    model = WhisperModel(WHISPER_MODEL_ID, device=device, compute_type=compute_type)
    _model_cache["model"] = model
    _model_cache["device"] = device
    return model


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
        msg = f"  💾 Saved file: {abs_path} | {char_count} chars."
        update_log(msg)
    except Exception as e:
        update_log(f"  ❌ Failed to save file {file_path}: {str(e)}")


def format_srt_time(seconds):
    ms = int(round((seconds % 1) * 1000))
    s = int(seconds)
    if ms >= 1000:
        ms -= 1000
        s += 1
    m, s_remaining = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s_remaining:02d},{ms:03d}"


def generate_srt_content(segments, offset=0):
    srt_lines = []
    for idx, seg in enumerate(segments, start=1):
        start = format_srt_time(seg["start"] + offset)
        end = format_srt_time(seg["end"] + offset)
        text = seg["text"].strip()
        srt_lines.append(f"{idx}\n{start} --> {end}\n{text}\n")
    return "\n".join(srt_lines), len(srt_lines)


def normalize_whisper_words(all_w_words):
    normalized = []
    for item in all_w_words or []:
        if isinstance(item, dict):
            word = item.get("word", "")
            start = item.get("start")
            end = item.get("end")
        else:
            if len(item) < 3:
                continue
            word, start, end = item[0], item[1], item[2]
        if word is None or start is None or end is None:
            continue
        word = str(word).strip()
        if not word:
            continue
        start = float(start)
        end = float(end)
        if end <= start:
            end = start + 0.05
        normalized.append({"word": word, "start": start, "end": end})
    normalized.sort(key=lambda x: (x["start"], x["end"]))
    return normalized


def extract_word_timestamps_from_segments(segments, offset=0.0):
    words = []
    for seg in segments or []:
        if seg.get("words"):
            for w in seg["words"]:
                word_text = str(w.get("word", "")).strip()
                if not word_text:
                    continue
                start = float(w.get("start", seg.get("start", 0.0))) + offset
                end = float(w.get("end", seg.get("end", start + 0.05))) + offset
                if end <= start:
                    end = start + 0.05
                words.append({"word": word_text, "start": start, "end": end})
        else:
            seg_text = seg.get("text", "").strip()
            split_words = seg_text.split()
            if not split_words:
                continue
            seg_start = float(seg.get("start", 0.0)) + offset
            seg_end = float(seg.get("end", seg_start + 0.05)) + offset
            step = max((seg_end - seg_start) / len(split_words), 0.05)
            for idx, word_text in enumerate(split_words):
                w_start = seg_start + idx * step
                words.append({"word": word_text, "start": w_start, "end": w_start + step})
    return normalize_whisper_words(words)


def do_whisper_transcribe(audio_file_path, device):
    filename = os.path.basename(audio_file_path)
    update_log(f"  🎙️ Transcribing: {filename}...")
    try:
        model = get_whisper_model(device)
        seg_start = time.time()
        segments_iter, info = model.transcribe(
            audio_file_path,
            beam_size=3,
            vad_filter=True,
            language="ar",
            word_timestamps=True,
        )
        segments_list = []
        text_parts = []
        for segment in segments_iter:
            text_parts.append(segment.text.strip())
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "words": [
                    {
                        "word": word.word,
                        "start": word.start,
                        "end": word.end,
                        "probability": getattr(word, "probability", None),
                    }
                    for word in (segment.words or [])
                ],
            })
        elapsed = time.time() - seg_start
        joined = " ".join(text_parts)
        update_log(f"  ✅ Transcribed in {elapsed:.2f}s")
        return joined, segments_list
    except Exception as e:
        update_log(f"  ❌ Whisper Error on {filename}: {str(e)}")
        return None, None


def process_single(file_path, device):
    logs = ""
    filename = os.path.basename(file_path)
    base_name = os.path.splitext(filename)[0]
    output_dir = os.path.dirname(file_path)

    logs += update_log("=" * 52)
    logs += update_log(f"  🎬  {filename}")
    logs += update_log("=" * 52)

    txt, segments = do_whisper_transcribe(file_path, device)
    if txt:
        txt_path = os.path.join(output_dir, f"{base_name}_Whisper.txt")
        write_file_with_log(txt_path, txt)
        logs += f"\n  📄 Raw text saved."

        srt_content, _ = generate_srt_content(segments, offset=0)
        srt_path = os.path.join(output_dir, f"{base_name}_Whisper.srt")
        write_file_with_log(srt_path, srt_content)
        logs += f"\n  📄 SRT saved."

        all_words = extract_word_timestamps_from_segments(segments)
        ts_path = os.path.join(output_dir, f"{base_name}_Timestamps.json")
        write_file_with_log(ts_path, json.dumps(all_words, ensure_ascii=False))
        logs += f"\n  📄 Timestamps saved."

    return logs


def process_folder_master(folder_path, device, seg_time=600):
    logs = ""
    vault_name = os.path.basename(os.path.normpath(folder_path))

    logs += update_log("=" * 52)
    logs += update_log(f"  🏛️ VAULT: {vault_name}")
    logs += update_log("=" * 52)

    lesson_dirs = sorted([
        os.path.join(folder_path, d)
        for d in os.listdir(folder_path)
        if os.path.isdir(os.path.join(folder_path, d))
    ])

    for lesson_dir in lesson_dirs:
        lesson_name = os.path.basename(lesson_dir)
        logs += update_log("=" * 52)
        logs += update_log(f"  📚 LESSON: {lesson_name}")
        logs += update_log("=" * 52)

        part_dirs = sorted([
            os.path.join(lesson_dir, d)
            for d in os.listdir(lesson_dir)
            if os.path.isdir(os.path.join(lesson_dir, d))
            and re.match(r"^part\d+$", d.lower())
        ])

        if not part_dirs:
            logs += update_log(
                f"  ⚠️ No part folders in {lesson_name}, skipping."
            )
            continue

        lesson_segments = []

        for part_dir in part_dirs:
            part_name = os.path.basename(part_dir)
            part_idx = int(re.search(r"\d+", part_name).group())
            logs += update_log(f"\n  📂 {lesson_name}/{part_name}")

            seg_mp3s = sorted([
                f for f in os.listdir(part_dir)
                if f.lower().endswith(".mp3") and "seg" in f.lower()
            ])

            if not seg_mp3s:
                logs += update_log(f"    ⚠️ No segment files in {part_name}.")
                continue

            part_segments = []

            for seg_file in seg_mp3s:
                seg_num = int(re.search(r"seg(\d+)", seg_file.lower()).group(1))
                global_idx = (part_idx - 1) * 3 + seg_num
                offset = (global_idx - 1) * seg_time

                seg_base = os.path.splitext(seg_file)[0]
                seg_abspath = os.path.join(part_dir, seg_file)

                logs += update_log(
                    f"    🎙️ {seg_base}  offset={format_srt_time(offset)}"
                )

                txt, segments = do_whisper_transcribe(seg_abspath, device)
                if not txt or not segments:
                    continue

                # ── Layer 4: individual segment outputs (raw timestamps) ──
                txt_path = os.path.join(part_dir, f"{seg_base}.txt")
                write_file_with_log(txt_path, txt)

                raw_srt, _ = generate_srt_content(segments, offset=0)
                srt_path = os.path.join(part_dir, f"{seg_base}.srt")
                write_file_with_log(srt_path, raw_srt)

                raw_words = extract_word_timestamps_from_segments(segments)
                json_path = os.path.join(part_dir, f"{seg_base}.json")
                write_file_with_log(
                    json_path, json.dumps(raw_words, ensure_ascii=False)
                )

                # accumulate with offset for merges
                for seg in segments:
                    entry = {
                        "start": seg["start"] + offset,
                        "end": seg["end"] + offset,
                        "text": seg["text"],
                        "words": [
                            {
                                "word": w["word"],
                                "start": w["start"] + offset,
                                "end": w["end"] + offset,
                                "probability": w.get("probability"),
                            }
                            for w in seg.get("words", [])
                        ],
                    }
                    part_segments.append(entry)
                    lesson_segments.append(entry)

            # ── Layer 3: part-level merge (only if >1 segment) ──
            if len(part_segments) > 1:
                part_segments.sort(key=lambda s: s["start"])
                logs += update_log(
                    f"    📝 Merging {len(part_segments)} segs → "
                    f"{part_name}-merged"
                )

                part_srt, _ = generate_srt_content(part_segments, offset=0)
                write_file_with_log(
                    os.path.join(part_dir, f"{part_name}-merged.srt"),
                    part_srt,
                )

                part_words = extract_word_timestamps_from_segments(
                    part_segments
                )
                write_file_with_log(
                    os.path.join(part_dir, f"{part_name}-merged.json"),
                    json.dumps(part_words, ensure_ascii=False),
                )

                part_text = " ".join(s["text"] for s in part_segments)
                write_file_with_log(
                    os.path.join(part_dir, f"{part_name}-merged.txt"),
                    part_text,
                )

        # ── Layer 2: lesson-level merge ──
        if lesson_segments:
            lesson_segments.sort(key=lambda s: s["start"])
            logs += update_log(
                f"\n  📝 Merging {len(lesson_segments)} segs → "
                f"{lesson_name}_total"
            )

            lesson_srt, _ = generate_srt_content(lesson_segments, offset=0)
            write_file_with_log(
                os.path.join(lesson_dir, f"{lesson_name}_total.srt"),
                lesson_srt,
            )

            lesson_words = extract_word_timestamps_from_segments(
                lesson_segments
            )
            write_file_with_log(
                os.path.join(lesson_dir, f"{lesson_name}_total.json"),
                json.dumps(lesson_words, ensure_ascii=False),
            )

            lesson_text = " ".join(s["text"] for s in lesson_segments)
            write_file_with_log(
                os.path.join(lesson_dir, f"{lesson_name}_total.txt"),
                lesson_text,
            )

            logs += update_log(f"  ✅ {lesson_name} complete!")

    logs += update_log("\n  🎉 All lessons processed.")

    # ── Fallback: no lesson dirs found → flat MP3 / flat-part mode ──
    if not lesson_dirs:
        logs += update_log(
            "  ⚠️ No lesson folders found. Falling back to flat mode..."
        )
        part_dirs = []
        for root, dirs, files in os.walk(folder_path):
            for d in dirs:
                if re.match(r"^part\d+$", d.lower()):
                    part_dirs.append(os.path.join(root, d))
        part_dirs.sort()

        if part_dirs:
            logs += update_log("  Found part folders in root, processing...")
            for part_dir in part_dirs:
                part_name = os.path.basename(part_dir)
                part_idx = int(re.search(r"\d+", part_name).group())
                seg_mp3s = sorted([
                    f for f in os.listdir(part_dir)
                    if f.lower().endswith(".mp3") and "seg" in f.lower()
                ])
                for seg_file in seg_mp3s:
                    seg_num = int(re.search(r"seg(\d+)", seg_file.lower()).group(1))
                    offset = ((part_idx - 1) * 3 + seg_num - 1) * seg_time
                    seg_base = os.path.splitext(seg_file)[0]
                    logs += update_log(f"    🎙️ {seg_base}")
                    txt, segments = do_whisper_transcribe(
                        os.path.join(part_dir, seg_file), device
                    )
                    if txt:
                        write_file_with_log(
                            os.path.join(part_dir, f"{seg_base}.txt"), txt
                        )
                        raw_srt, _ = generate_srt_content(segments, offset=0)
                        write_file_with_log(
                            os.path.join(part_dir, f"{seg_base}.srt"), raw_srt
                        )
                        raw_words = extract_word_timestamps_from_segments(segments)
                        write_file_with_log(
                            os.path.join(part_dir, f"{seg_base}.json"),
                            json.dumps(raw_words, ensure_ascii=False),
                        )
        else:
            mp3s = []
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    if f.lower().endswith(".mp3"):
                        mp3s.append(os.path.join(root, f))
            mp3s.sort()
            if mp3s:
                logs += update_log("  Transcribing loose MP3s...")
                for fpath in mp3s:
                    logs += "\n" + process_single(fpath, device)
            else:
                logs += update_log("  ❌ No MP3 files or lesson folders found.")

    return logs


def _stage_and_process(upload_item, device):
    if upload_item is None:
        return ""
    if isinstance(upload_item, dict):
        src_path = upload_item.get("path") or upload_item.get("name")
        orig_name = upload_item.get("orig_name")
    else:
        src_path = getattr(upload_item, "path", None) or getattr(upload_item, "name", None)
        orig_name = getattr(upload_item, "orig_name", None)
    if not src_path:
        return update_log("  ⚠️ Invalid upload item.")
    if not orig_name:
        orig_name = os.path.basename(src_path)
    os.makedirs(WORKSPACE, exist_ok=True)
    workspace_path = os.path.join(WORKSPACE, orig_name)
    if os.path.exists(workspace_path):
        try:
            os.remove(workspace_path)
        except Exception:
            pass
    shutil.copy2(src_path, workspace_path)
    return process_single(workspace_path, device)


def browse_folder():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory()
    root.destroy()
    return folder


def gradio_wrapper(scope, single_file, multi_files, folder_input, device_choice, split_mode, custom_seconds):
    try:
        with open(LOG_FILE_PATH, "w", encoding="utf-8") as f:
            f.write("")
    except Exception:
        pass

    update_log("🚀 TEXTWhisp  --  Gradio Session")
    update_log(f"   Device: {device_choice}")
    update_log("=" * 52)

    device = device_choice.lower()

    if split_mode == "10 min":
        seg_time = 600
    elif split_mode == "30 min":
        seg_time = 1800
    elif split_mode == "Custom":
        try:
            seg_time = int(custom_seconds)
        except Exception:
            seg_time = 600
    else:
        seg_time = 600

    if scope == "Single File":
        if not single_file:
            update_log("❌ Please upload an MP3 file.")
            return tail_logs()
        _stage_and_process(single_file, device)

    elif scope == "Multiple Files":
        if not multi_files:
            update_log("❌ Please select multiple files.")
            return tail_logs()
        for item in multi_files:
            _stage_and_process(item, device)

    elif scope == "Master Folder":
        if not folder_input:
            update_log("❌ Please select a folder.")
            return tail_logs()
        if not os.path.isdir(folder_input):
            update_log(f"❌ Folder not found: {folder_input}")
            return tail_logs()
        process_folder_master(folder_input, device, seg_time=seg_time)

    if device == "cuda" and torch is not None:
        torch.cuda.empty_cache()
    gc.collect()

    update_log("🎉 Session complete!")
    return tail_logs()


def main():
    parser = argparse.ArgumentParser(description="Standalone Whisper Transcriber")
    parser.add_argument("--file", help="Path to a single MP3 file")
    parser.add_argument("--files", nargs="+", help="Paths to multiple MP3 files")
    parser.add_argument("--folder", help="Path to directory with MP3 files")
    parser.add_argument("--device", default=None, choices=["cuda", "cpu"], help="Device (auto-detect if omitted)")

    args = parser.parse_args()
    device = args.device or get_device()
    update_log(f"🔧 Device: {device}")

    if args.file:
        process_single(args.file, device)
    elif args.files:
        for f in args.files:
            process_single(f, device)
    elif args.folder:
        if not os.path.isdir(args.folder):
            print(f"❌ Folder not found: {args.folder}")
            return
        process_folder_master(args.folder, device)
    else:
        parser.print_help()


with gr.Blocks(title="TEXTWhisp - Whisper Transcriber") as demo:
    gr.Markdown("# 🎙️ Standalone Whisper Transcription Hub")
    gr.Markdown(f"Workspace: `{WORKSPACE}`")

    with gr.Row():
        with gr.Column(scale=1):
            scope = gr.Radio(
                choices=["Single File", "Multiple Files", "Master Folder"],
                value="Single File",
                label="Execution Scope",
            )
            with gr.Group() as single_col:
                single_file = gr.File(
                    label="Upload MP3 File",
                    file_types=[".mp3"],
                    file_count="single",
                )
            with gr.Group(visible=False) as multi_col:
                multi_files = gr.File(
                    label="Upload Multiple MP3 Files",
                    file_types=[".mp3"],
                    file_count="multiple",
                )
            with gr.Group(visible=False) as folder_col:
                with gr.Row():
                    folder_input = gr.Textbox(
                        label="Master Folder Path",
                        scale=4,
                        placeholder=r"C:\path\to\lesson_folder",
                    )
                    folder_browse = gr.Button("📁 Browse Folder", scale=1)
                split_mode = gr.Radio(
                    choices=["10 min", "30 min", "Custom"],
                    value="10 min",
                    label="Original Split Mode Duration",
                )
                custom_seconds = gr.Number(
                    value=600,
                    label="Custom Slicing Duration (seconds)",
                    visible=False,
                )

            gr.Markdown("---")
            device_dd = gr.Dropdown(
                choices=["cuda", "cpu"],
                value=get_device(),
                label="Hardware Acceleration",
            )
            run_btn = gr.Button("🚀 Run Transcriber", variant="primary")

        with gr.Column(scale=2):
            log_box = gr.Textbox(
                label="Live Terminal Log",
                interactive=False,
                lines=25,
            )

    def _toggle_inputs(choice):
        return [
            gr.update(visible=(choice == "Single File")),
            gr.update(visible=(choice == "Multiple Files")),
            gr.update(visible=(choice == "Master Folder")),
        ]

    scope.change(_toggle_inputs, scope, [single_col, multi_col, folder_col])

    def _toggle_custom(choice):
        return gr.update(visible=(choice == "Custom"))

    split_mode.change(_toggle_custom, split_mode, custom_seconds)

    folder_browse.click(fn=browse_folder, outputs=folder_input)

    run_btn.click(
        fn=gradio_wrapper,
        inputs=[scope, single_file, multi_files, folder_input, device_dd, split_mode, custom_seconds],
        outputs=log_box,
    )

    gr.Timer(1).tick(fn=tail_logs, outputs=log_box)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        demo.launch(inbrowser=True)
