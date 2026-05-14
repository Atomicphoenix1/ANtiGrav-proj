"""
gradio_app.py — Web UI for Islamic Lecture Formatter
====================================================
"""

import gradio as gr
import os
import v2_formatter
import tkinter as tk
from tkinter import filedialog

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
TEMPLATE_PATH = os.path.join(PARENT_DIR, "template.docx")

def select_directory():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    folder_selected = filedialog.askdirectory()
    root.destroy()
    return folder_selected

def process_transcript(output_name, export_path, tagged_md):
    if not output_name.strip():
        return "Error: Please provide an output filename.", None, None
    
    if not tagged_md.strip():
        return "Error: Please paste the tagged transcription.", None, None
    
    target_dir = export_path.strip() if export_path.strip() else BASE_DIR
    if not os.path.exists(target_dir):
        try:
            os.makedirs(target_dir)
        except:
            return f"Error: Could not create or access directory {target_dir}", None, None

    # Ensure filename ends with .docx
    if not output_name.lower().endswith(".docx"):
        output_docx = f"{output_name}.docx"
    else:
        output_docx = output_name
        
    output_path = os.path.join(target_dir, output_docx)
    pdf_path = output_path.replace(".docx", ".pdf")
    
    try:
        # Run the formatter
        docx_out, pdf_out = v2_formatter.format_document(
            tagged_md, 
            TEMPLATE_PATH, 
            output_path, 
            is_file=False
        )
        
        return (
            f"Successfully processed!\nSaved to: {target_dir}\nSent to Telegram!",
            output_path,
            pdf_out
        )
    except Exception as e:
        return f"Error: {str(e)}", None, None

# Build UI
with gr.Blocks(title="Islamic Lecture Formatter") as demo:
    gr.Markdown("# 📜 Islamic Lecture Formatter")
    gr.Markdown("Paste your tagged transcription from AI Studio and get your professional Word & PDF docs.")
    
    with gr.Row():
        with gr.Column():
            output_filename = gr.Textbox(
                label="Output Filename", 
                placeholder="e.g. Lesson_05_Tawheed",
                info="The name of the files that will be created."
            )
            with gr.Row():
                export_path = gr.Textbox(
                    label="Export Path", 
                    value=BASE_DIR,
                    placeholder="C:\\path\\to\\save",
                    scale=4
                )
                browse_btn = gr.Button("📂 Browse", scale=1)
                
            transcript_input = gr.Textbox(
                label="Tagged Transcription (Markdown)", 
                placeholder="Paste the tagged text from AI Studio here...",
                lines=15
            )
            process_btn = gr.Button("Generate & Send to Telegram", variant="primary")
            
        with gr.Column():
            status_output = gr.Textbox(label="Status")
            docx_file = gr.File(label="Download Word (.docx)")
            pdf_file = gr.File(label="Download PDF (.pdf)")

    browse_btn.click(fn=select_directory, outputs=export_path)
    
    process_btn.click(
        fn=process_transcript,
        inputs=[output_filename, export_path, transcript_input],
        outputs=[status_output, docx_file, pdf_file]
    )

if __name__ == "__main__":
    demo.launch(inbrowser=True)
