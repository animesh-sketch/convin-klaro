"""
Convin Support - Multi-page Chat & Voice Support Platform
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

# Create KB directory if it doesn't exist
os.makedirs(KB_DIR, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

body, html, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 100%);
    color: #e5e7eb;
}

#MainMenu, footer, header {
    display: none !important;
}

.stDeployButton {
    display: none !important;
}

.widget-box {
    background: rgba(17, 24, 39, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 20px;
    backdrop-filter: blur(10px);
}

.message-container {
    background: rgba(13, 17, 23, 0.6);
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    border-left: 3px solid #6366f1;
    font-size: 0.95rem;
    line-height: 1.5;
    color: #e5e7eb;
}

.message-container.user {
    background: rgba(99, 102, 241, 0.15);
    border-left-color: #22d3ee;
    margin-left: 20px;
}

.message-container.assistant {
    background: rgba(99, 102, 241, 0.08);
    border-left-color: #10b981;
    margin-right: 20px;
}

.stTextInput input {
    background: rgba(17, 24, 39, 0.8) !important;
    border: 1px solid rgba(99, 102, 241, 0.2) !important;
    color: #e5e7eb !important;
    border-radius: 8px !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4) !important;
}

.metric-card {
    background: rgba(17, 24, 39, 0.6);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
}

.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #6366f1;
}

.metric-label {
    font-size: 0.9rem;
    color: #94a3b8;
    margin-top: 8px;
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
#  SIDEBAR & NAVIGATION
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔷 Convin Support")
    st.divider()

    page = st.radio(
        "Select Page",
        ["💬 Chat", "📊 Analytics", "⚙️ Settings"],
        label_visibility="collapsed"
    )

    st.divider()
    st.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
    st.markdown(f"**Messages:** {len(st.session_state.chat_messages)}")
    st.markdown(f"**KB Files:** {len(st.session_state.kb_files)}")

# ══════════════════════════════════════════════════════════════════
#  KB & API FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def load_kb_index():
    """Load KB index from file"""
    if os.path.exists(KB_INDEX):
        with open(KB_INDEX, 'r') as f:
            return json.load(f)
    return {"files": []}

def save_kb_index(index):
    """Save KB index to file"""
    with open(KB_INDEX, 'w') as f:
        json.dump(index, f)

def get_kb_context():
    """Get context from uploaded KB files"""
    context = ""
    kb_index = load_kb_index()
    for file_info in kb_index.get("files", []):
        file_path = file_info.get("path", "")
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read()[:500]  # First 500 chars
                    context += f"\n\n[From {file_info.get('name', 'file')}]\n{content}"
            except:
                pass
    return context

def get_chat_response(user_message: str) -> str:
    """Get response from Claude with KB context"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "⚠️ API key not configured. Please add ANTHROPIC_API_KEY to secrets."

        # Get KB context
        kb_context = get_kb_context()
        system_prompt = f"""You are a helpful support agent for Convin.

        Knowledge Base Information:
        {kb_context if kb_context else "No KB files uploaded yet."}

        Use the knowledge base to provide accurate answers."""

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
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

    col1, col2 = st.columns([1, 1], gap="large")

    # Chat column
    with col1:
        st.subheader("💬 Conversation")

        chat_display = st.container(height=400, border=True)

        if st.session_state.chat_messages:
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    chat_display.markdown(
                        f"""<div class="message-container user"><b>You:</b> {msg["content"]}</div>""",
                        unsafe_allow_html=True
                    )
                else:
                    chat_display.markdown(
                        f"""<div class="message-container assistant"><b>Support:</b> {msg["content"]}</div>""",
                        unsafe_allow_html=True
                    )
        else:
            chat_display.info("💬 Start a conversation...")

        st.divider()

        user_input = st.text_input(
            "Your message",
            placeholder="Type your question here...",
            label_visibility="collapsed",
            key="chat_input"
        )

        if user_input:
            st.session_state.chat_messages.append({
                "role": "user",
                "content": user_input
            })

            with st.spinner("Thinking..."):
                response = get_chat_response(user_input)

            st.session_state.chat_messages.append({
                "role": "assistant",
                "content": response
            })

            st.rerun()

    # Voice column
    with col2:
        st.subheader("📞 Voice Call")
        st.markdown("*Connect with agent via voice*")

        voice_col1, voice_col2 = st.columns(2)
        with voice_col1:
            st.metric("Status", "Ready" if not st.session_state.voice_active else "Active", "🟢")
        with voice_col2:
            st.metric("Session", st.session_state.session_id[:8], "ID")

        st.divider()

        phone_number = st.text_input(
            "Phone Number",
            placeholder="+1 (555) 000-0000",
            key="phone_input"
        )

        voice_api_key = st.text_input(
            "Voice Agent API Key",
            placeholder="Enter your API key",
            type="password",
            key="voice_key_input"
        )

        col_start, col_end = st.columns(2)

        with col_start:
            if st.button("📞 Start Call", use_container_width=True, key="start_call"):
                if phone_number and voice_api_key:
                    st.session_state.voice_active = True
                    st.success(f"✅ Call initiated!\n\nPhone: {phone_number}")
                else:
                    st.error("❌ Please enter phone number and API key")

        with col_end:
            if st.button(
                "❌ End Call",
                use_container_width=True,
                key="end_call",
                disabled=not st.session_state.voice_active
            ):
                st.session_state.voice_active = False
                st.info("✅ Call ended")

