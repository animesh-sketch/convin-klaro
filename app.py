"""
Convin Support
Chat & Voice Support Widget Platform
"""

import streamlit as st
import json
import os
import uuid
from datetime import datetime
from typing import Optional
import psycopg2
import psycopg2.extras
import anthropic
import base64

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

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stSidebar"],
[data-testid="collapsedControl"]   { display: none !important; }
.stDeployButton                    { display: none !important; }
[data-testid="stToolbar"]          { display: none !important; }

/*
 * ═══════════════════════════════════════════════════════════
 *  CONVIN SUPPORT — Premium Calm Design System
 * ───────────────────────────────────────────────────────────
 *  BG:         #0B0F1A   deep navy base
 *  Surface-1:  #111827   glass cards
 *  Surface-2:  #1A2035   elevated panels
 *  Accent:     #6366F1   indigo (calm, trustworthy)
 *  Accent-lt:  #818CF8   light indigo
 *  Cyan:       #22D3EE   subtle highlight
 *  Text-1:     #E5E7EB   soft white
 *  Text-2:     #94A3B8   muted steel blue
 *  Green:      #10B981   live/active
 * ═══════════════════════════════════════════════════════════
 */

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

.main {
    background: #060914;
    background-image:
        radial-gradient(ellipse 110% 55% at 50% -10%, rgba(139,92,246,0.18) 0%, transparent 55%),
        radial-gradient(ellipse 70%  45% at 95%  90%, rgba(236,72,153,0.12) 0%, transparent 50%),
        radial-gradient(ellipse 60%  40% at 5%   75%, rgba(34,211,238,0.09) 0%, transparent 50%);
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Top Nav */
.topnav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    height: 62px;
    background: rgba(6,9,20,0.88);
    backdrop-filter: blur(32px) saturate(220%);
    border-bottom: 1px solid rgba(139,92,246,0.18);
    display: flex; align-items: center;
    padding: 0 40px;
    justify-content: space-between;
    box-shadow: 0 1px 0 rgba(139,92,246,0.12), 0 4px 32px rgba(0,0,0,0.30);
}

.topnav-brand {
    display: flex; align-items: center; gap: 12px;
}

.topnav-brand .dot {
    width: 34px; height: 34px; border-radius: 10px;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.88rem; color: #fff; font-weight: 700;
    box-shadow: 0 0 22px rgba(99,102,241,0.45);
}

.topnav-brand .name {
    font-size: 0.95rem; font-weight: 700; color: #E5E7EB;
    letter-spacing: -0.025em;
}

.topnav-status {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.71rem; color: #10B981; font-weight: 600;
}

.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 8px rgba(16,185,129,0.60);
    animation: livepulse 3s ease-in-out infinite;
}

@keyframes livepulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.55; transform:scale(0.78); }
}

/* Main Container */
.support-container {
    padding-top: 80px;
    padding-bottom: 60px;
    min-height: 100vh;
}

.support-content {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
}

.widgets-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 32px;
    margin-top: 40px;
}

@media (max-width: 900px) {
    .widgets-grid {
        grid-template-columns: 1fr;
    }
}

/* Widget Container */
.widget-container {
    background: rgba(17, 24, 39, 0.55);
    border: 1px solid rgba(99, 102, 241, 0.22);
    border-radius: 16px;
    padding: 28px;
    backdrop-filter: blur(16px);
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.25);
}

.widget-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
}

.widget-icon {
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.3);
}

.widget-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #E5E7EB;
}

/* Chat Widget */
.chat-messages {
    background: rgba(13, 17, 23, 0.6);
    border-radius: 12px;
    padding: 16px;
    height: 400px;
    overflow-y: auto;
    margin-bottom: 16px;
    border: 1px solid rgba(99, 102, 241, 0.12);
}

.message {
    margin-bottom: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
    line-height: 1.5;
}

.message.user {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(139, 92, 246, 0.15) 100%);
    color: #C4B5FD;
    margin-left: 24px;
    border-left: 2px solid #6366F1;
}

.message.assistant {
    background: rgba(99, 102, 241, 0.12);
    color: #E5E7EB;
    margin-right: 24px;
    border-left: 2px solid #22D3EE;
}

.chat-input-container {
    display: flex;
    gap: 8px;
}

