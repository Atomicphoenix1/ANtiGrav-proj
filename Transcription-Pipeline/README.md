# Transcription & Formatting Pipeline

This pipeline automates the transformation of audio lectures into professionally formatted, scholarly documents. It is specifically optimized for Arabic/Islamic studies context, handling RTL alignment, honorifics, and structural symbols.

## ⚙️ How it Works

### 1. Audio Pre-processing (`prepare_audio.py`)
- **Action:** Monitors the system for new audio recordings.
- **Logic:** Uses **FFmpeg** to convert media into optimized, mono-channel MP3s (64k bitrate) to minimize upload size while maintaining voice clarity.
- **Trigger:** Automatically uploads the processed MP3 to an **n8n webhook** for the next stage.

### 2. AI Formatting Logic (`ai_studio_formatter.py` & `v2_formatter.py`)
- **Mechanism:** The raw transcript (usually from AI Studio/Whisper) is processed through a Python-based styling engine.
- **Features:**
  - **RTL Alignment:** Correctly handles Arabic text flow in Microsoft Word.
  - **Scholarly Formatting:** Automatically identifies and styles "Matn" (italics), Q&A sections, and specific scholarly brackets.
  - **Visual Elements:** Applies professional fonts (AAAGoldenLotus) and standard Islamic typography.

### 3. Distribution Workflow (`send docpdf.json`)
- **n8n Workflow:** This node-based logic receives the finalized text, triggers the Python formatter, and then pushes the generated `.docx` and `.pdf` files to specified **Telegram channels** for instant distribution.

## 📂 File Structure
- `prepare_audio.py`: The entry point for media optimization.
- `ai_studio_formatter.py`: The primary formatting engine.
- `v2_formatter.py`: Advanced styling logic for complex document structures.
- `send docpdf.json`: The n8n workflow export for document distribution.

---
*Part of the ANtiGrav Automation Suite.*
