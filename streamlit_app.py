import streamlit as st
from db import get_database_info

# ==================================================
# PAGE CONFIGURATION (Must be the very first Streamlit call)
# ==================================================
st.set_page_config(
    page_title="PhonePe Pulse Analytics",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================================================
# SIDEBAR BRANDING & INFO
# ==================================================
st.sidebar.markdown(
    """
    <div style="text-align: center; padding: 10px 0;">
        <h2 style="color: #6739B7; margin: 0;">💜 PhonePe Pulse</h2>
        <p style="color: #888; font-size: 13px; margin: 2px 0 10px 0;">Transaction & User Insights Dashboard</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Display database backend
db_backend = get_database_info()
st.sidebar.caption(f"⚡ **Backend**: `{db_backend}`")

# ==================================================
# NAVIGATION DEFINITIONS
# ==================================================
home_page = st.Page("Home_Page.py", title="Overview & Heatmap", icon="🏠", default=True)
scenario_1 = st.Page("Scenario_1.py", title="Transaction Dynamics", icon="💳")
scenario_2 = st.Page("Scenario_2.py", title="Device & User Engagement", icon="📱")
scenario_3 = st.Page("Scenario_3.py", title="Insurance Penetration", icon="🛡️")
scenario_4 = st.Page("Scenario_4.py", title="User Growth & District Strategy", icon="👥")
scenario_5 = st.Page("Scenario_5.py", title="Insurance Opportunity Analysis", icon="💼")

pg = st.navigation(
    {
        "Overview": [home_page],
        "Deep-Dive Analytics": [scenario_1, scenario_2, scenario_3, scenario_4, scenario_5]
    }
)

# Run page
pg.run()

# Sidebar footer
st.sidebar.markdown("---")
st.sidebar.caption("Data source: PhonePe Pulse Open Data")
