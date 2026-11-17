"""
FreshCart — Dark Theme CSS.
Premium grocery shopping UI with dark background aesthetic.
"""

CUSTOM_CSS = """
<style>
/* ── Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* ── Hide Streamlit chrome while preserving sidebar toggle ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header {
    background: transparent !important;
}
[data-testid="stSidebarCollapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    color: #3fb950 !important;
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    padding: 4px !important;
    margin-left: 8px !important;
    margin-top: 8px !important;
}
[data-testid="stSidebarCollapsedControl"]:hover {
    background: #21262d !important;
    border-color: #3fb950 !important;
}
[data-testid="stSidebarCollapsedControl"] svg {
    fill: #3fb950 !important;
}

[data-testid="stSidebarCollapseButton"] {
    color: #8b949e !important;
}
[data-testid="stSidebarCollapseButton"]:hover {
    color: #3fb950 !important;
}
[data-testid="stSidebarCollapseButton"] svg {
    fill: currentColor !important;
}

/* ── Dark page background ── */
.stApp {
    background: #0d1117 !important;
}

/* ── Dark sidebar ── */
[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d !important;
}
[data-testid="stSidebar"] * {
    color: #e6edf3 !important;
}

/* ── Dark main content ── */
[data-testid="stMain"] {
    background: #0d1117 !important;
}

/* ── Fix st.write / st.caption text color ── */
p, span, label, .stMarkdown {
    color: #e6edf3 !important;
}
.stCaption > p {
    color: #8b949e !important;
}

/* ── Dividers ── */
hr { border-color: #30363d !important; }

/* ═══════════════════════════════════════════
   TOP NAV BAR
══════════════════════════════════════════ */
.nav-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: #161b22;
    border-radius: 16px;
    padding: 0.9rem 1.6rem;
    margin-bottom: 1.5rem;
    border: 1px solid #30363d;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.nav-logo {
    font-size: 1.55rem;
    font-weight: 900;
    color: #3fb950;
    letter-spacing: -0.04em;
}
.nav-logo span { color: #e6edf3; }
.nav-tagline { font-size: 0.82rem; color: #8b949e; font-weight: 500; }
.nav-badges  { display: flex; gap: 0.5rem; }
.nav-badge {
    background: #1f2d1f;
    color: #3fb950;
    border: 1px solid #2ea043;
    padding: 0.28rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
}

/* ═══════════════════════════════════════════
   HERO
══════════════════════════════════════════ */
.hero-search-wrap {
    background: linear-gradient(135deg, #0d2818 0%, #0f3d20 50%, #163f2a 100%);
    border-radius: 20px;
    padding: 2.4rem 2.6rem;
    margin-bottom: 1.8rem;
    border: 1px solid #2ea043;
    box-shadow: 0 16px 40px rgba(0,0,0,0.5);
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-search-wrap::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: rgba(63,185,80,0.06);
    border-radius: 50%;
}
.hero-eyebrow {
    font-size: 0.8rem; font-weight: 700;
    color: #3fb950; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 0.5rem;
}
.hero-h1 {
    font-size: 2.4rem; font-weight: 900;
    color: #e6edf3 !important;
    margin: 0 0 0.5rem;
    letter-spacing: -0.04em; line-height: 1.1;
}
.hero-h1 em { color: #3fb950; font-style: normal; }
.hero-sub {
    font-size: 1rem; color: #8b949e !important;
    margin: 0 0 1.5rem; font-weight: 400;
}

/* ═══════════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════════ */
.section-label {
    font-size: 0.72rem; font-weight: 800;
    text-transform: uppercase; letter-spacing: 0.08em;
    color: #3fb950; margin-bottom: 0.3rem;
}
.section-title {
    font-size: 1.5rem; font-weight: 800;
    color: #e6edf3 !important;
    margin: 0 0 1.1rem; letter-spacing: -0.02em;
}

/* ═══════════════════════════════════════════
   PRODUCT CARDS (native st.container border=True)
   We only use inline HTML for the emoji+name header block.
══════════════════════════════════════════ */
.prod-header {
    text-align: center;
    padding: 0.5rem 0 0.3rem;
}
.prod-emoji {
    font-size: 3rem;
    display: block;
    line-height: 1;
    margin-bottom: 0.4rem;
}
.prod-name {
    font-size: 1.05rem;
    font-weight: 800;
    color: #e6edf3 !important;
    text-transform: capitalize;
    margin-bottom: 0.15rem;
}
.prod-category {
    font-size: 0.7rem;
    font-weight: 700;
    color: #8b949e !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
.prod-price {
    font-size: 1.3rem;
    font-weight: 900;
    color: #3fb950 !important;
    text-align: center;
    margin: 0.3rem 0 0.4rem;
}
.together-badge {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.3rem;
    background: #1f2d1f;
    border: 1px solid #2ea043;
    color: #3fb950 !important;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.3rem 0.8rem;
    border-radius: 9999px;
    margin: 0 auto 0.6rem;
    width: fit-content;
}
.top-pick-ribbon {
    display: inline-block;
    background: #da3633;
    color: #fff !important;
    font-size: 0.68rem;
    font-weight: 800;
    padding: 0.22rem 0.65rem;
    border-radius: 9999px;
    margin-bottom: 0.4rem;
}
.shoppers-str {
    font-size: 0.8rem;
    color: #8b949e !important;
    text-align: center;
    margin-top: 0.3rem;
}

/* ═══════════════════════════════════════════
   BASKET CHIPS
══════════════════════════════════════════ */
.basket-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: #1f2d1f;
    border: 1.5px solid #2ea043;
    color: #3fb950 !important;
    padding: 0.35rem 0.9rem;
    border-radius: 9999px;
    font-size: 0.83rem;
    font-weight: 700;
    text-transform: capitalize;
    margin: 0.2rem;
}

/* ═══════════════════════════════════════════
   MEAL KIT CARDS
══════════════════════════════════════════ */
.kit-card {
    background: #161b22;
    border: 1.5px solid #30363d;
    border-radius: 16px;
    padding: 1.3rem 1.25rem 1rem;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.kit-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #2ea043, #3fb950);
}
.kit-card:hover {
    border-color: #3fb950;
    box-shadow: 0 8px 24px rgba(63,185,80,0.12);
}
.kit-tag {
    font-size: 0.7rem; font-weight: 800;
    color: #3fb950 !important;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin-bottom: 0.25rem;
}
.kit-name {
    font-size: 1.15rem; font-weight: 800;
    color: #e6edf3 !important;
    margin: 0 0 0.35rem; letter-spacing: -0.02em;
}
.kit-desc {
    font-size: 0.85rem; color: #8b949e !important;
    margin-bottom: 0.8rem; line-height: 1.5;
}
.kit-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: #0d1117;
    border: 1px solid #30363d;
    padding: 0.28rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.78rem; font-weight: 600;
    color: #c9d1d9 !important;
    text-transform: capitalize;
    margin: 0.2rem 0.2rem 0 0;
}
.kit-orig {
    font-size: 0.9rem; color: #484f58 !important;
    text-decoration: line-through; margin-right: 0.5rem;
}
.kit-sale {
    font-size: 1.4rem; font-weight: 900;
    color: #3fb950 !important;
}
.kit-save {
    background: #1f2d1f; color: #3fb950 !important;
    border: 1px solid #2ea043;
    padding: 0.2rem 0.6rem; border-radius: 9999px;
    font-size: 0.72rem; font-weight: 800;
    margin-left: 0.5rem;
}
.kit-social {
    font-size: 0.75rem; color: #8b949e !important;
    margin-top: 0.4rem;
}

/* ═══════════════════════════════════════════
   HOW IT WORKS CARDS
══════════════════════════════════════════ */
.how-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 1.5rem 1.2rem;
    text-align: center;
}
.how-emoji { font-size: 2.5rem; margin-bottom: 0.5rem; }
.how-title {
    font-size: 1.05rem; font-weight: 800;
    color: #e6edf3 !important; margin-bottom: 0.3rem;
}
.how-desc { font-size: 0.84rem; color: #8b949e !important; line-height: 1.5; }

/* ═══════════════════════════════════════════
   EMPTY STATES
══════════════════════════════════════════ */
.empty-state {
    text-align: center;
    padding: 3rem 2rem;
    background: #161b22;
    border-radius: 16px;
    border: 1.5px dashed #30363d;
}
.empty-state-emoji { font-size: 3rem; margin-bottom: 0.5rem; }
.empty-state-title { font-size: 1.15rem; font-weight: 800; color: #e6edf3 !important; }
.empty-state-sub   { font-size: 0.88rem; color: #8b949e !important; margin-top: 0.3rem; }

/* ═══════════════════════════════════════════
   PROGRESS BAR (Match Strength)
══════════════════════════════════════════ */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #2ea043, #3fb950) !important;
}

/* ═══════════════════════════════════════════
   TABS
══════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    background: #161b22;
    border-radius: 12px;
    padding: 0.3rem;
    border: 1px solid #30363d;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 700;
    font-size: 0.88rem;
    padding: 0.5rem 1.2rem;
    color: #8b949e;
}
.stTabs [aria-selected="true"] {
    background: #0d2818 !important;
    color: #3fb950 !important;
    border: 1px solid #2ea043 !important;
}

/* ═══════════════════════════════════════════
   BUTTONS
══════════════════════════════════════════ */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2ea043, #3fb950) !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    color: #0d1117 !important;
    box-shadow: 0 4px 14px rgba(63,185,80,0.35) !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(63,185,80,0.5) !important;
}
.stButton > button[kind="secondary"] {
    border: 1.5px solid #2ea043 !important;
    background: #1f2d1f !important;
    color: #3fb950 !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
}
.stButton > button[kind="secondary"]:hover {
    background: #263d26 !important;
}
.stButton > button:disabled {
    background: #21262d !important;
    color: #484f58 !important;
    border-color: #30363d !important;
}

/* ═══════════════════════════════════════════
   MULTISELECT + INPUTS
══════════════════════════════════════════ */
[data-baseweb="select"] > div {
    background: #161b22 !important;
    border-color: #30363d !important;
    border-radius: 10px !important;
    color: #e6edf3 !important;
}
[data-baseweb="tag"] {
    background: #1f2d1f !important;
    border: 1px solid #2ea043 !important;
    color: #3fb950 !important;
    border-radius: 9999px !important;
}

/* ═══════════════════════════════════════════
   CONTAINERS / EXPANDER
══════════════════════════════════════════ */
[data-testid="stExpander"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
}
[data-testid="stVerticalBlock"] [data-testid="stContainer"] {
    background: #161b22 !important;
    border-color: #30363d !important;
    border-radius: 16px !important;
}

/* ── Metric cards ── */
[data-testid="stMetric"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
    padding: 0.8rem 1rem !important;
}
[data-testid="stMetricValue"] { color: #3fb950 !important; }
[data-testid="stMetricLabel"] { color: #8b949e !important; }

/* ── Info / success / warning boxes ── */
[data-testid="stAlert"] {
    background: #1c2433 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    background: #161b22 !important;
    border-radius: 10px !important;
    border: 1px solid #30363d !important;
}

/* ── Sidebar brand ── */
.sidebar-logo {
    font-size: 1.5rem; font-weight: 900;
    color: #3fb950; letter-spacing: -0.04em;
    text-align: center;
}
.sidebar-logo span { color: #e6edf3; }
</style>
"""
