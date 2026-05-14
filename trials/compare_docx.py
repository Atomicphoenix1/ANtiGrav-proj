import docx
from docx.oxml.ns import qn

def inspect_docx(filepath):
    try:
        doc = docx.Document(filepath)
    except Exception as e:
        return f"Error opening {filepath}: {e}"
        
    output = []
    output.append(f"--- Document: {filepath} ---")
    
    # Check first 5 paragraphs
    for i, para in enumerate(doc.paragraphs[:5]):
        output.append(f"Paragraph {i+1}:")
        
        # Check alignment
        align = para.alignment
        output.append(f"  Alignment: {align}")
        
        # Check RTL
        pPr = para._element.pPr
        is_rtl = False
        if pPr is not None:
            bidi = pPr.find(qn('w:bidi'))
            if bidi is not None:
                is_rtl = bidi.get(qn('w:val')) != '0'
        output.append(f"  RTL (w:bidi): {is_rtl}")
        
        # Check runs
        for j, run in enumerate(para.runs):
            text = run.text.strip()
            if not text:
                continue
            text = text[:30] + "..." if len(text) > 30 else text
            output.append(f"  Run {j+1}: '{text}'")
            output.append(f"    Font Name: {run.font.name}")
            output.append(f"    Font Size: {run.font.size.pt if run.font.size else None}")
            output.append(f"    Bold: {run.bold}")
            output.append(f"    Italic: {run.italic}")
            if run.font.color and run.font.color.rgb:
                output.append(f"    Color: #{run.font.color.rgb}")
            else:
                output.append(f"    Color: None (Auto)")
                
            # Check complex script tags
            rPr = run._element.rPr
            if rPr is not None:
                cs_font = None
                rFonts = rPr.find(qn('w:rFonts'))
                if rFonts is not None:
                    cs_font = rFonts.get(qn('w:cs'))
                
                bCs = rPr.find(qn('w:bCs')) is not None
                iCs = rPr.find(qn('w:iCs')) is not None
                rtl = rPr.find(qn('w:rtl')) is not None
                
                output.append(f"    Complex Script Font: {cs_font}")
                output.append(f"    Complex Script Bold (w:bCs): {bCs}")
                output.append(f"    Complex Script Italic (w:iCs): {iCs}")
                output.append(f"    Complex Script RTL (w:rtl): {rtl}")
                
    return "\n".join(output)

if __name__ == "__main__":
    f1 = "Al-Islam_Red_FinalWord.docx"
    f2 = "Final2.docx"
    with open("compare_output.txt", "w", encoding="utf-8") as f:
        f.write(inspect_docx(f1))
        f.write("\n" + "="*50 + "\n")
        f.write(inspect_docx(f2))
    print("Done. Saved to compare_output.txt")
