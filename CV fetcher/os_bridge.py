import os
import sys
import json
import subprocess

# Pre-defined paths for Seif's projects
PROJECT_PATHS = {
    "math": [r"C:\Users\saif_\Desktop\PYthon\Enigma 2.0", r"C:\Users\saif_\Desktop\PYthon"],
    "nano": [r"C:\Users\saif_\Desktop\downs\Junior", r"C:\Users\saif_\Desktop\downs\GV"],
    "teaching": [r"C:\Users\saif_\Desktop\downs\حاليًا\يومي\شغل"],
    "college": [r"C:\Users\saif_\Desktop\projects", r"C:\Users\saif_\Desktop\downs\here", r"C:\Users\saif_\Desktop\Year 2"]
}

def list_files(category):
    if category not in PROJECT_PATHS:
        return {"error": "Category not found"}
    results = []
    for path in PROJECT_PATHS[category]:
        if os.path.exists(path):
            files = os.listdir(path)
            relevant = [f for f in files if f.endswith(('.pdf', '.py', '.pptx', '.docx'))]
            results.append({"directory": path, "files": relevant[:10]})
    return results

def get_file_path(filename):
    for cat in PROJECT_PATHS:
        for path in PROJECT_PATHS[cat]:
            if os.path.exists(path):
                full_path = os.path.join(path, filename)
                if os.path.exists(full_path):
                    return {"abs_path": full_path}
    return {"error": "File not found"}

def run_powershell(command):
    try:
        # Run PowerShell command and capture output
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        return {
            "stdout": result.stdout[:2000],  # Truncate for AI context
            "stderr": result.stderr[:500],
            "exit_code": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: python os_bridge.py [list|find|exec] [arg]"}))
        sys.exit(1)
    
    cmd = sys.argv[1]
    arg = sys.argv[2]
    
    if cmd == "list":
        print(json.dumps(list_files(arg)))
    elif cmd == "find":
        print(json.dumps(get_file_path(arg)))
    elif cmd == "exec":
        print(json.dumps(run_powershell(arg)))
    else:
        print(json.dumps({"error": "Unknown command"}))