.chat-input-container input {
    flex: 1;
    padding: 10px 14px;
    border-radius: 8px;
    border: 1px solid rgba(99, 102, 241, 0.22);
    background: rgba(17, 24, 39, 0.8);
    color: #E5E7EB;
    font-size: 0.9rem;
}

.chat-input-container input::placeholder {
    color: #6B7280;
}

.chat-input-container button {
    padding: 10px 18px;
    border-radius: 8px;
    background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
    color: #fff;
    border: none;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.9rem;
}

.chat-input-container button:hover {
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.4);
}

/* Voice Widget */
.voice-display {
    background: rgba(13, 17, 23, 0.6);
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    border: 1px solid rgba(99, 102, 241, 0.12);
    margin-bottom: 20px;
}

.voice-icon-large {
    width: 80px;
    height: 80px;
    border-radius: 20px;
    background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.5rem;
    margin: 0 auto 16px;
    box-shadow: 0 0 32px rgba(16, 185, 129, 0.3);
}

.voice-status {
    font-size: 0.9rem;
    color: #94A3B8;
    margin-bottom: 16px;
}

.voice-controls {
    display: flex;
    gap: 12px;
    justify-content: center;
}

.voice-btn {
    padding: 12px 24px;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.3s ease;
}

.voice-btn.primary {
    background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
    color: #fff;
}

.voice-btn.primary:hover {
    box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
}

.voice-btn.secondary {
    background: rgba(99, 102, 241, 0.12);
    color: #E5E7EB;
    border: 1px solid rgba(99, 102, 241, 0.22);
}

.voice-btn.secondary:hover {
    background: rgba(99, 102, 241, 0.22);
}

/* Settings Panel */
.settings-panel {
    background: rgba(17, 24, 39, 0.55);
    border: 1px solid rgba(99, 102, 241, 0.22);
    border-radius: 16px;
    padding: 20px;
    margin-top: 32px;
}

.settings-title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #C4B5FD;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 16px;
}

.setting-item {
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(99, 102, 241, 0.12);
}

.setting-item:last-child {
    border-bottom: none;
}

.setting-label {
    font-size: 0.85rem;
    color: #E5E7EB;
    margin-bottom: 6px;
    display: block;
}

.setting-value {
    font-size: 0.8rem;
    color: #94A3B8;
    font-family: 'Monaco', monospace;
}

</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  TOP NAVIGATION
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="topnav">
    <div class="topnav-brand">
        <div class="dot">💬</div>
        <span class="name">Convin Support</span>
    </div>
    <div class="topnav-status">
        <div class="live-dot"></div>
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

if "voice_call_active" not in st.session_state:
    st.session_state.voice_call_active = False

if "voice_call_duration" not in st.session_state:
    st.session_state.voice_call_duration = 0

# ══════════════════════════════════════════════════════════════════
#  DATABASE FUNCTIONS
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_db_connection():
    """Connect to Supabase/PostgreSQL"""
    try:
        db_url = st.secrets.get("DATABASE_URL")
        if not db_url:
            return None
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def save_chat_message(user_id: str, role: str, message: str, session_id: str):
    """Save chat message to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO support_chats (session_id, user_id, role, message, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (session_id, user_id, role, message, datetime.now()))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Failed to save message: {e}")
        return False
    finally:
        conn.close()

def save_voice_call(user_id: str, session_id: str, duration: int, status: str):
    """Save voice call record to database"""
    conn = get_db_connection()
    if not conn:
        return False

    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO voice_calls (session_id, user_id, duration, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (session_id, user_id, duration, status, datetime.now()))
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        st.error(f"Failed to save voice call: {e}")
        return False
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════
#  API FUNCTIONS
# ══════════════════════════════════════════════════════════════════
def get_chat_response(user_message: str) -> str:
    """Get response from Claude via Anthropic API"""
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY")
        if not api_key:
            return "API key not configured"

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=500,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        return response.content[0].text
    except Exception as e:
        return f"Error: {str(e)}"

def initiate_voice_call(phone_number: str, voice_agent_api_key: str) -> dict:
    """Initiate voice call with Convin Voice Agent"""
    try:
        # This would call your Convin Voice Agent API
        # For now, returning a mock response
        return {
            "status": "initiated",
            "call_id": str(uuid.uuid4()),
            "agent": "Convin Voice Agent",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ══════════════════════════════════════════════════════════════════
#  MAIN CONTENT
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="support-container"><div class="support-content">', unsafe_allow_html=True)

# Title
st.markdown("""
<div style="text-align: center; margin-bottom: 32px; margin-top: 20px;">
    <h1 style="color: #E5E7EB; font-size: 2.2rem; margin-bottom: 8px;">
        Convin Support
    </h1>
    <p style="color: #94A3B8; font-size: 1rem;">
        Connect via chat or voice — instant support available
    </p>
