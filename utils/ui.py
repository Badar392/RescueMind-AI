import streamlit as st

def inject_css():
    st.markdown("""
    <style>
    .hero {
        padding: 22px;
        border: 1px solid #1d3855;
        border-radius: 16px;
        background: linear-gradient(135deg,#0d1d32,#0a1423);
        margin-bottom: 18px;
    }
    .hero h1 { margin: 0; }
    .hero p { color: #9db1c8; margin: 5px 0 0; }
    .notice {
        padding: 12px 15px;
        border-radius: 10px;
        border: 1px solid #6e491b;
        background: #281b0c;
    }
    </style>
    """, unsafe_allow_html=True)

def sidebar_navigation():
    with st.sidebar:
        st.markdown("## 🚨 RescueMind AI")
        st.caption("Emergency Intelligence & Resource Coordination")
        st.divider()

        page = st.radio(
            "Operations",
            [
                "Command Center",
                "Report Emergency",
                "Incidents",
                "Resources",
                "AI Activity",
                "Audit Trail",
            ],
            label_visibility="collapsed",
        )

        st.divider()
        st.caption("🟢 Prototype services online")
        st.caption("🛡 Human approval required")
        st.caption("📡 Simulated emergency data")

    return page
