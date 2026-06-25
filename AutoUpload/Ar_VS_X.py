import os
import sys

# =====================================================================
# ⚡️ NVIDIA DLL PATH INJECTOR: Fixes cublas64_12.dll Missing Error on Windows
# =====================================================================
python_base = os.path.dirname(sys.executable)
site_packages = os.path.join(python_base, "Lib", "site-packages")

# Define where pip installed the NVIDIA DLL binaries
nvidia_paths = [
    os.path.join(site_packages, "nvidia", "cublas", "bin"),
    os.path.join(site_packages, "nvidia", "cudnn", "bin"),
    os.path.join(site_packages, "nvidia", "cuda_nvrtc", "bin")
]

# Force Windows to look inside these directories for the missing .dll files
for path in nvidia_paths:
    if os.path.exists(path):
        os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
        if sys.version_info >= (3, 8):
            os.add_dll_directory(path)
# =====================================================================

import time
import re
import gc
import torch
import gradio as gr
import tkinter as tk
from tkinter import filedialog
from faster_whisper import WhisperModel
import whisperx
import warnings

warnings.filterwarnings("ignore", message="torchcodec")

# =====================================================================
# 🔥 AUTOMATIC DIRECTORY LOCK: Forces execution inside the script's folder
# =====================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)

# =========================================================================
# HELPERS FOR SORTING & FILTERING
# =========================================================================
def extract_segment_number(filename):
    """Looks for 'part' followed by digits at the end of the filename."""
    name_without_ext = os.path.splitext(filename)[0].lower()
    match = re.search(r'part(\d+)[^\d]*$', name_without_ext)
    if match:
        return int(match.group(1))
    return float('inf') 

def is_original_full_file(filename):
    """Determines if a file is the original track or a split segment."""
    name_without_ext = os.path.splitext(filename)[0].lower()
    if "part" in name_without_ext:
        return False # It's a split segment
    return True # It's the original full-length track

def get_original_track_name(all_files):
    """Finds the first file identified as the original track and returns its base name."""
    for f in all_files:
        if f.lower().endswith('.mp3') and is_original_full_file(f):
            return os.path.splitext(f)[0]
    return None

# =========================================================================
# CORE TRANSCRIPTION ENGINES (WITH STRICT VRAM FALLBACKS)
# =========================================================================
def process_finetuned_whisper(audio_path, device="cuda"):
    """Runs the Fine-Tuned Arabic Model and returns the formatted text with timestamps."""
    model = None
    try:
        compute_type = "int8_float16" if device == "cuda" else "int8"
        model = WhisperModel("dev-ahmedhany/whisper-large-v3-arabic-ft-v3-ct2-int8", device=device, compute_type=compute_type)
        
        segments, info = model.transcribe(
            audio_path, 
            beam_size=3, 
            vad_filter=True, 
            language="ar"
        )
        
        transcript_lines = []
        for segment in segments:
            start_str = time.strftime('%H:%M:%S', time.gmtime(segment.start))
            end_str = time.strftime('%H:%M:%S', time.gmtime(segment.end))
            transcript_lines.append(f"[{start_str} -> {end_str}] {segment.text}")
            
        return "\n".join(transcript_lines)
    except Exception as e:
        return f"❌ Fine-Tuned Whisper Error: {str(e)}"
    finally:
        # ABSOLUTE VRAM PURGE
        if model is not None:
            del model
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()

def process_whisperx(audio_path, device="cuda", batch_size=4):
    """Runs the WhisperX Transcription + Alignment Pipeline and returns RAW text without timestamps."""
    model = None
    align_model = None
    try:
        compute_type = "float16" if device == "cuda" else "int8"
        
        # Stage 1: Transcription
        model = whisperx.load_model("large-v3", device, compute_type=compute_type, language="ar")
        audio = whisperx.load_audio(audio_path)
        raw_result = model.transcribe(audio, batch_size=batch_size)
        
        # Immediate VRAM Dump before Alignment
        del model
        model = None
        gc.collect()
        if device == "cuda": torch.cuda.empty_cache()

        # Stage 2: Alignment
        align_model, metadata = whisperx.load_align_model(language_code="ar", device=device)
        aligned_result = whisperx.align(
            raw_result["segments"], align_model, metadata, audio, device, return_char_alignments=False
        )
        
        transcript_lines = []
        for segment in aligned_result["segments"]:
            # Extracted text directly without constructing timestamp strings
            transcript_lines.append(segment['text'].strip())
            
        return "\n".join(transcript_lines)
    except Exception as e:
        return f"❌ WhisperX Error: {str(e)}"
    finally:
        # ABSOLUTE VRAM PURGE
        if model is not None: del model
        if align_model is not None: del align_model
        gc.collect()
        if device == "cuda": torch.cuda.empty_cache()

