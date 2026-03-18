# ================================
# 🔧 STREAMLIT PAGE CONFIGURATION
# ================================
import streamlit as st

st.set_page_config(
    page_title="Boutiqaat Catalog Readiness Report",
    layout="wide",
    page_icon="🛍️",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.boutiqaat.com',
        'Report a bug': None,
        'About': "# Boutiqaat Catalog Readiness Dashboard\nPowered by Boutiqaat Merchandising Team"
    }
)

# ================================
# 📦 IMPORTS
# ================================
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os
import gc
import hmac
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# ================================
# ⚙️ LOGGING
# ================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ================================
# 🎨 BOUTIQAAT THEME SYSTEM
# ================================
class BoutiqaatTheme:
    """Centralized theme — Boutiqaat brand palette"""

    # PRIMARY — Deep Champagne Gold (from logo star)
    PRIMARY        = "#B8860B"
    PRIMARY_DARK   = "#8B6508"
    PRIMARY_LIGHT  = "#D4A017"
    PRIMARY_GLOW   = "rgba(184,134,11,0.25)"

    # SECONDARY — Rich Onyx (from logo wordmark)
    SECONDARY      = "#1A1A1A"
    SECONDARY_SOFT = "#2C2C2C"

    # ACCENT PALETTE — colourful & meaningful
    ACCENT_EMERALD  = "#10B981"   # ✅ Ready / success
    ACCENT_AMBER    = "#F59E0B"   # ⚠️ Near-ready / warning
    ACCENT_CRIMSON  = "#EF4444"   # ❌ Incomplete / danger
    ACCENT_SAPPHIRE = "#3B82F6"   # 📊 Info / charts
    ACCENT_VIOLET   = "#8B5CF6"   # 🔮 Secondary charts
    ACCENT_ROSE     = "#F43F5E"   # 💄 Skincare category
    ACCENT_TEAL     = "#14B8A6"   # 👕 Apparel category

    # BACKGROUND
    BG_WHITE        = "#FFFFFF"
    BG_LIGHT        = "#FAFAF8"
    BG_CARD         = "#FFFEF9"
    BG_DARK         = "#0F0F0F"

    # TEXT
    TEXT_PRIMARY    = "#1A1A1A"
    TEXT_SECONDARY  = "#6B7280"
    TEXT_LIGHT      = "#FFFFFF"
    TEXT_GOLD       = "#B8860B"

    # DESIGN TOKENS
    BORDER_RADIUS        = "14px"
    BORDER_RADIUS_LARGE  = "22px"
    BORDER_RADIUS_PILL   = "50px"

    SHADOW_SMALL  = "0 2px 8px rgba(184,134,11,0.12)"
    SHADOW_MEDIUM = "0 6px 20px rgba(184,134,11,0.18)"
    SHADOW_LARGE  = "0 12px 40px rgba(184,134,11,0.22)"
    SHADOW_HOVER  = "0 20px 60px rgba(184,134,11,0.30)"
    SHADOW_GLOW   = "0 0 30px rgba(184,134,11,0.35)"

    FONT_FAMILY   = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"

    # SCORE THRESHOLDS
    SCORE_FULL        = 100
    SCORE_NEAR_READY  = 75
    SCORE_PARTIAL     = 50

    @staticmethod
    def gradient(c1, c2, angle=135):
        return f"linear-gradient({angle}deg, {c1} 0%, {c2} 100%)"

    @staticmethod
    def gold_gradient(angle=135):
        return BoutiqaatTheme.gradient(BoutiqaatTheme.PRIMARY_DARK, BoutiqaatTheme.PRIMARY_LIGHT, angle)

    @staticmethod
    def score_color(score):
        if score >= BoutiqaatTheme.SCORE_FULL:
            return BoutiqaatTheme.ACCENT_EMERALD
        elif score >= BoutiqaatTheme.SCORE_NEAR_READY:
            return BoutiqaatTheme.ACCENT_AMBER
        elif score >= BoutiqaatTheme.SCORE_PARTIAL:
            return BoutiqaatTheme.ACCENT_SAPPHIRE
        else:
            return BoutiqaatTheme.ACCENT_CRIMSON

    @staticmethod
    def score_label(score):
        if score >= BoutiqaatTheme.SCORE_FULL:
            return "✅ Fully Ready"
        elif score >= BoutiqaatTheme.SCORE_NEAR_READY:
            return "⚠️ Near Ready"
        elif score >= BoutiqaatTheme.SCORE_PARTIAL:
            return "🔵 Partial"
        else:
            return "❌ Incomplete"

T = BoutiqaatTheme  # shorthand

# ================================
# 🖼️ LOGO HELPER
# ================================
def get_logo_base64():
    try:
        logo_path = Path(__file__).parent / "Boutiqaat.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None
    except Exception as e:
        logger.warning(f"Logo not found: {e}")
        return None

LOGO_B64 = get_logo_base64()

# ================================
# 🔢 UTILITY FUNCTIONS
# ================================
def fmt_num(n):
    if pd.isna(n): return "0"
    n = float(n)
    if abs(n) >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if abs(n) >= 1_000:     return f"{n/1_000:.1f}K"
    return f"{int(n):,}"

def fmt_pct(n, dp=1):
    if pd.isna(n): return "0.0%"
    return f"{float(n):.{dp}f}%"

