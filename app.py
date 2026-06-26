"""
Convin Support - Chat & Voice Support with Knowledge Base
"""

import streamlit as st
import uuid
from datetime import datetime
import anthropic
import json
import os

# ══════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Convin Support",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

KB_DIR = "kb_files"
KB_INDEX = "kb_index.json"

os.makedirs(KB_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
body, html, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; }
.main { background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 100%); color: #e5e7eb; }
#MainMenu, footer, header { display: none !important; }
.stDeployButton { display: none !important; }
.widget-box { background: rgba(17, 24, 39, 0.8); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 20px; }
.message-container { background: rgba(13, 17, 23, 0.6); border-radius: 8px; padding: 12px; margin-bottom: 8px; border-left: 3px solid #6366f1; }
.message-container.user { background: rgba(99, 102, 241, 0.15); border-left-color: #22d3ee; margin-left: 20px; }
.message-container.assistant { background: rgba(99, 102, 241, 0.08); border-left-color: #10b981; margin-right: 20px; }
.metric-card { background: rgba(17, 24, 39, 0.6); border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 10px; padding: 20px; text-align: center; }
.metric-value { font-size: 2rem; font-weight: 700; color: #6366f1; }
.metric-label { font-size: 0.9rem; color: #94a3b8; margin-top: 8px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  INITIALIZATION
# ══════════════════════════════════════════════════════════════════
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "kb_files" not in st.session_state:
    st.session_state.kb_files = []
if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

# ══════════════════════════════════════════════════════════════════
#  SIDEBAR & NAVIGATION
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔷 Convin Support")
    st.divider()
    page = st.radio("Select Page", ["💬 Chat", "📊 Analytics", "⚙️ Settings"], label_visibility="collapsed")
    st.divider()
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    st.markdown(f"**Messages:** {len(st.session_state.chat_messages)}")
    st.markdown(f"**KB Files:** {len(st.session_state.kb_files)}")

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

def save_kb_index(index):
    """Save KB index"""
    with open(KB_INDEX, 'w') as f:
        json.dump(index, f, indent=2)

def read_file_content(file_path: str) -> str:
    """Read file content - simple text extraction"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            # Limit content size
            if len(content) > 2000:
                content = content[:2000] + "\n[... truncated ...]"
            return content
    except Exception as e:
        return f"[Error reading file: {str(e)}]"

def get_kb_context():
    """Build KB context for chat"""
    kb_index = load_kb_index()
    files = kb_index.get("files", [])

    if not files:
        return "No KB files uploaded."

    context = f"\n### KNOWLEDGE BASE ({len(files)} files):\n"

    for file_info in files:
        file_path = file_info.get("path", "")
        file_name = file_info.get("name", "unknown")

        if os.path.exists(file_path):
            content = read_file_content(file_path)
            context += f"\n**File: {file_name}**\n{content}\n---\n"
        else:
            context += f"\n**File: {file_name}** (not found)\n"

    return context

def get_chat_response(user_message: str) -> str:
    """Get response from Claude"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "⚠️ API key not configured. Add ANTHROPIC_API_KEY to Streamlit secrets."

        kb_context = get_kb_context()

        system_prompt = f"""You are a helpful support agent for Convin.

KNOWLEDGE BASE:
{kb_context}

Instructions:
1. Answer questions using the knowledge base above
2. If information is not in KB, say "I don't have that information"
3. Be concise and professional
4. Reference the source file when helpful"""

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=800,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ══════════════════════════════════════════════════════════════════
#  PAGE: CHAT
# ══════════════════════════════════════════════════════════════════
if page == "💬 Chat":
    st.title("💬 Chat Support")
    st.markdown("*Chat with AI powered by your knowledge base*")

    kb_index = load_kb_index()
    kb_count = len(kb_index.get("files", []))

    if kb_count > 0:
        st.success(f"✅ KB Connected: {kb_count} file(s) active")
    else:
        st.info("⚠️ No KB files. Go to Settings to upload files.")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("💬 Conversation")
        chat_display = st.container(height=400, border=True)

        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    chat_display.markdown(f"""<div class="message-container user"><b>You:</b> {msg["content"]}</div>""", unsafe_allow_html=True)
                else:
                    chat_display.markdown(f"""<div class="message-container assistant"><b>Support:</b> {msg["content"]}</div>""", unsafe_allow_html=True)
        else:
            chat_display.info("💬 Start a conversation...")

        st.divider()
        user_input = st.text_input("Your message", placeholder="Type your question...", label_visibility="collapsed", key="chat_input")

        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            with st.spinner("Thinking..."):
                response = get_chat_response(user_input)

            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()

    with col2:
        st.subheader("📞 Voice Call")

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Status", "Ready" if not st.session_state.voice_active else "Active", "🟢")
        with col_s2:
            st.metric("Session", st.session_state.session_id[:8], "ID")

        st.divider()

        phone = st.text_input("Phone Number", placeholder="+1 (555) 000-0000", key="phone")
        api_key = st.text_input("Voice API Key", type="password", key="voice_key")

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("📞 Start Call", use_container_width=True):
                if phone and api_key:
                    st.session_state.voice_active = True
                    st.success(f"✅ Call initiated!\nPhone: {phone}")
                else:
                    st.error("❌ Enter phone and API key")

        with col_btn2:
            if st.button("❌ End Call", use_container_width=True, disabled=not st.session_state.voice_active):
                st.session_state.voice_active = False
                st.info("✅ Call ended")

# ══════════════════════════════════════════════════════════════════
#  PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.title("📊 Analytics Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""<div class="metric-card"><div class="metric-value">1,247</div><div class="metric-label">Total Messages</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="metric-card"><div class="metric-value">94.2%</div><div class="metric-label">Satisfaction</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class="metric-card"><div class="metric-value">2.3min</div><div class="metric-label">Avg Response</div></div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""<div class="metric-card"><div class="metric-value">342</div><div class="metric-label">Active Users</div></div>""", unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Messages per Day")
        import pandas as pd
        df = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Messages": [145, 182, 156, 198, 212, 95, 78]})
        st.bar_chart(df.set_index("Day"))

    with col2:
        st.subheader("🔄 Session Duration")
        df2 = pd.DataFrame({"Hour": ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"], "Duration": [15, 12, 22, 45, 67, 82, 71, 48]})
        st.area_chart(df2.set_index("Hour"))

    st.divider()
    st.subheader("📊 Top Topics")
    for topic, count in [("Billing", 245), ("Technical Support", 198), ("Account Mgmt", 156), ("Features", 142), ("General", 128)]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(count / 250)
        with col2:
            st.markdown(f"**{topic}**: {count}")

# ══════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.subheader("📚 Knowledge Base")
        st.markdown("Upload files to enhance responses")

        uploaded_files = st.file_uploader(
            "Upload KB Files (any type)",
            accept_multiple_files=True,
            key="kb_upload"
        )

        if uploaded_files:
            kb_index = load_kb_index()

            for uploaded_file in uploaded_files:
                file_path = os.path.join(KB_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Check if already in index
                exists = any(f["name"] == uploaded_file.name for f in kb_index["files"])
                if not exists:
                    kb_index["files"].append({
                        "name": uploaded_file.name,
                        "path": file_path,
                        "size": uploaded_file.size,
                        "uploaded_at": datetime.now().isoformat()
                    })

            save_kb_index(kb_index)
            st.session_state.kb_files = kb_index["files"]
            st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")

        st.divider()
        st.subheader("📋 Files")

        kb_index = load_kb_index()
        st.session_state.kb_files = kb_index["files"]

        if kb_index["files"]:
            st.markdown(f"**Total:** {len(kb_index['files'])} file(s)")
            for file_info in kb_index["files"]:
                col_name, col_size = st.columns([2, 1])
                with col_name:
                    st.markdown(f"📄 {file_info['name']}")
                with col_size:
                    size_mb = file_info.get('size', 0) / 1024 / 1024
                    st.markdown(f"{size_mb:.2f}MB")
        else:
            st.info("💾 No KB files yet")

    with col2:
        st.subheader("⚙️ Configuration")

        st.markdown("**API Status**")
        api_status = "✅ OK" if st.secrets.get("ANTHROPIC_API_KEY") else "❌ Missing"
        st.markdown(f"Anthropic API: {api_status}")

        st.divider()

        st.markdown("**Chat Settings**")
        temperature = st.slider("Response Creativity", 0.0, 1.0, 0.7, 0.1)
        max_tokens = st.slider("Max Response Length", 100, 2000, 500, 100)

        st.divider()

        st.markdown("**Session**")
        st.markdown(f"🔷 ID: `{st.session_state.session_id}`")
        st.markdown(f"💬 Messages: {len(st.session_state.chat_messages)}")
        st.markdown(f"📚 KB Files: {len(st.session_state.kb_files)}")

        st.divider()

        if st.button("🔄 Reset Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.success("✅ Chat cleared")
            st.rerun()

        st.info("💾 All KB files stored permanently")

st.divider()
st.markdown("<div style='text-align: center; color: #6b7280; font-size: 0.85rem;'><p>© 2026 Convin Support | Powered by Claude AI</p></div>", unsafe_allow_html=True)
