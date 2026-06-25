import os
import sys
import argparse
from datetime import datetime

# Force stdout to use UTF-8 to prevent encoding errors when printing Arabic text on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# Windows DLL loading optimization for local CUDA packages
if sys.platform == "win32":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Try different relative layout options
    possible_site_packages = [
        os.path.join(script_dir, ".venv", "Lib", "site-packages"),
        os.path.join(script_dir, "Lib", "site-packages")
    ]
    for sp in possible_site_packages:
        if os.path.exists(sp):
            cuda_paths = [
                os.path.join(sp, "nvidia", "cublas", "bin"),
                os.path.join(sp, "nvidia", "cudnn", "bin"),
                os.path.join(sp, "nvidia", "cuda_nvrtc", "bin")
            ]
            for path in cuda_paths:
                if os.path.exists(path):
                    print(f"Optimizing environment: Adding CUDA DLL path {path}")
                    os.environ["PATH"] = path + os.pathsep + os.environ["PATH"]
                    if hasattr(os, "add_dll_directory"):
                        try:
                            os.add_dll_directory(path)
                        except Exception as e:
                            print(f"Note: Could not add DLL directory explicitly: {e}")

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("Error: 'faster-whisper' package is not installed in this environment.")
    print("Please activate the virtual environment and run the script.")
    sys.exit(1)

def format_timestamp(seconds: float) -> str:
    """Formats seconds into HH:MM:SS format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def transcribe_audio(
    audio_path: str,
    # ┌─────────────────────────────────────────────────────────────────────┐
    # │ MODEL SIZE — change this string to switch models                    │
    # └─────────────────────────────────────────────────────────────────────┘
    model_size: str = "large-v3",
    device: str = "auto",
    compute_type: str = "auto",
    language: str = "ar"
):
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at '{audio_path}'")
        sys.exit(1)

    print(f"\n--- Whisper Arabic Transcription Setup ---")
    print(f"Target Audio File: {audio_path}")
    print(f"Model Size       : {model_size}")
    print(f"Target Language  : {language.upper()}")

    # Determine best device and compute type if set to auto
    if device == "auto":
        try:
            import ctypes
            # Quick check if CUDA driver is loaded and GPU is accessible
            device = "cuda"
            print("Detecting hardware... CUDA-capable GPU found.")
        except Exception:
            device = "cpu"
            print("Detecting hardware... No CUDA device accessible. Defaulting to CPU.")

    if compute_type == "auto":
        # CRITICAL FIX FOR 4GB VRAM: Use int8_float16 instead of raw float16 
        # This keeps the model size around ~1.5GB to fit perfectly in your RTX 3050
        compute_type = "int8_float16" if device == "cuda" else "int8"

    print(f"Execution Device : {device.upper()}")
    print(f"Precision Level  : {compute_type}")
    print(f"------------------------------------------\n")

    print("Loading model (this might take a few moments on the first run)...")
    start_time = datetime.now()
    
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        print(f"Initialization error: {e}")
        if device == "cuda":
            print("Attempting safer fallback to INT8 CUDA quantization...")
            try:
                model = WhisperModel(model_size, device="cuda", compute_type="int8")
                compute_type = "int8"
            except Exception as cuda_fallback_e:
                print(f"CUDA standard initialization failed: {cuda_fallback_e}")
                print("Attempting fallback to CPU mode...")
                try:
                    model = WhisperModel(model_size, device="cpu", compute_type="int8")
                    device = "cpu"
                    compute_type = "int8"
                except Exception as cpu_e:
                    print(f"CPU fallback failed: {cpu_e}")
                    sys.exit(1)
        else:
            sys.exit(1)

    model_load_time = (datetime.now() - start_time).total_seconds()
    print(f"Model successfully loaded in {model_load_time:.2f} seconds.")

    print("\nStarting transcription...")
    transcribe_start = datetime.now()
    
    # Run Whisper transcription
    # OPTIMIZATION: beam_size=3 lowers temporary memory calculation spike thresholds
    segments, info = model.transcribe(
        audio_path,
        beam_size=3,
        language=language,
        vad_filter=True, # Voice Activity Detection filters out silent/non-speech parts
        vad_parameters=dict(min_speech_duration_ms=250)
    )

    print(f"Detected language: {info.language} (Confidence: {info.language_probability:.2%})")
    print(f"Audio Duration   : {format_timestamp(info.duration)}")
    print("\nTranscribed Segments:")
    print("=" * 60)

    transcribed_text_segments = []
    
    try:
        for segment in segments:
            start_fmt = format_timestamp(segment.start)
            end_fmt = format_timestamp(segment.end)
            segment_text = segment.text.strip()
            
            # Real-time console output with encoding fallback
            try:
                print(f"[{start_fmt} -> {end_fmt}] {segment_text}")
            except Exception:
                try:
                    # Safe print fallback
                    print(f"[{start_fmt} -> {end_fmt}] <Segment encoded or not printable in console shell>")
                except Exception:
                    pass
            transcribed_text_segments.append(segment_text)
    except RuntimeError as run_e:
        if "out of memory" in str(run_e).lower():
            print("\nCRITICAL OUT OF MEMORY ERROR OCCURRED MID-STREAM!")
            print("Your GPU exhausted its capacity during processing. Try reducing --beam_size.")
        raise run_e

    print("=" * 60)
    
    # Save results
    output_filename = os.path.splitext(os.path.basename(audio_path))[0] + "_transcription.txt"
    output_dir = os.path.dirname(os.path.abspath(audio_path))
    output_path = os.path.join(output_dir, output_filename)

    # Group segments into clean paragraphs
    paragraphs = []
    current_paragraph = []
    
    for segment in transcribed_text_segments:
        current_paragraph.append(segment)
        if any(segment.endswith(p) for p in [".", "!", "?", "؟", "۔"]) or len(" ".join(current_paragraph)) > 300:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []
            
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    full_text = "\n\n".join(paragraphs)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"=== Audio Transcription Report ===\n")
        f.write(f"Source Audio  : {os.path.basename(audio_path)}\n")
        f.write(f"Duration      : {format_timestamp(info.duration)}\n")
        f.write(f"Transcribed On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model Used    : Whisper {model_size} ({device.upper()} / {compute_type})\n")
        f.write(f"==================================\n\n")
        f.write(full_text)

    total_time = (datetime.now() - transcribe_start).total_seconds()
    print(f"\nTranscription completed in {total_time:.2f} seconds.")
    print(f"Saved formatted transcription text to:\n-> {output_path}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Optimize Whisper Arabic audio transcription")
    parser.add_argument(
        "--audio", 
        type=str, 
        default=r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\Whisper\1.mp3",
        help="Path to the audio file"
    )
    parser.add_argument(
        "--model", 
        type=str, 
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
        help="Whisper model size"
    )
    parser.add_argument(
        "--device", 
        type=str, 
        default="auto", 
        choices=["auto", "cuda", "cpu"],
        help="Execution device"
    )
    parser.add_argument(
        "--compute_type", 
        type=str, 
        default="auto", 
        choices=["auto", "float16", "int8_float16", "int8", "float32"],
        help="Compute precision type"
    )
    
    args = parser.parse_args()
    transcribe_audio(
        audio_path=args.audio,
        model_size=args.model,
        device=args.device,
        compute_type=args.compute_type
    )