# ================================
# 🔐 AUTHENTICATION
# ================================
def check_password():
    VALID_USER = "Boutiqaat"
    VALID_PASS = "Boutiqaat@2026"

    def _verify():
        try:
            u_ok = hmac.compare_digest(st.session_state.get("username",""), VALID_USER)
            p_ok = hmac.compare_digest(st.session_state.get("password",""), VALID_PASS)
            st.session_state["auth_ok"] = u_ok and p_ok
            if u_ok and p_ok:
                st.session_state.pop("password", None)
                st.session_state.pop("username", None)
        except Exception:
            st.session_state["auth_ok"] = False

    if st.session_state.get("auth_ok", False):
        return True

    # ── Login page CSS ──────────────────────────────────────────────────────
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * {{ font-family: {T.FONT_FAMILY}; }}
    #MainMenu, footer, header {{ visibility: hidden; }}

    .stApp {{
        background: {T.gradient("#0F0F0F", "#1A1208", 160)};
        background-size: 400% 400%;
        animation: bgShift 12s ease infinite;
    }}
    @keyframes bgShift {{
        0%   {{ background-position: 0% 50%; }}
        50%  {{ background-position: 100% 50%; }}
        100% {{ background-position: 0% 50%; }}
    }}

    .login-wrap {{
        max-width: 460px;
        margin: 6vh auto 0;
    }}
    .login-logo-card {{
        background: {T.gradient("#1A1208","#2C2000",160)};
        border-radius: 22px 22px 0 0;
        padding: 2.8rem 2rem 2rem;
        text-align: center;
        border: 1px solid {T.PRIMARY};
        border-bottom: none;
        box-shadow: {T.SHADOW_GLOW};
    }}
    .login-title {{
        color: {T.PRIMARY_LIGHT};
        font-size: 1.6rem;
        font-weight: 800;
        margin: 1.2rem 0 0.3rem;
        letter-spacing: -0.02em;
    }}
    .login-sub {{
        color: {T.TEXT_SECONDARY};
        font-size: 0.95rem;
        font-weight: 500;
    }}
    .login-form-card {{
        background: {T.BG_CARD};
        border-radius: 0 0 22px 22px;
        padding: 2rem;
        border: 1px solid {T.PRIMARY};
        border-top: none;
        box-shadow: {T.SHADOW_LARGE};
    }}
    .stTextInput > label {{
        color: {T.PRIMARY} !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
    }}
    .stTextInput > div > div > input {{
        background: #FAFAF8;
        border: 2px solid #E5E0D5;
        border-radius: {T.BORDER_RADIUS};
        padding: 13px 16px;
        font-size: 1rem;
        font-weight: 500;
        color: {T.TEXT_PRIMARY};
        transition: all 0.3s ease;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: {T.PRIMARY};
        box-shadow: 0 0 0 4px {T.PRIMARY_GLOW};
    }}
    .stButton > button {{
        width: 100%;
        background: {T.gold_gradient()};
        color: {T.TEXT_LIGHT};
        border: none;
        border-radius: {T.BORDER_RADIUS};
        padding: 14px 20px;
        font-size: 1.05rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: {T.SHADOW_MEDIUM};
        margin-top: 1rem;
        text-transform: uppercase;
    }}
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: {T.SHADOW_HOVER};
    }}
    .login-footer {{
        text-align: center;
        color: rgba(255,255,255,0.5);
        margin-top: 1.8rem;
        font-size: 0.85rem;
        font-weight: 500;
        letter-spacing: 0.04em;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-wrap">', unsafe_allow_html=True)

    logo_html = (f'<img src="data:image/png;base64,{LOGO_B64}" style="max-width:200px;height:auto;'
                 f'filter:drop-shadow(0 4px 12px rgba(184,134,11,0.4));">'
                 if LOGO_B64 else
                 '<div style="font-size:3rem;">🛍️</div>')

    st.markdown(f"""
    <div class="login-logo-card">
        {logo_html}
        <div class="login-title">Catalog Readiness Portal</div>
        <div class="login-sub">Merchandising Analytics Dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-form-card">', unsafe_allow_html=True)
    with st.form("login_form"):
        st.text_input("👤 Username", key="username", placeholder="Enter username")
        st.text_input("🔑 Password", type="password", key="password", placeholder="Enter password")
        if st.form_submit_button("🚀 Sign In to Dashboard"):
            _verify()
            if st.session_state.get("auth_ok"):
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="login-footer">
        🔒 Secure Access &nbsp;|&nbsp; Boutiqaat Merchandising Team
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    return False

# ── Guard ───────────────────────────────────────────────────────────────────
if not check_password():
    st.stop()

# ================================
# 🎨 GLOBAL CSS (post-login)
# ================================
def inject_global_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    * {{ font-family: {T.FONT_FAMILY}; }}
    #MainMenu, footer {{ visibility: hidden; }}

    /* ── Animated background ── */
    .stApp {{
        background: linear-gradient(160deg, #FFFEF9 0%, #FDF8EE 50%, #FAF3E0 100%);
        background-size: 400% 400%;
        animation: bgPulse 20s ease infinite;
    }}
    @keyframes bgPulse {{
        0%,100% {{ background-position: 0% 50%; }}
        50%      {{ background-position: 100% 50%; }}
    }}

    /* ── Content container ── */
    .block-container {{
        padding: 1.5rem 2.5rem;
        background: rgba(255,255,255,0.97);
        border-radius: {T.BORDER_RADIUS_LARGE};
        box-shadow: 0 20px 60px rgba(184,134,11,0.10);
        backdrop-filter: blur(20px);
        max-width: 1600px;
        border: 1px solid rgba(184,134,11,0.12);
    }}

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {{
        background: {T.gradient("#0F0F0F","#1C1500",180)} !important;
    }}
    section[data-testid="stSidebar"] * {{ color: {T.TEXT_LIGHT} !important; }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMultiSelect label {{
        color: {T.PRIMARY_LIGHT} !important;
        font-weight: 600 !important;
    }}

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
        background: {T.gold_gradient(90)};
        padding: 12px 16px;
        border-radius: {T.BORDER_RADIUS_LARGE};
        box-shadow: {T.SHADOW_MEDIUM};
    }}
    .stTabs [data-baseweb="tab"] {{
        background: rgba(255,255,255,0.15);
        color: white !important;
        border-radius: {T.BORDER_RADIUS};
        padding: 12px 22px;
        font-weight: 600;
        font-size: 0.95rem;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background: rgba(255,255,255,0.28);
        transform: translateY(-2px);
    }}
    .stTabs [aria-selected="true"] {{
        background: white !important;
        color: {T.PRIMARY_DARK} !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.2);
        transform: translateY(-2px);
    }}

    /* ── Buttons ── */
    .stButton > button {{
        background: {T.gold_gradient()};
        color: white;
        border: none;
        border-radius: {T.BORDER_RADIUS};
        padding: 12px 24px;
        font-weight: 700;
        font-size: 0.95rem;
        letter-spacing: 0.03em;
        transition: all 0.3s ease;
        box-shadow: {T.SHADOW_SMALL};
    }}
    .stButton > button:hover {{
        transform: translateY(-3px);
        box-shadow: {T.SHADOW_HOVER};
    }}

    /* ── Download button ── */
    div.stDownloadButton > button {{
        background: {T.gold_gradient()} !important;
        color: white !important;
        border: none !important;
        border-radius: {T.BORDER_RADIUS} !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        box-shadow: {T.SHADOW_SMALL} !important;
    }}
    div.stDownloadButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: {T.SHADOW_MEDIUM} !important;
    }}

    /* ── Metric widgets ── */
    [data-testid="stMetric"] {{
        background: {T.BG_CARD};
        border: 1px solid rgba(184,134,11,0.2);
        border-radius: {T.BORDER_RADIUS};
        padding: 14px;
        box-shadow: {T.SHADOW_SMALL};
    }}

    /* ── Animated main header ── */
    .main-header {{
        text-align: center;
        padding: 3rem 2rem;
        background: {T.gold_gradient(135)};
        border-radius: {T.BORDER_RADIUS_LARGE};
        margin-bottom: 2rem;
        box-shadow: {T.SHADOW_GLOW};
        position: relative;
        overflow: hidden;
        animation: slideDown 0.8s ease-out;
    }}
    .main-header::before {{
        content: '';
        position: absolute;
        top: -50%; left: -50%;
        width: 200%; height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, transparent 70%);
        animation: rotate 18s linear infinite;
    }}
    @keyframes rotate  {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    @keyframes slideDown {{ from {{ opacity:0; transform:translateY(-50px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes fadeInUp  {{ from {{ opacity:0; transform:translateY(30px); }} to {{ opacity:1; transform:translateY(0); }} }}

    .main-header h1 {{
        color: white;
        font-size: 2.8rem;
        font-weight: 900;
        margin: 0;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        letter-spacing: -0.5px;
        position: relative; z-index: 1;
    }}
    .main-header p {{
        color: rgba(255,255,255,0.92);
        font-size: 1.15rem;
        margin-top: 0.7rem;
        font-weight: 400;
        position: relative; z-index: 1;
    }}

    /* ── KPI cards ── */
    .kpi-card {{
        background: {T.gold_gradient(135)};
        padding: 1.8rem 1.4rem;
        border-radius: {T.BORDER_RADIUS_LARGE};
        box-shadow: 0 10px 30px rgba(184,134,11,0.35);
        text-align: center;
        transition: all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);
        animation: fadeInUp 0.6s ease-out;
        color: white;
        position: relative;
        overflow: hidden;
        cursor: pointer;
        min-height: 155px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.22), transparent);
        transition: left 0.55s;
    }}
    .kpi-card:hover::before {{ left: 100%; }}
    .kpi-card:hover {{
        transform: translateY(-14px) scale(1.04);
        box-shadow: 0 22px 55px rgba(184,134,11,0.55);
    }}
    .kpi-card .kpi-icon  {{ font-size: 2.4rem; margin-bottom: 0.5rem; filter: drop-shadow(0 3px 6px rgba(0,0,0,0.2)); }}
    .kpi-card .kpi-value {{ font-size: 2.2rem; font-weight: 900; text-shadow: 1px 1px 4px rgba(0,0,0,0.2); line-height:1.1; }}
    .kpi-card .kpi-label {{ font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.8px; opacity: 0.92; margin-top: 0.4rem; }}
    .kpi-card .kpi-sub   {{ font-size: 0.8rem; opacity: 0.8; margin-top: 0.3rem; }}

    /* ── Coloured KPI variants ── */
    .kpi-emerald {{ background: linear-gradient(135deg, #059669 0%, #10B981 100%); box-shadow: 0 10px 30px rgba(16,185,129,0.35); }}
    .kpi-amber   {{ background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%); box-shadow: 0 10px 30px rgba(245,158,11,0.35); }}
    .kpi-crimson {{ background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%); box-shadow: 0 10px 30px rgba(239,68,68,0.35); }}
    .kpi-sapphire{{ background: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%); box-shadow: 0 10px 30px rgba(59,130,246,0.35); }}
    .kpi-violet  {{ background: linear-gradient(135deg, #6D28D9 0%, #8B5CF6 100%); box-shadow: 0 10px 30px rgba(139,92,246,0.35); }}
    .kpi-teal    {{ background: linear-gradient(135deg, #0D9488 0%, #14B8A6 100%); box-shadow: 0 10px 30px rgba(20,184,166,0.35); }}
    .kpi-rose    {{ background: linear-gradient(135deg, #BE185D 0%, #F43F5E 100%); box-shadow: 0 10px 30px rgba(244,63,94,0.35); }}

    /* ── Insight boxes ── */
    .insight-box {{
        padding: 1.3rem 1.5rem;
        border-radius: {T.BORDER_RADIUS};
        margin-bottom: 1rem;
        box-shadow: {T.SHADOW_SMALL};
        animation: fadeInUp 0.5s ease-out;
    }}
    .insight-success {{ background: rgba(16,185,129,0.08); border-left: 5px solid {T.ACCENT_EMERALD}; }}
    .insight-warning {{ background: rgba(245,158,11,0.08); border-left: 5px solid {T.ACCENT_AMBER}; }}
    .insight-danger  {{ background: rgba(239,68,68,0.08);  border-left: 5px solid {T.ACCENT_CRIMSON}; }}
    .insight-info    {{ background: rgba(59,130,246,0.08); border-left: 5px solid {T.ACCENT_SAPPHIRE}; }}
    .insight-gold    {{ background: rgba(184,134,11,0.08); border-left: 5px solid {T.PRIMARY}; }}

    /* ── Score badge ── */
    .score-badge {{
        display: inline-block;
        padding: 4px 12px;
        border-radius: 50px;
        font-size: 0.82rem;
        font-weight: 700;
        letter-spacing: 0.03em;
    }}
    </style>
    """, unsafe_allow_html=True)

inject_global_css()

# ================================
# 🗂️ SIDEBAR — Logo + Info
# ================================
def render_sidebar():
    logo_html = (f'<img src="data:image/png;base64,{LOGO_B64}" '
                 f'style="max-width:160px;height:auto;display:block;margin:0 auto 1rem;'
                 f'filter:drop-shadow(0 3px 10px rgba(184,134,11,0.5));">'
                 if LOGO_B64 else '<div style="font-size:2.5rem;text-align:center;">🛍️</div>')

    st.sidebar.markdown(f"""
    <div style="
        background: {T.gradient('#1C1500','#2C2000',160)};
        border: 1px solid {T.PRIMARY};
        border-radius: {T.BORDER_RADIUS_LARGE};
        padding: 1.8rem 1.2rem;
        text-align: center;
        margin-bottom: 1.2rem;
        box-shadow: {T.SHADOW_GLOW};
    ">
        {logo_html}
        <div style="color:{T.PRIMARY_LIGHT};font-size:1rem;font-weight:700;letter-spacing:0.04em;">
            Catalog Readiness
        </div>
        <div style="color:rgba(255,255,255,0.5);font-size:0.78rem;margin-top:0.3rem;">
            Merchandising Analytics
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style="
        background:rgba(184,134,11,0.12);
        border:1px solid {T.PRIMARY};
        border-radius:{T.BORDER_RADIUS};
        padding:1rem;
        margin-bottom:1rem;
    ">
        <div style="color:{T.PRIMARY_LIGHT};font-size:0.8rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.5rem;">
            📋 Scoring Standard
        </div>
        <div style="color:rgba(255,255,255,0.75);font-size:0.78rem;line-height:1.7;">
            ✅ <b style="color:#10B981;">100</b> — Fully Ready<br>
            ⚠️ <b style="color:#F59E0B;">75–99</b> — Near Ready<br>
            🔵 <b style="color:#3B82F6;">50–74</b> — Partial<br>
            ❌ <b style="color:#EF4444;">&lt;50</b> — Incomplete
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

render_sidebar()

# ================================
# 📊 SCORING ENGINE
# ================================

# ── Skincare weights ────────────────────────────────────────────────────────
SKINCARE_WEIGHTS = {
    "Product Name":   20,
    "Manufacturer":   20,
    "Image Count":    20,
    "Formulation":     5,
    "Benefits":       10,
    "Recommended For":10,
    "Preferences":    10,
    "Size":            5,
}
SKINCARE_IMG_COL   = "Image Count"
SKINCARE_IMG_FIELD = "Image Count"

# ── Apparel weights ─────────────────────────────────────────────────────────
APPAREL_WEIGHTS = {
    "Product Name":  20,
    "Manufacturer":  20,
    "Images":        20,
    "Colour":        10,
    "Material":      10,
    "Apparel Fit":   20,
}
APPAREL_IMG_COL   = "Images"
APPAREL_IMG_FIELD = "Images"

IMG_THRESHOLD = 3   # ≥3 images → full image score

def image_score(raw_val, full_weight):
    """Graduated image scoring: proportional up to threshold, capped at full_weight."""
    try:
        count = int(float(str(raw_val).strip()))
    except (ValueError, TypeError):
        return 0.0
    if count <= 0:
        return 0.0
    return min(count / IMG_THRESHOLD, 1.0) * full_weight

def is_filled(val):
    """Return True if a field value is non-empty."""
    if val is None:
        return False
    s = str(val).strip()
    return s not in ("", "nan", "None", "NaN")

def score_row(row, weights, img_col):
    """Score a single product row. Returns (total_score, field_scores_dict, missing_fields_list)."""
    field_scores  = {}
    missing       = []
    total         = 0.0

    for field, weight in weights.items():
        val = row.get(field, "")

        if field == img_col:
            s = image_score(val, weight)
            field_scores[field] = round(s, 2)
            total += s
            if s < weight:
                missing.append(field)
        else:
            if is_filled(val):
                field_scores[field] = weight
                total += weight
            else:
                field_scores[field] = 0
                missing.append(field)

    return round(total, 2), field_scores, missing

def score_dataframe(df, weights, img_col, category_name):
    """Score all rows in a dataframe. Returns enriched dataframe."""
    records = []
    for _, row in df.iterrows():
        score, field_scores, missing = score_row(row.to_dict(), weights, img_col)
        rec = {
            "SKU":          str(row.get("SKU", row.name)),
            "Product Name": str(row.get("Product Name", "")),
            "Manufacturer": str(row.get("Manufacturer", "")),
            "Category":     category_name,
            "Score":        score,
            "Status":       T.score_label(score),
            "Missing Fields": ", ".join(missing) if missing else "—",
            "Missing Count":  len(missing),
        }
        rec.update({f"Score: {k}": v for k, v in field_scores.items()})
        records.append(rec)
    return pd.DataFrame(records)

# ================================
# 📂 DATA LOADING & SCORING
# ================================
@st.cache_data(show_spinner=False)
def load_and_score():
    """Load raw Excel data and compute all scores."""
    data_path = Path(__file__).parent / "Skin Care.xlsx"
    app_path  = Path(__file__).parent / "Apparel.xlsx"

    results = {}

    # ── Skincare ────────────────────────────────────────────────────────────
    try:
        sc_raw = pd.read_excel(data_path, sheet_name="data", engine="openpyxl")
        sc_raw.columns = sc_raw.columns.str.strip()
        sc_raw["Image Count"] = pd.to_numeric(sc_raw.get("Image Count", 0), errors="coerce").fillna(0)
        results["skincare_raw"] = sc_raw
        results["skincare_scored"] = score_dataframe(sc_raw, SKINCARE_WEIGHTS, SKINCARE_IMG_COL, "Skincare")
    except Exception as e:
        logger.error(f"Skincare load error: {e}")
        results["skincare_raw"]    = pd.DataFrame()
        results["skincare_scored"] = pd.DataFrame()

    # ── Apparel ─────────────────────────────────────────────────────────────
    try:
        ap_raw = pd.read_excel(app_path, sheet_name="data", engine="openpyxl")
        ap_raw.columns = ap_raw.columns.str.strip()
        ap_raw["Images"] = pd.to_numeric(ap_raw.get("Images", 0), errors="coerce").fillna(0)
        results["apparel_raw"]    = ap_raw
        results["apparel_scored"] = score_dataframe(ap_raw, APPAREL_WEIGHTS, APPAREL_IMG_COL, "Apparel")
    except Exception as e:
        logger.error(f"Apparel load error: {e}")
        results["apparel_raw"]    = pd.DataFrame()
        results["apparel_scored"] = pd.DataFrame()

    # ── Combined ────────────────────────────────────────────────────────────
    frames = [f for f in [results["skincare_scored"], results["apparel_scored"]] if not f.empty]
    results["combined"] = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()

    return results

with st.spinner("⚡ Loading & scoring catalog data..."):
    DATA = load_and_score()

sc_scored  = DATA["skincare_scored"]
ap_scored  = DATA["apparel_scored"]
combined   = DATA["combined"]
sc_raw     = DATA["skincare_raw"]
ap_raw     = DATA["apparel_raw"]

# ================================
# 🧩 SHARED UI COMPONENTS
# ================================

def kpi_card(icon, value, label, variant="gold", subtitle=None):
    sub_html = f'<div class="kpi-sub">{subtitle}</div>' if subtitle else ""
    return f"""
    <div class="kpi-card {variant}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-label">{label}</div>
        {sub_html}
    </div>"""

def section_header(title, subtitle=""):
    sub = f'<p style="color:{T.TEXT_SECONDARY};margin:0.4rem 0 0;font-size:0.95rem;">{subtitle}</p>' if subtitle else ""
    return f"""
    <div style="
        padding:1.4rem 1.8rem;
        background:{T.gradient('rgba(184,134,11,0.06)','rgba(184,134,11,0.02)',135)};
        border-radius:{T.BORDER_RADIUS};
        border-left:5px solid {T.PRIMARY};
        margin-bottom:1.4rem;
        box-shadow:{T.SHADOW_SMALL};
    ">
        <h3 style="color:{T.PRIMARY_DARK};margin:0;font-size:1.35rem;font-weight:800;">{title}</h3>
        {sub}
    </div>"""

def display_table(df, title=None, download_name=None, scrollable=True,
                  max_height="520px", align="center", max_rows=None):
    """Render a styled Boutiqaat-branded HTML table."""
    if df is None or df.empty:
        st.warning("⚠️ No data to display.")
        return

    display_df = df.head(max_rows).copy() if max_rows else df.copy()

    if title:
        st.markdown(f'<h4 style="color:{T.PRIMARY_DARK};font-weight:800;margin-bottom:0.6rem;">{title}</h4>',
                    unsafe_allow_html=True)

    scroll_css = f"""
        overflow-x: auto;
        overflow-y: auto;
        max-height: {max_height};
        border: 2px solid {T.PRIMARY};
        border-radius: {T.BORDER_RADIUS};
        box-shadow: {T.SHADOW_MEDIUM};
    """ if scrollable else f"""
        border: 2px solid {T.PRIMARY};
        border-radius: {T.BORDER_RADIUS};
        box-shadow: {T.SHADOW_MEDIUM};
        overflow-x: auto;
    """

    html = f"""
    <style>
    .bq-table {{ width:100%; border-collapse:collapse; font-size:14px; background:white; }}
    .bq-table thead tr {{
        background: {T.gold_gradient(135)};
        color: white;
        position: sticky; top: 0; z-index: 10;
    }}
    .bq-table th {{
        padding: 11px 14px; border: 1px solid {T.PRIMARY_DARK};
        font-size: 13px; font-weight: 700; letter-spacing: 0.4px;
        white-space: nowrap; text-align: center;
    }}
    .bq-table tbody tr:nth-child(odd)  {{ background: #FFFEF9; }}
    .bq-table tbody tr:nth-child(even) {{ background: #FDF8EE; }}
    .bq-table tbody tr:hover {{
        background: rgba(184,134,11,0.10) !important;
        transition: background 0.2s;
    }}
    .bq-table td {{
        padding: 9px 13px;
        border: 1px solid rgba(184,134,11,0.18);
        color: {T.TEXT_PRIMARY};
        font-size: 13px; font-weight: 500;
        text-align: {align};
        vertical-align: middle;
        word-break: break-word;
    }}
    .bq-table td:first-child {{ 
        color:{T.PRIMARY_DARK}; 
        font-weight:700; 
        white-space:nowrap;
        min-width:120px;
    }}
    </style>
    <div style="{scroll_css}">
    <table class="bq-table">
    <thead><tr>{"".join(f"<th>{c}</th>" for c in display_df.columns)}</tr></thead>
    <tbody>
    """
    for _, row in display_df.iterrows():
        html += "<tr>"
        for val in row:
            cell = "" if pd.isna(val) else str(val)
            html += f'<td style="text-align:{align};">{cell}</td>'
        html += "</tr>"
    html += "</tbody></table></div>"

    st.markdown(html, unsafe_allow_html=True)

    if max_rows and len(df) > max_rows:
        st.caption(f"📊 Showing {max_rows} of {len(df):,} rows")

    if download_name:
        st.download_button(
            f"📥 Download {download_name}",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=download_name,
            mime="text/csv",
            key=f"dl_{download_name}_{id(df)}"
        )

def plotly_layout(fig, title="", height=480):
    """Apply unified Boutiqaat Plotly theme."""
    fig.update_layout(
        title=dict(
            text=f'<b style="color:{T.PRIMARY_DARK};font-size:17px;">{title}</b>',
            x=0.01, xanchor="left"
        ),
        plot_bgcolor="rgba(253,248,238,0.7)",
        paper_bgcolor="rgba(255,254,249,0.9)",
        font=dict(color=T.TEXT_PRIMARY, family=T.FONT_FAMILY, size=12),
        height=height,
        margin=dict(l=50, r=30, t=70, b=60),
        hovermode="x unified",
        legend=dict(
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=T.PRIMARY_LIGHT,
            borderwidth=1,
            font=dict(size=12)
        )
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(184,134,11,0.10)",
                     linecolor=T.PRIMARY_LIGHT, tickfont=dict(size=11))
    fig.update_yaxes(showgrid=True, gridcolor="rgba(184,134,11,0.10)",
                     linecolor=T.PRIMARY_LIGHT, tickfont=dict(size=11))
    return fig

# ── Colour palette for charts ────────────────────────────────────────────────
CHART_COLORS = [
    T.PRIMARY, T.ACCENT_EMERALD, T.ACCENT_SAPPHIRE, T.ACCENT_VIOLET,
    T.ACCENT_AMBER, T.ACCENT_ROSE, T.ACCENT_TEAL, T.ACCENT_CRIMSON,
    "#F97316", "#06B6D4", "#84CC16", "#EC4899"
]

# ================================
# 📊 MAIN DASHBOARD HEADER
# ================================
logo_html_header = (
    f'<img src="data:image/png;base64,{LOGO_B64}" '
    f'style="max-height:60px;width:auto;vertical-align:middle;'
    f'filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3));">'
    if LOGO_B64 else "🛍️"
)

st.markdown(f"""
<div class="main-header">
    <div style="position:relative;z-index:1;">
        {logo_html_header}
        <h1 style="margin-top:0.8rem;">Catalog Readiness Report</h1>
        <p>eCommerce Merchandising Analytics &nbsp;•&nbsp; Skincare &amp; Apparel &nbsp;•&nbsp;
           {len(combined):,} SKUs Analyzed</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ================================
# 📑 TABS
# ================================
(tab_guide,
 tab_exec,
 tab_category,
 tab_sku,
 tab_insights) = st.tabs([
    "📖 User Guide",
    "📊 Executive Summary",
    "🗂️ Category Breakdown",
    "🔍 SKU Drill-Down",
    "💡 Insights & Recommendations",
])

# ============================================================
# TAB 0 — USER GUIDE / TECHNICAL DOCUMENTATION
# ============================================================
with tab_guide:
    st.markdown(section_header(
        "📖 User Guide & Technical Documentation",
        "Everything you need to understand, navigate, and interpret this dashboard"
    ), unsafe_allow_html=True)

    col_g1, col_g2 = st.columns([1.1, 0.9])

    with col_g1:
        st.markdown(f"""
        <div class="insight-box insight-gold">
            <h4 style="color:{T.PRIMARY_DARK};margin-top:0;">🎯 Purpose</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;">
            This dashboard evaluates whether each product SKU across <strong>Skincare</strong>
            and <strong>Apparel</strong> categories is <em>ready to be published</em> on the
            Boutiqaat website. A <strong>Catalog Readiness Score</strong> (0–100) is computed
            for every SKU based on the completeness of key data fields, weighted by their
            business importance.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-box insight-info">
            <h4 style="color:{T.ACCENT_SAPPHIRE};margin-top:0;">🧮 Scoring Methodology</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin-bottom:0.6rem;">
            Each field contributes a weighted score. A field is considered
            <em>filled</em> if it contains a non-empty, non-null value.
            </p>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;">
            <strong>Image Count</strong> uses a <em>graduated</em> scale:
            </p>
            <ul style="color:{T.TEXT_PRIMARY};line-height:2;margin:0.4rem 0 0 1rem;">
                <li>0 images → <strong>0 pts</strong> (hard blocker)</li>
                <li>1 image  → <strong>⅓ × weight</strong></li>
                <li>2 images → <strong>⅔ × weight</strong></li>
                <li>≥3 images → <strong>full weight ✅</strong> (catalog standard)</li>
                <li>4–5 images → <strong>full weight</strong> (no bonus — score capped at 100)</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="insight-box insight-success">
            <h4 style="color:{T.ACCENT_EMERALD};margin-top:0;">🚦 Readiness Status Thresholds</h4>
            <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
                <tr style="background:rgba(16,185,129,0.1);">
                    <td style="padding:8px 12px;font-weight:700;color:{T.ACCENT_EMERALD};">✅ Fully Ready</td>
                    <td style="padding:8px 12px;">Score = 100</td>
                    <td style="padding:8px 12px;">All fields complete — safe to publish</td>
                </tr>
                <tr style="background:rgba(245,158,11,0.08);">
                    <td style="padding:8px 12px;font-weight:700;color:{T.ACCENT_AMBER};">⚠️ Near Ready</td>
                    <td style="padding:8px 12px;">75 – 99</td>
                    <td style="padding:8px 12px;">Minor gaps — review before publishing</td>
                </tr>
                <tr style="background:rgba(59,130,246,0.08);">
                    <td style="padding:8px 12px;font-weight:700;color:{T.ACCENT_SAPPHIRE};">🔵 Partial</td>
                    <td style="padding:8px 12px;">50 – 74</td>
                    <td style="padding:8px 12px;">Significant gaps — enrichment needed</td>
                </tr>
                <tr style="background:rgba(239,68,68,0.08);">
                    <td style="padding:8px 12px;font-weight:700;color:{T.ACCENT_CRIMSON};">❌ Incomplete</td>
                    <td style="padding:8px 12px;">&lt; 50</td>
                    <td style="padding:8px 12px;">Critical gaps — do not publish</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    with col_g2:
        # ── Skincare Field Weights ──────────────────────────────────────────
        sc_rows = ""
        for i, (field, w) in enumerate(SKINCARE_WEIGHTS.items()):
            bg   = "rgba(184,134,11,0.06)" if i % 2 == 0 else "white"
            note = " 🖼️ graduated" if field == SKINCARE_IMG_FIELD else ""
            sc_rows += f"""
            <tr style="background:{bg};">
                <td style="padding:7px 10px;font-weight:600;">{field}{note}</td>
                <td style="padding:7px 10px;text-align:center;font-weight:700;color:{T.PRIMARY_DARK};">{w}</td>
                <td style="padding:7px 10px;text-align:center;">{w}%</td>
            </tr>"""

        # ── Apparel Field Weights ───────────────────────────────────────────
        ap_rows = ""
        for i, (field, w) in enumerate(APPAREL_WEIGHTS.items()):
            bg   = "rgba(59,130,246,0.05)" if i % 2 == 0 else "white"
            note = " 🖼️ graduated" if field == APPAREL_IMG_FIELD else ""
            ap_rows += f"""
            <tr style="background:{bg};">
                <td style="padding:7px 10px;font-weight:600;">{field}{note}</td>
                <td style="padding:7px 10px;text-align:center;font-weight:700;color:{T.ACCENT_SAPPHIRE};">{w}</td>
                <td style="padding:7px 10px;text-align:center;">{w}%</td>
            </tr>"""

        st.markdown(f"""
        <div class="insight-box insight-gold">
            <h4 style="color:{T.PRIMARY_DARK};margin-top:0;">⚖️ Skincare Field Weights</h4>
            <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
                <tr style="background:{T.gold_gradient(90)};color:white;">
                    <th style="padding:7px 10px;text-align:left;">Field</th>
                    <th style="padding:7px 10px;text-align:center;">Weight</th>
                    <th style="padding:7px 10px;text-align:center;">% of Score</th>
                </tr>
                {sc_rows}
                <tr style="background:rgba(184,134,11,0.15);font-weight:800;">
                    <td style="padding:8px 10px;">TOTAL</td>
                    <td style="padding:8px 10px;text-align:center;">100</td>
                    <td style="padding:8px 10px;text-align:center;">100%</td>
                </tr>
            </table>
        </div>

        <div class="insight-box insight-info">
            <h4 style="color:{T.ACCENT_SAPPHIRE};margin-top:0;">⚖️ Apparel Field Weights</h4>
            <table style="width:100%;border-collapse:collapse;font-size:0.88rem;">
                <tr style="background:linear-gradient(90deg,{T.ACCENT_SAPPHIRE},{T.ACCENT_VIOLET});color:white;">
                    <th style="padding:7px 10px;text-align:left;">Field</th>
                    <th style="padding:7px 10px;text-align:center;">Weight</th>
                    <th style="padding:7px 10px;text-align:center;">% of Score</th>
                </tr>
                {ap_rows}
                <tr style="background:rgba(59,130,246,0.12);font-weight:800;">
                    <td style="padding:8px 10px;">TOTAL</td>
                    <td style="padding:8px 10px;text-align:center;">100</td>
                    <td style="padding:8px 10px;text-align:center;">100%</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"""
    <div class="insight-box insight-gold">
        <h4 style="color:{T.PRIMARY_DARK};margin-top:0;">🗺️ Dashboard Navigation</h4>
        <table style="width:100%;border-collapse:collapse;font-size:0.9rem;">
            <tr style="background:{T.gold_gradient(90)};color:white;">
                <th style="padding:9px 14px;text-align:left;">Tab</th>
                <th style="padding:9px 14px;text-align:left;">What You'll Find</th>
            </tr>
            <tr style="background:rgba(184,134,11,0.05);">
                <td style="padding:9px 14px;font-weight:700;">📖 User Guide</td>
                <td style="padding:9px 14px;">Scoring logic, field weights, thresholds, navigation guide (you are here)</td>
            </tr>
            <tr>
                <td style="padding:9px 14px;font-weight:700;">📊 Executive Summary</td>
                <td style="padding:9px 14px;">Overall KPIs, readiness % across both categories, status breakdown</td>
            </tr>
            <tr style="background:rgba(184,134,11,0.05);">
                <td style="padding:9px 14px;font-weight:700;">🗂️ Category Breakdown</td>
                <td style="padding:9px 14px;">Skincare vs Apparel comparison, score distribution, field completion heatmap</td>
            </tr>
            <tr>
                <td style="padding:9px 14px;font-weight:700;">🔍 SKU Drill-Down</td>
                <td style="padding:9px 14px;">Full scored SKU table with filters, color-coded status, missing fields detail</td>
            </tr>
            <tr style="background:rgba(184,134,11,0.05);">
                <td style="padding:9px 14px;font-weight:700;">💡 Insights & Recommendations</td>
                <td style="padding:9px 14px;">Top gaps, manufacturer readiness, actionable next steps</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# TAB 1 — EXECUTIVE SUMMARY
# ============================================================
with tab_exec:
    st.markdown(section_header(
        "📊 Executive Summary",
        "Overall catalog readiness across Skincare & Apparel — at a glance"
    ), unsafe_allow_html=True)

    if combined.empty:
        st.error("❌ No data loaded. Please ensure Skin Care.xlsx and Apparel.xlsx are in the same folder.")
        st.stop()

    # ── Aggregate metrics ────────────────────────────────────────────────────
    total_skus   = len(combined)
    sc_count     = len(sc_scored)
    ap_count     = len(ap_scored)
    fully_ready  = int((combined["Score"] == 100).sum())
    near_ready   = int(((combined["Score"] >= 75) & (combined["Score"] < 100)).sum())
    partial      = int(((combined["Score"] >= 50) & (combined["Score"] < 75)).sum())
    incomplete   = int((combined["Score"] < 50).sum())
    avg_score    = combined["Score"].mean()
    pct_ready    = fully_ready / total_skus * 100 if total_skus else 0
    pct_attention= (total_skus - fully_ready) / total_skus * 100 if total_skus else 0

    sc_avg = sc_scored["Score"].mean() if not sc_scored.empty else 0
    ap_avg = ap_scored["Score"].mean() if not ap_scored.empty else 0
    sc_ready = int((sc_scored["Score"] == 100).sum()) if not sc_scored.empty else 0
    ap_ready = int((ap_scored["Score"] == 100).sum()) if not ap_scored.empty else 0

    # ── Hero banner ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="
        text-align:center;
        padding:2.2rem 2rem;
        background:{T.gradient('rgba(184,134,11,0.06)','rgba(184,134,11,0.02)',135)};
        border-radius:{T.BORDER_RADIUS_LARGE};
        border:2px solid rgba(184,134,11,0.2);
        margin-bottom:1.8rem;
        box-shadow:{T.SHADOW_SMALL};
    ">
        <h2 style="color:{T.PRIMARY_DARK};margin:0;font-size:2rem;font-weight:900;">
            🛍️ Boutiqaat Catalog Readiness Report
        </h2>
        <p style="color:{T.TEXT_SECONDARY};margin:0.6rem 0 0;font-size:1rem;">
            Combined analysis of <strong>{total_skus:,} SKUs</strong> across
            <strong>Skincare</strong> ({sc_count}) and <strong>Apparel</strong> ({ap_count}) categories
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI Row 1 ────────────────────────────────────────────────────────────
    st.markdown("### 🔢 Overall KPIs")
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        st.markdown(kpi_card("📦", fmt_num(total_skus), "Total SKUs", "gold"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("✅", fmt_num(fully_ready), "Fully Ready",
                             "emerald", f"{pct_ready:.1f}% of catalog"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("⚠️", fmt_num(near_ready), "Near Ready",
                             "amber", "Score 75–99"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("🔵", fmt_num(partial), "Partial",
                            "sapphire", "Score 50–74"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("📈", f"{avg_score:.1f}", "Avg Score",
                             "sapphire", "Out of 100"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPI Row 2 — Category split ───────────────────────────────────────────
    st.markdown("### 🗂️ Category KPIs")
    cc1, cc2, cc3, cc4 = st.columns(4)

    with cc1:
        st.markdown(kpi_card("💄", fmt_num(sc_count), "Skincare SKUs", "rose"), unsafe_allow_html=True)
    with cc2:
        st.markdown(kpi_card("📊", f"{sc_avg:.1f}", "Skincare Avg Score",
                             "rose", f"{sc_ready} fully ready"), unsafe_allow_html=True)
    with cc3:
        st.markdown(kpi_card("👕", fmt_num(ap_count), "Apparel SKUs", "teal"), unsafe_allow_html=True)
    with cc4:
        st.markdown(kpi_card("📊", f"{ap_avg:.1f}", "Apparel Avg Score",
                             "teal", f"{ap_ready} fully ready"), unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts row ───────────────────────────────────────────────────────────
    st.markdown("### 📈 Readiness Visualizations")
    ch1, ch2 = st.columns(2)

    with ch1:
        # Donut — overall status breakdown
        status_counts = combined["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        status_color_map = {
            "✅ Fully Ready":  T.ACCENT_EMERALD,
            "⚠️ Near Ready":   T.ACCENT_AMBER,
            "🔵 Partial":      T.ACCENT_SAPPHIRE,
            "❌ Incomplete":   T.ACCENT_CRIMSON,
        }
        donut_colors = [status_color_map.get(s, T.PRIMARY) for s in status_counts["Status"]]

        fig_donut = go.Figure(go.Pie(
            labels=status_counts["Status"],
            values=status_counts["Count"],
            hole=0.55,
            marker=dict(colors=donut_colors, line=dict(color="white", width=3)),
            textinfo="label+percent",
            textposition="outside",
            textfont=dict(size=13, family=T.FONT_FAMILY, color=T.TEXT_PRIMARY),
            hovertemplate="<b>%{label}</b><br>SKUs: %{value:,}<br>Share: %{percent}<extra></extra>",
            pull=[0.04 if s == "✅ Fully Ready" else 0 for s in status_counts["Status"]],
        ))
        fig_donut.add_annotation(
            text=f"<b>{pct_ready:.0f}%</b><br><span style='font-size:11px'>Ready</span>",
            x=0.5, y=0.5, font_size=22, showarrow=False,
            font=dict(color=T.ACCENT_EMERALD, family=T.FONT_FAMILY)
        )
        fig_donut = plotly_layout(fig_donut, "🍩 Overall Readiness Status Distribution", height=420)
        fig_donut.update_layout(showlegend=True,
                                legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"))
        st.plotly_chart(fig_donut, use_container_width=True)

    with ch2:
        # Grouped bar — Skincare vs Apparel status comparison
        def status_breakdown(df):
            order = ["✅ Fully Ready", "⚠️ Near Ready", "🔵 Partial", "❌ Incomplete"]
            counts = df["Status"].value_counts()
            return [int(counts.get(s, 0)) for s in order]

        statuses = ["✅ Fully Ready", "⚠️ Near Ready", "🔵 Partial", "❌ Incomplete"]
        sc_vals  = status_breakdown(sc_scored)
        ap_vals  = status_breakdown(ap_scored)

        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            name="💄 Skincare", x=statuses, y=sc_vals,
            marker_color=T.ACCENT_ROSE,
            text=[str(v) for v in sc_vals], textposition="outside",
            textfont=dict(size=13, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
            hovertemplate="<b>Skincare</b><br>%{x}: %{y} SKUs<extra></extra>",
        ))
        fig_bar.add_trace(go.Bar(
            name="👕 Apparel", x=statuses, y=ap_vals,
            marker_color=T.ACCENT_TEAL,
            text=[str(v) for v in ap_vals], textposition="outside",
            textfont=dict(size=13, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
            hovertemplate="<b>Apparel</b><br>%{x}: %{y} SKUs<extra></extra>",
        ))
        fig_bar = plotly_layout(fig_bar, "📊 Skincare vs Apparel — Status Breakdown", height=420)
        fig_bar.update_layout(barmode="group", bargap=0.25, bargroupgap=0.08)
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ── Score distribution histogram ─────────────────────────────────────────
    st.markdown("### 📉 Score Distribution")
    col_hist1, col_hist2 = st.columns([2, 1])

    with col_hist1:
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=sc_scored["Score"], name="💄 Skincare",
            nbinsx=20, marker_color=T.ACCENT_ROSE, opacity=0.80,
            hovertemplate="Score: %{x}<br>Count: %{y}<extra>Skincare</extra>",
        ))
        fig_hist.add_trace(go.Histogram(
            x=ap_scored["Score"], name="👕 Apparel",
            nbinsx=20, marker_color=T.ACCENT_TEAL, opacity=0.80,
            hovertemplate="Score: %{x}<br>Count: %{y}<extra>Apparel</extra>",
        ))
        # Threshold lines
        for thresh, label, color in [
            (100, "Fully Ready", T.ACCENT_EMERALD),
            (75,  "Near Ready",  T.ACCENT_AMBER),
            (50,  "Partial",     T.ACCENT_SAPPHIRE),
        ]:
            fig_hist.add_vline(
                x=thresh, line_dash="dash", line_color=color, line_width=2,
                annotation_text=label,
                annotation_position="top right",
                annotation_font=dict(size=11, color=color, family=T.FONT_FAMILY)
            )
        fig_hist = plotly_layout(fig_hist, "📉 Score Distribution by Category", height=380)
        fig_hist.update_layout(barmode="overlay", bargap=0.05)
        fig_hist.update_xaxes(title_text="Readiness Score", range=[0, 105])
        fig_hist.update_yaxes(title_text="Number of SKUs")
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_hist2:
        # Score bucket summary table
        def bucket_summary(df, label):
            return {
                "Category":     label,
                "Total SKUs":   len(df),
                "Avg Score":    f"{df['Score'].mean():.1f}",
                "Fully Ready":  int((df["Score"] == 100).sum()),
                "Near Ready":   int(((df["Score"] >= 75) & (df["Score"] < 100)).sum()),
                "Partial":      int(((df["Score"] >= 50) & (df["Score"] < 75)).sum()),
                "Incomplete":   int((df["Score"] < 50).sum()),
            }

        summary_rows = []
        if not sc_scored.empty: summary_rows.append(bucket_summary(sc_scored, "💄 Skincare"))
        if not ap_scored.empty: summary_rows.append(bucket_summary(ap_scored, "👕 Apparel"))
        combined_row = {
            "Category":    "🛍️ Combined",
            "Total SKUs":  total_skus,
            "Avg Score":   f"{avg_score:.1f}",
            "Fully Ready": fully_ready,
            "Near Ready":  near_ready,
            "Partial":     partial,
            "Incomplete":  incomplete,
        }
        summary_rows.append(combined_row)
        summary_df = pd.DataFrame(summary_rows)

        display_table(
            summary_df,
            title="📋 Score Bucket Summary",
            download_name="score_summary.csv",
            scrollable=False,
            align="center"
        )

    st.markdown("---")

    # ── Readiness gauge ──────────────────────────────────────────────────────
    st.markdown("### 🎯 Catalog Readiness Gauge")
    g1, g2, g3 = st.columns(3)

    def gauge_chart(value, title, color, ref_value=None):
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta" if ref_value else "gauge+number",
            value=value,
            delta={"reference": ref_value, "valueformat": ".1f"} if ref_value else None,
            number={"suffix": "%", "font": {"size": 36, "color": color, "family": T.FONT_FAMILY}},
            title={"text": f"<b>{title}</b>",
                   "font": {"size": 14, "color": T.TEXT_PRIMARY, "family": T.FONT_FAMILY}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1,
                         "tickcolor": T.TEXT_SECONDARY, "tickfont": {"size": 10}},
                "bar":  {"color": color, "thickness": 0.28},
                "bgcolor": "rgba(253,248,238,0.8)",
                "borderwidth": 2,
                "bordercolor": T.PRIMARY_LIGHT,
                "steps": [
                    {"range": [0,  50], "color": "rgba(239,68,68,0.12)"},
                    {"range": [50, 75], "color": "rgba(59,130,246,0.12)"},
                    {"range": [75, 100],"color": "rgba(16,185,129,0.12)"},
                ],
                "threshold": {
                    "line": {"color": T.PRIMARY_DARK, "width": 3},
                    "thickness": 0.8,
                    "value": 75
                }
            }
        ))
        fig.update_layout(
            height=260,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor="rgba(255,254,249,0.9)",
            font=dict(family=T.FONT_FAMILY)
        )
        return fig

    with g1:
        sc_pct_ready = sc_ready / sc_count * 100 if sc_count else 0
        st.plotly_chart(gauge_chart(sc_pct_ready, "💄 Skincare % Fully Ready",
                                    T.ACCENT_ROSE), use_container_width=True)
    with g2:
        st.plotly_chart(gauge_chart(pct_ready, "🛍️ Overall % Fully Ready",
                                    T.PRIMARY, ref_value=75), use_container_width=True)
    with g3:
        ap_pct_ready = ap_ready / ap_count * 100 if ap_count else 0
        st.plotly_chart(gauge_chart(ap_pct_ready, "👕 Apparel % Fully Ready",
                                    T.ACCENT_TEAL), use_container_width=True)

    st.markdown("---")

    # ── Executive insight cards ──────────────────────────────────────────────
    st.markdown("### 💡 Executive Highlights")
    ei1, ei2 = st.columns(2)

    with ei1:
        best_cat  = "Skincare" if sc_avg >= ap_avg else "Apparel"
        best_avg  = max(sc_avg, ap_avg)
        worst_cat = "Skincare" if sc_avg < ap_avg else "Apparel"
        worst_avg = min(sc_avg, ap_avg)

        st.markdown(f"""
        <div class="insight-box insight-success">
            <h4 style="color:{T.ACCENT_EMERALD};margin-top:0;">🏆 Strongest Category</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;">
            <strong>{best_cat}</strong> leads with an average readiness score of
            <strong>{best_avg:.1f}/100</strong>. This category is closest to full catalog
            readiness and requires the least enrichment effort.
            </p>
        </div>
        <div class="insight-box insight-danger">
            <h4 style="color:{T.ACCENT_CRIMSON};margin-top:0;">⚠️ Needs Most Attention</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;">
            <strong>{worst_cat}</strong> has an average score of
            <strong>{worst_avg:.1f}/100</strong>. Prioritise data enrichment here
            before the next publishing cycle.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with ei2:
        st.markdown(f"""
        <div class="insight-box insight-warning">
            <h4 style="color:{T.ACCENT_AMBER};margin-top:0;">📋 Readiness at a Glance</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.9;margin:0;">
            ✅ <strong>{fully_ready}</strong> SKUs ({pct_ready:.1f}%) are <em>fully ready</em> to publish.<br>
            ⚠️ <strong>{near_ready}</strong> SKUs need minor fixes to reach 100.<br>
            🔵 <strong>{partial}</strong> SKUs require significant enrichment.<br>
            ❌ <strong>{incomplete}</strong> SKUs are critical — do not publish.
            </p>
        </div>
        <div class="insight-box insight-info">
            <h4 style="color:{T.ACCENT_SAPPHIRE};margin-top:0;">🎯 Quick Win Opportunity</h4>
            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;">
            <strong>{near_ready}</strong> SKUs are within reach of 100 — fixing just
            1–2 fields per SKU could push them to fully ready, immediately improving
            catalog quality without heavy effort.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TAB 2 — CATEGORY BREAKDOWN
# ============================================================
with tab_category:
    st.markdown(section_header(
        "🗂️ Category Breakdown",
        "Deep-dive comparison: Skincare vs Apparel — score distributions, field completion heatmap"
    ), unsafe_allow_html=True)

    # ── Category selector ────────────────────────────────────────────────────
    cat_sel = st.radio(
        "🔎 View Category",
        ["🛍️ Combined", "💄 Skincare", "👕 Apparel"],
        horizontal=True, key="cat_radio"
    )

    if cat_sel == "💄 Skincare":
        view_df    = sc_scored
        view_raw   = sc_raw
        view_weights = SKINCARE_WEIGHTS
        view_img   = SKINCARE_IMG_COL
        cat_color  = T.ACCENT_ROSE
        cat_label  = "Skincare"
    elif cat_sel == "👕 Apparel":
        view_df    = ap_scored
        view_raw   = ap_raw
        view_weights = APPAREL_WEIGHTS
        view_img   = APPAREL_IMG_COL
        cat_color  = T.ACCENT_TEAL
        cat_label  = "Apparel"
    else:
        view_df    = combined
        view_raw   = pd.concat([sc_raw, ap_raw], ignore_index=True)
        view_weights = {**SKINCARE_WEIGHTS, **APPAREL_WEIGHTS}
        view_img   = None
        cat_color  = T.PRIMARY
        cat_label  = "Combined"

    if view_df.empty:
        st.warning("⚠️ No data available for this selection.")
    else:
        # ── Score distribution ───────────────────────────────────────────────
        st.markdown("#### 📊 Score Distribution")
        sd1, sd2 = st.columns([3, 1])

        with sd1:
            bins   = [0, 25, 50, 75, 90, 100]
            labels = ["0–24", "25–49", "50–74", "75–89", "90–100"]
            view_df["Score Bucket"] = pd.cut(
                view_df["Score"], bins=bins, labels=labels, include_lowest=True
            )
            bucket_counts = view_df["Score Bucket"].value_counts().reindex(labels, fill_value=0)

            bucket_colors = [T.ACCENT_CRIMSON, T.ACCENT_CRIMSON,
                             T.ACCENT_SAPPHIRE, T.ACCENT_AMBER, T.ACCENT_EMERALD]

            fig_bucket = go.Figure(go.Bar(
                x=bucket_counts.index.tolist(),
                y=bucket_counts.values.tolist(),
                marker_color=bucket_colors,
                marker_line=dict(color="white", width=2),
                text=[str(v) for v in bucket_counts.values],
                textposition="outside",
                textfont=dict(size=14, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
                hovertemplate="Score Range: <b>%{x}</b><br>SKUs: <b>%{y}</b><extra></extra>",
            ))
            fig_bucket = plotly_layout(
                fig_bucket,
                f"📊 {cat_label} — SKU Count by Score Bucket",
                height=380
            )
            fig_bucket.update_xaxes(title_text="Score Range")
            fig_bucket.update_yaxes(title_text="Number of SKUs")
            st.plotly_chart(fig_bucket, use_container_width=True)

        with sd2:
            bucket_pct = (bucket_counts / len(view_df) * 100).round(1)
            bucket_table = pd.DataFrame({
                "Score Range": labels,
                "SKUs":        bucket_counts.values,
                "% of Total":  [f"{v}%" for v in bucket_pct.values],
            })
            display_table(
                bucket_table,
                title="📋 Bucket Breakdown",
                scrollable=False,
                align="center"
            )

        st.markdown("---")

        # ── Field completion heatmap ─────────────────────────────────────────
        st.markdown("#### 🔥 Field Completion Heatmap")
        st.markdown(
            f'<p style="color:{T.TEXT_SECONDARY};font-size:0.9rem;margin-bottom:1rem;">'
            "Shows the % of SKUs where each field is <strong>filled</strong>. "
            "Darker = more complete. Red cells highlight critical gaps.</p>",
            unsafe_allow_html=True
        )

        def field_completion(df_raw, weights):
            result = {}
            for field in weights.keys():
                if field in df_raw.columns:
                    filled = df_raw[field].apply(
                        lambda v: is_filled(v) if field != view_img
                        else (pd.to_numeric(v, errors="coerce") or 0) > 0
                    ).sum()
                    result[field] = round(filled / len(df_raw) * 100, 1) if len(df_raw) else 0
                else:
                    result[field] = 0.0
            return result

        if cat_sel == "🛍️ Combined":
            sc_comp = field_completion(sc_raw, SKINCARE_WEIGHTS)
            ap_comp = field_completion(ap_raw, APPAREL_WEIGHTS)
            all_fields = sorted(set(list(sc_comp.keys()) + list(ap_comp.keys())))
            heatmap_data = pd.DataFrame({
                "💄 Skincare": [sc_comp.get(f, None) for f in all_fields],
                "👕 Apparel":  [ap_comp.get(f, None) for f in all_fields],
            }, index=all_fields)
        else:
            comp = field_completion(view_raw, view_weights)
            heatmap_data = pd.DataFrame(
                {cat_label: list(comp.values())},
                index=list(comp.keys())
            )

        fig_heat = go.Figure(go.Heatmap(
            z=heatmap_data.values.tolist(),
            x=heatmap_data.columns.tolist(),
            y=heatmap_data.index.tolist(),
            colorscale=[
                [0.0,  "#EF4444"],
                [0.5,  "#F59E0B"],
                [0.75, "#10B981"],
                [1.0,  "#059669"],
            ],
            zmin=0, zmax=100,
            text=[[f"{v:.1f}%" if v is not None else "N/A"
                for v in row] for row in heatmap_data.values.tolist()],
            texttemplate="%{text}",
            textfont=dict(size=14, color="white", family=T.FONT_FAMILY),
            hovertemplate="<b>%{y}</b><br>Category: %{x}<br>Completion: %{z:.1f}%<extra></extra>",
            colorbar=dict(
                title=dict(
                    text="Completion %",
                    font=dict(size=12, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY)
                ),
                tickfont=dict(size=11, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
                thickness=16,
            )
        ))

        fig_heat = plotly_layout(fig_heat, "🔥 Field Completion Rate by Category (%)", height=420)
        fig_heat.update_xaxes(side="top", tickfont=dict(size=13, color=T.TEXT_PRIMARY))
        fig_heat.update_yaxes(tickfont=dict(size=12, color=T.TEXT_PRIMARY))
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("---")

        # ── Manufacturer readiness (category view) ───────────────────────────
        st.markdown("#### 🏭 Manufacturer Readiness Overview")

        mfr_ctrl1, mfr_ctrl2 = st.columns([2, 1])
        with mfr_ctrl1:
            mfr_metric = st.selectbox(
                "📊 Metric",
                ["Avg Score", "% Fully Ready", "SKU Count"],
                key="cat_mfr_metric"
            )
        with mfr_ctrl2:
            mfr_top_n = st.slider("Top N Manufacturers", 5, 20, 10, key="cat_mfr_n")

        mfr_grp = view_df.groupby("Manufacturer").agg(
            SKU_Count=("Score", "count"),
            Avg_Score=("Score", "mean"),
            Fully_Ready=("Score", lambda x: (x == 100).sum())
        ).reset_index()
        mfr_grp["Pct_Ready"] = (mfr_grp["Fully_Ready"] / mfr_grp["SKU_Count"] * 100).round(1)
        mfr_grp["Avg_Score"] = mfr_grp["Avg_Score"].round(1)

        metric_col_map = {
            "Avg Score":      ("Avg_Score",  "Avg Readiness Score"),
            "% Fully Ready":  ("Pct_Ready",  "% Fully Ready"),
            "SKU Count":      ("SKU_Count",  "Number of SKUs"),
        }
        y_col, y_title = metric_col_map[mfr_metric]
        mfr_plot = mfr_grp.sort_values(y_col, ascending=False).head(mfr_top_n)

        bar_colors_mfr = [
            T.ACCENT_EMERALD if v >= 75 else (T.ACCENT_AMBER if v >= 50 else T.ACCENT_CRIMSON)
            for v in mfr_plot[y_col]
        ]

        fig_mfr = go.Figure(go.Bar(
            x=mfr_plot["Manufacturer"],
            y=mfr_plot[y_col],
            marker_color=bar_colors_mfr,
            marker_line=dict(color="white", width=1.5),
            text=[f"{v:.1f}" for v in mfr_plot[y_col]],
            textposition="outside",
            textfont=dict(size=12, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
            hovertemplate=(
                "<b>%{x}</b><br>"
                + y_title + ": <b>%{y:.1f}</b><extra></extra>"
            ),
        ))
        if mfr_metric in ["Avg Score", "% Fully Ready"]:
            fig_mfr.add_hline(
                y=75, line_dash="dash", line_color=T.ACCENT_AMBER, line_width=2,
                annotation_text="75 threshold",
                annotation_font=dict(size=11, color=T.ACCENT_AMBER)
            )
        fig_mfr = plotly_layout(
            fig_mfr,
            f"🏭 Top {mfr_top_n} Manufacturers — {mfr_metric} ({cat_label})",
            height=420
        )
        fig_mfr.update_xaxes(tickangle=35)
        fig_mfr.update_yaxes(title_text=y_title)
        st.plotly_chart(fig_mfr, use_container_width=True)

        # Manufacturer table
        mfr_display = mfr_grp.sort_values("Avg_Score", ascending=False).copy()
        mfr_display.columns = ["Manufacturer", "SKU Count", "Avg Score",
                                "Fully Ready", "% Fully Ready"]
        display_table(
            mfr_display,
            title=f"🏭 Full Manufacturer Readiness Table — {cat_label}",
            download_name=f"manufacturer_readiness_{cat_label.lower()}.csv",
            scrollable=True, max_height="400px", align="center"
        )

        st.markdown("---")

        # ── Radar chart — avg field score ────────────────────────────────────
        st.markdown("#### 🕸️ Field Score Radar")

        if cat_sel != "🛍️ Combined":
            score_cols = [c for c in view_df.columns if c.startswith("Score: ")]
            if score_cols:
                avg_field_scores = view_df[score_cols].mean()
                field_names = [c.replace("Score: ", "") for c in score_cols]
                field_vals  = avg_field_scores.values.tolist()
                max_vals    = [view_weights.get(f, 1) for f in field_names]
                pct_vals    = [round(v / m * 100, 1) for v, m in zip(field_vals, max_vals)]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=pct_vals + [pct_vals[0]],
                    theta=field_names + [field_names[0]],
                    fill="toself",
                    fillcolor=f"rgba({','.join(str(int(cat_color.lstrip('#')[i:i+2],16)) for i in (0,2,4))},0.18)",
                    line=dict(color=cat_color, width=3),
                    marker=dict(size=8, color=cat_color),
                    name=cat_label,
                    hovertemplate="<b>%{theta}</b><br>Avg: %{r:.1f}%<extra></extra>"
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True, range=[0, 100],
                            tickfont=dict(size=10, color=T.TEXT_SECONDARY),
                            gridcolor="rgba(184,134,11,0.15)"
                        ),
                        angularaxis=dict(
                            tickfont=dict(size=12, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY)
                        ),
                        bgcolor="rgba(253,248,238,0.6)"
                    ),
                    showlegend=False,
                    height=420,
                    paper_bgcolor="rgba(255,254,249,0.9)",
                    font=dict(family=T.FONT_FAMILY),
                    title=dict(
                        text=f'<b style="color:{T.PRIMARY_DARK};">🕸️ {cat_label} — Avg Field Score (%)</b>',
                        x=0.5, xanchor="center", font=dict(size=16)
                    ),
                    margin=dict(l=60, r=60, t=70, b=40)
                )
                st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("💡 Select a specific category (Skincare or Apparel) to view the field-level radar chart.")


# ============================================================
# TAB 3 — SKU DRILL-DOWN
# ============================================================
with tab_sku:
    st.markdown(section_header(
        "🔍 SKU-Level Drill-Down",
        "Full scored SKU table — filter, sort, and export. Color-coded by readiness status."
    ), unsafe_allow_html=True)

    if combined.empty:
        st.warning("⚠️ No data available.")
    else:
        # ── Interactive controls ─────────────────────────────────────────────
        st.markdown("#### 🎛️ Filters & Controls")
        fc1, fc2, fc3, fc4 = st.columns(4)

        with fc1:
            cat_filter = st.multiselect(
                "🗂️ Category",
                options=combined["Category"].unique().tolist(),
                default=combined["Category"].unique().tolist(),
                key="sku_cat_filter"
            )
        with fc2:
            status_opts = combined["Status"].unique().tolist()
            status_filter = st.multiselect(
                "🚦 Status",
                options=status_opts,
                default=status_opts,
                key="sku_status_filter"
            )
        with fc3:
            all_mfrs = sorted(combined["Manufacturer"].unique().tolist())
            mfr_filter = st.multiselect(
                "🏭 Manufacturer",
                options=all_mfrs,
                default=all_mfrs,
                key="sku_mfr_filter"
            )
        with fc4:
            score_range = st.slider(
                "📊 Score Range",
                min_value=0, max_value=100,
                value=(0, 100), step=5,
                key="sku_score_range"
            )

        fc5, fc6, fc7 = st.columns(3)
        with fc5:
            sort_col = st.selectbox(
                "↕️ Sort By",
                ["Score", "Product Name", "Manufacturer", "Missing Count"],
                key="sku_sort_col"
            )
        with fc6:
            sort_asc = st.radio("Sort Order", ["⬇️ Descending", "⬆️ Ascending"],
                                horizontal=True, key="sku_sort_order")
        with fc7:
            search_sku = st.text_input("🔍 Search SKU / Product Name",
                                       placeholder="Type to filter...", key="sku_search")

        # ── Apply filters ────────────────────────────────────────────────────
        filtered = combined.copy()
        if cat_filter:
            filtered = filtered[filtered["Category"].isin(cat_filter)]
        if status_filter:
            filtered = filtered[filtered["Status"].isin(status_filter)]
        if mfr_filter:
            filtered = filtered[filtered["Manufacturer"].isin(mfr_filter)]
        filtered = filtered[
            (filtered["Score"] >= score_range[0]) &
            (filtered["Score"] <= score_range[1])
        ]
        if search_sku:
            mask = (
                filtered["SKU"].str.contains(search_sku, case=False, na=False) |
                filtered["Product Name"].str.contains(search_sku, case=False, na=False)
            )
            filtered = filtered[mask]

        ascending = sort_asc == "⬆️ Ascending"
        filtered  = filtered.sort_values(sort_col, ascending=ascending)

        # ── Filter result KPIs ───────────────────────────────────────────────
        fk1, fk2, fk3, fk4 = st.columns(4)
        with fk1:
            st.markdown(kpi_card("📦", fmt_num(len(filtered)), "Filtered SKUs", "gold"),
                        unsafe_allow_html=True)
        with fk2:
            f_ready = int((filtered["Score"] == 100).sum())
            st.markdown(kpi_card("✅", fmt_num(f_ready), "Fully Ready", "emerald"),
                        unsafe_allow_html=True)
        with fk3:
            f_avg = filtered["Score"].mean() if len(filtered) else 0
            st.markdown(kpi_card("📈", f"{f_avg:.1f}", "Avg Score", "sapphire"),
                        unsafe_allow_html=True)
        with fk4:
            f_incomplete = int((filtered["Score"] < 50).sum())
            st.markdown(kpi_card("❌", fmt_num(f_incomplete), "Incomplete", "crimson"),
                        unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Color-coded SKU table ────────────────────────────────────────────
        st.markdown("#### 📋 SKU Readiness Table")

        display_cols = ["SKU", "Product Name", "Manufacturer",
                        "Category", "Score", "Status", "Missing Fields", "Missing Count"]
        table_data   = filtered[display_cols].copy()

        # Build color-coded HTML table
        scroll_style = (
            f"overflow-x:auto; overflow-y:auto; max-height:600px;"
            f"border:2px solid {T.PRIMARY}; border-radius:{T.BORDER_RADIUS};"
            f"box-shadow:{T.SHADOW_MEDIUM};"
        )

        html_sku = f"""
        <style>
        .sku-table {{ width:100%; border-collapse:collapse; font-size:13px; background:white; }}
        .sku-table thead tr {{
            background: {T.gold_gradient(135)};
            color: white;
            position: sticky; top: 0; z-index: 10;
        }}
        .sku-table th {{
            padding: 11px 13px; border: 1px solid {T.PRIMARY_DARK};
            font-size: 12px; font-weight: 700; letter-spacing: 0.4px;
            white-space: nowrap; text-align: center;
        }}
        .sku-table td {{
            padding: 9px 12px;
            border: 1px solid rgba(184,134,11,0.15);
            font-size: 12.5px; font-weight: 500;
            text-align: center; vertical-align: middle;
        }}
        .sku-table tbody tr:hover {{ background: rgba(184,134,11,0.08) !important; }}
        </style>
        <div style="{scroll_style}">
        <table class="sku-table">
        <thead><tr>{"".join(f"<th>{c}</th>" for c in display_cols)}</tr></thead>
        <tbody>
        """

        for _, row in table_data.iterrows():
            score = row["Score"]
            if score == 100:
                row_bg    = "rgba(16,185,129,0.07)"
                score_bg  = T.ACCENT_EMERALD
            elif score >= 75:
                row_bg    = "rgba(245,158,11,0.07)"
                score_bg  = T.ACCENT_AMBER
            elif score >= 50:
                row_bg    = "rgba(59,130,246,0.07)"
                score_bg  = T.ACCENT_SAPPHIRE
            else:
                row_bg    = "rgba(239,68,68,0.07)"
                score_bg  = T.ACCENT_CRIMSON

            html_sku += f'<tr style="background:{row_bg};">'
            for col in display_cols:
                val = row[col]
                cell = "" if pd.isna(val) else str(val)
                if col == "Score":
                    html_sku += (
                        f'<td><span style="'
                        f'background:{score_bg};color:white;'
                        f'padding:3px 10px;border-radius:50px;'
                        f'font-weight:700;font-size:12px;">'
                        f'{cell}</span></td>'
                    )
                elif col == "Status":
                    html_sku += (
                        f'<td><span style="'
                        f'background:{score_bg};color:white;'
                        f'padding:3px 10px;border-radius:50px;'
                        f'font-weight:600;font-size:11px;white-space:nowrap;">'
                        f'{cell}</span></td>'
                    )
                elif col == "Missing Fields":
                    color = T.ACCENT_CRIMSON if cell != "—" else T.ACCENT_EMERALD
                    html_sku += (
                        f'<td style="color:{color};font-weight:600;'
                        f'text-align:left;max-width:220px;word-break:break-word;">'
                        f'{cell}</td>'
                    )
                elif col == "SKU":
                    html_sku += (
                        f'<td style="color:{T.PRIMARY_DARK};font-weight:700;">'
                        f'{cell}</td>'
                    )
                else:
                    html_sku += f'<td>{cell}</td>'
            html_sku += "</tr>"

        html_sku += "</tbody></table></div>"
        st.markdown(html_sku, unsafe_allow_html=True)

        st.markdown(f"""
        <p style="color:{T.TEXT_SECONDARY};font-size:0.82rem;margin-top:0.5rem;">
        Showing <strong>{len(table_data):,}</strong> of <strong>{len(combined):,}</strong> total SKUs
        </p>""", unsafe_allow_html=True)

        st.download_button(
            "📥 Download Filtered SKU Report",
            data=filtered.to_csv(index=False).encode("utf-8"),
            file_name="boutiqaat_sku_readiness.csv",
            mime="text/csv",
            key="dl_sku_full"
        )

        st.markdown("---")

        # ── Score scatter ────────────────────────────────────────────────────
        st.markdown("#### 📈 Score Distribution — Interactive Scatter")

        fig_scatter = px.strip(
            filtered,
            x="Category", y="Score",
            color="Status",
            hover_data=["SKU", "Product Name", "Manufacturer", "Missing Fields"],
            color_discrete_map={
                "✅ Fully Ready": T.ACCENT_EMERALD,
                "⚠️ Near Ready":  T.ACCENT_AMBER,
                "🔵 Partial":     T.ACCENT_SAPPHIRE,
                "❌ Incomplete":  T.ACCENT_CRIMSON,
            },
            stripmode="overlay",
        )
        fig_scatter.update_traces(marker=dict(size=9, opacity=0.75,
                                              line=dict(color="white", width=1)))
        for thresh, label, color in [
            (100, "Fully Ready", T.ACCENT_EMERALD),
            (75,  "Near Ready",  T.ACCENT_AMBER),
            (50,  "Partial",     T.ACCENT_SAPPHIRE),
        ]:
            fig_scatter.add_hline(
                y=thresh, line_dash="dash", line_color=color, line_width=1.5,
                annotation_text=label,
                annotation_position="right",
                annotation_font=dict(size=10, color=color)
            )
        fig_scatter = plotly_layout(fig_scatter, "📈 SKU Score Distribution by Category", height=420)
        fig_scatter.update_yaxes(range=[-2, 105], title_text="Readiness Score")
        st.plotly_chart(fig_scatter, use_container_width=True)


# ============================================================
# TAB 4 — INSIGHTS & RECOMMENDATIONS
# ============================================================
with tab_insights:
    st.markdown(section_header(
        "💡 Insights & Actionable Recommendations",
        "Data-driven findings to guide your catalog enrichment strategy"
    ), unsafe_allow_html=True)

    if combined.empty:
        st.warning("⚠️ No data available.")
    else:
        # ── Top missing fields ───────────────────────────────────────────────
        st.markdown("#### 🔴 Top Missing Fields by Category")

        def missing_field_analysis(df_raw, weights, img_col, label):
            missing_counts = {}
            for field in weights.keys():
                if field not in df_raw.columns:
                    missing_counts[field] = len(df_raw)
                    continue
                if field == img_col:
                    empty = (pd.to_numeric(df_raw[field], errors="coerce").fillna(0) < IMG_THRESHOLD).sum()
                else:
                    empty = df_raw[field].apply(lambda v: not is_filled(v)).sum()
                missing_counts[field] = int(empty)
            result = pd.DataFrame({
                "Field":         list(missing_counts.keys()),
                "Missing SKUs":  list(missing_counts.values()),
                "Category":      label,
                "Weight":        [weights[f] for f in missing_counts.keys()],
            })
            result["Missing %"] = (result["Missing SKUs"] / len(df_raw) * 100).round(1)
            result["Impact Score"] = (result["Missing %"] * result["Weight"] / 100).round(1)
            return result.sort_values("Impact Score", ascending=False)

        sc_missing = missing_field_analysis(sc_raw, SKINCARE_WEIGHTS, SKINCARE_IMG_COL, "Skincare")
        ap_missing = missing_field_analysis(ap_raw, APPAREL_WEIGHTS,  APPAREL_IMG_COL,  "Apparel")

        ins1, ins2 = st.columns(2)

        with ins1:
            fig_sc_miss = go.Figure(go.Bar(
                x=sc_missing["Field"],
                y=sc_missing["Missing %"],
                marker_color=[
                    T.ACCENT_CRIMSON if v > 50 else
                    (T.ACCENT_AMBER if v > 20 else T.ACCENT_EMERALD)
                    for v in sc_missing["Missing %"]
                ],
                marker_line=dict(color="white", width=1.5),
                text=[f"{v:.0f}%" for v in sc_missing["Missing %"]],
                textposition="outside",
                textfont=dict(size=12, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
                hovertemplate="<b>%{x}</b><br>Missing: %{y:.1f}%<extra>Skincare</extra>",
            ))
            fig_sc_miss = plotly_layout(fig_sc_miss, "💄 Skincare — Missing Fields %", height=380)
            fig_sc_miss.update_xaxes(tickangle=35)
            fig_sc_miss.update_yaxes(title_text="% SKUs Missing", range=[0, 110])
            st.plotly_chart(fig_sc_miss, use_container_width=True)

        with ins2:
            fig_ap_miss = go.Figure(go.Bar(
                x=ap_missing["Field"],
                y=ap_missing["Missing %"],
                marker_color=[
                    T.ACCENT_CRIMSON if v > 50 else
                    (T.ACCENT_AMBER if v > 20 else T.ACCENT_EMERALD)
                    for v in ap_missing["Missing %"]
                ],
                marker_line=dict(color="white", width=1.5),
                text=[f"{v:.0f}%" for v in ap_missing["Missing %"]],
                textposition="outside",
                textfont=dict(size=12, color=T.TEXT_PRIMARY, family=T.FONT_FAMILY),
                hovertemplate="<b>%{x}</b><br>Missing: %{y:.1f}%<extra>Apparel</extra>",
            ))
            fig_ap_miss = plotly_layout(fig_ap_miss, "👕 Apparel — Missing Fields %", height=380)
            fig_ap_miss.update_xaxes(tickangle=35)
            fig_ap_miss.update_yaxes(title_text="% SKUs Missing", range=[0, 110])
            st.plotly_chart(fig_ap_miss, use_container_width=True)

        # Impact score tables
        it1, it2 = st.columns(2)
        with it1:
            display_table(
                sc_missing[["Field", "Weight", "Missing SKUs", "Missing %", "Impact Score"]],
                title="💄 Skincare — Field Impact Analysis",
                download_name="skincare_missing_fields.csv",
                scrollable=False, align="center"
            )
        with it2:
            display_table(
                ap_missing[["Field", "Weight", "Missing SKUs", "Missing %", "Impact Score"]],
                title="👕 Apparel — Field Impact Analysis",
                download_name="apparel_missing_fields.csv",
                scrollable=False, align="center"
            )

        st.markdown("---")

        # ── Manufacturer deep-dive ───────────────────────────────────────────
        st.markdown("#### 🏭 Manufacturer Readiness Deep-Dive")

        mfr_combined = combined.groupby(["Manufacturer", "Category"]).agg(
            SKU_Count   =("Score", "count"),
            Avg_Score   =("Score", "mean"),
            Fully_Ready =("Score", lambda x: (x == 100).sum()),
            Near_Ready  =("Score", lambda x: ((x >= 75) & (x < 100)).sum()),
            Incomplete  =("Score", lambda x: (x < 50).sum()),
        ).reset_index()
        mfr_combined["Avg_Score"]  = mfr_combined["Avg_Score"].round(1)
        mfr_combined["Pct_Ready"]  = (mfr_combined["Fully_Ready"] / mfr_combined["SKU_Count"] * 100).round(1)
        mfr_combined.columns = ["Manufacturer", "Category", "SKU Count",
                                 "Avg Score", "Fully Ready", "Near Ready",
                                 "Incomplete", "% Fully Ready"]

        mfr_chart_data = mfr_combined.sort_values("Avg Score", ascending=False).head(15)

        fig_mfr2 = px.scatter(
            mfr_chart_data,
            x="SKU Count", y="Avg Score",
            size="SKU Count", color="Category",
            hover_name="Manufacturer",
            hover_data={"Fully Ready": True, "Incomplete": True,
                        "% Fully Ready": True, "SKU Count": True},
            color_discrete_map={"Skincare": T.ACCENT_ROSE, "Apparel": T.ACCENT_TEAL},
            size_max=55,
        )
        fig_mfr2.add_hline(y=75, line_dash="dash", line_color=T.ACCENT_AMBER, line_width=2,
                           annotation_text="75 — Near Ready threshold",
                           annotation_font=dict(size=11, color=T.ACCENT_AMBER))
        fig_mfr2 = plotly_layout(
            fig_mfr2,
            "🏭 Manufacturer Bubble Chart — SKU Count vs Avg Score",
            height=460
        )
        fig_mfr2.update_xaxes(title_text="Number of SKUs")
        fig_mfr2.update_yaxes(title_text="Average Readiness Score", range=[0, 105])
        st.plotly_chart(fig_mfr2, use_container_width=True)

        display_table(
            mfr_combined.sort_values("Avg Score", ascending=False),
            title="🏭 Full Manufacturer Readiness Table",
            download_name="manufacturer_readiness_full.csv",
            scrollable=True, max_height="420px", align="center"
        )

        st.markdown("---")

        # ── Actionable recommendations ───────────────────────────────────────
        st.markdown("#### 🚀 Actionable Recommendations")

        # Compute dynamic insights
        top_sc_miss = sc_missing.iloc[0]["Field"] if not sc_missing.empty else "N/A"
        top_ap_miss = ap_missing.iloc[0]["Field"] if not ap_missing.empty else "N/A"
        near_ready_count = int(((combined["Score"] >= 75) & (combined["Score"] < 100)).sum())
        worst_mfr = (mfr_combined.sort_values("Avg Score").iloc[0]["Manufacturer"]
                     if not mfr_combined.empty else "N/A")
        best_mfr  = (mfr_combined.sort_values("Avg Score", ascending=False).iloc[0]["Manufacturer"]
                     if not mfr_combined.empty else "N/A")

        sc_img_below = int((sc_raw.get("Image Count", pd.Series(dtype=float))
                            .apply(lambda v: pd.to_numeric(v, errors="coerce") or 0) < IMG_THRESHOLD).sum())
        ap_img_below = int((ap_raw.get("Images", pd.Series(dtype=float))
                            .apply(lambda v: pd.to_numeric(v, errors="coerce") or 0) < IMG_THRESHOLD).sum())

        rec_data = [
            {
                "priority": "🔴 Critical",
                "color":    T.ACCENT_CRIMSON,
                "variant":  "danger",
                "title":    "Fix Image Gaps Immediately",
                "body":     (
                    f"<strong>{sc_img_below}</strong> Skincare SKUs and "
                    f"<strong>{ap_img_below}</strong> Apparel SKUs have fewer than "
                    f"{IMG_THRESHOLD} images — the catalog publishing standard. "
                    "Images carry a <strong>20-point weight</strong>. Uploading missing "
                    "images is the single highest-ROI action to boost scores."
                )
            },
            {
                "priority": "🔴 Critical",
                "color":    T.ACCENT_CRIMSON,
                "variant":  "danger",
                "title":    f"Enrich Top Missing Field: Skincare → '{top_sc_miss}'",
                "body":     (
                    f"<strong>{top_sc_miss}</strong> is the highest-impact missing field "
                    f"in Skincare (Impact Score: {sc_missing.iloc[0]['Impact Score']:.1f}). "
                    "Completing this field across all affected SKUs will deliver the "
                    "largest single improvement to the Skincare readiness score."
                )
            },
            {
                "priority": "🟡 High",
                "color":    T.ACCENT_AMBER,
                "variant":  "warning",
                "title":    f"Quick Win: Push {near_ready_count} 'Near Ready' SKUs to 100",
                "body":     (
                    f"<strong>{near_ready_count}</strong> SKUs are already scoring 75–99. "
                    "Each needs only <strong>1–2 field fixes</strong> to reach full readiness. "
                    "Filter by '⚠️ Near Ready' in the SKU Drill-Down tab, sort by "
                    "Missing Count, and action the smallest gaps first."
                )
            },
            {
                "priority": "🟡 High",
                "color":    T.ACCENT_AMBER,
                "variant":  "warning",
                "title":    f"Enrich Top Missing Field: Apparel → '{top_ap_miss}'",
                "body":     (
                    f"<strong>{top_ap_miss}</strong> is the highest-impact missing field "
                    f"in Apparel (Impact Score: {ap_missing.iloc[0]['Impact Score']:.1f}). "
                    "Coordinate with the Apparel buying team to source and populate "
                    "this attribute across all affected SKUs."
                )
            },
            {
                "priority": "🟢 Strategic",
                "color":    T.ACCENT_EMERALD,
                "variant":  "success",
                "title":    f"Benchmark Best Manufacturer: {best_mfr}",
                "body":     (
                    f"<strong>{best_mfr}</strong> has the highest average readiness score. "
                    "Use their data submission format as a <strong>template</strong> for "
                    "onboarding new suppliers and for re-requesting data from underperforming "
                    "manufacturers."
                )
            },
            {
                "priority": "🟢 Strategic",
                "color":    T.ACCENT_EMERALD,
                "variant":  "success",
                "title":    f"Supplier Engagement: Escalate to {worst_mfr}",
                "body":     (
                    f"<strong>{worst_mfr}</strong> has the lowest average readiness score. "
                    "Schedule a data quality review with this supplier and share a "
                    "<strong>field completion checklist</strong> aligned to Boutiqaat's "
                    "catalog standards to prevent future publishing blockers."
                )
            },
        ]

        for i in range(0, len(rec_data), 2):
            rc1, rc2 = st.columns(2)
            cols_pair = [rc1, rc2]
            for j, col in enumerate(cols_pair):
                if i + j < len(rec_data):
                    r = rec_data[i + j]
                    with col:
                        st.markdown(f"""
                        <div class="insight-box insight-{r['variant']}">
                            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
                                <span style="
                                    background:{r['color']};color:white;
                                    padding:3px 10px;border-radius:50px;
                                    font-size:0.75rem;font-weight:700;
                                ">{r['priority']}</span>
                                <h4 style="color:{r['color']};margin:0;font-size:1rem;">
                                    {r['title']}
                                </h4>
                            </div>
                            <p style="color:{T.TEXT_PRIMARY};line-height:1.75;margin:0;font-size:0.9rem;">
                                {r['body']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Final summary download ───────────────────────────────────────────
        st.markdown("#### 📥 Export Full Report")

        ex1, ex2, ex3 = st.columns(3)
        with ex1:
            st.download_button(
                "📥 Full Combined Report",
                data=combined.to_csv(index=False).encode("utf-8"),
                file_name="boutiqaat_catalog_readiness_full.csv",
                mime="text/csv", key="dl_full_combined"
            )
        with ex2:
            st.download_button(
                "💄 Skincare Report",
                data=sc_scored.to_csv(index=False).encode("utf-8"),
                file_name="boutiqaat_skincare_readiness.csv",
                mime="text/csv", key="dl_sc_export"
            )
        with ex3:
            st.download_button(
                "👕 Apparel Report",
                data=ap_scored.to_csv(index=False).encode("utf-8"),
                file_name="boutiqaat_apparel_readiness.csv",
                mime="text/csv", key="dl_ap_export"
            )

        st.markdown(f"""
        <div class="insight-box insight-gold" style="margin-top:1.5rem;text-align:center;">
            <p style="color:{T.PRIMARY_DARK};font-size:0.9rem;margin:0;font-weight:600;">
                🛍️ Boutiqaat Catalog Readiness Dashboard &nbsp;|&nbsp;
                Built for the Merchandising Team &nbsp;|&nbsp;
                {len(combined):,} SKUs Analyzed across Skincare & Apparel
            </p>
        </div>
        """, unsafe_allow_html=True)
