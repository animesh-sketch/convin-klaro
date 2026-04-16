"""
Convin Klaro
AI-powered knowledge & support intelligence platform
"""

import streamlit as st
import json, re, os, base64, zipfile, io
from datetime import datetime
from urllib.parse import urljoin, urlparse
import anthropic

def _b64_img(path):
    """Return base64 data-URI for an image file, or '' if not found."""
    try:
        with open(path, "rb") as f:
            ext = path.rsplit(".", 1)[-1].lower()
            mime = {"png":"image/png","jpg":"image/jpeg","jpeg":"image/jpeg",
                    "svg":"image/svg+xml","webp":"image/webp"}.get(ext,"image/png")
            return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"
    except Exception:
        return ""

_LOGO_URI = _b64_img(os.path.join(os.path.dirname(os.path.abspath(__file__)), "convin_logo.png"))

# ══════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════
APP_DIR = os.path.dirname(os.path.abspath(__file__))
KB_FILE = os.path.join(APP_DIR, "kb_store.json")
KB_KEYS = ("kb_documents", "kb_links", "kb_whatsapp", "kb_crawled", "kb_faqs")
MAX_CTX  = 580_000   # chars — safely under Claude's 200k-token window

st.set_page_config(
    page_title="Convin Klaro",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════════
#  GLOBAL STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Reset Streamlit chrome ── */
#MainMenu, footer, header,
[data-testid="stSidebar"],
[data-testid="collapsedControl"]          { display: none !important; }
.stDeployButton                            { display: none !important; }
[data-testid="stToolbar"]                  { display: none !important; }

/*
 * ═══════════════════════════════════════════════════════════
 *  CONVIN KLARO — Unified Design System
 * ───────────────────────────────────────────────────────────
 *  BG Base    : #060710   deepest layer
 *  Surface-1  : #0D0E1C   cards, nav
 *  Surface-2  : #13142A   elevated / expander header
 *  Surface-3  : #191A34   answer blocks
 *  Primary    : #7C3AED   single violet accent
 *  Pri-light  : #A78BFA   text accents, bold
 *  Pri-glow   : rgba(124,58,237,0.15)
 *  Text-1     : #EEF0FA   headings, content
 *  Text-2     : #8D90AA   secondary labels
 *  Text-3     : #454666   muted / disabled
 *  Border     : rgba(255,255,255,0.07)   normal
 *  Border-acc : rgba(124,58,237,0.30)    accent
 *  Green      : #10B981   WhatsApp / live
 *  Green-bg   : rgba(16,185,129,0.10)
 * ═══════════════════════════════════════════════════════════
 */

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    -webkit-font-smoothing: antialiased;
}
.main {
    background: #060710;
    background-image:
        radial-gradient(ellipse 90% 55% at 50% -5%, rgba(124,58,237,0.13) 0%, transparent 55%),
        radial-gradient(ellipse 50% 35% at 90% 85%, rgba(99,102,241,0.07) 0%, transparent 55%);
}
.main .block-container { padding: 0 !important; max-width: 100% !important; }

/* Subtle animated grid */
[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background-image: radial-gradient(rgba(124,58,237,0.055) 1px, transparent 1px);
    background-size: 38px 38px;
    pointer-events: none; z-index: 0;
    animation: gridshift 28s linear infinite;
}
@keyframes gridshift {
    0%   { background-position: 0 0; }
    100% { background-position: 38px 38px; }
}

/* ══ TOP NAV ══════════════════════════════════════════════ */
.topnav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 999;
    height: 60px;
    background: rgba(6,7,16,0.90);
    backdrop-filter: blur(24px);
    border-bottom: 1px solid rgba(124,58,237,0.18);
    display: flex; align-items: center;
    padding: 0 36px;
    justify-content: space-between;
}
.topnav-brand { display: flex; align-items: center; gap: 10px; }
.topnav-logo { height: 28px; width: auto; object-fit: contain; }
.topnav-brand .dot {
    width: 32px; height: 32px; border-radius: 9px;
    background: linear-gradient(135deg, #7C3AED 0%, #6366F1 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.9rem; color: #fff; font-weight: 800;
    box-shadow: 0 0 18px rgba(124,58,237,0.5);
}
.topnav-brand .name {
    font-size: 0.95rem; font-weight: 700; color: #EEF0FA;
    letter-spacing: -0.02em;
}
.topnav-brand .badge {
    font-size: 0.57rem; font-weight: 700; letter-spacing: 0.12em;
    background: rgba(124,58,237,0.14);
    color: #A78BFA;
    border: 1px solid rgba(124,58,237,0.30);
    padding: 2px 9px; border-radius: 20px;
    text-transform: uppercase;
}
.topnav-right { display: flex; align-items: center; gap: 8px; }
.topnav-status {
    display: flex; align-items: center; gap: 6px;
    font-size: 0.71rem; color: #454666; font-weight: 500;
}
.live-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 7px rgba(16,185,129,0.65);
    animation: livepulse 2.8s ease-in-out infinite;
}
@keyframes livepulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:0.65; transform:scale(0.82); }
}

/* ══ CHAT PAGE ════════════════════════════════════════════ */
.chat-page { min-height:100vh; padding-top:60px; }
.chat-feed { max-width:760px; width:100%; margin:0 auto; padding:40px 24px 170px; }

