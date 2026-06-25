import markdown
import os
import subprocess
import time

# Read the markdown file
with open('project_documentation.md', 'r', encoding='utf-8') as f:
    text = f.read()

# Convert to HTML
html_content = markdown.markdown(text, extensions=['tables', 'fenced_code'])

# Wrap in basic HTML structure with CSS to ensure it takes up multiple pages and looks professional
full_html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        font-family: Arial, sans-serif;
        line-height: 1.6;
        padding: 40px;
        color: #333;
    }}
    h1 {{
        color: #2c3e50;
        text-align: center;
        border-bottom: 2px solid #2c3e50;
        padding-bottom: 10px;
        margin-bottom: 30px;
        page-break-after: avoid;
    }}
    h2 {{
        color: #34495e;
        margin-top: 40px;
        border-bottom: 1px solid #ccc;
        padding-bottom: 5px;
        page-break-after: avoid;
    }}
    h3 {{
        color: #7f8c8d;
        page-break-after: avoid;
    }}
    pre {{
        background-color: #f4f4f4;
        padding: 15px;
        border-radius: 5px;
        overflow-x: auto;
        page-break-inside: avoid;
    }}
    code {{
        font-family: Consolas, monospace;
    }}
    ul, ol {{
        margin-bottom: 20px;
    }}
    li {{
        margin-bottom: 10px;
    }}
    .page-break {{
        page-break-before: always;
    }}
</style>
</head>
<body>
{html_content.replace('<hr />', '<hr class="page-break" />')}
</body>
</html>
"""

html_path = os.path.abspath('project_documentation.html')
pdf_path = os.path.abspath('project_documentation.pdf')

# Write HTML file
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

# Use MS Edge to print to PDF
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    print("Edge not found at default path, trying alternative...")
    # Add logic for other paths or use PowerShell to find it if needed
    edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

if os.path.exists(edge_path):
    print("Converting HTML to PDF using MS Edge headless mode...")
    subprocess.run([
        edge_path,
        "--headless",
        "--disable-gpu",
        "--run-all-compositor-stages-before-draw",
        f"--print-to-pdf={pdf_path}",
        html_path
    ])
    print(f"PDF successfully generated at {pdf_path}")
else:
    print("MS Edge could not be found.")