# =========================================================================
# MASTER CONTROLLER RUNNER (GENERATOR FOR GRADIO LIVE LOGS)
# =========================================================================
def run_master_pipeline(master_folder_path, device_selection):
    if not os.path.exists(master_folder_path):
        yield "❌ Error: The Master Folder path provided does not exist."
        return

    master_folder_path = os.path.abspath(master_folder_path)
    subfolders = [os.path.join(master_folder_path, d) for d in os.listdir(master_folder_path) 
                  if os.path.isdir(os.path.join(master_folder_path, d))]
    
    if not subfolders:
        yield "ℹ️ Process Finished: No subfolders found inside the specified Master Folder."
        return

    current_logs = "🚀 Local AI Pipeline Started...\n"
    yield current_logs
    
    for folder in subfolders:
        folder_name = os.path.basename(folder)
        current_logs += f"\n📁 Inside Folder: {folder_name}\n"
        yield current_logs
        
        all_files = os.listdir(folder)
        all_mp3s = [f for f in all_files if f.lower().endswith('.mp3')]
        
        original_track_name = get_original_track_name(all_mp3s)
        if original_track_name:
            current_logs += f"  🎯 Identified original track name: '{original_track_name}'\n"
        else:
            original_track_name = f"{folder_name}_merged"
            current_logs += f"  ⚠️ Original track missing. Using folder name: '{original_track_name}'\n"
        yield current_logs
        
        segments = [f for f in all_mp3s if not is_original_full_file(f)]
        segments.sort(key=extract_segment_number)
        
        if not segments:
            current_logs += f"  ⚠️ No valid segments found. Skipping.\n"
            yield current_logs
            continue
            
        merged_ft_transcript = []
        merged_wx_transcript = []
        
        # Isolated accumulation timers per model execution loop
        total_ft_duration = 0.0
        total_wx_duration = 0.0
        
        for idx, segment_name in enumerate(segments):
            full_segment_path = os.path.join(folder, segment_name)
            current_logs += f"  🕒 Processing Segment ({idx+1}/{len(segments)}): {segment_name}\n"
            yield current_logs
            
            # --- RUN FINE-TUNED WHISPER ---
            current_logs += f"     [1/2] Running Fine-Tuned Arabic Model...\n"
            yield current_logs
            
            start_ft = time.time()
            ft_result = process_finetuned_whisper(full_segment_path, device=device_selection)
            total_ft_duration += (time.time() - start_ft)
            
            merged_ft_transcript.append(ft_result)
            
            # --- RUN WHISPERX ---
            current_logs += f"     [2/2] Running WhisperX (No Timestamps)...\n"
            yield current_logs
            
            start_wx = time.time()
            wx_result = process_whisperx(full_segment_path, device=device_selection)
            total_wx_duration += (time.time() - start_wx)
            
            merged_wx_transcript.append(wx_result)
            
            current_logs += f"  ✅ Finished Segment: {segment_name}\n"
            yield current_logs
        
        # --- SAVE MERGED OUTPUTS WITH METADATA METRICS ---
        current_logs += f"\n💾 Exporting Merged Transcripts to {folder_name}...\n"
        yield current_logs
        
        # Structure timing metadata block
        ft_meta_footer = f"\n\n========================================\n⏱️ Total Transcription Time: {total_ft_duration:.2f} seconds\n========================================"
        wx_meta_footer = f"\n\n========================================\n⏱️ Total Transcription Time: {total_wx_duration:.2f} seconds\n========================================"
        
        # Save Fine-Tuned Output
        ft_out_path = os.path.join(folder, f"{original_track_name}_FineTuned.txt")
        with open(ft_out_path, "w", encoding="utf-8") as out_file:
            out_file.write("\n\n".join(merged_ft_transcript))
            out_file.write(ft_meta_footer)
            
        # Save WhisperX Output
        wx_out_path = os.path.join(folder, f"{original_track_name}_WhisperX.txt")
        with open(wx_out_path, "w", encoding="utf-8") as out_file:
            out_file.write("\n\n".join(merged_wx_transcript))
            out_file.write(wx_meta_footer)
            
        current_logs += f"✅ Successfully generated both comparative transcripts!\n"
        current_logs += f"     ⏱️ Fine-Tuned Total Time: {total_ft_duration:.2f}s | WhisperX Total Time: {total_wx_duration:.2f}s\n"
        yield current_logs

    current_logs += "\n🚀 All processing tasks completely finished!"
    yield current_logs

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
# GRADIO WEB INTERFACE
# =========================================================================
with gr.Blocks(title="Local Dual-Whisper Transcriber") as demo:
    gr.Markdown("""
    # 🎙️ Local Dual-Whisper Transcriber (Fine-Tuned vs WhisperX)
    This pipeline batch-processes audio files sequentially using **`part000`** naming rules. 
    To save GPU resources, it isolates VRAM execution for each model per segment, purges the cache, tracks total execution execution metrics, and sets WhisperX to output clean text lines without timestamp markers.
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            with gr.Row():
                master_dir_input = gr.Textbox(
                    label="Master Folder Path", 
                    placeholder="Click Browse or paste directory absolute path...",
                    scale=4
                )
                browse_btn = gr.Button("📁 Browse...", scale=1)
                
            device_dropdown = gr.Dropdown(
                choices=["cuda", "cpu"],
                value="cuda",
                label="Hardware Device"
            )
            submit_btn = gr.Button("🚀 Run Dual-Transcription Pipeline", variant="primary")
            
        with gr.Column(scale=2):
            status_output = gr.Textbox(
                label="Live Log Pipeline Terminal Streaming Output", 
                interactive=False, 
                lines=20
            )

    browse_btn.click(fn=browse_folder, outputs=master_dir_input)
    submit_btn.click(
        fn=run_master_pipeline, 
        inputs=[master_dir_input, device_dropdown], 
        outputs=status_output
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)