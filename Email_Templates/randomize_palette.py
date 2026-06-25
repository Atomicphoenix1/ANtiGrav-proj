import random
import re
import os

# REINVENTED VIBRANT PALETTES (High Saturation, Pop Art Style)
PALETTES = [
    ["#FF006E", "#3A86FF", "#FFBE0B", "#FB5607", "#fdfcf0"], 
    ["#FF595E", "#FFCA3A", "#8AC926", "#1982C4", "#f0f9ff"], 
    ["#F15BB5", "#FEE440", "#00BBF9", "#00F5D4", "#f5f5f5"], 
    ["#9B5DE5", "#F15BB5", "#FEE440", "#00BBF9", "#fafafa"], 
    ["#FF70A6", "#FF9770", "#FFD670", "#E9FF70", "#fff9f0"], 
    ["#FFBC42", "#D81159", "#218380", "#73D2DE", "#f0fff4"], 
    ["#FF99C8", "#FCF6BD", "#D0F4DE", "#A9DEF9", "#fff0f5"], 
    ["#00F5D4", "#00BBF9", "#9B5DE5", "#F15BB5", "#f0ffff"], 
    ["#FF5F5F", "#FFD15F", "#5FFF9F", "#5F9FFF", "#f9f9f9"], 
    ["#FF9F1C", "#2EC4B6", "#E71D36", "#011627", "#ffffff"], 
    ["#70D6FF", "#FF70A6", "#FF9770", "#FFD670", "#f0f2f5"], 
    ["#EF476F", "#FFD166", "#06D6A0", "#118AB2", "#f8fafc"], 
]

FILES = ["formal_template.html", "newsletter_template.html"]

def update_file(file_path, palette):
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Inject colors into the markers
    for i, color in enumerate(palette):
        marker = f"C{i+1}"
        pattern = rf"/\*{marker}\*/#[0-9a-fA-F]{{3,6}}/\*{marker}\*/"
        replacement = f"/*{marker}*/{color}/*{marker}*/"
        content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Permanently updated colors in {file_path}")
    return True

if __name__ == "__main__":
    palette = random.choice(PALETTES)
    random.shuffle(palette[:4])
    for f in FILES:
        update_file(f, palette)
