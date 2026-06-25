import fitz  # PyMuPDF

def extract_pdf_fonts(pdf_path):
    print(f"Scanning {pdf_path} for fonts...\n")
    doc = fitz.open(pdf_path)
    
    # Use a set to avoid printing duplicate fonts
    unique_fonts = set()
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        font_list = page.get_fonts()
        
        for font in font_list:
            # font[3] contains the actual font name
            font_name = font[3]
            
            # Clean up the subset prefix (e.g., "AAAAAA+FontName" -> "FontName")
            if "+" in font_name:
                font_name = font_name.split("+")[1]
                
            unique_fonts.add(font_name)
            
    print("Fonts found in this PDF:")
    for f in sorted(unique_fonts):
        print(f" - {f}")

# --- SET YOUR PATH ---
pdf_file = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\01 الرسالة التبوكية لابن القيم\01 الرسالة التبوكية لابن القيم_Final.pdf"
extract_pdf_fonts(pdf_file)