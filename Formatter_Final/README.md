# Islamic Lecture Formatter — Final Production Suite

This folder contains the complete, automated pipeline for formatting Islamic lecture transcripts into scholarly-compliant Microsoft Word documents.

## 📂 Folder Structure
- `run.py`: The main script you will use to generate documents.
- `v2_formatter.py`: The formatting engine (don't edit).
- `tagging_prompt.md`: The instructions to copy-paste into AI Studio.
- `sample.md`: A complete example of a tagged transcript.
- `fasils.py`: Decorative symbols for section breaks.
- `backup/`: A folder for you to keep copies of your transcripts.

---

## 🚀 How to Use (3-Step Workflow)

### Step 1: AI Studio Tagging
1. Open a new chat in **AI Studio** (gemini-1.5-pro or 1.5-flash).
2. Copy the entire contents of `tagging_prompt.md` and paste it into the chat.
3. Paste your raw transcription text after the prompt and press Enter.
4. When it finishes, click the **"Copy Markdown"** button (this is crucial to keep the tags).

### Step 2: Save the File
1. Paste the tagged text into a new text file inside this folder.
2. Save it with a `.md` extension (e.g., `lesson_01.md`).

### Step 3: Generate the Word Doc
You have two options:

#### Option A: Web Interface (Easiest)
1. Run: `python gradio_app.py`
2. Enter the output name and paste the tagged text.
3. Click "Generate". It will automatically create DOCX/PDF and send them to Telegram.

#### Option B: Terminal
1. Save the tagged text as `lecture.md` and run:
   ```bash
   python run.py lecture.md
   ```

---

## 🛠 Features
- **Automatic PDF**: Every DOCX is automatically converted to PDF.
- **n8n/Telegram Integration**: Documents are sent to your Telegram via n8n immediately after creation.
- **End Symbol**: Documents now end with a decorative green symbol automatically.

---

## 🎨 Setting the Icon
To use the `app_icon.ico` for the launcher:
1. Right-click `Start_Formatter.bat` and select **Create Shortcut**.
2. Right-click the new shortcut and select **Properties**.
3. Go to the **Shortcut** tab and click **Change Icon...**.
4. Click **Browse...** and select `app_icon.ico` from this folder.
5. Click **OK** and rename the shortcut to "Islamic Formatter".
