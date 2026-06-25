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

# Keep your original code imports underneath...
import argparse
import time
from faster_whisper import WhisperModel

# ... the rest of your script continues exactly as before


import argparse
import os
import sys
import time
from faster_whisper import WhisperModel

# =====================================================================
# 🔥 AUTOMATIC DIRECTORY LOCK: Forces execution inside the script's folder
# =====================================================================
script_directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_directory)
# =====================================================================

def transcribe_arabic_finedtuned(audio_path: str, device: str = "cuda", compute_type: str = "int8_float16"):
    # Target an active, public, pre-converted CTranslate2 Arabic Fine-Tuned repository
    arabic_model_checkpoint = "dev-ahmedhany/whisper-large-v3-arabic-ft-v3-ct2-int8"
    
    print(f"📦 Loading Fine-Tuned Arabic Model: {arabic_model_checkpoint}...")
    print("⚠️  First run will download the specialized quantized weights...")
    
    # Initialize the model using the optimized public repository
    model = WhisperModel(
        arabic_model_checkpoint, 
        device=device, 
        compute_type=compute_type
    )
    
    # Check if the audio file exists inside the locked folder directory
    if not os.path.exists(audio_path):
        absolute_expected_path = os.path.abspath(audio_path)
        raise FileNotFoundError(
            f"\n❌ ERROR: Audio file missing!\n"
            f"Looking for: '{audio_path}'\n"
            f"Resolved Absolute Path: '{absolute_expected_path}'\n"
            f"👉 Resolution: Please drop your '{audio_path}' file directly inside the folder: {script_directory}"
        )
        
    print(f"🎙️  Processing Audio File: {audio_path}")
    start_time = time.time()
    
    # Run the model with Voice Activity Detection (VAD) active to suppress silence loops
    segments, info = model.transcribe(
        audio_path, 
        beam_size=3,              # Protects your 4GB RTX 3050 VRAM boundary
        vad_filter=True,          # Essential defense against hallucination loops
        language="ar"             # Forces Arabic processing immediately
    )
    
    print(f"🔍 Detected Language: {info.language} (Probability: {info.language_probability:.2f})")
    print("✍️  Writing transcription data...\n")
    
    # Output file will be written right next to the script in the Whisper folder
    output_filename = "arabic_finetuned_transcript.txt"
    with open(output_filename, "w", encoding="utf-8") as f:
        for segment in segments:
            # Format clean timestamp blocks
            timestamp = f"[{time.strftime('%H:%M:%S', time.gmtime(segment.start))} -> {time.strftime('%H:%M:%S', time.gmtime(segment.end))}]"
            line = f"{timestamp} {segment.text}"
            print(line)
            f.write(line + "\n")
            
    elapsed_time = time.time() - start_time
    print(f"\n✅ Done! Transcript safely stored in '{os.path.abspath(output_filename)}'")
    print(f"⏱️ Total Execution Time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Arabic Specialized Fine-Tuned Whisper Pipeline")
    # Default file target is now explicitly 1.mp3
    parser.add_argument("--audio", type=str, default="1.mp3", help="Name or path of your local audio file")
    parser.add_argument("--device", type=str, default="cuda", help="cuda or cpu")
    parser.add_argument("--compute_type", type=str, default="int8_float16", help="Quantization setting")
    
    args = parser.parse_args()
    transcribe_arabic_finedtuned(audio_path=args.audio, device=args.device, compute_type=args.compute_type)