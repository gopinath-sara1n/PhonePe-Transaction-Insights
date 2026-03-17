import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(page_title="User Engagement Analysis", layout="wide")

st.title("📊 User Engagement and Growth Strategy")

st.write("""
This dashboard analyzes PhonePe user engagement across states and districts.
It helps identify highly engaged regions and growth opportunities.
""")

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Qwerty@123",
        database="phonepe"
    )

conn = get_connection()

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

query = """
SELECT state, year, quarter, district_name,
registered_users, app_opens
FROM map_user
"""

df = pd.read_sql(query, conn)

# --------------------------------------------------
# CREATE PERIOD
# --------------------------------------------------

df["period"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Filters")

states = ["All"] + sorted(df["state"].unique())
periods = ["All"] + sorted(df["period"].unique())

selected_state = st.sidebar.selectbox("Select State", states)
selected_period = st.sidebar.selectbox("Select Period", periods)

df_filtered = df.copy()

if selected_state != "All":
    df_filtered = df_filtered[df_filtered["state"] == selected_state]

# --------------------------------------------------
# SNAPSHOT PERIOD
# --------------------------------------------------

if selected_period == "All":
    snapshot_period = df["period"].max()
else:
    snapshot_period = selected_period

df_snapshot = df_filtered[df_filtered["period"] == snapshot_period]

st.info(f"Snapshot Period : {snapshot_period}")

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------

state_users = df_snapshot.groupby("state")["registered_users"].sum().reset_index()

total_users = int(state_users["registered_users"].sum())
total_opens = int(df_snapshot["app_opens"].sum())
engagement_ratio = round(total_opens / total_users, 2)

col1,col2,col3 = st.columns(3)

col1.metric("Total Registered Users", f"{total_users:,}")
col2.metric("Total App Opens", f"{total_opens:,}")
col3.metric("Engagement Ratio", engagement_ratio)

st.markdown("---")

# --------------------------------------------------
# USER GROWTH CHARTS
# --------------------------------------------------

st.subheader("User Growth Over Time")

trend = df.groupby("period")[["registered_users","app_opens"]].sum().reset_index()
trend["engagement_ratio"] = trend["app_opens"] / trend["registered_users"]

col1,col2 = st.columns(2)

with col1:
    fig1 = px.line(
        trend,
        x="period",
        y="registered_users",
        markers=True,
        title="Registered Users Growth"
    )
    fig1.update_layout(template="plotly_dark",height=420)
    st.plotly_chart(fig1,use_container_width=True)

with col2:
    fig2 = px.line(
        trend,
        x="period",
        y="app_opens",
        markers=True,
        title="App Opens Growth"
    )
    fig2.update_layout(template="plotly_dark",height=420)
    st.plotly_chart(fig2,use_container_width=True)

# Full width ratio chart

fig3 = px.line(
    trend,
    x="period",
    y="engagement_ratio",
    markers=True,
    title="Engagement Ratio Growth"
)

fig3.update_layout(template="plotly_dark",height=420)

st.plotly_chart(fig3,use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# STATE ANALYSIS
# --------------------------------------------------

st.subheader("State-wise User Metrics")

state_analysis = df_snapshot.groupby("state")[["registered_users","app_opens"]].sum().reset_index()

state_analysis["engagement_ratio"] = (
    state_analysis["app_opens"] /
    state_analysis["registered_users"]
)

col1,col2 = st.columns(2)

with col1:
    fig4 = px.bar(
        state_analysis.sort_values("registered_users",ascending=False),
        x="state",
        y="registered_users",
        title="Registered Users by State"
    )
    fig4.update_layout(template="plotly_dark",height=420)
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4,use_container_width=True)

with col2:
    fig5 = px.bar(
        state_analysis.sort_values("app_opens",ascending=False),
        x="state",
        y="app_opens",
        title="App Opens by State"
    )
    fig5.update_layout(template="plotly_dark",height=420)
    fig5.update_xaxes(tickangle=45)
    st.plotly_chart(fig5,use_container_width=True)

# Full width ratio chart

fig6 = px.bar(
    state_analysis.sort_values("engagement_ratio",ascending=False),
    x="state",
    y="engagement_ratio",
    title="Engagement Ratio by State"
)

fig6.update_layout(template="plotly_dark",height=420)
fig6.update_xaxes(tickangle=45)

st.plotly_chart(fig6,use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# DISTRICT ANALYSIS
# --------------------------------------------------

st.subheader("Top Engaged Districts")

district_analysis = df_snapshot.groupby("district_name")[["registered_users","app_opens"]].sum().reset_index()

district_analysis["engagement_ratio"] = (
    district_analysis["app_opens"] /
    district_analysis["registered_users"]
)

col1,col2 = st.columns(2)

with col1:
    top_users = district_analysis.sort_values("registered_users",ascending=False).head(10)

    fig7 = px.bar(
        top_users,
        x="district_name",
        y="registered_users",
        title="Top 10 Districts by Users"
    )
    fig7.update_layout(template="plotly_dark",height=420)
    fig7.update_xaxes(tickangle=45)
    st.plotly_chart(fig7,use_container_width=True)

with col2:
    top_opens = district_analysis.sort_values("app_opens",ascending=False).head(10)

    fig8 = px.bar(
        top_opens,
        x="district_name",
        y="app_opens",
        title="Top 10 Districts by App Opens"
    )
    fig8.update_layout(template="plotly_dark",height=420)
    fig8.update_xaxes(tickangle=45)
    st.plotly_chart(fig8,use_container_width=True)

# Full width ratio

top_ratio = district_analysis.sort_values("engagement_ratio",ascending=False).head(10)

fig9 = px.bar(
    top_ratio,
    x="district_name",
    y="engagement_ratio",
    title="Top 10 Districts by Engagement Ratio"
)

fig9.update_layout(template="plotly_dark",height=420)
fig9.update_xaxes(tickangle=45)

st.plotly_chart(fig9,use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# OPPORTUNITY ANALYSIS
# --------------------------------------------------

st.subheader("User Engagement Opportunity Analysis")

fig10 = px.scatter(
    state_analysis,
    x="registered_users",
    y="app_opens",
    size="registered_users",
    color="engagement_ratio",
    hover_name="state",
    color_continuous_scale="viridis",
    size_max=60,
    title="Users vs Engagement Opportunity"
)

fig10.update_layout(
    template="plotly_dark",
    height=550
)

st.plotly_chart(fig10,use_container_width=True)

st.markdown("---")

# --------------------------------------------------
# SNAPSHOT TABLE
# --------------------------------------------------

st.subheader("📋 Engagement Snapshot Table")

eng_table = df_snapshot.groupby(
["state","district_name","period"]
)[["registered_users","app_opens"]].sum().reset_index()

eng_table["engagement_ratio"] = (
eng_table["app_opens"] /
eng_table["registered_users"]
)

eng_table = eng_table.sort_values("engagement_ratio",ascending=False)

st.dataframe(eng_table,use_container_width=True)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.markdown("---")
st.caption("PhonePe User Engagement Dashboard")