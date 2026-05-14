"""
pipeline.py — Full Automated Islamic Lecture Formatting Pipeline
================================================================
Usage:
    python pipeline.py --input raw_transcript.txt

Steps:
    1. Reads raw transcription from a .txt file
    2. Sends it to the Gemini API with the semantic tagging prompt
    3. Saves the tagged output as a .md file
    4. Runs v2_formatter.py to produce the final .docx
"""

import os
import sys
import argparse
import subprocess
import google.generativeai as genai

# ── Configuration ──────────────────────────────────────────────────────────────

# Your Gemini API Key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

# Paths (adjust if needed)
BASE_DIR       = r"C:\Users\saif_\Desktop\downs\حاليًا\يومي\Lectures\ANtiGrav"
FORMATTER_PATH = os.path.join(BASE_DIR, "Formatter_V2", "v2_formatter.py")
TEMPLATE_PATH  = os.path.join(BASE_DIR, "تفريغ كتاب التوحيد - باب 9.docx")
OUTPUT_DIR     = os.path.join(BASE_DIR, "Formatter_V2")
PYTHON_EXE     = r"C:\Users\saif_\AppData\Local\Programs\Python\Python312\python.exe"

# Gemini model to use
MODEL_NAME = "gemini-1.5-pro"

# ── Tagging Prompt ─────────────────────────────────────────────────────────────

TAGGING_PROMPT = """
You will receive the raw text of an Islamic lecture transcription. Your job is to add semantic tags to it so that it can be processed by an automated formatting pipeline. You must follow the rules below EXACTLY and without exception. Output ONLY the tagged text with no commentary, preamble, or explanation.

## RULES

### 1. Full Diacritization (Tashkeel)
Every Arabic word must be FULLY diacritized. Do not omit a single diacritic.

### 2. Speaker Tags
- Commentator: <speaker>قال الشارح [du'a e.g. هداه الله]:</speaker>
- Author:       <speaker>قال المصنف [mercy phrase e.g. رحمه الله]:</speaker>

### 3. Matn Tags
Wrap the Author's body text (not his speaker tag) in <matn> tags:
<speaker>قال المصنف رحمه الله:</speaker>
<matn>
[Author's text here]
</matn>

### 4. Hadith Tags
Prophetic narrations: <hadith>[نَصُّ الْحَدِيثِ]</hadith>
The hadith text MUST be inside square brackets inside the tag.

### 5. Quran Tags
Quranic verses: <quran>﴿نَصُّ الْآيَةِ﴾</quran>
Must use the decorative brackets ﴿﴾ (NOT square brackets).

### 6. Book Titles
Wrap in plain square brackets with NO surrounding tags: [اسْمُ الْكِتَابِ]
Examples: [فَضْلُ الْإِسْلَامِ] | [مُغْنِي اللَّبِيبِ] | [بَدَائِعِ الْفَوَائِدِ]

### 7. Scholar/Poet Quotes (non-Hadith)
Wrap in plain square brackets with NO surrounding tags: [نَصُّ الِاقْتِبَاسِ]
Use this for quotes from imams, scholars, poets — anyone other than the Prophet ﷺ.

### 8. Bold List Labels
Wrap ONLY the label in <strong> tags:
- <strong>أَحَدُهُمَا:</strong> rest of sentence
- <strong>وَالآخَرُ:</strong> rest of sentence

### 9. Bullet Points
Prefix every list item with a dash and space: "- "

### 10. Honorifics — Leave as plain diacritized text (no tags needed):
صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ | عَزَّ وَجَلَّ | سُبْحَانَهُ وَتَعَالَى | تَعَالَى

## CRITICAL RULES
- NEVER nest <hadith> inside <quran> or vice versa
- NEVER use <hadith> for non-Prophetic quotes
- NEVER omit tashkeel from any word
- NEVER add blank lines except between speaker sections
- Output ONLY the tagged text, nothing else

## Raw Transcription to Tag:
"""

# ──────────────────────────────────────────────────────────────────────────────

def tag_transcription(raw_text: str) -> str:
    """Send raw text to Gemini API and return the tagged MD output."""
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    
    full_prompt = TAGGING_PROMPT + "\n\n" + raw_text
    
    print("[1/3] Sending transcription to Gemini for tagging...")
    response = model.generate_content(full_prompt)
    return response.text


def save_markdown(tagged_text: str, output_md_path: str):
    """Save the tagged text as a .md file."""
    with open(output_md_path, 'w', encoding='utf-8') as f:
        f.write(tagged_text)
    print(f"[2/3] Tagged Markdown saved to: {output_md_path}")


def run_formatter(md_path: str, output_docx_path: str):
    """Run v2_formatter.py with custom input/output paths."""
    print("[3/3] Running v2_formatter.py to generate Word document...")
    
    # Temporarily patch formatter to use our paths
    cmd = [
        PYTHON_EXE,
        "-c",
        f"""
import sys
sys.path.insert(0, r'{os.path.join(BASE_DIR, "Formatter_V2")}')
import v2_formatter
v2_formatter.format_document(
    r'{md_path}',
    r'{TEMPLATE_PATH}',
    r'{output_docx_path}'
)
print('Done.')
"""
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print("ERROR from formatter:")
        print(result.stderr)
    else:
        print(f"Word document saved to: {output_docx_path}")


def main():
    parser = argparse.ArgumentParser(description="Islamic Lecture Formatting Pipeline")
    parser.add_argument("--input", required=True, help="Path to raw transcript .txt file")
    parser.add_argument("--name",  default="output", help="Base name for output files (no extension)")
    args = parser.parse_args()

    # Resolve paths
    input_path   = os.path.abspath(args.input)
    output_md    = os.path.join(OUTPUT_DIR, f"{args.name}.md")
    output_docx  = os.path.join(OUTPUT_DIR, f"{args.name}.docx")

    # Read raw transcript
    with open(input_path, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    if not raw_text.strip():
        print("ERROR: Input file is empty.")
        sys.exit(1)

    # Run pipeline
    tagged_text = tag_transcription(raw_text)
    save_markdown(tagged_text, output_md)
    run_formatter(output_md, output_docx)

    print("\nPipeline complete!")
    print(f"  MD:   {output_md}")
    print(f"  DOCX: {output_docx}")


if __name__ == "__main__":
    main()