# ══════════════════════════════════════════════════════════════════
#  PAGE: ANALYTICS
# ══════════════════════════════════════════════════════════════════
elif page == "📊 Analytics":
    st.title("📊 Analytics Dashboard")
    st.markdown("*Support metrics and insights*")

    # Demo data
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">1,247</div>
            <div class="metric-label">Total Messages</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">94.2%</div>
            <div class="metric-label">Satisfaction Rate</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">2.3min</div>
            <div class="metric-label">Avg Response Time</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">342</div>
            <div class="metric-label">Active Users</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Messages per Day")
        import pandas as pd
        df = pd.DataFrame({
            "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "Messages": [145, 182, 156, 198, 212, 95, 78]
        })
        st.bar_chart(df.set_index("Day"))

    with col2:
        st.subheader("🔄 Session Duration")
        df2 = pd.DataFrame({
            "Hour": ["12am", "3am", "6am", "9am", "12pm", "3pm", "6pm", "9pm"],
            "Duration": [15, 12, 22, 45, 67, 82, 71, 48]
        })
        st.area_chart(df2.set_index("Hour"))

    st.divider()

    st.subheader("📊 Top Topics")
    topics_data = {
        "Billing": 245,
        "Technical Support": 198,
        "Account Management": 156,
        "Product Features": 142,
        "General Inquiry": 128
    }

    for topic, count in topics_data.items():
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
    st.markdown("*Manage knowledge base and configuration*")

    col1, col2 = st.columns([1, 1], gap="large")

    # KB Upload
    with col1:
        st.subheader("📚 Knowledge Base")
        st.markdown("Upload files to enhance chat responses")

        uploaded_files = st.file_uploader(
            "Upload KB Files (PDF, DOCX, TXT, MD, JSON, CSV, etc.)",
            accept_multiple_files=True,
            key="kb_uploader"
        )

        if uploaded_files:
            kb_index = load_kb_index()

            for uploaded_file in uploaded_files:
                # Save file
                file_path = os.path.join(KB_DIR, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Add to index
                file_entry = {
                    "name": uploaded_file.name,
                    "path": file_path,
                    "size": uploaded_file.size,
                    "uploaded_at": datetime.now().isoformat()
                }

                # Check if already exists
                existing = [f for f in kb_index["files"] if f["name"] == uploaded_file.name]
                if not existing:
                    kb_index["files"].append(file_entry)

            save_kb_index(kb_index)
            st.session_state.kb_files = kb_index["files"]
            st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")

        st.divider()

        # KB Files List
        st.subheader("📋 Uploaded Files")

        kb_index = load_kb_index()
        st.session_state.kb_files = kb_index["files"]

        if kb_index["files"]:
            for i, file_info in enumerate(kb_index["files"]):
                col_name, col_size, col_delete = st.columns([2, 1, 1])

                with col_name:
                    st.markdown(f"📄 **{file_info['name']}**")

                with col_size:
                    size_mb = file_info.get('size', 0) / 1024 / 1024
                    st.markdown(f"`{size_mb:.2f}MB`")

                with col_delete:
                    if st.button("🗑️", key=f"delete_{i}"):
                        # Remove file
                        try:
                            os.remove(file_info["path"])
                        except:
                            pass

                        # Remove from index
                        kb_index["files"].pop(i)
                        save_kb_index(kb_index)
                        st.session_state.kb_files = kb_index["files"]
                        st.rerun()
        else:
            st.info("No KB files uploaded yet. Upload files to get started!")

    # Settings
    with col2:
        st.subheader("⚙️ Configuration")

        st.markdown("**API Settings**")
        api_key_status = "✅ Configured" if st.secrets.get("ANTHROPIC_API_KEY") else "❌ Not configured"
        st.markdown(f"Anthropic API Key: {api_key_status}")

        st.divider()

        st.markdown("**Chat Settings**")
        temperature = st.slider(
            "Response Creativity",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Lower = more focused, Higher = more creative"
        )

        max_tokens = st.slider(
            "Max Response Length",
            min_value=100,
            max_value=2000,
            value=500,
            step=100
        )

        st.divider()

        st.markdown("**Session Info**")
        st.markdown(f"🔷 Session ID: `{st.session_state.session_id}`")
        st.markdown(f"💬 Total Messages: {len(st.session_state.chat_messages)}")
        st.markdown(f"📚 KB Files: {len(st.session_state.kb_files)}")

        st.divider()

        if st.button("🔄 Reset Chat History", use_container_width=True):
            st.session_state.chat_messages = []
            st.success("✅ Chat history cleared")
            st.rerun()

        if st.button("🗑️ Clear KB", use_container_width=True):
            # Clear KB directory
            import shutil
            if os.path.exists(KB_DIR):
                shutil.rmtree(KB_DIR)
            os.makedirs(KB_DIR, exist_ok=True)

            # Clear index
            kb_index = {"files": []}
            save_kb_index(kb_index)
            st.session_state.kb_files = []
            st.success("✅ KB cleared")
            st.rerun()

st.divider()
st.markdown(
    "<div style='text-align: center; color: #6b7280; font-size: 0.85rem;'>"
    "<p>© 2026 Convin Support | Powered by Claude AI</p>"
    "</div>",
    unsafe_allow_html=True
)
