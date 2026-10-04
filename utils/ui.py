import streamlit as st

NAV = [
    ("Command Center", "▦"), ("Report Emergency", "⚠"), ("Incidents", "☰"),
    ("Resources", "⛑"), ("AI Monitoring", "✦"), ("Audit Trail", "✓"),
]
TONES = {"red": "#ff6b81", "orange": "#fbbf24", "blue": "#8b93ff", "green": "#34d399", "cyan": "#22d3ee"}
SEV_COLORS = {"Critical": "#ff4d6d", "High": "#fb923c", "Medium": "#facc15", "Low": "#34d399"}


def inject_css():
    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{--bg:#142041;--card:#1e2d57;--card2:#263767;--line:rgba(203,213,245,.22);--txt:#f4f7ff;--mut:#b4c2e0;--acc:#8b93ff;--red:#ff5d73}
html,body,.stApp,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:radial-gradient(1000px 500px at 90% -5%,rgba(139,147,255,.35),transparent),
 radial-gradient(800px 500px at 0% 100%,rgba(255,93,115,.20),transparent),var(--bg)}
[data-testid="stHeader"]{background:transparent}
.block-container{max-width:1480px;padding:1.6rem 2rem 3rem}
#MainMenu,footer{visibility:hidden}

/* Sidebar */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#1a2a5a,#142041);border-right:1px solid var(--line)}
.brand{display:flex;gap:12px;align-items:center;padding:6px 4px 14px}
.logo{width:40px;height:40px;border-radius:12px;display:grid;place-items:center;font-size:20px;
 background:linear-gradient(135deg,#ef4444,#6366f1);box-shadow:0 8px 22px rgba(239,68,68,.35)}
.brand-title{font-weight:800;font-size:1.15rem;letter-spacing:-.03em;color:#fff}
.brand-title span{background:linear-gradient(90deg,#f87171,#818cf8);-webkit-background-clip:text;color:transparent}
.brand-sub{color:var(--mut);font-size:.68rem}
.nav-label{color:#a5b4d8;font-size:.64rem;font-weight:700;letter-spacing:.14em;margin:14px 6px 6px}
[data-testid="stSidebar"] [role="radiogroup"]{gap:3px}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:10px 12px;border-radius:10px;width:100%;
 border:1px solid transparent;transition:.15s;cursor:pointer}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(99,102,241,.08)}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
 background:linear-gradient(90deg,rgba(99,102,241,.22),rgba(99,102,241,.05));border-color:rgba(99,102,241,.35)}
[data-testid="stSidebar"] [role="radiogroup"] label>div:first-child{display:none}
[data-testid="stSidebar"] [role="radiogroup"] p{font-size:.88rem;font-weight:600;color:#eef2ff}
.status-card{margin-top:18px;padding:12px 14px;border:1px solid var(--line);border-radius:12px;background:var(--card)}
.status-row{display:flex;align-items:center;gap:10px;color:#e6ecff;font-size:.92rem;font-weight:500;margin:9px 0}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 10px #22c55e;animation:pulse 2s infinite}
@keyframes pulse{50%{opacity:.4}}

/* Hero */
.hero{position:relative;overflow:hidden;padding:22px 28px;margin-bottom:20px;border-radius:20px;
 border:1px solid var(--line);background:linear-gradient(120deg,#4f46e5 0%,#3b5bdb 50%,#d6336c 100%)}
.hero:before{content:"";position:absolute;right:-60px;top:-90px;width:300px;height:300px;border-radius:50%;
 background:radial-gradient(circle,rgba(255,255,255,.28),transparent 70%)}
.hero-kicker{color:#e0e7ff;font-size:.68rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}
.hero h1{margin:6px 0 4px;font-size:1.55rem;font-weight:700;letter-spacing:-.03em;color:#fff;position:relative}
.hero p{margin:0;color:#eef2ff;font-size:.86rem;max-width:760px;position:relative}

/* KPI */
.kpi{position:relative;padding:18px;border-radius:16px;border:1px solid var(--line);
 background:linear-gradient(160deg,var(--card2),var(--card));overflow:hidden;transition:.2s}
.kpi:hover{transform:translateY(-3px);border-color:rgba(99,102,241,.4);box-shadow:0 14px 30px rgba(0,0,0,.35)}
.kpi:after{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--c)}
.kpi-top{display:flex;justify-content:space-between;align-items:center}
.kpi-label{color:var(--mut);font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em}
.kpi-icon{width:34px;height:34px;border-radius:10px;display:grid;place-items:center;font-size:16px;
 background:color-mix(in srgb,var(--c) 16%,transparent);color:var(--c)}
.kpi-value{font-size:1.7rem;font-weight:700;color:#fff;letter-spacing:-.03em;margin-top:6px}
.kpi-hint{color:var(--mut);font-size:.72rem}

/* Panels */
.section-title{display:flex;align-items:center;gap:8px;color:#fff;font-size:.95rem;font-weight:700;margin:18px 0 12px}
.section-title:before{content:"";width:4px;height:16px;border-radius:2px;background:linear-gradient(var(--acc),var(--red))}
.panel{padding:18px;border:1px solid var(--line);border-radius:16px;background:var(--card)}
.mini-label{color:var(--mut);text-transform:uppercase;letter-spacing:.09em;font-size:.65rem;font-weight:700}
.incident-card{padding:13px 15px;margin:8px 0;border:1px solid var(--line);border-radius:12px;
 background:var(--card);transition:.15s}
.incident-card:hover{border-color:rgba(99,102,241,.4);background:var(--card2)}
.incident-code{color:#fff;font-weight:700;font-size:.85rem}
.incident-meta{color:var(--mut);font-size:.72rem;margin-top:4px}
.badge{display:inline-block;padding:3px 10px;border-radius:999px;font-size:.64rem;font-weight:700;
 border:1px solid var(--line);background:rgba(100,116,139,.12);color:#cbd5e1}
.badge-red{color:#fca5a5;background:rgba(239,68,68,.12);border-color:rgba(239,68,68,.3)}
.badge-orange{color:#fdba74;background:rgba(249,115,22,.12);border-color:rgba(249,115,22,.3)}
.badge-yellow{color:#fde68a;background:rgba(234,179,8,.12);border-color:rgba(234,179,8,.3)}
.badge-green{color:#86efac;background:rgba(34,197,94,.12);border-color:rgba(34,197,94,.3)}
.badge-blue{color:#a5b4fc;background:rgba(99,102,241,.14);border-color:rgba(99,102,241,.35)}
.notice{padding:14px 16px;border-radius:12px;border:1px solid rgba(245,158,11,.28);background:rgba(245,158,11,.07);color:#fcd34d;font-size:.84rem}
.safe-notice{padding:14px 16px;border-radius:12px;border:1px solid rgba(34,197,94,.25);background:rgba(34,197,94,.06);color:#bbf7d0;font-size:.82rem}

/* Streamlit widgets */
div[data-testid="stMetric"]{padding:16px;border-radius:16px;border:1px solid var(--line);
 background:linear-gradient(160deg,var(--card2),var(--card))}
[data-testid="stMetricLabel"],[data-testid="stMetricLabel"] *{color:var(--mut)!important;font-size:.78rem!important;font-weight:600}
[data-testid="stMetricValue"]{font-weight:700;letter-spacing:-.02em;line-height:1.3}
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{font-size:1.4rem!important;font-weight:700!important;white-space:normal!important;overflow:visible!important;text-overflow:clip!important;line-height:1.3!important;word-break:break-word}
.panel h1,.panel h2,.panel h3{font-size:1.2rem!important;font-weight:700;letter-spacing:-.02em}
.stButton>button,.stFormSubmitButton>button{border-radius:10px;font-weight:700;border:1px solid var(--line);transition:.15s}
.stButton>button[kind="primary"],.stFormSubmitButton>button{background:linear-gradient(90deg,#ff5d73,#8b93ff);border:0;color:#fff}
.stButton>button:hover,.stFormSubmitButton>button:hover{transform:translateY(-1px);box-shadow:0 8px 20px rgba(99,102,241,.3)}
/* Fields: fill + border + radius come from .streamlit/config.toml (secondaryBackgroundColor, showWidgetBorder, borderColor, baseRadius) so they work for every widget incl. dropdowns */
[data-testid="stWidgetLabel"] p{color:#eef2ff!important;font-weight:600;font-size:.86rem}
[data-testid="stForm"]{background:linear-gradient(160deg,#18274f,#111b3d)!important;border:1px solid var(--line);border-radius:18px;padding:24px;box-shadow:0 14px 34px rgba(6,10,32,.40)}
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea,[data-testid="stNumberInput"] input{color:#fff!important}
[data-testid="stTextInput"] input::placeholder,[data-testid="stTextArea"] textarea::placeholder{color:#b9c5ee!important;opacity:.85}
[data-testid="stFileUploaderDropzone"]{background:rgba(139,147,255,.16)!important;border:1.5px dashed #9aa3ff!important;border-radius:14px}
[data-testid="stExpander"]{border:1px solid var(--line);border-radius:12px;background:var(--card)}
[data-testid="stTabs"] [role="tablist"]{gap:14px;border-bottom:1px solid var(--line);padding-bottom:2px}
[data-testid="stTabs"] button[role="tab"]{font-weight:600;border-radius:10px 10px 0 0;padding:10px 18px;margin-right:8px;transition:.15s}
[data-testid="stTabs"] button[role="tab"]:hover{background:rgba(139,147,255,.14)}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{background:rgba(139,147,255,.20)}
[data-testid="stTabs"] button[role="tab"] p{font-size:.92rem}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px}
.stDataFrame{border:1px solid var(--line);border-radius:12px;overflow:hidden}
"""
    # Streamlit's markdown parser ends an HTML block at any blank line, which makes the
    # rest of the CSS render as visible text. Strip blank lines before injecting.
    css = "\n".join(line for line in css.splitlines() if line.strip())
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def page_hero(kicker, title, subtitle):
    st.markdown(f'<div class="hero"><div class="hero-kicker">{kicker}</div><h1>{title}</h1><p>{subtitle}</p></div>',
                unsafe_allow_html=True)


def kpi_row(items):
    """items: list of (label, value, icon, tone, hint)"""
    for col, (label, value, icon, tone, hint) in zip(st.columns(len(items), gap="medium"), items):
        col.markdown(
            f'<div class="kpi" style="--c:{TONES.get(tone, tone)}"><div class="kpi-top">'
            f'<span class="kpi-label">{label}</span><span class="kpi-icon">{icon}</span></div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-hint">{hint}</div></div>',
            unsafe_allow_html=True)


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def style_fig(fig, height=300):
    fig.update_layout(height=height, margin=dict(l=8, r=8, t=8, b=8), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color="#dbe4ff"),
                      legend=dict(orientation="h", y=-0.15))
    fig.update_xaxes(gridcolor="rgba(203,213,245,.15)")
    fig.update_yaxes(gridcolor="rgba(203,213,245,.15)")
    if fig.data and fig.data[0].type == "scattermap":
        fig.update_layout(map_style="carto-voyager")  # brighter map
    return fig


def severity_badge(severity):
    css = {"Critical": "badge-red", "High": "badge-orange", "Medium": "badge-yellow", "Low": "badge-green"}.get(severity, "")
    return f'<span class="badge {css}">{severity or "Unknown"}</span>'


def status_badge(status):
    css = {"Pending": "badge-yellow", "Under Review": "badge-blue", "Approved": "badge-green",
           "Assigned": "badge-blue", "In Progress": "badge-orange", "Resolved": "badge-green"}.get(status, "")
    return f'<span class="badge {css}">{status or "Unknown"}</span>'


def sidebar_navigation():
    icons = dict(NAV)
    with st.sidebar:
        st.markdown('<div class="brand"><div class="logo">🚨</div><div><div class="brand-title">RescueMind <span>AI</span></div>'
                    '<div class="brand-sub">Emergency coordination center</div></div></div>'
                    '<div class="nav-label">NAVIGATION</div>', unsafe_allow_html=True)
        page = st.radio("Navigation", [n for n, _ in NAV], label_visibility="collapsed",
                        format_func=lambda n: f"{icons[n]}   {n}")
        st.markdown('<div class="status-card"><div class="status-row"><span class="dot"></span>All systems online</div>'
                    '<div class="status-row">🛡️ Human approval required</div>'
                    '<div class="status-row">📡 Simulated emergency data</div></div>', unsafe_allow_html=True)
    return page
