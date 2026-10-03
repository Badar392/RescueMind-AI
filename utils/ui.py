import streamlit as st


def inject_css():
    st.markdown(
        """
        <style>
        /* ---------- Global ---------- */
        .stApp {
            background:
                radial-gradient(circle at 85% 0%, rgba(239,68,68,.08), transparent 28%),
                radial-gradient(circle at 15% 100%, rgba(245,158,11,.05), transparent 30%),
                #07111f;
        }

        [data-testid="stHeader"] {
            background: rgba(7,17,31,.78);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #091625 0%, #06101d 100%);
            border-right: 1px solid rgba(148,163,184,.12);
        }

        [data-testid="stSidebarContent"] {
            padding-top: 1.2rem;
        }

        .block-container {
            max-width: 1500px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        /* ---------- Sidebar ---------- */
        .brand {
            padding: 4px 4px 16px;
        }
        .brand-title {
            font-size: 1.35rem;
            font-weight: 800;
            letter-spacing: -.03em;
            color: #f8fafc;
        }
        .brand-title span {
            color: #ef4444;
        }
        .brand-subtitle {
            color: #8294aa;
            font-size: .76rem;
            line-height: 1.45;
            margin-top: 3px;
        }
        .system-chip {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            padding: 5px 9px;
            margin-top: 10px;
            border-radius: 999px;
            border: 1px solid rgba(34,197,94,.22);
            background: rgba(34,197,94,.07);
            color: #86efac;
            font-size: .68rem;
            font-weight: 700;
            letter-spacing: .02em;
        }
        .system-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 10px rgba(34,197,94,.65);
        }
        .sidebar-footer {
            margin-top: 1.5rem;
            padding: 12px;
            border: 1px solid rgba(148,163,184,.12);
            border-radius: 12px;
            background: rgba(15,23,42,.55);
        }
        .sidebar-footer-line {
            display: flex;
            gap: 8px;
            align-items: center;
            color: #94a3b8;
            font-size: .72rem;
            margin: 6px 0;
        }

        /* ---------- Hero ---------- */
        .hero {
            position: relative;
            overflow: hidden;
            padding: 26px 28px;
            border: 1px solid rgba(148,163,184,.13);
            border-radius: 18px;
            background:
                linear-gradient(135deg, rgba(15,30,51,.98), rgba(8,19,33,.98));
            box-shadow: 0 18px 45px rgba(0,0,0,.18);
            margin-bottom: 20px;
        }
        .hero:after {
            content: "";
            position: absolute;
            right: -80px;
            top: -110px;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: rgba(239,68,68,.08);
            border: 1px solid rgba(239,68,68,.08);
        }
        .hero-kicker {
            color: #f87171;
            text-transform: uppercase;
            letter-spacing: .14em;
            font-size: .68rem;
            font-weight: 800;
            margin-bottom: 7px;
        }
        .hero h1 {
            position: relative;
            z-index: 1;
            margin: 0;
            color: #f8fafc;
            font-size: 1.9rem;
            letter-spacing: -.04em;
        }
        .hero p {
            position: relative;
            z-index: 1;
            color: #94a8bf;
            margin: 7px 0 0;
            max-width: 760px;
            font-size: .9rem;
        }

        /* ---------- Cards ---------- */
        .section-title {
            color: #e2e8f0;
            font-size: 1rem;
            font-weight: 750;
            margin: 8px 0 12px;
        }
        .mini-label {
            color: #71849b;
            text-transform: uppercase;
            letter-spacing: .09em;
            font-size: .63rem;
            font-weight: 800;
        }
        .panel {
            padding: 16px 18px;
            border: 1px solid rgba(148,163,184,.12);
            border-radius: 14px;
            background: rgba(10,22,40,.72);
            box-shadow: 0 10px 30px rgba(0,0,0,.12);
        }
        .incident-card {
            padding: 13px 14px;
            margin: 8px 0;
            border: 1px solid rgba(148,163,184,.11);
            border-radius: 12px;
            background: rgba(15,23,42,.56);
        }
        .incident-code {
            color: #f8fafc;
            font-weight: 800;
            font-size: .82rem;
        }
        .incident-meta {
            color: #7f92aa;
            font-size: .69rem;
            margin-top: 4px;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 999px;
            font-size: .62rem;
            font-weight: 800;
            letter-spacing: .03em;
            border: 1px solid rgba(148,163,184,.16);
            background: rgba(100,116,139,.10);
            color: #cbd5e1;
        }
        .badge-red { color:#fca5a5; background:rgba(239,68,68,.10); border-color:rgba(239,68,68,.25); }
        .badge-orange { color:#fdba74; background:rgba(249,115,22,.10); border-color:rgba(249,115,22,.25); }
        .badge-yellow { color:#fde68a; background:rgba(234,179,8,.10); border-color:rgba(234,179,8,.25); }
        .badge-green { color:#86efac; background:rgba(34,197,94,.10); border-color:rgba(34,197,94,.25); }
        .badge-blue { color:#93c5fd; background:rgba(59,130,246,.10); border-color:rgba(59,130,246,.25); }

        /* ---------- Notices ---------- */
        .notice {
            padding: 14px 16px;
            border-radius: 13px;
            border: 1px solid rgba(245,158,11,.25);
            background: rgba(120,70,10,.13);
            color: #fcd34d;
            font-size: .82rem;
        }
        .safe-notice {
            padding: 13px 15px;
            border-radius: 12px;
            border: 1px solid rgba(34,197,94,.20);
            background: rgba(34,197,94,.06);
            color: #bbf7d0;
            font-size: .8rem;
        }

        /* ---------- Streamlit widgets ---------- */
        div[data-testid="stMetric"] {
            padding: 15px 16px;
            border-radius: 14px;
            border: 1px solid rgba(148,163,184,.12);
            background: linear-gradient(145deg, rgba(15,30,50,.82), rgba(9,20,35,.82));
            min-height: 100px;
        }
        div[data-testid="stMetricLabel"] {
            color: #8194aa;
        }
        div[data-testid="stMetricValue"] {
            color: #f8fafc;
        }

        .stButton > button {
            border-radius: 9px;
            font-weight: 700;
            border: 1px solid rgba(148,163,184,.15);
        }
        .stButton > button:hover {
            border-color: rgba(239,68,68,.45);
        }
        .stFormSubmitButton > button {
            border-radius: 9px;
            font-weight: 800;
        }
        [data-testid="stExpander"] {
            border: 1px solid rgba(148,163,184,.12);
            border-radius: 12px;
            background: rgba(10,22,40,.5);
        }
        [data-testid="stTabs"] button {
            font-weight: 700;
        }
        .stDataFrame {
            border: 1px solid rgba(148,163,184,.10);
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_hero(kicker: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-kicker">{kicker}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def severity_badge(severity: str) -> str:
    mapping = {
        "Critical": "badge-red",
        "High": "badge-orange",
        "Medium": "badge-yellow",
        "Low": "badge-green",
    }
    css = mapping.get(severity, "badge")
    return f'<span class="badge {css}">{severity or "Unknown"}</span>'


def status_badge(status: str) -> str:
    mapping = {
        "Pending": "badge-yellow",
        "Under Review": "badge-blue",
        "Approved": "badge-green",
        "Assigned": "badge-blue",
        "In Progress": "badge-orange",
        "Resolved": "badge-green",
    }
    css = mapping.get(status, "badge")
    return f'<span class="badge {css}">{status or "Unknown"}</span>'


def sidebar_navigation():
    with st.sidebar:
        st.markdown(
            """
            <div class="brand">
                <div class="brand-title">🚨 RescueMind <span>AI</span></div>
                <div class="brand-subtitle">Emergency intelligence & resource coordination command center</div>
                <div class="system-chip"><span class="system-dot"></span> SYSTEMS ONLINE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("**OPERATIONS**")
        page = st.radio(
            "Operations",
            [
                "Command Center",
                "Report Emergency",
                "Incidents",
                "Resources",
                "AI Activity",
                "Live Monitoring",
                "Audit Trail",
            ],
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div class="sidebar-footer">
                <div class="sidebar-footer-line">🟢 <span>Prototype services online</span></div>
                <div class="sidebar-footer-line">🛡️ <span>Human approval required</span></div>
                <div class="sidebar-footer-line">📡 <span>Simulated emergency data</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page
