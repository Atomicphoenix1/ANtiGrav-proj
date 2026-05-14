import docx
from docx.shared import RGBColor
from docx.oxml.ns import qn
import os

# ==========================================
# 1. EASY CONFIGURATION
# ==========================================
# Choose your color: 'red', 'blue', 'green', 'purple', 'orange', 'gold'
MY_COLOR = 'purple' 

INPUT_FILE = r"C:\Users\saif_\Desktop\downs\حاليًا\يومي\Lectures\ANtiGrav\test.docx"
OUTPUT_FILE = r"C:\Users\saif_\Desktop\downs\حاليًا\يومي\Lectures\ANtiGrav\mid.docx"

# ==========================================
# COLOR HELPER (Dictionary)
# ==========================================
COLORS = {
    'red':    (RGBColor(255, 0, 0), "FF0000"),
    'blue':   (RGBColor(0, 0, 255), "0000FF"),
    'green':  (RGBColor(0, 128, 0), "008000"),
    'purple': (RGBColor(128, 0, 128), "800080"),
    'orange': (RGBColor(255, 165, 0), "FFA500"),
    'gold':   (RGBColor(255, 215, 0), "FFD700"),
    'black':  (RGBColor(0, 0, 0), "000000")
}

def apply_color(run, color_tuple):
    standard_rgb, hex_code = color_tuple
    
    # Set standard color
    run.font.color.rgb = standard_rgb
    
    # Set Arabic-specific color (Complex Script)
    rPr = run._element.get_or_add_rPr()
    color = rPr.find(qn('w:color'))
    if color is None:
        color = docx.oxml.shared.OxmlElement('w:color')
        rPr.append(color)
    color.set(qn('w:val'), hex_code)

def process_file():
    if not os.path.exists(INPUT_FILE):
        print(f"File not found! Check your path.")
        return

    selected_color = COLORS.get(MY_COLOR.lower(), COLORS['red'])
    doc = docx.Document(INPUT_FILE)
    count = 0

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            if run.italic:
                apply_color(run, selected_color)
                count += 1

    doc.save(OUTPUT_FILE)
    print(f"Success! All italics are now {MY_COLOR}. Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_file()