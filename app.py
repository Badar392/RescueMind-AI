import streamlit as st
from utils.database import init_db, get_db
from utils.seed import seed_database
from utils.ui import inject_css, sidebar_navigation
from utils.pages import (
    dashboard_page, report_page, incidents_page,
    resources_page, ai_activity_page, audit_page
)

st.set_page_config(
    page_title="RescueMind AI",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()
init_db()
seed_database()

page = sidebar_navigation()

with get_db() as db:
    if page == "Command Center":
        dashboard_page(db)
    elif page == "Report Emergency":
        report_page(db)
    elif page == "Incidents":
        incidents_page(db)
    elif page == "Resources":
        resources_page(db)
    elif page == "AI Activity":
        ai_activity_page(db)
    elif page == "Audit Trail":
        audit_page(db)
