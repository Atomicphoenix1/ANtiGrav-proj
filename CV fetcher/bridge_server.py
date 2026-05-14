from flask import Flask, request, jsonify
import os
import subprocess
import json

app = Flask(__name__)

# SECURITY: Replace this with a random password of your choice
SECRET_KEY = "SEIF_SECRET_123"

# Pre-defined paths (Same as os_bridge.py)
PROJECT_PATHS = {
    "math": [r"C:\Users\saif_\Desktop\PYthon\Enigma 2.0", r"C:\Users\saif_\Desktop\PYthon"],
    "nano": [r"C:\Users\saif_\Desktop\downs\Junior", r"C:\Users\saif_\Desktop\downs\GV"],
    "teaching": [r"C:\Users\saif_\Desktop\downs\حاليًا\يومي\شغل"],
    "college": [r"C:\Users\saif_\Desktop\projects", r"C:\Users\saif_\Desktop\downs\here", r"C:\Users\saif_\Desktop\Year 2"]
}

def verify_request():
    print(f"DEBUG: Headers received: {request.headers}")
    auth_header = request.headers.get("Authorization")
    auth_param = request.args.get("key")
    
    if auth_header == f"Bearer {SECRET_KEY}" or auth_param == SECRET_KEY:
        return True
    
    print(f"DEBUG: Auth failed. Expected 'Bearer {SECRET_KEY}' or key param.")
    return False

@app.route('/list', methods=['GET'])
def list_files():
    if not verify_request(): return jsonify({"error": "Unauthorized"}), 401
    
    raw_input = request.args.get("category", "").lower().strip()
    
    # Strip common prefixes if AI includes them (e.g., "list math" -> "math")
    category = raw_input.replace("list ", "").replace("show ", "").replace("projects ", "").strip()
    
    if not category or category not in PROJECT_PATHS: 
        return jsonify({
            "error": f"Category '{category}' not found.",
            "valid_categories": list(PROJECT_PATHS.keys()),
            "tip": "Call this tool with just the category name (e.g., 'math')"
        }), 404
    
    results = []
    for path in PROJECT_PATHS[category]:
        if os.path.exists(path):
            files = os.listdir(path)
            relevant = [f for f in files if f.endswith(('.pdf', '.py', '.pptx', '.docx'))]
            results.append({"directory": path, "files": relevant[:10]})
    return jsonify(results)

@app.route('/exec', methods=['POST'])
def run_powershell():
    if not verify_request(): return jsonify({"error": "Unauthorized"}), 401
    
    command = None
    if request.is_json:
        command = request.get_json().get("command")
    
    if not command:
        command = request.form.get("command") or request.args.get("command")
    
    # Fallback: Use the raw body if it's not empty and not JSON
    if not command and request.data:
        try:
            command = request.data.decode('utf-8').strip()
        except:
            pass

    if not command: 
        return jsonify({"error": "No command provided. Send 'command' in JSON/Form or raw body."}), 400
    
    try:
        print(f"DEBUG: Running command: {command}")
        result = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        return jsonify({
            "stdout": result.stdout[:2000],
            "stderr": result.stderr[:500],
            "exit_code": result.returncode
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("Seif's OS Bridge is starting...")
    print("Connect this to Cloudflared or Ngrok on port 5000.")
    app.run(port=5000)
