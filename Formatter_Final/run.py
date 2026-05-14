"""
run.py — Easy Runner for Islamic Lecture Formatter
==================================================
Usage:
    python run.py session_name.md

Description:
    This script runs the v2_formatter.py on a specified markdown file.
    It automatically looks for the template in the parent directory.
"""

import os
import sys
import subprocess
import sys

# Fix Windows console encoding for Arabic characters
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

def main():
    if len(sys.argv) < 2:
        print("Usage: python run.py your_file.md")
        sys.exit(1)

    md_file = sys.argv[1]
    if not os.path.exists(md_file):
        print(f"Error: File '{md_file}' not found.")
        sys.exit(1)

    base_name = os.path.splitext(os.path.basename(md_file))[0]
    output_docx = f"{base_name}.docx"

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    template_path = os.path.join(parent_dir, "template.docx")
    
    # Check for template
    if not os.path.exists(template_path):
        # Fallback if the user moved the folder
        print(f"Warning: Template not found at {template_path}")
        print("Please ensure the Word template is in the directory above this folder.")
        sys.exit(1)

    print(f"Processing: {md_file}")
    print(f"Using Template: {os.path.basename(template_path)}")

    # Import and run the formatter directly
    sys.path.append(base_dir)
    try:
        import v2_formatter
        v2_formatter.format_document(md_file, template_path, output_docx)
        print(f"\nSUCCESS!")
        print(f"Final Document: {os.path.abspath(output_docx)}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
