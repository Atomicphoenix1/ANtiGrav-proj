import zipfile
import os
import base64

def dump_docx_to_txt(docx_path, output_txt_path):
    if not os.path.exists(docx_path):
        print(f"ERROR: Cannot find {docx_path}")
        return

    print(f"Extracting EVERY file from {docx_path} into text format...")

    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        all_files = docx_zip.namelist()
        
        with open(output_txt_path, 'w', encoding='utf-8') as out_file:
            out_file.write("=== DOCX FULL RECREATION DUMP ===\n")
            out_file.write("FILE_LIST: " + ",".join(all_files) + "\n\n")
            
            for file_path in all_files:
                print(f" -> Processing {file_path}")
                out_file.write(f"--- BEGIN FILE: {file_path} ---\n")
                
                # Read the raw bytes of the file
                file_bytes = docx_zip.read(file_path)
                
                # If it's an XML or RELS file, extract the raw text
                if file_path.endswith('.xml') or file_path.endswith('.rels'):
                    try:
                        text_content = file_bytes.decode('utf-8')
                        out_file.write(text_content)
                    except UnicodeDecodeError:
                        # Fallback just in case
                        out_file.write("BASE64:" + base64.b64encode(file_bytes).decode('utf-8'))
                
                # If it's a binary file (like media/image1.png), encode it in Base64 text
                else:
                    out_file.write("BASE64:" + base64.b64encode(file_bytes).decode('utf-8'))
                
                out_file.write(f"\n--- END FILE: {file_path} ---\n\n")

    print(f"\nSUCCESS! Complete document text dump saved to:\n{output_txt_path}")

# --- SET YOUR PATHS ---
input_file = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload\template.docx"
output_file = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload\COMPLETE_AI_DUMP.txt"

dump_docx_to_txt(input_file, output_file)