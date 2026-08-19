import streamlit as st
import pandas as pd
import io
import csv
import base64
import os
import plotly.express as px
from dotenv import load_dotenv

# Environment Variables auto-load
load_dotenv()


# ── Base64 Logo Helper ────────────────────────────────────────────────────────
def get_logo_base64(path: str = "assets/logo.png") -> str:
    """Encode the brand logo to a base64 data URI for inline HTML rendering."""
    try:
        with open(path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{encoded}"
    except FileNotFoundError:
        return ""  # Safe fallback – callers must handle empty string


LOGO_B64 = get_logo_base64()

import uuid
import importlib
import database.schema
importlib.reload(database.schema)
from database.schema import (
    save_query_history, 
    get_all_history, 
    delete_query_history,
    create_session,
    get_all_sessions,
    rename_session,
    delete_session,
    save_message,
    get_session_messages
)
from database.connection import get_db_connection
from agent.graph import agent_app

# 1. Page Configuration
st.set_page_config(
    page_title="OmniQuery | Autonomous AI Analytics",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Custom CSS — Main app + Gemini-style Sidebar
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Global ──────────────────────────────────────────────────────────────── */
    .stApp {
        background-color: #0E1117;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ── Main Content Top Padding ────────────────────────────────────────────── */
    .block-container { padding-top: 2rem !important; }

    /* ── Hide Deploy Button ───────────────────────────────────────────────────── */
    .stDeployButton,
    [data-testid="stDeployButton"] { display: none !important; }

    /* ── Sidebar Shell (Gemini / ChatGPT Style: Fixed Header & Footer, Scrollable History) ── */
    [data-testid="stSidebar"] {
        background-color: #111214 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #111214 !important;
    }
    /* Hide Streamlit's native sidebar header bar to reclaim space */
    [data-testid="stSidebarHeader"] {
        display: none !important;
    }
    [data-testid="stSidebarContent"] {
        background-color: #111214 !important;
        padding-top: 0.8rem !important;
        padding-left: 0.6rem !important;
        padding-right: 0.6rem !important;
        padding-bottom: 0.8rem !important;
        display: flex !important;
        flex-direction: column !important;
        height: 100vh !important;
        max-height: 100vh !important;
        overflow: hidden !important; /* Disables whole sidebar outer scroll */
    }
    [data-testid="stSidebarUserContent"] {
        padding: 0 !important;
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        height: 100% !important;
        max-height: 100% !important;
        overflow: hidden !important;
    }
    [data-testid="stSidebarUserContent"] > div[data-testid="stVerticalBlock"],
    [data-testid="stSidebarUserContent"] > div:first-child {
        display: flex !important;
        flex-direction: column !important;
        flex: 1 1 auto !important;
        height: 100% !important;
        max-height: 100% !important;
        overflow: hidden !important;
        gap: 0.4rem !important;
    }

    /* ── New Analysis Pill Button (Gemini Style) ──────────────────────────────── */
    .st-key-new_analysis_btn > button,
    div[data-testid="stSidebar"] button[kind="secondary"].new-analysis-btn,
    .new-analysis-btn > button {
        background: #1A1C1E !important;
        border: 1px solid #2D3035 !important;
        border-radius: 24px !important;
        color: #C4C7C5 !important;
        font-weight: 500 !important;
        font-size: 13.5px !important;
        padding: 8px 16px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 8px !important;
        box-shadow: none !important;
        transition: background 0.2s ease, border-color 0.2s ease !important;
    }
    .st-key-new_analysis_btn > button:hover,
    .new-analysis-btn > button:hover {
        background: #2D2F31 !important;
        border-color: #3D4045 !important;
        color: #FFFFFF !important;
    }

    /* ── Search Input ────────────────────────────────────────────────────────── */
    div[data-testid="stSidebar"] .stTextInput input {
        background: #1A1C1E !important;
        border: 1px solid #2D3035 !important;
        border-radius: 8px !important;
        color: #E3E3E3 !important;
        font-size: 13px !important;
        padding: 6px 12px !important;
    }
    div[data-testid="stSidebar"] .stTextInput input:focus {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 1px #38BDF8 !important;
    }
    div[data-testid="stSidebar"] .stTextInput input::placeholder { color: #8E918F !important; }

    /* ── Scrollable History Feed Container ───────────────────────────────────── */
    .st-key-sidebar_history_box,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-sidebar_history_box),
    div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stVerticalBlock"].st-key-sidebar_history_box) {
        flex: 1 1 auto !important;
        min-height: 120px !important;
        max-height: calc(100vh - 250px) !important;
        overflow-y: auto !important;
        overflow-x: hidden !important;
        padding-right: 3px !important;
        display: flex !important;
        flex-direction: column !important;
        gap: 2px !important;
    }
    .st-key-sidebar_history_box > div[data-testid="stVerticalBlock"] {
        gap: 2px !important;
        padding-right: 2px !important;
    }

    /* Minimalist Dark Scrollbar for History container */
    .st-key-sidebar_history_box::-webkit-scrollbar,
    .st-key-sidebar_history_box *::-webkit-scrollbar,
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar {
        width: 4px !important;
    }
    .st-key-sidebar_history_box::-webkit-scrollbar-track,
    .st-key-sidebar_history_box *::-webkit-scrollbar-track,
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-track {
        background: transparent !important;
    }
    .st-key-sidebar_history_box::-webkit-scrollbar-thumb,
    .st-key-sidebar_history_box *::-webkit-scrollbar-thumb,
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-thumb {
        background: #2D3035 !important;
        border-radius: 4px !important;
    }
    .st-key-sidebar_history_box::-webkit-scrollbar-thumb:hover,
    .st-key-sidebar_history_box *::-webkit-scrollbar-thumb:hover,
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"]::-webkit-scrollbar-thumb:hover {
        background: #38BDF8 !important;
    }

    /* ── History Thread Buttons (Gemini flat style) ─────────────────── */
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button,
    div[data-testid="stSidebar"] div[class*="st-key-hist_btn_"] > button {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        color: #C4C7C5 !important;
        font-size: 13px !important;
        font-weight: 400 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 7px 10px !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        box-shadow: none !important;
        min-height: 34px !important;
        transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease !important;
    }
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button:hover,
    div[data-testid="stSidebar"] div[class*="st-key-hist_btn_"] > button:hover {
        background: #1E2022 !important;
        border-color: #2D3035 !important;
        color: #E3E3E3 !important;
    }
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button:focus,
    div[data-testid="stSidebar"] div[class*="st-key-hist_btn_"] > button:focus {
        background: #2D3035 !important;
        border-color: #38BDF8 !important;
        color: #38BDF8 !important;
        box-shadow: none !important;
    }

    /* Ensure text inside history button is aligned to the left and truncated nicely */
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button div,
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button p,
    div[data-testid="stSidebar"] div[class*="st-key-hist_btn_"] > button div,
    div[data-testid="stSidebar"] div[class*="st-key-hist_btn_"] > button p {
        text-align: left !important;
        justify-content: flex-start !important;
        width: 100% !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
        display: block !important;
    }

    /* Style the delete button next to each history button */
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button[key*="delete_btn_"],
    div[data-testid="stSidebar"] div[class*="st-key-delete_btn_"] > button {
        background: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        color: #8E918F !important;
        font-size: 14px !important;
        padding: 0 !important;
        text-align: center !important;
        justify-content: center !important;
        width: 32px !important;
        height: 32px !important;
        min-height: 32px !important;
        box-shadow: none !important;
        transition: color 0.15s ease, background 0.15s ease !important;
    }
    div[data-testid="stSidebar"] .st-key-sidebar_history_box button[key*="delete_btn_"]:hover,
    div[data-testid="stSidebar"] div[class*="st-key-delete_btn_"] > button:hover {
        background: rgba(239, 68, 68, 0.15) !important;
        color: #EF4444 !important;
    }

    /* Make the columns in history row stay tight and neat */
    .st-key-sidebar_history_box [data-testid="stHorizontalBlock"] {
        gap: 2px !important;
        align-items: center !important;
        margin-bottom: 2px !important;
    }
    .st-key-sidebar_history_box [data-testid="stHorizontalBlock"] > div {
        padding: 0 !important;
    }

    /* ── Fixed Footer Controls ───────────────────────────────────────────────── */
    .st-key-sidebar_footer_box,
    div[data-testid="stVerticalBlockBorderWrapper"]:has(.st-key-sidebar_footer_box) {
        margin-top: auto !important;
        padding-top: 8px !important;
        border-top: 1px solid #2D3035 !important;
        flex-shrink: 0 !important;
    }

    /* ── User Profile Footer ─────────────────────────────────────────────────── */
    .user-profile-bar {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 2px 0;
    }
    .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: linear-gradient(135deg, #38BDF8, #818CF8);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 700;
        color: #FFFFFF;
        flex-shrink: 0;
    }
    .user-name {
        font-size: 13px;
        font-weight: 500;
        color: #E3E3E3;
        line-height: 1.2;
    }
    .user-plan {
        font-size: 11px;
        color: #8E918F;
    }

    /* ── Settings Popover Button (Gemini gear icon style) ────────────────────── */
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button {
        background: transparent !important;
        border: none !important;
        border-radius: 50% !important;
        color: #C4C7C5 !important;
        font-size: 18px !important;
        width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: background 0.15s ease, color 0.15s ease !important;
    }
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button:hover {
        background: #2D2F31 !important;
        color: #FFFFFF !important;
        box-shadow: none !important;
    }
    /* Hide the default Streamlit popover arrow/chevron */
    div[data-testid="stSidebar"] div[data-testid="stPopover"] > button svg {
        display: none !important;
    }

    /* ── Card & Metric ───────────────────────────────────────────────────────── */
    .custom-card {
        background: #1E222D;
        border: 1px solid #2E3440;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-box {
        background: linear-gradient(135deg, #1F2937 0%, #111827 100%);
        border: 1px solid #374151;
        border-radius: 10px;
        padding: 14px;
        text-align: center;
    }
    .metric-value { font-size: 22px; font-weight: 700; color: #38BDF8; }
    .metric-label { font-size: 11px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em; }
    .section-header { font-size: 18px; font-weight: 600; color: #F3F4F6; margin-bottom: 12px; }

   .welcome-shell {
       display: flex;
       flex-direction: column;
       align-items: center;
       justify-content: center;
       text-align: center;
       min-height: 58vh;
       padding: 2rem 1rem 4rem;
   }
   .welcome-badge {
       display: inline-flex;
       align-items: center;
       gap: 8px;
       background: rgba(56, 189, 248, 0.10);
       border: 1px solid rgba(56, 189, 248, 0.30);
       border-radius: 999px;
       padding: 0.45rem 1rem;
       color: #7dd3fc;
       font-size: 12px;
       font-weight: 600;
       margin-bottom: 1.25rem;
   }
   .welcome-title {
       font-size: clamp(2.5rem, 4vw, 4.3rem);
       font-weight: 800;
       letter-spacing: -0.06em;
       margin: 0;
       background: linear-gradient(135deg, #a78bfa 0%, #7dd3fc 35%, #5eead4 100%);
       -webkit-background-clip: text;
       -webkit-text-fill-color: transparent;
       line-height: 1.05;
   }
   .welcome-subtitle {
       color: #94a3b8;
       font-size: 1.02rem;
       max-width: 620px;
       margin: 1rem auto 2.2rem;
       line-height: 1.6;
   }
   .quick-grid {
       display: grid;
       grid-template-columns: repeat(2, minmax(220px, 1fr));
       gap: 1rem;
       max-width: 640px;
       width: 100%;
   }
   .quick-card {
       background: rgba(15, 23, 42, 0.45);
       border: 1px solid rgba(148, 163, 184, 0.2);
       border-radius: 14px;
       padding: 1rem 1.2rem;
       min-height: 116px;
       color: #e2e8f0;
       text-align: left;
       box-shadow: 0 8px 30px rgba(15, 23, 42, 0.15);
       transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
   }
   .quick-card:hover {
       transform: translateY(-2px);
       border-color: rgba(56, 189, 248, 0.5);
       box-shadow: 0 14px 30px rgba(56, 189, 248, 0.12);
   }
   .quick-card-title {
       display: flex;
       align-items: center;
       gap: 8px;
       font-weight: 700;
       font-size: 1rem;
       margin-bottom: 0.5rem;
   }
   .quick-card-desc {
       color: #94a3b8;
       font-size: 0.88rem;
       line-height: 1.45;
   }
</style>
""", unsafe_allow_html=True)

# ── 3. GEMINI-STYLE SIDEBAR ──────────────────────────────────────────────────

# 3a. Brand Header (Pinned Top)
_logo_img = f'<img src="{LOGO_B64}" width="34" style="border-radius:7px; flex-shrink:0;"/>' if LOGO_B64 else "🔷"
st.sidebar.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:10px; padding:2px 2px 10px 2px; border-bottom:1px solid #2D3035; margin-bottom:10px;">
        {_logo_img}
        <div>
            <span style="font-size:16px; font-weight:700; color:#F1F5F9; letter-spacing:-0.01em;">OmniQuery</span><br/>
            <span style="font-size:9.5px; font-weight:600; color:#38BDF8; letter-spacing:0.1em;">ENTERPRISE AI</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Initialize session state for multi-turn chats
sessions = get_all_sessions()
if "active_session_id" not in st.session_state:
    if sessions:
        st.session_state.active_session_id = sessions[0]["session_id"]
    else:
        new_id = str(uuid.uuid4())
        create_session(new_id, "New Chat")
        st.session_state.active_session_id = new_id
        sessions = get_all_sessions()

# 3b. ➕ New Analysis Button (Pinned Top)
with st.sidebar:
    if st.button("➕  New Analysis", key="new_analysis_btn", use_container_width=True):
        new_id = str(uuid.uuid4())
        create_session(new_id, "New Chat")
        st.session_state.active_session_id = new_id
        if "last_result" in st.session_state:
            st.session_state.last_result = None
        st.rerun()

# 3c. Search Input (Pinned Top)
search_query = st.sidebar.text_input(
    "Search chats",
    placeholder="🔍  Search analyses...",
    label_visibility="collapsed",
    key="sidebar_search"
)

# 3d. Section Header (Pinned Top)
st.sidebar.markdown(
    '<p style="font-size:10.5px; color:#8E918F; font-weight:600; letter-spacing:0.07em; '
    'text-transform:uppercase; margin:8px 2px 4px 2px;">Recent Analyses</p>',
    unsafe_allow_html=True
)

# 3e. History Feed (Scrollable Middle Section — ONLY this section scrolls)
with st.sidebar.container(key="sidebar_history_box", height=420, border=False):
    if sessions:
        # Apply search filter
        filtered_sessions = [
            s for s in sessions
            if not search_query or search_query.lower() in s["session_name"].lower()
        ]

        if filtered_sessions:
            for i, s in enumerate(filtered_sessions):
                session_id = s["session_id"]
                name = s["session_name"]
                short_name = (name[:32] + "…") if len(name) > 32 else name
                
                # Render active state styling if active
                active_label = f"💬  {short_name}"
                if st.button(
                    active_label,
                    key=f"session_btn_{session_id}",
                    help=name,
                    use_container_width=True
                ):
                    st.session_state.active_session_id = session_id
                    st.rerun()
        else:
            st.markdown(
                '<p style="color:#8E918F; font-size:12.5px; padding:10px 4px; text-align:center;">No matching analyses.</p>',
                unsafe_allow_html=True
            )
    else:
        st.markdown(
            '<p style="color:#8E918F; font-size:12.5px; padding:10px 4px; text-align:center;">No analyses yet. Run your first query!</p>',
            unsafe_allow_html=True
        )

# 3f. Sidebar Footer (Pinned Fixed at Bottom)
with st.sidebar.container(key="sidebar_footer_box", border=False):
    col_prof, col_settings = st.columns([3.8, 1.2])
    with col_prof:
        st.markdown(
            """
            <div class="user-profile-bar">
                <div class="user-avatar">SS</div>
                <div>
                    <div class="user-name">S.Sadishan</div>
                    <div class="user-plan">Enterprise AI Pro</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_settings:
        with st.popover("⚙️", use_container_width=True, help="System Controls"):
            st.markdown(
                '<p style="font-size:13px; font-weight:600; color:#F1F5F9; margin-bottom:10px;">System Controls</p>',
                unsafe_allow_html=True
            )
            if st.button("🔄 Reset Session", use_container_width=True, key="pop_reset"):
                keys_to_clear = list(st.session_state.keys())
                for k in keys_to_clear:
                    del st.session_state[k]
                st.rerun()
            if st.button("🧹 Clear Cache", use_container_width=True, key="pop_cache"):
                st.cache_data.clear()
                st.toast("✅ Cache cleared!", icon="🧹")
            st.divider()
            st.markdown(
                """
                <div style="font-size:12px; color:#94A3B8; line-height:1.8;">
                    <b style="color:#38BDF8;">Llama 3.3 70B</b> &middot; Groq LPU<br/>
                    <b style="color:#34D399;">LangGraph</b> Stateful Agent<br/>
                    <b style="color:#FBBF24;">SQLite</b> &middot; enterprise_data.db
                </div>
                """,
                unsafe_allow_html=True
            )


# 4. Compact Branded Main Header
_header_logo = f'<img src="{LOGO_B64}" width="46" style="border-radius:8px; margin-right:14px; vertical-align:middle;"/>' if LOGO_B64 else ""
st.markdown(
    f"""
    <div style="display:flex; align-items:center; padding:10px 0 4px 0; margin-bottom:2px;">
        {_header_logo}
        <div>
            <h1 style="font-size:25px; font-weight:800; color:#F3F4F6; margin:0; line-height:1.25;">OmniQuery&nbsp;<span style="color:#38BDF8;">|</span>&nbsp;Autonomous BI Agent</h1>
            <p style="color:#9CA3AF; font-size:13px; margin:2px 0 0 0; letter-spacing:0.02em;">Enterprise Text-to-SQL &amp; Automated Business Intelligence Analytics</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# 5. Multi-Turn Chat Feed
active_session_id = st.session_state.active_session_id
messages = get_session_messages(active_session_id)

quick_prompts = [
    {"title": "💰 Total Revenue", "query": "What is the total sales amount?"},
    {"title": "🔥 Top Customer", "query": "Which customer purchased the most in electronics?"},
    {"title": "📈 Product Profits", "query": "wadiyenma sale wenne mona itemsda charts ekkama profit ekath ekka danna?"},
    {"title": "📊 Category Overview", "query": "Show sales distribution and details by product categories."},
]

if not messages:
    st.markdown(
        """
        <div class="welcome-shell">
            <div class="welcome-badge">✨ Autonomous BI Analytics Engine</div>
            <h2 class="welcome-title">Ask OmniQuery Anything</h2>
            <p class="welcome-subtitle">Enter complex business intelligence questions. The agent will write SQLite queries, execute them, correct syntax, and render visualizations.</p>
            <div class="quick-grid">
                <button class="quick-card" onclick="document.body.click();"> 
                    <div class="quick-card-title">💰 Total Revenue</div>
                    <div class="quick-card-desc">Calculate cumulative sales earnings across all categories.</div>
                </button>
                <button class="quick-card" onclick="document.body.click();">
                    <div class="quick-card-title">🔥 Top Customer</div>
                    <div class="quick-card-desc">Retrieve details of the highest spending customer.</div>
                </button>
                <button class="quick-card" onclick="document.body.click();">
                    <div class="quick-card-title">📈 Product Profits</div>
                    <div class="quick-card-desc">Show highest selling products and analyze profit margins.</div>
                </button>
                <button class="quick-card" onclick="document.body.click();">
                    <div class="quick-card-title">📊 Category Overview</div>
                    <div class="quick-card-desc">Get group-wise categories metrics breakdown.</div>
                </button>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns(2)
    for idx, prompt in enumerate(quick_prompts):
        with cols[idx % 2]:
            if st.button(f"{prompt['title']}\n{prompt['query']}", key=f"quick_prompt_{idx}", use_container_width=True):
                st.session_state.pending_prompt = prompt["query"]
                st.rerun()

if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    user_question = st.session_state.pending_prompt
    st.session_state.pending_prompt = ""
else:
    user_question = None

# Loop and render existing conversation messages
for idx, msg in enumerate(messages):
    role = msg["role"]
    content = msg["content"]
    
    with st.chat_message(role):
        st.write(content)
        
        # If assistant has executed SQL and results, display them beautifully
        if role == "assistant" and msg.get("sql_query"):
            with st.expander("💻 Executed SQL Query"):
                st.code(msg["sql_query"], language="sql")
                
            query_result_json = msg.get("query_result_json")
            if query_result_json:
                try:
                    import json
                    res_data = json.loads(query_result_json)
                    columns = res_data.get("columns", [])
                    rows = res_data.get("rows", [])
                    
                    if columns and rows:
                        df = pd.DataFrame(rows, columns=columns)
                        
                        # Metric summary cards
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.markdown(f'<div class="metric-box"><div class="metric-value">{len(rows)}</div><div class="metric-label">Rows Fetched</div></div>', unsafe_allow_html=True)
                        with m2:
                            st.markdown('<div class="metric-box"><div class="metric-value">Groq 70B</div><div class="metric-label">LPU Engine</div></div>', unsafe_allow_html=True)
                        with m3:
                            st.markdown('<div class="metric-box"><div class="metric-value">SUCCESS</div><div class="metric-label">Agent Status</div></div>', unsafe_allow_html=True)
                        with m4:
                            st.markdown('<div class="metric-box"><div class="metric-value">ACTIVE</div><div class="metric-label">Guardrails</div></div>', unsafe_allow_html=True)
                            
                        # Layout cols: left holds raw data table & export, right holds interactive visualization
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            st.markdown('<div class="section-header">📋 Raw Query Results Table</div>', unsafe_allow_html=True)
                            st.dataframe(df, use_container_width=True)
                            
                            # CSV export buffer
                            import csv
                            import io
                            csv_buffer = io.StringIO()
                            csv_writer = csv.writer(csv_buffer)
                            csv_writer.writerow(["Enterprise Text-to-SQL Analytics Report"])
                            csv_writer.writerow([])
                            csv_writer.writerow(["Question", messages[max(0, idx-1)]["content"] if idx > 0 else ""])
                            csv_writer.writerow(["Executed SQL Query", msg["sql_query"]])
                            csv_writer.writerow([])
                            csv_writer.writerow(["Raw Data Table"])
                            csv_writer.writerow(columns)
                            for row in rows:
                                csv_writer.writerow(row)
                            csv_data = csv_buffer.getvalue()
                            
                            st.download_button(
                                label="📥 Export Raw Data CSV",
                                data=csv_data,
                                file_name=f"query_result_{idx}.csv",
                                mime="text/csv",
                                key=f"dl_btn_{idx}",
                                use_container_width=True
                            )
                        with col2:
                            st.markdown('<div class="section-header">📊 Interactive Data Visualization</div>', unsafe_allow_html=True)
                            fig = None
                            if len(df.columns) >= 2 and len(df) > 0:
                                x_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
                                y_col = df.columns[-1]
                                if pd.api.types.is_numeric_dtype(df[y_col]):
                                    fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}", template="plotly_white")
                                    fig.update_layout(
                                        paper_bgcolor="rgba(0,0,0,0)",
                                        plot_bgcolor="rgba(0,0,0,0)",
                                        font=dict(color="#E5E7EB"),
                                        margin=dict(l=20, r=20, t=30, b=20)
                                    )
                                    st.plotly_chart(fig, use_container_width=True)
                            if not fig:
                                st.info("No visual chart available for this query.")
                except Exception as e:
                    st.error(f"Error rendering visual data components: {e}")

# 6. Streamlit Chat Input (Pinned Bottom)
user_question = st.chat_input("Ask a question about your business data...")

if user_question:
    # Render user query immediately
    with st.chat_message("user"):
        st.write(user_question)
        
    # Save user message to database
    save_message(session_id=active_session_id, role="user", content=user_question)
    
    # Auto-rename session if it was named "New Chat" and this is the first question
    if not messages or len(messages) == 0:
        rename_session(active_session_id, user_question[:36])
        
    # Format history context string to pass to LangGraph
    history_parts = []
    for msg in messages:
        role_label = "User" if msg["role"] == "user" else "Assistant"
        history_parts.append(f"{role_label}: {msg['content']}")
    history_str = "\n".join(history_parts)
    
    with st.spinner("🤖 Agent is thinking, writing SQL, and analyzing data..."):
        # Initializing Graph State
        initial_state = {
            "question": user_question,
            "sql_query": None,
            "column_names": None,
            "query_result": None,
            "error_message": None,
            "retry_count": 0,
            "insights": None,
            "chart_json": None,
            "history": history_str
        }
        
        # Execute LangGraph Workflow
        final_output = agent_app.invoke(initial_state)
        
        # Prepare assistant text content
        error_msg = final_output.get("error_message")
        if error_msg:
            assistant_content = f"❌ Execution Error: {error_msg}"
            result_json_str = None
        else:
            assistant_content = final_output.get("insights", "Here are the query results:")
            
            # Prepare result JSON
            columns = final_output.get("column_names") or []
            rows = final_output.get("query_result") or []
            import json
            result_json_str = json.dumps({"columns": columns, "rows": rows})
            
        # Save assistant message to database
        save_message(
            session_id=active_session_id,
            role="assistant",
            content=assistant_content,
            sql_query=final_output.get("sql_query"),
            query_result_json=result_json_str
        )
        
        # Rerun to update chat screen
        st.rerun()