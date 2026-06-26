"""
Convin Chat Widget Server
Serves the embeddable chat widget with backend API
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import anthropic
import json
import os
from datetime import datetime
from functools import lru_cache

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configuration
KB_DIR = "kb_files"
KB_INDEX = "kb_index.json"
os.makedirs(KB_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  KB FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def load_kb_index():
    """Load KB index"""
    try:
        if os.path.exists(KB_INDEX):
            with open(KB_INDEX, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"files": []}

def read_file_content(file_path: str) -> str:
    """Read file content"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if len(content) > 2000:
                content = content[:2000] + "\n[... truncated ...]"
            return content
    except:
        return "[Error reading file]"

def get_kb_context():
    """Build KB context for chat"""
    kb_index = load_kb_index()
    files = kb_index.get("files", [])

    if not files:
        return "No KB files available."

    context = f"\n### KNOWLEDGE BASE ({len(files)} files):\n"

    for file_info in files:
        file_path = file_info.get("path", "")
        file_name = file_info.get("name", "unknown")

        if os.path.exists(file_path):
            content = read_file_content(file_path)
            context += f"\n**File: {file_name}**\n{content}\n---\n"

    return context

def get_chat_response(user_message: str, api_key: str = None) -> dict:
    """Get response from Claude"""
    try:
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            return {
                "status": "error",
                "message": "API key not configured",
                "reply": "❌ API key not configured on server"
            }

        kb_context = get_kb_context()

        system_prompt = f"""You are a helpful support agent for Convin.

KNOWLEDGE BASE:
{kb_context}

Instructions:
1. Answer questions using the knowledge base above
2. If information is not in KB, say "I don't have that information"
3. Be concise and professional (max 150 words)
4. Reference the source file when helpful
5. Be friendly and helpful"""

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )

        reply = response.content[0].text

        return {
            "status": "success",
            "message": user_message,
            "reply": reply,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "reply": f"❌ Error: {str(e)}"
        }

# ══════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def home():
    """Home page with widget demo"""
    return render_template('widget_demo.html')

@app.route('/analytics', methods=['GET'])
def analytics():
    """Analytics dashboard"""
    return render_template('analytics.html')

@app.route('/floating-widget', methods=['GET'])
def floating_widget():
    """Floating chat widget page"""
    return render_template('floating_widget.html')

@app.route('/widget', methods=['GET'])
def widget():
    """Serve the widget HTML"""
    return render_template('chat_widget.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat API endpoint"""
    try:
        data = request.json
        message = data.get('message', '').strip()

        if not message:
            return jsonify({
                "status": "error",
                "reply": "Please send a message"
            }), 400

        # Get API key from request or env
        api_key = data.get('api_key') or os.environ.get('ANTHROPIC_API_KEY')

        # Get response
        result = get_chat_response(message, api_key)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "reply": f"Server error: {str(e)}"
        }), 500

@app.route('/api/kb/status', methods=['GET'])
def kb_status():
    """Get KB status"""
    kb_index = load_kb_index()
    files = kb_index.get("files", [])

    return jsonify({
        "status": "connected",
        "kb_files": len(files),
        "files": [{"name": f["name"], "size": f.get("size", 0)} for f in files]
    })

@app.route('/api/kb/upload', methods=['POST'])
def kb_upload():
    """Upload KB file"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "No file provided"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "No file selected"}), 400

        # Save file
        file_path = os.path.join(KB_DIR, file.filename)
        file.save(file_path)

        # Update index
        kb_index = load_kb_index()
        exists = any(f["name"] == file.filename for f in kb_index["files"])

        if not exists:
            kb_index["files"].append({
                "name": file.filename,
                "path": file_path,
                "size": os.path.getsize(file_path),
                "uploaded_at": datetime.now().isoformat()
            })
            with open(KB_INDEX, 'w') as f:
                json.dump(kb_index, f, indent=2)

        return jsonify({
            "status": "success",
            "message": f"File '{file.filename}' uploaded",
            "kb_files": len(kb_index["files"])
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "Convin Chat Widget Server",
        "version": "1.0.0"
    })

# ══════════════════════════════════════════════════════════════════
#  ERROR HANDLERS
# ══════════════════════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": "error", "message": "Not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"status": "error", "message": "Server error"}), 500

# ══════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🚀 Convin Chat Widget Server Starting...")
    print("📍 Home: http://localhost:5000")
    print("💬 Widget: http://localhost:5000/widget")
    print("🔗 API: http://localhost:5000/api/chat")
    print("\nSet ANTHROPIC_API_KEY environment variable to enable chat")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
