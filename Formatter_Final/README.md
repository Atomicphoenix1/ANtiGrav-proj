# Deterministic Document Formatting Suite

A 4-stage automation workflow designed to transform audio lectures into professionally formatted, publication-ready documents. While the initial transcription utilizes AI for text generation, the **workflow orchestration is entirely deterministic**, ensuring consistent and predictable output.

## ⚙️ The Workflow Mechanism

### Stage 1: Transcription (AI Studio)
- **Action:** Audio files are processed using high-precision prompts on **AI Studio** (Gemini/Whisper) to generate a raw text transcript.

### Stage 2: Prompt-based Tagging
- **Action:** The raw transcript is passed through a secondary tagging prompt.
- **Goal:** Identifying structural elements such as headers, "Matn" (source text), and Q&A segments with predetermined tags.

### Stage 3: Python Formatting Engine
- **Logic:** A custom Python script imports the tagged Markdown.
- **Formatting:** It applies specific styles to each tag using a **`.docx` template**.
- **Output:** Automatically exports both a **Microsoft Word (.docx)** and **PDF** version of the document.

### Stage 4: n8n Distribution & Human Approval
- **Orchestration:** The files are linked to an **n8n workflow**.
- **Process:** 
  1. The workflow sends the files to a **Telegram Admin Bot** for review.
  2. The system waits for **Human Approval**.
  3. Once approved, the workflow automatically forwards the final documents to the designated public/private distribution chat.

## 🛠️ Design Philosophy
This system is **NOT an AI agent pipeline**. It is a structured, code-driven workflow that uses AI as a tool for the *transcription* component while maintaining total control over the formatting and distribution logic.

---
*Developed as part of the ANtiGrav Automation Series.*
