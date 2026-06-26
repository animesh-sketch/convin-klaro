"""
Convin Support - Chat & Voice Support Widget
"""

import streamlit as st
import uuid
from datetime import datetime
import anthropic
import os

# ══════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Convin Support",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body, html, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

.main {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1117 100%);
    color: #e5e7eb;
}

/* Hide Streamlit elements */
#MainMenu, footer, header {
    display: none !important;
}

.stDeployButton {
    display: none !important;
}

/* Customize sections */
.stContainer {
    max-width: 100%;
}

/* Widget styling */
[data-testid="stHorizontalBlock"] {
    gap: 2rem;
}

.widget-box {
    background: rgba(17, 24, 39, 0.8);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 20px;
    backdrop-filter: blur(10px);
}

.chat-area {
    display: flex;
    flex-direction: column;
    height: 100%;
    gap: 1rem;
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

.voice-button > button {
    background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
}

.voice-button > button:hover {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.4) !important;
}

.title-section {
    text-align: center;
    padding: 20px 0;
    margin-bottom: 30px;
}

.title-section h1 {
    color: #e5e7eb;
    font-size: 2rem;
    margin-bottom: 8px;
}

.title-section p {
    color: #94a3b8;
    font-size: 1rem;
}

/* Header */
.header-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 15px 40px;
    background: rgba(6, 9, 20, 0.9);
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
    margin-bottom: 20px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}

.header-icon {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}

.header-name {
    font-size: 1rem;
    font-weight: 700;
    color: #e5e7eb;
}

.header-status {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 0.85rem;
    color: #10b981;
}

.status-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="header-bar">
    <div class="header-left">
        <div class="header-icon">💬</div>
        <div class="header-name">Convin Support</div>
    </div>
    <div class="header-status">
        <div class="status-dot"></div>
        <span>Live & Ready</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  INITIALIZATION
# ══════════════════════════════════════════════════════════════════
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "voice_active" not in st.session_state:
    st.session_state.voice_active = False

# ══════════════════════════════════════════════════════════════════
#  API FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def get_chat_response(user_message: str) -> str:
    """Get response from Claude"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "⚠️ API key not configured. Please add ANTHROPIC_API_KEY to secrets."

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ══════════════════════════════════════════════════════════════════
#  TITLE
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="title-section">
    <h1>Convin Support</h1>
    <p>Chat with our AI agent or schedule a voice call</p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════
col1, col2 = st.columns([1, 1], gap="large")

# ──────────────────────────────────────────────────────────────────
#  CHAT WIDGET
# ──────────────────────────────────────────────────────────────────
with col1:
    st.markdown('<div class="widget-box">', unsafe_allow_html=True)

    st.subheader("💬 Chat Support")
    st.markdown("*AI-powered instant support*")

    # Chat display area
    chat_display = st.container(height=350, border=True)

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

    # Chat input
    st.divider()
    user_input = st.text_input(
        "Your message",
        placeholder="Type your question here...",
        label_visibility="collapsed",
        key="chat_input"
    )

    if user_input:
        # Add user message
        st.session_state.chat_messages.append({
            "role": "user",
            "content": user_input
        })

        # Get AI response
        with st.spinner("Thinking..."):
            response = get_chat_response(user_input)

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response
        })

        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────
#  VOICE WIDGET
# ──────────────────────────────────────────────────────────────────
with col2:
    st.markdown('<div class="widget-box">', unsafe_allow_html=True)

    st.subheader("📞 Voice Call")
    st.markdown("*Connect with Convin Voice Agent*")

    # Voice display
    voice_col1, voice_col2 = st.columns(2)
    with voice_col1:
        st.metric("Status", "Ready" if not st.session_state.voice_active else "Active", "🟢")
    with voice_col2:
        st.metric("Session", st.session_state.session_id[:8], "ID")

    st.divider()

    # Voice inputs
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

    # Voice buttons
    col_start, col_end = st.columns(2)

    with col_start:
        if st.button("📞 Start Call", use_container_width=True, key="start_call"):
            if phone_number and voice_api_key:
                st.session_state.voice_active = True
                st.success(f"✅ Call initiated!\n\nPhone: {phone_number}\nAgent: Convin Voice Agent")
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

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FOOTER / SESSION INFO
# ══════════════════════════════════════════════════════════════════
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.metric("Messages", len(st.session_state.chat_messages))

with footer_col2:
    st.metric("Session ID", st.session_state.session_id[:12] + "...")

with footer_col3:
    st.metric("Status", "🟢 Active")

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #6b7280; font-size: 0.85rem;'>"
    "<p>© 2026 Convin Support | Powered by Claude AI</p>"
    "</div>",
    unsafe_allow_html=True
)