</div>
""", unsafe_allow_html=True)

# Widgets Grid
st.markdown('<div class="widgets-grid">', unsafe_allow_html=True)

# ── CHAT WIDGET ──
st.markdown("""
<div class="widget-container">
    <div class="widget-header">
        <div class="widget-icon">💬</div>
        <div class="widget-title">Chat Support</div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="chat-messages" id="chat-messages">', unsafe_allow_html=True)

    # Display chat history
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="message user">
                    <strong>You:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="message assistant">
                    <strong>Support:</strong> {msg["content"]}
                </div>
                """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Chat input
    user_input = st.text_input(
        "Your message",
        placeholder="Type your question...",
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
        response = get_chat_response(user_input)
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response
        })

        # Save to database
        save_chat_message("user", "user", user_input, st.session_state.session_id)
        save_chat_message("support", "assistant", response, st.session_state.session_id)

        st.rerun()

# ── VOICE WIDGET ──
with col2:
    st.markdown("""
    <div class="widget-container">
        <div class="widget-header">
            <div class="widget-icon" style="background: linear-gradient(135deg, #10B981 0%, #34D399 100%); box-shadow: 0 0 16px rgba(16, 185, 129, 0.3);">📞</div>
            <div class="widget-title">Voice Call</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="voice-display">
        <div class="voice-icon-large">📞</div>
        <div class="voice-status">
            <strong>Convin Voice Agent</strong><br>
            Premium voice support available
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_phone, col_key = st.columns([1, 1])

    with col_phone:
        phone_number = st.text_input(
            "Phone Number",
            placeholder="+1 (555) 000-0000",
            key="phone_input"
        )

    with col_key:
        voice_api_key = st.text_input(
            "Voice Agent API Key",
            placeholder="Enter your API key",
            type="password",
            key="voice_key_input"
        )

    col_start, col_end = st.columns([1, 1])

    with col_start:
        if st.button("Start Call", key="start_call", use_container_width=True):
            if phone_number and voice_api_key:
                st.session_state.voice_call_active = True
                call_result = initiate_voice_call(phone_number, voice_api_key)

                if call_result["status"] == "initiated":
                    st.success(f"Call initiated! Call ID: {call_result['call_id']}")
                    save_voice_call("user", st.session_state.session_id, 0, "initiated")
                else:
                    st.error("Failed to initiate call")
            else:
                st.warning("Please enter phone number and API key")

    with col_end:
        if st.button("End Call", key="end_call", use_container_width=True, disabled=not st.session_state.voice_call_active):
            st.session_state.voice_call_active = False
            save_voice_call("user", st.session_state.session_id, st.session_state.voice_call_duration, "completed")
            st.info("Call ended")

st.markdown('</div>', unsafe_allow_html=True)

# ── SETTINGS PANEL ──
st.markdown("""
<div class="settings-panel">
    <div class="settings-title">Session Info</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="setting-item">
        <label class="setting-label">Session ID</label>
        <div class="setting-value">{st.session_state.session_id[:8]}...</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="setting-item">
        <label class="setting-label">Messages</label>
        <div class="setting-value">{len(st.session_state.chat_messages)}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="setting-item">
        <label class="setting-label">Status</label>
        <div class="setting-value" style="color: #10B981;">Active</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div style="text-align: center; padding: 40px 24px 24px; color: #6B7280; font-size: 0.85rem; border-top: 1px solid rgba(99, 102, 241, 0.12); margin-top: 60px;">
    <p>© 2026 Convin Support. All rights reserved. | Powered by Claude AI</p>
</div>
""", unsafe_allow_html=True)