/* Welcome */
.welcome-card { text-align:center; padding:76px 24px 48px; }
.welcome-icon {
    width: 70px; height: 70px; border-radius: 22px;
    background: linear-gradient(135deg, #7C3AED 0%, #5B21B6 100%);
    margin: 0 auto 22px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.9rem;
    box-shadow: 0 0 44px rgba(124,58,237,0.38), 0 8px 28px rgba(0,0,0,0.45);
    animation: float 4.2s ease-in-out infinite;
}
@keyframes float {
    0%,100% { transform:translateY(0); }
    50%      { transform:translateY(-7px); }
}
.welcome-eyebrow {
    display: inline-block;
    font-size: 0.64rem; font-weight: 700; letter-spacing: 0.13em;
    text-transform: uppercase; color: #7C3AED;
    background: rgba(124,58,237,0.10);
    border: 1px solid rgba(124,58,237,0.28);
    padding: 4px 13px; border-radius: 20px;
    margin-bottom: 16px;
}
.welcome-title {
    font-size: 1.7rem; font-weight: 800;
    color: #EEF0FA; letter-spacing: -0.03em;
    line-height: 1.22; margin-bottom: 10px;
}
.welcome-title span {
    background: linear-gradient(90deg, #A78BFA, #7C3AED);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.welcome-sub { font-size: 0.88rem; color: #5A5C78; line-height: 1.68; }

/* Messages */
.msg-group { margin-bottom: 26px; animation: fadeUp 0.22s ease; }
@keyframes fadeUp {
    from { opacity:0; transform:translateY(10px); }
    to   { opacity:1; transform:translateY(0); }
}
.msg-user-row { display:flex; justify-content:flex-end; margin-bottom:4px; }
.msg-user-bubble {
    background: linear-gradient(135deg, #7C3AED, #5B21B6);
    color: #F5F3FF;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    max-width: 68%;
    font-size: 0.875rem; line-height: 1.62;
    box-shadow: 0 4px 22px rgba(124,58,237,0.32);
}
.msg-ai-row { display:flex; align-items:flex-start; gap:12px; }
.msg-ai-avatar {
    position: relative;
    width: 32px; height: 32px; border-radius: 10px;
    background: linear-gradient(135deg, #7C3AED, #5B21B6);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; color: #fff; font-weight: 800;
    flex-shrink: 0; margin-top: 2px;
    box-shadow: 0 0 14px rgba(124,58,237,0.35);
}
.msg-ai-avatar::before {
    content: '';
    position: absolute; top: -2px; left: -2px;
    width: 36px; height: 36px; border-radius: 12px;
    border: 1.5px solid rgba(124,58,237,0.30);
    animation: avatarring 3s ease-out infinite;
}
@keyframes avatarring {
    0%   { opacity:1; transform:scale(1); }
    100% { opacity:0; transform:scale(1.55); }
}
.msg-ai-bubble {
    background: #0D0E1C;
    color: #D6D8F0;
    padding: 14px 18px;
    border-radius: 4px 18px 18px 18px;
    max-width: 72%;
    font-size: 0.875rem; line-height: 1.75;
    border: 1px solid rgba(124,58,237,0.18);
}
.msg-ai-bubble b, .msg-ai-bubble strong { color: #A78BFA; }
.msg-ai-bubble ol, .msg-ai-bubble ul { padding-left: 18px; margin: 8px 0; }
.msg-ai-bubble li { margin-bottom: 5px; color: #C2C4DE; }
.msg-ai-bubble blockquote {
    border-left: 3px solid #10B981;
    background: rgba(16,185,129,0.08);
    border-radius: 0 8px 8px 0;
    padding: 6px 12px; margin: 10px 0 4px;
    font-size: 0.82rem; color: #34D399;
}
.msg-ts { font-size:0.6rem; color:#30314C; margin-top:4px; text-align:right; }
.msg-ts-left { text-align:left; margin-left:44px; }
.sources-bar { display:flex; align-items:center; gap:5px; margin-top:7px; margin-left:44px; flex-wrap:wrap; }
.source-tag {
    font-size: 0.62rem; font-weight: 500; color: #454666;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    padding: 2px 8px; border-radius: 10px;
}

/* Input bar */
.input-bar-wrap {
    position:fixed; bottom:0; left:0; right:0; z-index:998;
    background: rgba(6,7,16,0.94);
    backdrop-filter: blur(22px);
    border-top: 1px solid rgba(124,58,237,0.15);
    padding: 13px 0 18px;
}
.input-bar-inner { max-width:760px; margin:0 auto; padding:0 24px; display:flex; align-items:center; gap:10px; }
.input-bar-inner .stTextInput > div > div {
    background: #0D0E1C !important;
    border: 1px solid rgba(124,58,237,0.22) !important;
    border-radius: 14px !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    color: #EEF0FA !important;
}
.input-bar-inner .stTextInput > div > div:focus-within {
    border-color: rgba(124,58,237,0.65) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.13) !important;
}
.input-bar-inner .stTextInput input {
    font-size:0.9rem !important; color:#EEF0FA !important;
    background: transparent !important;
}
.input-bar-inner .stTextInput input::placeholder { color:#30314C !important; }

/* ══ KB STATS CHIPS ════════════════════════════════════ */
.kb-stats-row { display:flex; gap:10px; justify-content:center; flex-wrap:wrap; margin-top:26px; }
.kb-stat-chip {
    display: flex; align-items: center; gap: 7px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 28px; padding: 7px 16px;
    font-size: 0.78rem; color: #5A5C78;
    animation: popIn 0.4s ease forwards; opacity: 0;
}
.kb-stat-chip:nth-child(1) { animation-delay: 0.1s; }
.kb-stat-chip:nth-child(2) { animation-delay: 0.2s; }
.kb-stat-chip:nth-child(3) { animation-delay: 0.3s; }
@keyframes popIn {
    from { opacity:0; transform:translateY(8px) scale(0.95); }
    to   { opacity:1; transform:translateY(0) scale(1); }
}
.kb-stat-chip.active {
    border-color: rgba(124,58,237,0.32);
    background: rgba(124,58,237,0.09);
    color: #8D90AA;
}
.kb-stat-chip.wa.active {
    border-color: rgba(16,185,129,0.32);
    background: rgba(16,185,129,0.07);
}
.kb-stat-chip .num {
    font-weight: 800; font-size: 0.88rem;
    background: linear-gradient(135deg, #A78BFA, #7C3AED);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.kb-stat-chip.wa .num {
    background: linear-gradient(135deg, #34D399, #10B981);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.no-kb-hint {
    margin-top: 20px; font-size: 0.75rem; color: #30314C;
    background: rgba(255,255,255,0.025);
    border: 1px dashed rgba(255,255,255,0.08);
    border-radius: 20px; padding: 8px 20px; display: inline-block;
}
.ready-badge {
    display: inline-flex; align-items: center; gap: 6px;
    margin-top: 16px;
    font-size: 0.64rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #10B981;
    background: rgba(16,185,129,0.09);
    border: 1px solid rgba(16,185,129,0.25);
    padding: 4px 14px; border-radius: 20px;
    animation: readypop 0.6s 0.5s ease forwards; opacity: 0;
}
@keyframes readypop {
    from { opacity:0; transform:scale(0.9); }
    to   { opacity:1; transform:scale(1); }
}

/* ══ SUGGESTION CHIPS ══════════════════════════════════ */
[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"] {
    border-radius: 24px !important;
    padding: 8px 14px !important;
    font-size: 0.79rem !important;
    background: rgba(13,14,28,0.8) !important;
    border: 1px solid rgba(124,58,237,0.18) !important;
    color: #6B6D88 !important;
    white-space: nowrap !important;
    transition: all 0.2s !important;
}
[data-testid="stHorizontalBlock"] .stButton > button[kind="secondary"]:hover {
    border-color: rgba(124,58,237,0.50) !important;
    color: #A78BFA !important;
    background: rgba(124,58,237,0.10) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.18) !important;
}

/* ══ SETTINGS / FAQ PAGES ════════════════════════════ */
.settings-page { padding-top:60px; min-height:100vh; }
.settings-inner { max-width:920px; margin:0 auto; padding:40px 32px; }
.settings-title { font-size:1.3rem; font-weight:800; color:#EEF0FA; letter-spacing:-0.025em; margin-bottom:4px; }
.settings-sub   { font-size:0.82rem; color:#454666; margin-bottom:28px; }
.file-row {
    display:flex; align-items:center; gap:10px;
    padding:10px 14px; border-radius:10px;
    background: #0D0E1C;
    border: 1px solid rgba(124,58,237,0.14);
    margin-bottom:6px; transition: border-color 0.18s;
}
.file-row:hover { border-color: rgba(124,58,237,0.32); }
.file-row-icon { font-size:1rem; flex-shrink:0; }
.file-row-name { font-size:0.82rem; font-weight:500; color:#BCC0DC; flex:1; }
.file-row-meta { font-size:0.69rem; color:#454666; }

/* Upload zone */
div[data-testid="stFileUploader"] {
    background: rgba(124,58,237,0.04) !important;
    border: 1.5px dashed rgba(124,58,237,0.32) !important;
    border-radius: 12px !important;
}

/* Buttons */
.stButton > button {
    border-radius:10px !important; font-weight:600 !important;
    font-size:0.82rem !important; transition:all 0.18s !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #5B21B6) !important;
    color:#fff !important; border:none !important;
    box-shadow: 0 4px 18px rgba(124,58,237,0.38) !important;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #8B5CF6, #6D28D9) !important;
    box-shadow: 0 6px 26px rgba(124,58,237,0.52) !important;
    transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"] {
    background: rgba(13,14,28,0.8) !important;
    color: #8D90AA !important;
    border: 1px solid rgba(124,58,237,0.18) !important;
}
.stButton > button[kind="secondary"]:hover {
    border-color: rgba(124,58,237,0.42) !important;
    color: #A78BFA !important;
    background: rgba(124,58,237,0.08) !important;
}

/* Inputs */
.stTextInput > div > div {
    background: #0D0E1C !important;
    border: 1px solid rgba(124,58,237,0.20) !important;
    border-radius: 10px !important; color: #EEF0FA !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div:focus-within {
    border-color: rgba(124,58,237,0.60) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.12) !important;
}
.stTextInput input { color:#EEF0FA !important; background:transparent !important; }
.stTextInput input::placeholder { color:#30314C !important; }
.stTextInput label { color:#8D90AA !important; font-size:0.82rem !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0D0E1C; border-radius:10px; padding:4px; gap:2px;
    border: 1px solid rgba(124,58,237,0.16);
}
.stTabs [data-baseweb="tab"] {
    border-radius:8px !important; font-size:0.8rem !important;
    font-weight:500 !important; padding:6px 14px !important;
    color: #454666 !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(124,58,237,0.16) !important;
    color: #A78BFA !important;
    box-shadow: 0 0 0 1px rgba(124,58,237,0.32) !important;
}

/* Toggle / checkbox */
.stCheckbox label { font-size:0.85rem !important; color:#BCC0DC !important; font-weight:500 !important; }

/* Slider */
.stSlider [data-baseweb="slider"] div[role="slider"] {
    background: #7C3AED !important;
    box-shadow: 0 0 8px rgba(124,58,237,0.55) !important;
}

/* Divider */
hr { border:none; border-top:1px solid rgba(124,58,237,0.12) !important; margin:20px 0 !important; }

/* ── Expanders — unified, single definition ──────────────── */
/* Streamlit legacy selectors */
.streamlit-expanderHeader {
    background: #13142A !important;
    border: 1px solid rgba(124,58,237,0.30) !important;
    border-radius: 10px !important;
    color: #D4D7F2 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    padding: 12px 16px !important;
}
.streamlit-expanderHeader:hover {
    background: #191A34 !important;
    color: #EEF0FA !important;
}
.streamlit-expanderContent {
    background: #0D0E1C !important;
    border: 1px solid rgba(124,58,237,0.22) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
}
/* Streamlit 1.30+ data-testid selectors */
[data-testid="stExpander"] {
    border: 1px solid rgba(124,58,237,0.28) !important;
    border-radius: 10px !important;
    background: #13142A !important;
    margin-bottom: 8px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
[data-testid="stExpander"]:hover {
    border-color: rgba(124,58,237,0.50) !important;
    box-shadow: 0 4px 20px rgba(124,58,237,0.10) !important;
}
[data-testid="stExpander"] summary {
    background: #13142A !important;
    color: #D4D7F2 !important;
    font-size: 0.88rem !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    padding: 13px 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #191A34 !important;
    color: #EEF0FA !important;
}
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
    color: #D4D7F2 !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] > div:last-child {
    background: #0A0B18 !important;
    border-top: 1px solid rgba(124,58,237,0.20) !important;
    padding: 0 !important;
}
[data-testid="stExpander"] > div:last-child *,
[data-testid="stExpander"] > div:last-child p,
[data-testid="stExpander"] > div:last-child span,
[data-testid="stExpander"] > div:last-child li,
[data-testid="stExpander"] > div:last-child div {
    color: #EEF0FA !important;
}
[data-testid="stExpander"] > div:last-child strong,
[data-testid="stExpander"] > div:last-child b {
    color: #A78BFA !important;
}

/* Progress */
.stProgress > div > div {
    background: linear-gradient(90deg, #7C3AED, #5B21B6) !important;
    border-radius: 4px !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: #0D0E1C;
    border: 1px solid rgba(124,58,237,0.16);
    border-radius: 12px; padding: 14px 18px;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #EEF0FA !important; font-weight:800 !important;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    color: #454666 !important; font-size: 0.75rem !important;
}

/* Alert boxes */
.stAlert { border-radius:10px !important; border:none !important; }

/* Scrollbar */
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background: rgba(124,58,237,0.22); border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.42); }

/* ══ FAQ / ANSWER STUDIO PAGE ═══════════════════════════ */
.faq-hero {
    background: linear-gradient(135deg, #0D0E1C 0%, #13142A 55%, #191A34 100%);
    border: 1px solid rgba(124,58,237,0.28);
    border-radius: 18px; padding: 28px 32px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 0 60px rgba(124,58,237,0.12), inset 0 1px 0 rgba(255,255,255,0.04);
    position: relative; overflow: hidden;
}
.faq-hero::before {
    content:''; position:absolute; top:-60px; right:-60px;
    width:220px; height:220px; border-radius:50%;
    background: radial-gradient(circle, rgba(124,58,237,0.14) 0%, transparent 70%);
}
.faq-hero::after {
    content:''; position:absolute; bottom:-40px; left:20%;
    width:160px; height:160px; border-radius:50%;
    background: radial-gradient(circle, rgba(99,102,241,0.09) 0%, transparent 70%);
}
.faq-hero-left h2 {
    color: #EEF0FA !important; font-size:1.25rem; font-weight:800;
    margin:0; letter-spacing:-0.02em;
}
.faq-hero-left p { color: #6B6D88 !important; font-size:0.78rem; margin:6px 0 0; }
.faq-stat-row { display:flex; gap:12px; z-index:1; }
.faq-stat-box {
    background: rgba(124,58,237,0.08);
    border: 1px solid rgba(124,58,237,0.22);
    border-radius: 12px; padding: 10px 22px; text-align: center;
}
.faq-stat-box .n {
    font-size:1.45rem; font-weight:800;
    background: linear-gradient(135deg, #EEF0FA, #A78BFA);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.faq-stat-box .l {
    font-size:0.6rem; color: #454666 !important;
    text-transform:uppercase; letter-spacing:0.09em;
}

.cat-label {
    display: inline-flex; align-items: center; gap: 6px;
    background: linear-gradient(135deg, rgba(124,58,237,0.22), rgba(99,102,241,0.22));
    border: 1px solid rgba(124,58,237,0.40);
    color: #C4B5FD !important; padding: 6px 16px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 800; letter-spacing: 0.06em;
    margin: 24px 0 12px;
    box-shadow: 0 0 14px rgba(124,58,237,0.14);
}

.no-faq {
    text-align:center; padding:70px 24px;
    background: #0D0E1C;
    border-radius:18px;
    border: 1px solid rgba(124,58,237,0.14);
}
.no-faq-icon { font-size:3rem; margin-bottom:14px; }
.no-faq h3 { font-size:1rem; color:#8D90AA; font-weight:600; margin-bottom:6px; }
.no-faq p  { font-size:0.82rem; color:#454666; }

/* Answer blocks inside expanders */
.faq-answer-wrap {
    padding: 16px 18px 18px;
    background: #0A0B18;
}
.faq-answer-label {
    font-size: 0.68rem; font-weight: 800; letter-spacing: 0.12em;
    text-transform: uppercase; color: #7C3AED; margin-bottom: 10px;
}
.faq-answer-body {
    font-size: 0.92rem; color: #DDE0F5;
    line-height: 1.82;
    padding: 14px 18px 14px 16px;
    background: #13142A;
    border-left: 3px solid #7C3AED;
    border-radius: 0 10px 10px 0;
}
.faq-answer-body strong, .faq-answer-body b { color: #A78BFA; }
.faq-answer-body em { color: #8B8FA8; font-style: italic; }

/* WA source badges */
.faq-wa-badge {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(16,185,129,0.10);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 12px; padding: 2px 9px;
    font-size: 0.65rem; font-weight: 700; color: #34D399;
}
.faq-doc-badge {
    display: inline-flex; align-items: center; gap: 4px;
    background: rgba(124,58,237,0.10);
    border: 1px solid rgba(124,58,237,0.22);
    border-radius: 12px; padding: 2px 9px;
    font-size: 0.65rem; font-weight: 700; color: #A78BFA;
}

/* WA citation inline */
.wa-cite {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(16,185,129,0.09);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 10px; padding: 4px 12px;
    font-size: 0.72rem; font-weight: 600; color: #34D399;
    margin-top: 10px;
}

/* WA panel */
.wa-panel {
    background: rgba(16,185,129,0.05);
    border: 1px solid rgba(16,185,129,0.16);
    border-radius: 14px; padding: 16px 20px; margin-bottom: 18px;
}
.wa-panel-title {
    font-size: 0.77rem; font-weight: 700; color: #10B981;
    letter-spacing: 0.07em; text-transform: uppercase; margin-bottom: 12px;
}
.wa-cards-row { display:flex; flex-wrap:wrap; gap:12px; }
.wa-chat-card {
    background: #0D0E1C;
    border: 1px solid rgba(16,185,129,0.18);
    border-radius: 12px; padding: 12px 16px; min-width: 240px; flex: 1;
    transition: border-color 0.2s;
}
.wa-chat-card:hover { border-color: rgba(16,185,129,0.38); }
.wa-chat-top { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
.wa-chat-icon { font-size:1rem; }
.wa-chat-name { font-size:0.82rem; font-weight:600; color:#D4D7F2; flex:1; }
.wa-chat-badge {
    font-size: 0.65rem; font-weight: 700; color: #10B981;
    background: rgba(16,185,129,0.10);
    border: 1px solid rgba(16,185,129,0.22);
    border-radius: 10px; padding: 2px 8px;
}
.wa-chat-meta { font-size:0.72rem; color:#5A5C78; margin-bottom:4px; }
.wa-chat-qa   { font-size:0.7rem; color:#10B981; font-weight:600; margin-top:4px; }

/* Nav pill buttons */
div[data-testid="stHorizontalBlock"]:has(button[key="faq_nav_btn"]) .stButton > button,
div[data-testid="stHorizontalBlock"]:has(button[key="settings_btn"]) .stButton > button {
    border-radius: 20px !important;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  STORAGE  —  Streamlit-native JSON file (kb_store.json)
# ══════════════════════════════════════════════════════════════════
def load_kb():
    if st.session_state.get("_kb_loaded"):
        return
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            for k in KB_KEYS:
                st.session_state[k] = d.get(k, [])
            st.session_state["show_sources"] = d.get("show_sources", False)
        except Exception:
            pass
    st.session_state["_kb_loaded"] = True

def save_kb():
    data = {k: st.session_state.get(k, []) for k in KB_KEYS}
    data["show_sources"] = st.session_state.get("show_sources", False)
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def kb_stats():
    docs  = len(st.session_state.get("kb_documents", []))
    links = len(st.session_state.get("kb_links",     []))
    wa    = len(st.session_state.get("kb_whatsapp",  []))
    pages = len(st.session_state.get("kb_crawled",   []))
    return docs, links, wa, pages

def total_sources():
    return sum(kb_stats())


# ══════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════
_DEFAULTS = {
    "page":          "chat",
    "chat_history":  [],
    "_last_input":   "",
    "quick_q":       "",
    "show_sources":  False,
    "_kb_loaded":    False,
    "kb_faqs":       [],
    **{k: [] for k in KB_KEYS},
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

load_kb()


# ══════════════════════════════════════════════════════════════════
#  FILE PARSERS
# ══════════════════════════════════════════════════════════════════
def _ext(filename): return filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

def FILE_ICON(ext):
    return {
        "pdf":"📄","txt":"📝","md":"📝","docx":"📋","doc":"📋","odt":"📋",
        "xlsx":"📊","xls":"📊","xlsm":"📊","ods":"📊","csv":"📊",
        "pptx":"🖼️","ppt":"🖼️","odp":"🖼️",
        "html":"🌐","htm":"🌐","mhtml":"🌐","xhtml":"🌐",
        "json":"🗂️","jsonl":"🗂️","yaml":"🗂️","xml":"🗂️",
        "epub":"📚","rtf":"📄","eml":"📧","msg":"📧",
        "ipynb":"📓","py":"🐍","js":"📜","ts":"📜","sql":"🗄️",
        "sh":"⚙️","rb":"💎","go":"🐹","rs":"⚙️","java":"☕",
    }.get(ext, "📎")

def parse_file(f) -> str:
    import io
    name = f.name.lower(); raw = f.read(); ext = _ext(name)

    # ── Plain-text formats (direct decode) ───────────────────────
    PLAIN_TEXT = {
        "txt","md","markdown","rst","log","csv","tsv",
        "yaml","yml","toml","ini","cfg","env",
        "sh","bash","zsh","fish",
        "py","js","ts","jsx","tsx","mjs","cjs",
        "json","jsonl","ndjson",
        "sql","r","rb","php","java","cpp","c","h","hpp",
        "go","rs","swift","kt","cs","lua","tex","scala","pl",
        "xml","svg","rss","atom",
    }
    if ext in PLAIN_TEXT:
        return raw.decode("utf-8", errors="ignore")

    # ── HTML / HTM — strip tags, keep readable text ───────────────
    if ext in ("html","htm","mhtml","mht","xhtml"):
        try:
            from bs4 import BeautifulSoup as BS
            soup = BS(raw.decode("utf-8","ignore"), "html.parser")
            for tag in soup(["script","style","nav","footer","header",
                             "aside","noscript","meta","link"]):
                tag.decompose()
            title = soup.title.string.strip() if soup.title else ""
            text  = soup.get_text("\n", strip=True)
            return (f"[Title: {title}]\n\n" if title else "") + text
        except Exception as e:
            return raw.decode("utf-8","ignore")

    # ── PDF ───────────────────────────────────────────────────────
    if ext == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(io.BytesIO(raw)) as pdf:
                return "\n\n".join(p.extract_text() or "" for p in pdf.pages)
        except Exception:
            try:
                import PyPDF2
                r = PyPDF2.PdfReader(io.BytesIO(raw))
                return "\n\n".join(p.extract_text() or "" for p in r.pages)
            except Exception as e: return f"[PDF error: {e}]"

    # ── Word ──────────────────────────────────────────────────────
    if ext in ("docx","doc","odt"):
        try:
            import docx
            d = docx.Document(io.BytesIO(raw))
            parts = [p.text for p in d.paragraphs if p.text.strip()]
            for tbl in d.tables:
                for row in tbl.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
            return "\n".join(parts)
        except Exception as e: return f"[DOCX error: {e}]"

    # ── Excel ─────────────────────────────────────────────────────
    if ext in ("xlsx","xls","xlsm","ods"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
            parts = []
            for sn in wb.sheetnames:
                ws = wb[sn]; parts.append(f"=== Sheet: {sn} ===")
                for row in ws.iter_rows(values_only=True):
                    s = " | ".join(str(c) for c in row if c is not None)
                    if s.strip(): parts.append(s)
            return "\n".join(parts)
        except Exception as e: return f"[Excel error: {e}]"

    # ── PowerPoint ────────────────────────────────────────────────
    if ext in ("pptx","ppt","odp"):
        try:
            from pptx import Presentation
            prs = Presentation(io.BytesIO(raw)); parts = []
            for i,sl in enumerate(prs.slides,1):
                parts.append(f"=== Slide {i} ===")
                for sh in sl.shapes:
                    if hasattr(sh,"text") and sh.text.strip(): parts.append(sh.text)
            return "\n".join(parts)
        except Exception as e: return f"[PPTX error: {e}]"

    # ── RTF ───────────────────────────────────────────────────────
    if ext == "rtf":
        try:
            from striprtf.striprtf import rtf_to_text
            return rtf_to_text(raw.decode("utf-8","ignore"))
        except Exception as e: return f"[RTF error: {e}]"

    # ── EPUB ──────────────────────────────────────────────────────
    if ext == "epub":
        try:
            import ebooklib; from ebooklib import epub; from bs4 import BeautifulSoup as BS
            book = epub.read_epub(io.BytesIO(raw)); parts = []
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                soup = BS(item.get_content(),"html.parser")
                t = soup.get_text(" ",strip=True)
                if t: parts.append(t)
            return "\n\n".join(parts)
        except Exception as e: return f"[EPUB error: {e}]"

    # ── Email (.eml / .msg) ───────────────────────────────────────
    if ext in ("eml","msg"):
        try:
            import email
            msg = email.message_from_bytes(raw)
            parts = []
            for hdr in ("From","To","Subject","Date"):
                if msg.get(hdr): parts.append(f"{hdr}: {msg[hdr]}")
            parts.append("")
            for part in msg.walk():
                ct = part.get_content_type()
                if ct == "text/plain":
                    parts.append(part.get_payload(decode=True).decode("utf-8","ignore"))
                elif ct == "text/html":
                    try:
                        from bs4 import BeautifulSoup as BS
                        parts.append(BS(part.get_payload(decode=True),"html.parser").get_text("\n",strip=True))
                    except Exception:
                        pass
            return "\n".join(parts)
        except Exception as e: return f"[EML error: {e}]"

    # ── Notebook (.ipynb) ─────────────────────────────────────────
    if ext == "ipynb":
        try:
            nb = json.loads(raw.decode("utf-8","ignore"))
            parts = []
            for cell in nb.get("cells",[]):
                ct = cell.get("cell_type","")
                src = "".join(cell.get("source",[]))
                if ct == "markdown":
                    parts.append(src)
                elif ct == "code":
                    parts.append(f"```python\n{src}\n```")
                for out in cell.get("outputs",[]):
                    text = "".join(out.get("text",""))
                    if text: parts.append(text)
            return "\n\n".join(parts)
        except Exception as e: return f"[IPYNB error: {e}]"

    # ── Fallback: try raw text decode ─────────────────────────────
    for enc in ("utf-8","latin-1","cp1252"):
        try: return raw.decode(enc)
        except: continue
    return f"[Unsupported format: {f.name}]"


# ══════════════════════════════════════════════════════════════════
#  WEB HELPERS
# ══════════════════════════════════════════════════════════════════
def _http(url):
    import requests
    return requests.get(url, headers={"User-Agent":"Mozilla/5.0 (ConvinBot/1.0)"}, timeout=12)

def _scrape(soup, url):
    for t in soup(["script","style","nav","footer","header","aside","noscript"]):
        t.decompose()
    title = (soup.title.string.strip() if soup.title else url)[:120]
    text  = "\n".join(
        p.get_text(" ",strip=True)
        for p in soup.find_all(["p","h1","h2","h3","h4","li","td","blockquote"])
        if len(p.get_text(strip=True)) > 25
    )
    return title, text[:16000]

def fetch_url(url):
    try:
        from bs4 import BeautifulSoup
        r = _http(url); r.raise_for_status()
        return _scrape(BeautifulSoup(r.text,"html.parser"), url)
    except Exception as e:
        return url, f"[Error: {e}]"

_WA_SKIP = {
    "<Media omitted>", "This message was deleted", "image omitted",
    "video omitted", "audio omitted", "sticker omitted", "document omitted",
    "GIF omitted", "Contact card omitted", "Missed voice call",
    "Missed video call", "null", "",
}

# WhatsApp message patterns — iOS and Android, 12h and 24h
_WA_PATTERNS = [
    # iOS:     [DD/MM/YYYY, HH:MM:SS] Sender: Msg
    re.compile(r"^\[(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),\s*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\]\s+([^:]+):\s*(.*)"),
    # Android: DD/MM/YYYY, HH:MM - Sender: Msg
    re.compile(r"^(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AaPp][Mm])?)\s*[-–]\s*([^:]+):\s*(.*)"),
]

def _wa_match(line: str):
    """Try all WA patterns; return (date, time, sender, msg) or None."""
    for pat in _WA_PATTERNS:
        m = pat.match(line.strip())
        if m:
            return m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
    return None

def parse_wa(raw: str) -> str:
    """Parse a WhatsApp export preserving full [date time] Sender: message format."""
    lines_out = []
    for ln in raw.split("\n"):
        s = ln.strip()
        if not s:
            continue
        hit = _wa_match(s)
        if hit:
            date, time_, sender, msg = hit
            if not msg or msg in _WA_SKIP or any(sk.lower() in msg.lower() for sk in _WA_SKIP):
                continue
            lines_out.append(f"[{date} {time_}] {sender}: {msg}")
        elif lines_out:
            lines_out[-1] = lines_out[-1] + " " + s  # continuation
    return "\n".join(lines_out)

def parse_wa_meta(content: str) -> dict:
    """Extract chat metadata for the Answer Studio pre-analysis header."""
    messages = []
    for ln in content.split("\n"):
        hit = _wa_match(ln)
        if hit:
            date, time_, sender, msg = hit
            messages.append({"date": date, "time": time_, "sender": sender, "text": msg})

    if not messages:
        return {"valid": False, "total": 0, "participants": [], "date_range": ""}

    participants = list(dict.fromkeys(m["sender"] for m in messages))
    counts = {}
    for m in messages:
        counts[m["sender"]] = counts.get(m["sender"], 0) + 1

    return {
        "valid": True,
        "total": len(messages),
        "participants": participants,
        "msg_counts": counts,
        "first_date": messages[0]["date"],
        "last_date": messages[-1]["date"],
        "date_range": f"{messages[0]['date']} → {messages[-1]['date']}",
    }

def crawl_site(root, max_p, status_ph, prog_ph):
    try:
        import requests; from bs4 import BeautifulSoup
    except ImportError:
        return 0
    pr = urlparse(root); base = f"{pr.scheme}://{pr.netloc}"; host = pr.netloc
    SKIP = {".pdf",".png",".jpg",".jpeg",".gif",".svg",".zip",".exe",
            ".mp4",".mp3",".webp",".ico",".css",".js",".woff",".ttf"}
    def ok(h):
        p = urlparse(h)
        return (not p.netloc or p.netloc==host) and \
               not any(p.path.lower().endswith(e) for e in SKIP) and \
               p.scheme in ("http","https","")
    visited = set(); queue = [root]; done = 0
    existing = {p["url"] for p in st.session_state.kb_crawled}; new_pages = []
    while queue and done < max_p:
        url = queue.pop(0).split("#")[0].rstrip("/") or root
        if url in visited: continue
        visited.add(url)
        try:
            resp = _http(url)
            if "text/html" not in resp.headers.get("Content-Type",""): continue
            soup = BeautifulSoup(resp.text,"html.parser")
            for a in soup.find_all("a",href=True):
                h = urljoin(base,a["href"]).split("#")[0].rstrip("/")
                if ok(h) and h not in visited: queue.append(h)
            title, text = _scrape(soup, url)
            if not text.strip(): continue
            done += 1
            pg = {"url":url,"title":title,"content":text,
                  "added_at":datetime.now().isoformat(),"size":len(text)}
            if url not in existing:
                new_pages.append(pg); existing.add(url)
            prog_ph.progress(min(done/max_p,1.0))
            status_ph.caption(f"🕷️  {done}/{max_p} — {url[:60]}")
        except Exception: continue
    st.session_state.kb_crawled.extend(new_pages)
    prog_ph.empty(); status_ph.empty()
    return done


# ══════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE CONTEXT
# ══════════════════════════════════════════════════════════════════
def build_context():
    """Return (full_context_string, list_of_source_names)."""
    parts, names = [], []
    for d in st.session_state.kb_documents:
        parts.append(f"=== DOCUMENT: {d['name']} ===\n{d['content']}")
        names.append(d["name"])
    for l in st.session_state.kb_links:
        parts.append(f"=== WEBSITE: {l['title']} ===\n{l['content']}")
        names.append(l["title"])
    for w in st.session_state.kb_whatsapp:
        parts.append(f"=== WHATSAPP CHAT: {w['name']} ===\n{w['content']}")
        names.append(w["name"])
    for p in st.session_state.kb_crawled:
        parts.append(f"=== PAGE: {p['title']} ===\n{p['content']}")
        names.append(p["title"])
    ctx = "\n\n".join(parts)
    return ctx[:MAX_CTX], names


# ══════════════════════════════════════════════════════════════════
#  CLAUDE  —  full context, prompt caching
# ══════════════════════════════════════════════════════════════════
def get_client():
    key = st.secrets.get("ANTHROPIC_API_KEY", os.getenv("ANTHROPIC_API_KEY",""))
    if not key:
        raise ValueError("ANTHROPIC_API_KEY not configured.")
    return anthropic.Anthropic(api_key=key)

def ask_claude(query: str) -> tuple[str, list[str]]:
    ctx, names = build_context()
    if not ctx.strip():
        return (
            "I don't have any knowledge base loaded yet. "
            "Please ask your admin to add documents or resources.",
            [],
        )

    client = get_client()

    SYSTEM_INSTRUCTIONS = (
        "You are a professional Customer Support AI for Convin.\n\n"
        "Behavior:\n"
        "• Answer ONLY from the knowledge base provided — never fabricate facts.\n"
        "• Read the ENTIRE knowledge base before responding, including WhatsApp chats.\n"
        "• Structure every response:\n"
        "    1. Direct answer (1–2 sentences)\n"
        "    2. Steps or details (numbered list if 3+ steps, otherwise inline)\n"
        "    3. Brief explanation (only if it adds value)\n"
        "    4. Friendly closing line\n"
        "• Use **bold** for key terms, product names, and important values.\n"
        "• Keep answers concise — no filler words, no repetition.\n"
        "• If the answer is NOT in the knowledge base, respond with:\n"
        "  \"This might need further verification — let me connect you with "
        "the right person from our team.\"\n"
        "• For WhatsApp conversations: ALWAYS cite the source with this exact format:\n"
        "  > 💬 Chatted by [Sender Name] at [Time] on [Date]\n"
        "  Include the actual sender name, time, and date from the message metadata.\n"
        "• Do NOT say 'based on the document' or 'according to the file' for documents.\n"
        "• Do NOT reveal file names or document titles in answers.\n"
        "• WhatsApp references are valuable citations — always include them when used.\n"
    )

    system = [
        {"type": "text", "text": SYSTEM_INSTRUCTIONS},
        {"type": "text", "text": "KNOWLEDGE BASE:\n" + ctx,
         "cache_control": {"type": "ephemeral"}},
    ]

    history = [{"role": m["role"], "content": m["content"]}
               for m in st.session_state.chat_history[-10:]]
    history.append({"role": "user", "content": query})

    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=900,
        system=system,
        messages=history,
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return r.content[0].text, names


# ══════════════════════════════════════════════════════════════════
#  FAQ GENERATOR
# ══════════════════════════════════════════════════════════════════
def _faq_call(client, prompt: str) -> list[dict]:
    """Single Claude call → parsed FAQ list."""
    r = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=16000,
        messages=[{
            "role": "user",
            "content": [{"type": "text", "text": prompt,
                         "cache_control": {"type": "ephemeral"}}],
        }],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    raw = re.sub(r"^```[a-z]*\n?", "", r.content[0].text.strip())
    raw = re.sub(r"\n?```$", "", raw)
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        pairs = re.findall(
            r'"question"\s*:\s*"([^"]+)"[^}]*"answer"\s*:\s*"([^"]+)"', raw
        )
        return [{"category": "General", "question": q, "answer": a} for q, a in pairs]
    return [
        {
            "category": str(i.get("category", "General")),
            "question": str(i.get("question", i.get("q", ""))),
            "answer":   str(i.get("answer",   i.get("a", ""))),
        }
        for i in items if isinstance(i, dict) and i.get("question")
    ]


def generate_faqs(progress_cb=None) -> list[dict]:
    """Multi-pass FAQ generation — one full Claude call per source type.

    progress_cb(pct, label) is called after each pass so the UI can update.
    """
    client  = get_client()
    all_faqs: list[dict] = []

    BASE_RULES = (
        "Rules:\n"
        "• Only include facts present in the content — never invent.\n"
        "• Be EXHAUSTIVE: cover every topic, feature, process, policy, edge case, "
        "decision, question, issue, and fact — no matter how minor.\n"
        "• Each answer: 2–6 sentences or a short bullet list.\n"
        "• Group into specific, descriptive categories.\n"
        "• Return ONLY a raw JSON array (no markdown, no extra text):\n"
        '[\n  {"category":"Name","question":"Q?","answer":"A."},\n  ...\n]\n'
    )

    # ── Pass 1: Documents ─────────────────────────────────────────
    docs = st.session_state.get("kb_documents", [])
    if docs:
        ctx = "\n\n".join(
            f"=== DOCUMENT: {d['name']} ===\n{d['content']}" for d in docs
        )[:MAX_CTX]
        prompt = (
            "You are extracting the maximum possible FAQs from uploaded documents.\n"
            "Read every sentence. Extract every question a user could ever ask.\n\n"
            + BASE_RULES +
            "\nExtract the MAXIMUM number of Q&A pairs possible.\n\n"
            "DOCUMENTS:\n" + ctx
        )
        if progress_cb: progress_cb(0.15, f"📄 Processing {len(docs)} document(s)…")
        try:
            all_faqs.extend(_faq_call(client, prompt))
        except Exception:
            pass

    # ── Pass 2: Web links + crawled pages ────────────────────────
    web = st.session_state.get("kb_links", []) + st.session_state.get("kb_crawled", [])
    if web:
        ctx = "\n\n".join(
            f"=== PAGE: {p.get('title', p.get('url',''))} ===\n{p['content']}"
            for p in web
        )[:MAX_CTX]
        prompt = (
            f"You are extracting the maximum possible FAQs from {len(web)} web page(s).\n"
            "Read every sentence. Extract every question a user could ever ask.\n\n"
            + BASE_RULES +
            "\nExtract the MAXIMUM number of Q&A pairs possible.\n\n"
            "WEB PAGES:\n" + ctx
        )
        if progress_cb: progress_cb(0.45, f"🌐 Processing {len(web)} web page(s)…")
        try:
            all_faqs.extend(_faq_call(client, prompt))
        except Exception:
            pass

    # ── Pass 3 & 4: WhatsApp — two deep-extraction passes per chat ──
    wa_chats = st.session_state.get("kb_whatsapp", [])
    if wa_chats:
        total_wa = len(wa_chats)
        for wi, chat in enumerate(wa_chats):
            content = chat.get("content", "").strip()
            if not content:
                continue

            meta = parse_wa_meta(content)
            plist = ", ".join(meta["participants"]) if meta["valid"] else "unknown"
            drange = meta.get("date_range", "")
            total_msg = meta.get("total", "?")

            pct_a = 0.60 + (wi / total_wa) * 0.15
            pct_b = pct_a + 0.07

            CITE_RULE = (
                "CITATION RULE — every answer MUST end with one of:\n"
                "  • Single person: '💬 [Name] on [Date] at [Time]'\n"
                "  • Exchange: '💬 [Name1] asked, [Name2] replied on [Date]'\n"
                "  • Group: '💬 Discussed by [Name1], [Name2] on [Date]'\n"
                "Use the actual names, dates, and times from the messages.\n\n"
            )

            HEADER = (
                f"WhatsApp chat: {chat['name']}\n"
                f"Participants: {plist}\n"
                f"Date range: {drange}  |  Messages: {total_msg}\n\n"
                "Each line format: [DD/MM/YY HH:MM] Sender: Message\n\n"
            )

            # ── Sub-pass A: Direct Q&As + Decisions + Action items ──
            if progress_cb:
                progress_cb(pct_a, f"💬 Chat {wi+1}/{total_wa} — extracting Q&As, decisions, actions…")
            prompt_a = (
                "You are a knowledge analyst. Deeply read this WhatsApp conversation.\n\n"
                + HEADER
                + CITE_RULE
                + "EXTRACT THESE THREE TYPES (be exhaustive):\n\n"
                "TYPE 1 — QUESTIONS & ANSWERS\n"
                "Find every explicit question (ends with ?, starts with how/what/when/why/who/where/can/should/is/are/do/does/will/would) "
                "AND every implied question (topic raised that others responded to). "
                "Pair each with its answer from the conversation.\n"
                "→ Category: 'WhatsApp: Questions & Answers'\n\n"
                "TYPE 2 — DECISIONS & AGREEMENTS\n"
                "Find everything agreed upon, confirmed, resolved, or decided. "
                "Look for: 'agreed', 'decided', 'confirmed', 'let's go with', 'we'll', 'done', 'sorted', 'ok let's'.\n"
                "→ Category: 'WhatsApp: Decisions & Agreements'\n\n"
                "TYPE 3 — ACTION ITEMS & TASKS\n"
                "Find every task assigned, promise made, or next step defined. "
                "Look for: 'will do', 'I'll', 'you need to', 'please', 'can you', 'by [date]', 'follow up'.\n"
                "→ Category: 'WhatsApp: Action Items & Tasks'\n\n"
                "Return ONLY raw JSON array:\n"
                '[\n  {"category":"WhatsApp: Questions & Answers","question":"Q?","answer":"A. 💬 ..."},\n  ...\n]\n\n'
                "Be exhaustive — extract every single instance.\n\n"
                "CHAT:\n" + content[:MAX_CTX]
            )
            try:
                all_faqs.extend(_faq_call(client, prompt_a))
            except Exception:
                pass

            # ── Sub-pass B: Information + Problems + Context + Insights ──
            if progress_cb:
                progress_cb(pct_b, f"💬 Chat {wi+1}/{total_wa} — extracting knowledge, issues, insights…")
            prompt_b = (
                "You are a knowledge analyst. Deeply read this WhatsApp conversation.\n\n"
                + HEADER
                + CITE_RULE
                + "EXTRACT THESE FOUR TYPES (be exhaustive):\n\n"
                "TYPE 4 — INFORMATION & KNOWLEDGE SHARED\n"
                "Find every fact, figure, process, instruction, contact, link, or data point shared. "
                "Turn each into 'What is/How does/What was...?' format.\n"
                "→ Category: 'WhatsApp: Information & Knowledge'\n\n"
                "TYPE 5 — PROBLEMS & RESOLUTIONS\n"
                "Find every issue, complaint, bug, confusion, or blocker raised — and how it was resolved. "
                "If unresolved, note that.\n"
                "→ Category: 'WhatsApp: Issues & Resolutions'\n\n"
                "TYPE 6 — BUSINESS & PRODUCT INSIGHTS\n"
                "Find anything about clients, products, features, pricing, timelines, deals, or strategy.\n"
                "→ Category: 'WhatsApp: Business & Product Insights'\n\n"
                "TYPE 7 — CONTEXT & BACKGROUND\n"
                "Find any background context, history, or explanations given about the situation or topic.\n"
                "→ Category: 'WhatsApp: Context & Background'\n\n"
                "Return ONLY raw JSON array:\n"
                '[\n  {"category":"WhatsApp: Information & Knowledge","question":"Q?","answer":"A. 💬 ..."},\n  ...\n]\n\n'
                "Be exhaustive — extract every single piece of knowledge.\n\n"
                "CHAT:\n" + content[:MAX_CTX]
            )
            try:
                all_faqs.extend(_faq_call(client, prompt_b))
            except Exception:
                pass

    if progress_cb: progress_cb(0.95, "✨ Deduplicating and finalising…")

    # ── Deduplicate by question (case-insensitive) ────────────────
    seen: set[str] = set()
    deduped: list[dict] = []
    for f in all_faqs:
        key_q = f["question"].lower().strip()
        if key_q and key_q not in seen:
            seen.add(key_q)
            deduped.append(f)

    return deduped


# ══════════════════════════════════════════════════════════════════
#  SHARED TOP NAV
# ══════════════════════════════════════════════════════════════════
def render_topnav(show_settings_btn=True, show_back_btn=False):
    docs, links, wa, pages = kb_stats()
    total = docs + links + wa + pages
    status_label = f"{total} sources loaded" if total else "No knowledge base"

    # HTML-only portion (purely visual)
    logo_html = (
        f'<img src="{_LOGO_URI}" class="topnav-logo" alt="Convin">'
        if _LOGO_URI else
        '<div class="dot">K</div>'
    )
    st.markdown(f"""
    <div class="topnav">
      <div class="topnav-brand">
        {logo_html}
        <span class="name">Convin Klaro</span>
        <span class="badge">AI Support Intelligence</span>
      </div>
      <div class="topnav-right">
        <span class="topnav-status">
          <span class="live-dot"></span>
          {status_label}
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Streamlit buttons — functional nav row
    nav_spacer = st.container()
    with nav_spacer:
        c_l, c_faq, c_set = st.columns([7, 1, 1])
        if show_back_btn:
            with c_l:
                if st.button("← Back to Chat", key="back_btn", type="secondary"):
                    st.session_state.page = "chat"
                    st.rerun()
        if show_settings_btn:
            with c_faq:
                if st.button("✦ Answer Studio", key="faq_nav_btn", type="secondary",
                             use_container_width=True):
                    st.session_state.page = "faq"
                    st.rerun()
            with c_set:
                if st.button("⚙ Settings", key="settings_btn", type="secondary",
                             use_container_width=True):
                    st.session_state.page = "settings"
                    st.rerun()


# ══════════════════════════════════════════════════════════════════
#  CHAT PAGE
# ══════════════════════════════════════════════════════════════════
SUGGESTIONS = [
    "🤖  What is Convin AI?",
    "📊  How does call scoring work?",
    "🔗  What integrations are supported?",
    "⚡  How to set up Auto QA?",
    "💬  Any recent discussions or decisions?",
    "📤  How to export reports?",
]

def render_chat():
    render_topnav(show_settings_btn=True, show_back_btn=False)

    # ── Center column for chat
    _, main, _ = st.columns([1, 5, 1])
    with main:

        # ── Message feed
        if not st.session_state.chat_history:
            # Welcome screen — live KB stats
            docs, links, wa, pages = kb_stats()
            total = docs + links + wa + pages
            stat_chips = []
            if docs:
                stat_chips.append(f'<div class="kb-stat-chip active"><span class="num">{docs}</span><span>📄 Docs</span></div>')
            if links + pages:
                stat_chips.append(f'<div class="kb-stat-chip active"><span class="num">{links+pages}</span><span>🌐 Web pages</span></div>')
            if wa:
                stat_chips.append(f'<div class="kb-stat-chip active wa"><span class="num">{wa}</span><span>💬 WA chats</span></div>')

            if stat_chips:
                stats_html = '<div class="kb-stats-row">' + "".join(stat_chips) + '</div>'
                ready_badge = '<div class="ready-badge">✦ Knowledge base ready</div>'
            else:
                stats_html = '<div class="no-kb-hint">No sources loaded yet — add documents in ⚙ Settings</div>'
                ready_badge = ''

            st.markdown(f"""
            <div class="welcome-card">
              <div class="welcome-icon">✦</div>
              <div class="welcome-eyebrow">Convin Klaro</div>
              <div class="welcome-title">Ask anything. <span>Get instant answers.</span></div>
              <div class="welcome-sub">
                AI-powered knowledge &amp; support intelligence — searches all your docs, web pages &amp; chats.
              </div>
              {stats_html}
              {ready_badge}
            </div>
            """, unsafe_allow_html=True)

            # Suggestion chips — two rows of 3
            row1, row2 = SUGGESTIONS[:3], SUGGESTIONS[3:]
            scols1 = st.columns(3)
            for i, (col, q) in enumerate(zip(scols1, row1)):
                with col:
                    if st.button(q, key=f"sugg_{i}", use_container_width=True):
                        st.session_state.quick_q = q
                        st.rerun()
            scols2 = st.columns(3)
            for i, (col, q) in enumerate(zip(scols2, row2)):
                with col:
                    if st.button(q, key=f"sugg_{i+3}", use_container_width=True):
                        st.session_state.quick_q = q
                        st.rerun()
        else:
            # Render history
            for msg in st.session_state.chat_history:
                ts = msg.get("ts", "")
                content = msg["content"]

                if msg["role"] == "user":
                    safe = content.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("\n","<br>")
                    st.markdown(
                        f'<div class="msg-group">'
                        f'<div class="msg-user-row">'
                        f'<div class="msg-user-bubble">{safe}</div>'
                        f'</div>'
                        f'<div class="msg-ts">{ts}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    # Render assistant message via st.markdown for proper formatting
                    st.markdown(
                        '<div class="msg-group"><div class="msg-ai-row">'
                        '<div class="msg-ai-avatar">AI</div>'
                        '<div style="flex:1;max-width:72%">',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f'<div class="msg-ai-bubble">{content}</div>',
                        unsafe_allow_html=True,
                    )
                    # Sources (only if toggle is ON)
                    if st.session_state.get("show_sources") and msg.get("sources"):
                        tags = " ".join(
                            f'<span class="source-tag">{s[:30]}</span>'
                            for s in msg["sources"][:5]
                        )
                        st.markdown(
                            f'<div class="sources-bar">{tags}</div>',
                            unsafe_allow_html=True,
                        )
                    st.markdown(
                        f'<div class="msg-ts msg-ts-left">{ts}</div>'
                        '</div></div></div>',
                        unsafe_allow_html=True,
                    )

        # Scroll anchor
        st.markdown("<div id='chat-end'></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:130px'></div>", unsafe_allow_html=True)

    # ── Fixed input bar
    st.markdown('<div class="input-bar-wrap"><div class="input-bar-inner">', unsafe_allow_html=True)
    input_l, input_r = st.columns([9, 1])
    with input_l:
        user_input = st.text_input(
            "query", placeholder="Ask a question…",
            label_visibility="collapsed", key="chat_input",
            value=st.session_state.quick_q,
        )
    with input_r:
        send = st.button("Send", type="primary", use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # Clear quick_q after it was used
    if st.session_state.quick_q:
        st.session_state.quick_q = ""

    # ── Handle message send
    active = user_input.strip()
    if (send or (active and st.session_state._last_input != active)) and active:
        st.session_state._last_input = active
        ts_now = datetime.now().strftime("%H:%M")
        st.session_state.chat_history.append(
            {"role": "user", "content": active, "ts": ts_now}
        )
        with st.spinner(""):
            try:
                answer, sources = ask_claude(active)
            except Exception as e:
                answer  = f"Something went wrong — please try again. *(Error: {e})*"
                sources = []
        st.session_state.chat_history.append(
            {"role": "assistant", "content": answer, "ts": ts_now, "sources": sources}
        )
        st.rerun()


# ══════════════════════════════════════════════════════════════════
#  SETTINGS PAGE
# ══════════════════════════════════════════════════════════════════
def ts_label(iso):
    try: return datetime.fromisoformat(iso).strftime("%d %b %H:%M")
    except: return ""

def render_settings():
    render_topnav(show_settings_btn=False, show_back_btn=True)

    docs, links, wa, pages = kb_stats()

    # Page header
    st.markdown("""
    <div class="settings-page">
    <div class="settings-inner">
    """, unsafe_allow_html=True)

    # Back link + title row
    st.markdown("""
    <div class="settings-title">Knowledge Base Settings</div>
    <div class="settings-sub">
        Manage the documents and data sources that power the AI assistant.
        None of these sources are visible to end users.
    </div>
    """, unsafe_allow_html=True)

    # ── Stats row ──────────────────────────────────────────────────
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Documents", docs)
    s2.metric("Web pages", links)
    s3.metric("WA chats",  wa)
    s4.metric("Crawled",   pages)
    s5.metric("Total",     docs + links + wa + pages)

    st.markdown("---")

    # ── Tabs ────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5 = st.tabs([
        "📄 Documents", "🌐 Web Links", "💬 WhatsApp", "🕷️ Crawl Site", "⚙️ Preferences"
    ])

    # ── Documents ──────────────────────────────────────────────────
    with t1:
        st.caption("Supported: PDF · DOCX · XLSX · PPTX · HTML · TXT · CSV · JSON · RTF · EPUB · EML · Jupyter (.ipynb) · code files · and more.")
        ups = st.file_uploader(
            "upload_docs", accept_multiple_files=True,
            key="doc_uploader", label_visibility="collapsed",
        )
        if ups:
            ex = {d["name"] for d in st.session_state.kb_documents}
            added = 0
            for f in ups:
                if f.name not in ex:
                    with st.spinner(f"Parsing {f.name}…"):
                        content = parse_file(f)
                    st.session_state.kb_documents.append({
                        "name": f.name,
                        "content": content,
                        "type": _ext(f.name),
                        "added_at": datetime.now().isoformat(),
                        "size": len(content),
                    })
                    added += 1
            if added:
                save_kb()
                st.success(f"✅ {added} file(s) added and saved.")

        if st.session_state.kb_documents:
            st.markdown("**Loaded documents**")
            for i, d in enumerate(st.session_state.kb_documents):
                ca, cb = st.columns([6, 1])
                with ca:
                    st.markdown(
                        f'<div class="file-row">'
                        f'<span class="file-row-icon">{FILE_ICON(d["type"])}</span>'
                        f'<span class="file-row-name">{d["name"]}</span>'
                        f'<span class="file-row-meta">{d["size"]:,} chars · {ts_label(d["added_at"])}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with cb:
                    if st.button("Remove", key=f"rm_doc_{i}", type="secondary"):
                        st.session_state.kb_documents.pop(i)
                        save_kb(); st.rerun()

    # ── Web Links ──────────────────────────────────────────────────
    with t2:
        st.caption("Paste a URL to scrape and index that page's content.")
        url_in = st.text_input("URL", placeholder="https://convin.ai/features", key="link_url")
        if st.button("Add page", key="add_link", type="primary"):
            u = url_in.strip()
            if u:
                if u in {l["url"] for l in st.session_state.kb_links}:
                    st.warning("This URL is already in the knowledge base.")
                else:
                    with st.spinner("Fetching page…"):
                        title, content = fetch_url(u)
                    st.session_state.kb_links.append({
                        "url": u, "title": title, "content": content,
                        "added_at": datetime.now().isoformat(), "size": len(content),
                    })
                    save_kb()
                    st.success(f"Added: {title[:50]}")
            else:
                st.error("Enter a URL first.")

        if st.session_state.kb_links:
            st.markdown("**Loaded links**")
            for i, l in enumerate(st.session_state.kb_links):
                ca, cb = st.columns([6, 1])
                with ca:
                    st.markdown(
                        f'<div class="file-row">'
                        f'<span class="file-row-icon">🌐</span>'
                        f'<span class="file-row-name">{l["title"][:50]}</span>'
                        f'<span class="file-row-meta">{l["size"]:,} chars · {ts_label(l["added_at"])}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with cb:
                    if st.button("Remove", key=f"rm_link_{i}", type="secondary"):
                        st.session_state.kb_links.pop(i)
                        save_kb(); st.rerun()

    # ── WhatsApp ───────────────────────────────────────────────────
    with t3:
        st.markdown("""
        <div style='background:rgba(16,185,129,0.07);border:1px solid rgba(16,185,129,0.20);
        border-radius:12px;padding:12px 16px;margin-bottom:14px;font-size:0.82rem;color:#6EE7B7'>
        📱 <b>How to export:</b> Open WhatsApp → Chat → ⋮ / ⋯ → More → Export Chat → share the <code>.txt</code> or <code>.zip</code> file here.
        </div>
        """, unsafe_allow_html=True)

        wa_up = st.file_uploader(
            "wa_upload", accept_multiple_files=True,
            type=["txt", "zip", "pdf", "docx", "doc", "xlsx", "xls", "csv", "pptx", "ppt", "png", "jpg", "jpeg", "webp", "gif", "mp4", "mp3", "ogg", "opus", "aac", "wav", "json", "html", "htm"],
            key="wa_uploader", label_visibility="collapsed",
        )
        if wa_up:
            ex = {w["name"] for w in st.session_state.kb_whatsapp}
            added, skipped = 0, []
            for f in wa_up:
                if f.name in ex:
                    continue

                # Extract text from zip (WhatsApp export with media)
                if f.name.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(io.BytesIO(f.read())) as zf:
                            txt_files = [n for n in zf.namelist() if n.endswith(".txt")]
                            if not txt_files:
                                skipped.append(f.name)
                                continue
                            raw = zf.read(txt_files[0]).decode("utf-8", "ignore")
                            display_name = f.name
                    except Exception:
                        skipped.append(f.name)
                        continue
                elif f.name.lower().endswith(".txt"):
                    raw = f.read().decode("utf-8", "ignore")
                    display_name = f.name
                else:
                    # Non-text files: store as attachment reference
                    b64 = base64.b64encode(f.read()).decode()
                    st.session_state.kb_whatsapp.append({
                        "name": f.name, "content": f"[Attached file: {f.name}]",
                        "added_at": datetime.now().isoformat(),
                        "size": f.size,
                        "meta": {"valid": True, "total": 0, "participants": [], "date_range": "", "is_attachment": True},
                        "attachment_data": b64,
                        "attachment_mime": f.type or "application/octet-stream",
                    })
                    added += 1
                    continue

                parsed = parse_wa(raw)
                meta   = parse_wa_meta(parsed)

                # Validate it's a real WhatsApp export
                if not meta["valid"] or meta["total"] < 3:
                    skipped.append(f.name)
                    continue

                st.session_state.kb_whatsapp.append({
                    "name": display_name, "content": parsed,
                    "added_at": datetime.now().isoformat(),
                    "size": len(parsed),
                    "meta": meta,
                })
                added += 1

            if added:
                save_kb()
                st.success(f"✅ {added} file(s) added.")
            if skipped:
                st.warning(f"⚠️ {', '.join(skipped)} — doesn't look like a WhatsApp export (no messages found).")

        if st.session_state.kb_whatsapp:
            st.markdown("**Loaded chats**")
            for i, w in enumerate(st.session_state.kb_whatsapp):
                meta = w.get("meta") or parse_wa_meta(w.get("content", ""))
                plist = ", ".join(meta.get("participants", [])[:4]) if meta.get("valid") else "—"
                if len(meta.get("participants", [])) > 4:
                    plist += f" +{len(meta['participants'])-4} more"
                drange = meta.get("date_range", "")
                total_m = meta.get("total", 0)

                ca, cb = st.columns([6, 1])
                with ca:
                    st.markdown(
                        f'<div class="file-row" style="flex-direction:column;align-items:flex-start;gap:6px;padding:12px 16px">'
                        f'<div style="display:flex;align-items:center;gap:8px;width:100%">'
                        f'<span class="file-row-icon">💬</span>'
                        f'<span class="file-row-name">{w["name"]}</span>'
                        f'<span class="file-row-meta">{w["size"]:,} chars · {ts_label(w["added_at"])}</span>'
                        f'</div>'
                        f'<div style="display:flex;gap:10px;flex-wrap:wrap;padding-left:24px">'
                        f'<span style="font-size:0.7rem;color:#10B981">👥 {plist}</span>'
                        f'<span style="font-size:0.7rem;color:#8D90AA">📅 {drange}</span>'
                        f'<span style="font-size:0.7rem;color:#8D90AA">💬 {total_m:,} messages</span>'
                        f'</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with cb:
                    if st.button("Remove", key=f"rm_wa_{i}", type="secondary"):
                        st.session_state.kb_whatsapp.pop(i)
                        save_kb(); st.rerun()

    # ── Crawl Site ─────────────────────────────────────────────────
    with t4:
        st.caption("Automatically crawl all pages on a website and add them to the knowledge base.")
        crawl_url = st.text_input("Root URL", value="https://convin.ai", key="crawl_url")
        max_p     = st.slider("Max pages", 5, 100, 30, 5)
        col_go, col_clr = st.columns([2, 1])
        go  = col_go.button("Start crawl", type="primary", use_container_width=True)
        clr = col_clr.button("Clear all crawled", type="secondary", use_container_width=True)

        if clr:
            st.session_state.kb_crawled = []; save_kb(); st.rerun()

        s_ph = st.empty(); p_ph = st.empty()
        if go:
            u = crawl_url.strip()
            if u:
                s_ph.info(f"Crawling **{u}** …")
                n = crawl_site(u, max_p, s_ph, p_ph)
                save_kb()
                s_ph.success(f"✅ Done — {n} pages indexed.")
                st.rerun()
            else:
                st.error("Enter a URL.")

        if st.session_state.kb_crawled:
            with st.expander(f"📑 {len(st.session_state.kb_crawled)} crawled pages", expanded=False):
                for i, pg in enumerate(st.session_state.kb_crawled):
                    ca, cb = st.columns([6, 1])
                    with ca:
                        st.markdown(
                            f'<div class="file-row">'
                            f'<span class="file-row-icon">🕷️</span>'
                            f'<span class="file-row-name">{pg["title"][:55]}</span>'
                            f'<span class="file-row-meta">{pg["size"]:,} chars</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with cb:
                        if st.button("Remove", key=f"rm_pg_{i}", type="secondary"):
                            st.session_state.kb_crawled.pop(i)
                            save_kb(); st.rerun()

    # ── Preferences ────────────────────────────────────────────────
    with t5:
        st.markdown("**Display settings**")
        show_src = st.toggle(
            "Show sources under AI answers",
            value=st.session_state.get("show_sources", False),
            help="When enabled, the document/page names used to generate each answer are shown below the response.",
        )
        if show_src != st.session_state.get("show_sources", False):
            st.session_state["show_sources"] = show_src
            save_kb()

        st.markdown("---")
        st.markdown("**Danger zone**")
        if st.button("🗑️  Clear entire knowledge base", type="secondary"):
            for k in KB_KEYS:
                st.session_state[k] = []
            save_kb()
            st.success("Knowledge base cleared.")
            st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  FAQ PAGE
# ══════════════════════════════════════════════════════════════════
def render_faq():
    render_topnav(show_settings_btn=False, show_back_btn=True)

    faqs  = st.session_state.get("kb_faqs", [])
    cats  = list(dict.fromkeys(f["category"] for f in faqs)) if faqs else []
    total = total_sources()

    # ── Hero ──────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="faq-hero">
      <div class="faq-hero-left">
        <h2>✦ Answer Studio</h2>
        <p>Auto-generated answers from your entire knowledge base — always up to date</p>
      </div>
      <div class="faq-stat-row">
        <div class="faq-stat-box"><div class="n">{len(faqs)}</div><div class="l">Questions</div></div>
        <div class="faq-stat-box"><div class="n">{len(cats)}</div><div class="l">Categories</div></div>
        <div class="faq-stat-box"><div class="n">{total}</div><div class="l">KB Sources</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── WhatsApp chats panel ──────────────────────────────────────
    wa_chats = st.session_state.get("kb_whatsapp", [])
    if wa_chats:
        wa_cards = ""
        for w in wa_chats:
            meta = w.get("meta") or parse_wa_meta(w.get("content", ""))
            if not meta.get("valid"):
                continue
            plist   = " · ".join(meta.get("participants", [])[:3])
            if len(meta.get("participants", [])) > 3:
                plist += f" +{len(meta['participants'])-3}"
            wa_cats = [c for c in cats if c.startswith("WhatsApp:")]
            wa_q_count = len([f for f in faqs if f["category"].startswith("WhatsApp:")])
            wa_cards += (
                f'<div class="wa-chat-card">'
                f'<div class="wa-chat-top"><span class="wa-chat-icon">💬</span>'
                f'<span class="wa-chat-name">{w["name"]}</span>'
                f'<span class="wa-chat-badge">{meta.get("total",0):,} msgs</span></div>'
                f'<div class="wa-chat-meta">👥 {plist} &nbsp;·&nbsp; 📅 {meta.get("date_range","")}</div>'
                + (f'<div class="wa-chat-qa">✦ {wa_q_count} answers extracted across {len(wa_cats)} categories</div>' if wa_q_count else '')
                + f'</div>'
            )
        if wa_cards:
            st.markdown(
                f'<div class="wa-panel"><div class="wa-panel-title">💬 WhatsApp Chats</div>'
                f'<div class="wa-cards-row">{wa_cards}</div></div>',
                unsafe_allow_html=True,
            )

    # ── Action bar ────────────────────────────────────────────────
    ab1, ab2, ab3, ab4 = st.columns([3, 2, 2, 2])
    with ab1:
        gen_btn = st.button(
            "✨ Generate Answers" if not faqs else "🔄 Regenerate Answers",
            type="primary", use_container_width=True, disabled=(total == 0),
        )
    with ab2:
        if faqs and st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.kb_faqs = []
            save_kb(); st.rerun()
    with ab3:
        if faqs:
            st.download_button(
                "⬇️ Export JSON",
                data=json.dumps(faqs, indent=2, ensure_ascii=False),
                file_name="answer-studio.json", mime="application/json",
                use_container_width=True,
            )
    with ab4:
        if faqs:
            lines = []
            for cat in cats:
                lines += [f"\n{'='*50}", f"  {cat.upper()}", f"{'='*50}\n"]
                for idx, faq in enumerate([f for f in faqs if f["category"]==cat], 1):
                    lines += [f"Q{idx}. {faq['question']}", f"A:  {faq['answer']}\n"]
            st.download_button(
                "⬇️ Export TXT",
                data="\n".join(lines), file_name="answer-studio.txt", mime="text/plain",
                use_container_width=True,
            )

    if total == 0:
        st.info("Add documents or links from Settings first, then click Generate.")

    # ── Generate ──────────────────────────────────────────────────
    if gen_btn:
        prog_ph   = st.empty()
        status_ph = st.empty()

        docs_n  = len(st.session_state.get("kb_documents", []))
        links_n = len(st.session_state.get("kb_links", [])) + len(st.session_state.get("kb_crawled", []))
        wa_n    = len(st.session_state.get("kb_whatsapp", []))
        passes  = sum(1 for x in [docs_n, links_n, wa_n] if x > 0)

        status_ph.markdown(
            f"<span style='color:#A78BFA;font-size:0.85rem'>"
            f"🤖 Running {passes} extraction pass(es) across all sources — "
            f"building your Answer Studio…</span>",
            unsafe_allow_html=True,
        )
        prog_ph.progress(0.05)

        def _progress(pct, label):
            prog_ph.progress(pct)
            status_ph.markdown(
                f"<span style='color:#A78BFA;font-size:0.85rem'>{label}</span>",
                unsafe_allow_html=True,
            )

        try:
            new_faqs = generate_faqs(progress_cb=_progress)
            prog_ph.progress(1.0)
            if new_faqs:
                st.session_state.kb_faqs = new_faqs
                save_kb()
                prog_ph.empty()
                n_cats = len(set(f["category"] for f in new_faqs))
                status_ph.success(
                    f"✅ {len(new_faqs)} answers generated across {n_cats} categories — saved to Answer Studio!"
                )
                st.rerun()
            else:
                prog_ph.empty()
                status_ph.warning("No answers extracted. Try adding more content.")
        except Exception as e:
            prog_ph.empty()
            status_ph.error(f"Error: {e}")

    # ── Search ────────────────────────────────────────────────────
    if faqs:
        sc, qc = st.columns([6, 1])
        with sc:
            search = st.text_input(
                "search", placeholder="🔍  Search questions and answers…",
                label_visibility="collapsed", key="faq_search",
            )
        with qc:
            st.markdown(
                f"<div style='text-align:right;padding-top:8px;"
                f"font-size:0.78rem;color:#8D90AA'><b style='color:#A78BFA'>{len(faqs)}</b> Q&As</div>",
                unsafe_allow_html=True,
            )
        slc = search.lower().strip() if search else ""

        # ── Categories ────────────────────────────────────────────
        for cat in cats:
            cat_faqs = [f for f in faqs if f["category"] == cat]
            if slc:
                cat_faqs = [
                    f for f in cat_faqs
                    if slc in f["question"].lower() or slc in f["answer"].lower()
                ]
            if not cat_faqs:
                continue

            st.markdown(
                f'<div class="cat-label">📂 {cat} &nbsp;·&nbsp; {len(cat_faqs)} questions</div>',
                unsafe_allow_html=True,
            )

            for idx, faq in enumerate(cat_faqs):
                q_disp = faq["question"]
                a_disp = faq["answer"]

                # Detect source type for badge
                has_wa  = "💬 Chatted by" in a_disp or "chatted by" in a_disp.lower()
                badge_html = (
                    '<span class="faq-wa-badge">💬 WhatsApp source</span>'
                    if has_wa else
                    '<span class="faq-doc-badge">📄 KB source</span>'
                )

                if slc:
                    def hl(text, term=slc):
                        return re.sub(
                            f"({re.escape(term)})",
                            r'<mark style="background:rgba(124,58,237,0.28);'
                            r'border-radius:3px;padding:0 3px;color:#EEF0FA">\1</mark>',
                            text, flags=re.IGNORECASE,
                        )
                    a_disp = hl(a_disp)
                    q_disp = hl(q_disp)

                # Convert WA citation lines to styled blockquote
                a_rendered = re.sub(
                    r"(💬 Chatted by[^\n]+)",
                    r'<div class="wa-cite">🟢 \1</div>',
                    a_disp,
                )

                exp_label = f"Q: {faq['question']}"
                with st.expander(exp_label, expanded=False):
                    st.markdown(
                        f"<div class='faq-answer-wrap'>"
                        f"<div style='margin-bottom:10px'>{badge_html}</div>"
                        f"<div class='faq-answer-label'>Answer</div>"
                        f"<div class='faq-answer-body'>{a_rendered}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "💬 Ask follow-up in chat",
                        key=f"faq_ask_{cat}_{idx}",
                        type="secondary",
                    ):
                        st.session_state.quick_q   = faq["question"]
                        st.session_state.page      = "chat"
                        st.rerun()
    else:
        st.markdown("""
        <div class="no-faq">
          <div class="no-faq-icon">✦</div>
          <h3>Answer Studio is empty</h3>
          <p>Load at least one source in Settings,<br>
             then click <b>✨ Generate Answers</b> above.</p>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════════════════
if st.session_state.page == "chat":
    render_chat()
elif st.session_state.page == "settings":
    render_settings()
elif st.session_state.page == "faq":
    render_faq()
