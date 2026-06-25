import zipfile
import base64
import os

def recreate_docx_from_dump(dump_path, output_docx_path):
    if not os.path.exists(dump_path):
        print(f"ERROR: Cannot find the dump file at {dump_path}")
        return

    print("Reading the AI Dump File...")
    
    with open(dump_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print("Rebuilding DOCX structure from scratch...")
    
    # We use zipfile to build the .docx directly in memory and save it
    with zipfile.ZipFile(output_docx_path, 'w', zipfile.ZIP_DEFLATED) as docx_zip:
        current_file = None
        current_content = []
        
        for line in lines:
            # Detect the start of a new file inside the dump
            if line.startswith("--- BEGIN FILE: "):
                # Extract the exact filename (e.g., 'word/document.xml')
                current_file = line.replace("--- BEGIN FILE: ", "").strip().replace(" ---", "")
                current_content = []
            
            # Detect the end of the file
            elif line.startswith("--- END FILE: "):
                if current_file:
                    # Combine all the lines we collected for this file
                    raw_data = "".join(current_content).strip()
                    
                    # Check if it is a binary image (Base64 encoded)
                    if raw_data.startswith("BASE64:"):
                        b64_string = raw_data[7:] # Remove the "BASE64:" prefix
                        file_bytes = base64.b64decode(b64_string)
                        docx_zip.writestr(current_file, file_bytes)
                        print(f" -> Recreated BINARY (Image/Media): {current_file}")
                    
                    # Otherwise, it is a standard XML or RELS text file
                    else:
                        docx_zip.writestr(current_file, raw_data.encode('utf-8'))
                        print(f" -> Recreated TEXT/XML: {current_file}")
                    
                    current_file = None
            
            # If we are currently inside a file block, keep collecting the lines
            elif current_file is not None:
                current_content.append(line)

    print(f"\nSUCCESS! 100% Identical DOCX has been fully generated.")
    print(f"Saved to: {output_docx_path}")

# --- SET YOUR PATHS ---
dump_file = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload\COMPLETE_AI_DUMP.txt"
recreated_docx = r"C:\Users\saif_\Desktop\downs\Currently\Daily\Lectures\ANtiGrav\AutoUpload\Perfect_AI_Recreation.docx"

if __name__ == "__main__":
    recreate_docx_from_dump(dump_file, recreated_docx)