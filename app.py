"""
Convin Support - Modern Chat & Voice Support Platform
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
#  MODERN STYLING
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #0f172a !important;
    color: #e2e8f0 !important;
}

/* Main background */
.main {
    background: linear-gradient(135deg, #0f172a 0%, #1a202c 100%);
    background-attachment: fixed;
}

/* Hide unwanted elements */
#MainMenu, footer, header { display: none !important; }
.stDeployButton { display: none !important; }

/* ────────────────────────────────────── */
/* SIDEBAR STYLING */
/* ────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [style*="flex-direction"] {
    gap: 1rem;
}

/* ────────────────────────────────────── */
/* CARD & CONTAINER STYLING */
/* ────────────────────────────────────── */
.card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.6) 100%);
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    padding: 24px;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.card:hover {
    border-color: rgba(148, 163, 184, 0.4);
    box-shadow: 0 12px 48px rgba(59, 130, 246, 0.2);
}

/* ────────────────────────────────────── */
/* TYPOGRAPHY */
/* ────────────────────────────────────── */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.5px;
}

h1 {
    font-size: 2.5rem !important;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

h2 {
    font-size: 1.75rem !important;
    color: #e2e8f0 !important;
    margin-bottom: 1rem !important;
}

h3 {
    font-size: 1.25rem !important;
    color: #cbd5e1 !important;
}

/* ────────────────────────────────────── */
/* BUTTONS */
/* ────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 12px 24px !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.5) !important;
}

/* ────────────────────────────────────── */
/* INPUTS */
/* ────────────────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > select {
    background: rgba(30, 41, 59, 0.6) !important;
    border: 1px solid rgba(148, 163, 184, 0.3) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    padding: 12px 16px !important;
    font-size: 0.95rem !important;
    transition: all 0.3s ease !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
}

/* ────────────────────────────────────── */
/* MESSAGE CONTAINERS */
/* ────────────────────────────────────── */
.message-user {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(99, 102, 241, 0.1) 100%);
    border-left: 3px solid #3b82f6;
    padding: 14px 16px;
    border-radius: 10px;
    margin-bottom: 10px;
    margin-left: 30px;
    color: #cbd5e1;
    font-size: 0.95rem;
    line-height: 1.6;
}

.message-assistant {
    background: linear-gradient(135deg, rgba(34, 211, 238, 0.1) 0%, rgba(16, 185, 129, 0.05) 100%);
    border-left: 3px solid #22d3ee;
    padding: 14px 16px;
    border-radius: 10px;
    margin-bottom: 10px;
    margin-right: 30px;
    color: #e2e8f0;
    font-size: 0.95rem;
    line-height: 1.6;
}

.message-user strong { color: #7dd3fc; }
.message-assistant strong { color: #22d3ee; }

/* ────────────────────────────────────── */
/* METRIC CARDS */
/* ────────────────────────────────────── */
.metric-box {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(99, 102, 241, 0.05) 100%);
    border: 1px solid rgba(59, 130, 246, 0.3);
    border-radius: 14px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-box:hover {
    border-color: rgba(59, 130, 246, 0.6);
    box-shadow: 0 8px 25px rgba(59, 130, 246, 0.2);
    transform: translateY(-4px);
}

.metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-top: 8px;
    font-weight: 500;
}

/* ────────────────────────────────────── */
/* FILE UPLOAD */
/* ────────────────────────────────────── */
[data-testid="stFileUploadDropzone"] {
    border: 2px dashed rgba(59, 130, 246, 0.4) !important;
    border-radius: 12px !important;
    background: rgba(59, 130, 246, 0.05) !important;
    padding: 30px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploadDropzone"]:hover {
    border-color: rgba(59, 130, 246, 0.8) !important;
    background: rgba(59, 130, 246, 0.1) !important;
}

/* ────────────────────────────────────── */
/* DIVIDER */
/* ────────────────────────────────────── */
hr {
    background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.2), transparent);
    border: none;
    height: 1px;
    margin: 2rem 0 !important;
}

/* ────────────────────────────────────── */
/* STATUS BADGES */
/* ────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.status-active {
    background: rgba(16, 185, 129, 0.2);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.4);
}

.status-inactive {
    background: rgba(148, 163, 184, 0.2);
    color: #94a3b8;
    border: 1px solid rgba(148, 163, 184, 0.4);
}

/* ────────────────────────────────────── */
/* RADIO BUTTONS */
/* ────────────────────────────────────── */
[data-testid="stRadio"] {
    display: flex;
    gap: 1rem;
}

[data-testid="stRadio"] label {
    background: rgba(30, 41, 59, 0.6);
    border: 2px solid rgba(148, 163, 184, 0.2);
    padding: 12px 20px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-weight: 500;
}

[data-testid="stRadio"] label:hover {
    border-color: rgba(59, 130, 246, 0.5);
    background: rgba(59, 130, 246, 0.1);
}

/* ────────────────────────────────────── */
/* ANIMATIONS */
/* ────────────────────────────────────── */
@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-in {
    animation: slideIn 0.3s ease-out;
}

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
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔷 Convin Support")
    st.markdown("*Modern Support Platform*")
    st.divider()

    page = st.radio(
        "Navigation",
        ["💬 Chat", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()

    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state.chat_messages), "📬")
        with col2:
            st.metric("KB Files", len(st.session_state.kb_files), "📚")

    st.markdown("---")

    st.markdown("""
    **Session Info**
    - 🔷 ID: `" + st.session_state.session_id[:8] + "...`
    - ✅ Status: Active
    - 🌍 Region: Cloud
    """)

# ══════════════════════════════════════════════════════════════════
#  KB FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def load_kb_index():
    try:
        if os.path.exists(KB_INDEX):
            with open(KB_INDEX, 'r') as f:
                return json.load(f)
    except:
        pass
    return {"files": []}

def save_kb_index(index):
    with open(KB_INDEX, 'w') as f:
        json.dump(index, f, indent=2)

def read_file_content(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            if len(content) > 2000:
                content = content[:2000] + "\n[... truncated ...]"
            return content
    except Exception as e:
        return f"[Error: {str(e)}]"

def get_kb_context():
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
    st.markdown("""
    <style>
    .page-title {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    </style>
    <div class="page-title">💬 Chat Support</div>
    """, unsafe_allow_html=True)

    st.markdown("*Powered by your knowledge base*")

    kb_index = load_kb_index()
    kb_count = len(kb_index.get("files", []))

    if kb_count > 0:
        st.success(f"✅ **KB Active** — {kb_count} file(s) connected", icon="📚")
    else:
        st.info("⚠️ No KB files. Upload files in Settings for better answers.", icon="💡")

    st.divider()

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("### 💬 Conversation")

        chat_display = st.container(height=450, border=False)

        with chat_display:
            if st.session_state.chat_messages:
                for msg in st.session_state.chat_messages:
                    if msg["role"] == "user":
                        st.markdown(
                            f"""<div class="message-user"><strong>You:</strong> {msg["content"]}</div>""",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""<div class="message-assistant"><strong>Support:</strong> {msg["content"]}</div>""",
                            unsafe_allow_html=True
                        )
            else:
                st.info("💬 Start a conversation...", icon="🔷")

        st.divider()

        col_input = st.columns([1])[0]
        with col_input:
            user_input = st.text_input(
                "Message",
                placeholder="Ask me anything...",
                label_visibility="collapsed",
                key="chat_input"
            )

        if user_input:
            st.session_state.chat_messages.append({"role": "user", "content": user_input})

            with st.spinner("⏳ Thinking..."):
                response = get_chat_response(user_input)

            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()

    with col2:
        st.markdown("### 📞 Voice Call")

        st.markdown("<br>", unsafe_allow_html=True)

        with st.container():
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.markdown("""
                <div class="metric-box">
                    <div style="font-size: 2rem; margin-bottom: 8px;">🟢</div>
                    <div class="metric-label">Status</div>
                    <div class="metric-value" style="font-size: 1.3rem; margin-top: 4px;">
                    """ + ("Active" if st.session_state.voice_active else "Ready") + """
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_s2:
                st.markdown(f"""
                <div class="metric-box">
                    <div style="font-size: 2rem; margin-bottom: 8px;">📞</div>
                    <div class="metric-label">Calls</div>
                    <div class="metric-value" style="font-size: 1.3rem; margin-top: 4px;">0</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        st.markdown("**Enter Details**")

        phone = st.text_input(
            "Phone",
            placeholder="+1 (555) 000-0000",
            key="phone",
            label_visibility="collapsed"
        )

        api_key = st.text_input(
            "API Key",
            type="password",
            placeholder="Voice agent API key",
            key="voice_key",
            label_visibility="collapsed"
        )

        col_btn1, col_btn2 = st.columns(2)

        with col_btn1:
            if st.button("📞 Start", use_container_width=True, key="start"):
                if phone and api_key:
                    st.session_state.voice_active = True
                    st.success(f"✅ Call started\n📱 {phone}")
                else:
                    st.error("❌ Enter phone & API key")

        with col_btn2:
            if st.button("❌ End", use_container_width=True, key="end", disabled=not st.session_state.voice_active):
                st.session_state.voice_active = False
                st.info("✅ Call ended")

# ══════════════════════════════════════════════════════════════════
#  PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.markdown("""<div class="page-title">📊 Analytics Dashboard</div>""", unsafe_allow_html=True)
    st.markdown("*Support performance metrics*")

    st.divider()

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">1.2K</div>
            <div class="metric-label">Total Messages</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">94%</div>
            <div class="metric-label">Satisfaction</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">2.3m</div>
            <div class="metric-label">Avg Response</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-box">
            <div class="metric-value">342</div>
            <div class="metric-label">Active Users</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.markdown("### 📈 Messages per Day")
        import pandas as pd
        df = pd.DataFrame({"Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"], "Messages": [145, 182, 156, 198, 212, 95, 78]})
        st.bar_chart(df.set_index("Day"), use_container_width=True)

    with col2:
        st.markdown("### 🔄 Session Duration")
        df2 = pd.DataFrame({"Hour": ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"], "Duration": [15, 12, 22, 45, 67, 82, 71, 48]})
        st.area_chart(df2.set_index("Hour"), use_container_width=True)

    st.divider()

    st.markdown("### 📊 Top Topics")
    topics = [("Billing", 245), ("Technical Support", 198), ("Account Mgmt", 156), ("Features", 142), ("General", 128)]

    for topic, count in topics:
        col1, col2, col3 = st.columns([2, 0.5, 1])
        with col1:
            st.progress(count / 250)
        with col2:
            st.write("")
        with col3:
            st.markdown(f"**{topic}**: {count}")

# ══════════════════════════════════════════════════════════════════
#  PAGE: SETTINGS
# ══════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.markdown("""<div class="page-title">⚙️ Settings & Configuration</div>""", unsafe_allow_html=True)
    st.markdown("*Manage KB and preferences*")

    st.divider()

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown("### 📚 Knowledge Base Management")
        st.markdown("Upload files to enhance AI responses")

        st.divider()

        uploaded_files = st.file_uploader(
            "Upload Files",
            accept_multiple_files=True,
            key="kb_upload"
        )

        if uploaded_files:
            kb_index = load_kb_index()

            for uploaded_file in uploaded_files:
                file_path = os.path.join(KB_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

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
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded!", icon="📥")

        st.divider()

        st.markdown("### 📋 Uploaded Files")

        kb_index = load_kb_index()
        st.session_state.kb_files = kb_index["files"]

        if kb_index["files"]:
            st.markdown(f"**Total:** `{len(kb_index['files'])} files` • 💾 Permanent Storage")

            for file_info in kb_index["files"]:
                with st.container():
                    col_icon, col_name, col_size, col_date = st.columns([0.5, 2, 1, 1.5])

                    with col_icon:
                        st.markdown("📄")
                    with col_name:
                        st.markdown(f"**{file_info['name']}**")
                    with col_size:
                        size_mb = file_info.get('size', 0) / 1024 / 1024
                        st.markdown(f"`{size_mb:.2f}MB`")
                    with col_date:
                        st.markdown(f"*{file_info.get('uploaded_at', 'N/A')[:10]}*", help="Upload date")

                    st.divider()
        else:
            st.info("💾 No KB files yet. Start uploading to enhance AI responses!", icon="📂")

    with col2:
        st.markdown("### 🔧 Configuration")

        st.markdown("**API Status**")
        api_ok = "✅ OK" if st.secrets.get("ANTHROPIC_API_KEY") else "❌ Missing"
        st.markdown(f"""
        <div class="metric-box">
            <div style="text-align: left; padding: 16px;">
                <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 8px;">Anthropic API</div>
                <div style="font-size: 1.2rem; font-weight: 600; color: {'#10b981' if api_ok == '✅ OK' else '#ef4444'};">{api_ok}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.markdown("**Chat Settings**")

        col_temp, col_tokens = st.columns(2)
        with col_temp:
            temperature = st.slider("Creativity", 0.0, 1.0, 0.7, 0.1)
        with col_tokens:
            max_tokens = st.slider("Response Length", 100, 2000, 800, 100)

        st.divider()

        st.markdown("**Session Information**")

        st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6; padding: 16px; border-radius: 8px;">
            <div style="font-size: 0.9rem; color: #94a3b8; margin-bottom: 12px;">🔷 <strong>Session ID</strong></div>
            <code style="font-family: 'Fira Code'; font-size: 0.85rem; color: #cbd5e1;">{st.session_state.session_id}</code>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        col_msgs, col_files = st.columns(2)
        with col_msgs:
            st.metric("Messages", len(st.session_state.chat_messages), "💬")
        with col_files:
            st.metric("KB Files", len(st.session_state.kb_files), "📚")

        st.divider()

        if st.button("🔄 Reset Chat History", use_container_width=True):
            st.session_state.chat_messages = []
            st.success("✅ Chat history cleared", icon="🗑️")
            st.rerun()

        st.markdown("""
        <div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 12px; border-radius: 8px; margin-top: 12px;">
            <div style="font-size: 0.85rem; color: #10b981; font-weight: 600;">💾 All KB files are stored permanently</div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
<div style="text-align: center; padding: 24px 0; color: #64748b; font-size: 0.9rem;">
    <p>🔷 <strong>Convin Support</strong> — Modern AI-Powered Support Platform</p>
    <p style="margin-top: 8px; font-size: 0.8rem;">© 2026 Convin | Powered by Claude AI</p>
</div>
""", unsafe_allow_html=True)
