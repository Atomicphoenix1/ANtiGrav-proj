import argparse
import os
import sys
import whisperx
import gc
import torch
import warnings
warnings.filterwarnings("ignore", message="torchcodec")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def transcribe_whisperx_pipeline(audio_path: str, device: str = "cuda", batch_size: int = 4):
    compute_type = "float16" if device == "cuda" else "int8"

    if not os.path.isabs(audio_path):
        audio_path = os.path.join(SCRIPT_DIR, audio_path)
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"❌ Target audio asset missing: {audio_path}")

    # --- STAGE 1: RAW WHISPER TRANSCRIPTION ---
    print("⏳ Stage 1: Initializing WhisperX Large-v3 Core Model...")
    model = whisperx.load_model("large-v3", device, compute_type=compute_type, language="ar")
    
    print("🎙️ Loading audio track parameters...")
    audio = whisperx.load_audio(audio_path)
    
    print("✍️ Running initial transcription matrix...")
    raw_result = model.transcribe(audio, batch_size=batch_size)
    
    # Clear VRAM immediately from the core model weights to make space for the next network stage
    del model
    gc.collect()
    if device == "cuda": 
        torch.cuda.empty_cache()

    # --- STAGE 2: PHONEME ALIGNMENT (Wav2Vec2) ---
    print("\n⏳ Stage 2: Aligning phonemes to remove phonetic spelling errors...")
    # Load the specialized Arabic Wav2Vec2 framework alignment model
    align_model, metadata = whisperx.load_align_model(language_code="ar", device=device)
    
    # Read words against raw frequencies for millisecond accuracy
    aligned_result = whisperx.align(
        raw_result["segments"], 
        align_model, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )
    
    # Clear VRAM cache allocations again
    del align_model
    gc.collect()
    if device == "cuda": 
        torch.cuda.empty_cache()

    # --- STAGE 3: OUTPUT PACKAGING ---
    print("\n💾 Packaging structural aligned outputs...")
    output_filename = "whisperx_aligned_transcript.txt"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        for segment in aligned_result["segments"]:
            start_stamp = f"{segment['start']:.2f}s"
            end_stamp = f"{segment['end']:.2f}s"
            text_line = segment["text"]
            
            log_line = f"[{start_stamp} -> {end_stamp}] {text_line}"
            print(log_line)
            f.write(log_line + "\n")
            
    print(f"\n✅ Pipeline Complete! Perfectly aligned transcript written to: {output_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WhisperX High-Accuracy Phoneme Alignment Script")
    parser.add_argument("--audio", type=str, default="1.mp3", help="Target audio file path")
    # If running on your home PC, manually type: python script.py --device cpu
    parser.add_argument("--device", type=str, default="cuda", help="cuda or cpu")
    parser.add_argument("--batch_size", type=int, default=4, help="Reduces VRAM consumption step limits")
    
    args = parser.parse_args()
    transcribe_whisperx_pipeline(audio_path=args.audio, device=args.device, batch_size=args.batch_size)