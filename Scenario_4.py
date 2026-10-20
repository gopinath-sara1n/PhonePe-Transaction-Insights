import streamlit as st
import pandas as pd
import plotly.express as px
from db import read_sql

st.title("👥 User Engagement and Regional Growth Strategy")
st.markdown("Analyze PhonePe registered user counts, app activity patterns, and pinpoint regional engagement hotspots.")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
query = """
SELECT state, year, quarter, district_name,
registered_users, app_opens
FROM map_user
"""

df = read_sql(query)

# --------------------------------------------------
# CREATE PERIOD
# --------------------------------------------------
df["period"] = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.markdown("### 🔍 Engagement Filters")

states = ["All"] + sorted(df["state"].dropna().unique().tolist())
periods = ["All"] + sorted(df["period"].dropna().unique().tolist())

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

st.info(f"📌 Showing Metrics for Snapshot Period: **{snapshot_period}**")

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
state_users = df_snapshot.groupby("state")["registered_users"].sum().reset_index()
total_users = int(state_users["registered_users"].sum()) if not state_users.empty else 0
total_opens = int(df_snapshot["app_opens"].sum()) if not df_snapshot.empty else 0
engagement_ratio = round(total_opens / total_users, 2) if total_users > 0 else 0.0

col1, col2, col3 = st.columns(3)

col1.metric("👥 Total Registered Users", f"{total_users:,}")
col2.metric("📲 Total App Opens", f"{total_opens:,}")
col3.metric("⚡ Engagement Ratio (Opens/User)", engagement_ratio)

st.divider()

# --------------------------------------------------
# USER GROWTH CHARTS
# --------------------------------------------------
st.subheader("📈 User Growth and Activity Over Time")

trend = df_filtered.groupby("period")[["registered_users", "app_opens"]].sum().reset_index()
trend["engagement_ratio"] = (
    trend["app_opens"] / trend["registered_users"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.line(
        trend,
        x="period",
        y="registered_users",
        markers=True,
        title="Registered Users Growth",
        labels={"registered_users": "Registered Users", "period": "Quarter"}
    )
    fig1.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.line(
        trend,
        x="period",
        y="app_opens",
        markers=True,
        title="App Opens Growth",
        labels={"app_opens": "App Opens", "period": "Quarter"}
    )
    fig2.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig2, use_container_width=True)

# Engagement ratio chart
fig3 = px.line(
    trend,
    x="period",
    y="engagement_ratio",
    markers=True,
    title="Quarterly Engagement Ratio (App Opens per User)",
    labels={"engagement_ratio": "Ratio", "period": "Quarter"}
)
fig3.update_layout(template="plotly_dark", height=380)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# --------------------------------------------------
# STATE ANALYSIS
# --------------------------------------------------
st.subheader("🗺️ State-wise User Engagement")

state_analysis = df_snapshot.groupby("state")[["registered_users", "app_opens"]].sum().reset_index()
state_analysis["engagement_ratio"] = (
    state_analysis["app_opens"] / state_analysis["registered_users"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    fig4 = px.bar(
        state_analysis.sort_values("registered_users", ascending=False).head(15),
        x="state",
        y="registered_users",
        color="registered_users",
        color_continuous_scale="Purples",
        title="Top 15 States by Registered Users",
        labels={"registered_users": "Users", "state": "State"}
    )
    fig4.update_layout(template="plotly_dark", height=420)
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    fig5 = px.bar(
        state_analysis.sort_values("app_opens", ascending=False).head(15),
        x="state",
        y="app_opens",
        color="app_opens",
        color_continuous_scale="Purples",
        title="Top 15 States by App Opens",
        labels={"app_opens": "App Opens", "state": "State"}
    )
    fig5.update_layout(template="plotly_dark", height=420)
    fig5.update_xaxes(tickangle=45)
    st.plotly_chart(fig5, use_container_width=True)

# --------------------------------------------------
# DISTRICT ANALYSIS
# --------------------------------------------------
st.subheader("📍 District-Level Leaders")

district_analysis = df_snapshot.groupby("district_name")[["registered_users", "app_opens"]].sum().reset_index()
district_analysis["engagement_ratio"] = (
    district_analysis["app_opens"] / district_analysis["registered_users"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    top_users = district_analysis.sort_values("registered_users", ascending=False).head(10)
    fig7 = px.bar(
        top_users,
        x="district_name",
        y="registered_users",
        color="registered_users",
        color_continuous_scale="Purples",
        title="Top 10 Districts by Users",
        labels={"registered_users": "Registered Users", "district_name": "District"}
    )
    fig7.update_layout(template="plotly_dark", height=420)
    fig7.update_xaxes(tickangle=45)
    st.plotly_chart(fig7, use_container_width=True)

with col2:
    top_opens = district_analysis.sort_values("app_opens", ascending=False).head(10)
    fig8 = px.bar(
        top_opens,
        x="district_name",
        y="app_opens",
        color="app_opens",
        color_continuous_scale="Purples",
        title="Top 10 Districts by App Opens",
        labels={"app_opens": "App Opens", "district_name": "District"}
    )
    fig8.update_layout(template="plotly_dark", height=420)
    fig8.update_xaxes(tickangle=45)
    st.plotly_chart(fig8, use_container_width=True)

# --------------------------------------------------
# OPPORTUNITY ANALYSIS
# --------------------------------------------------
st.subheader("🎯 User Engagement Opportunity Matrix")

fig10 = px.scatter(
    state_analysis,
    x="registered_users",
    y="app_opens",
    size="registered_users",
    color="engagement_ratio",
    hover_name="state",
    color_continuous_scale="Viridis",
    size_max=45,
    title="State Registered Users vs App Opens (Size = Users, Color = Engagement)",
    labels={"registered_users": "Registered Users", "app_opens": "App Opens", "engagement_ratio": "Engagement"}
)
fig10.update_layout(template="plotly_dark", height=520)
st.plotly_chart(fig10, use_container_width=True)

# --------------------------------------------------
# SNAPSHOT TABLE
# --------------------------------------------------
st.subheader("📋 Engagement Snapshot Data")

eng_table = df_snapshot.groupby(
    ["state", "district_name", "period"]
)[["registered_users", "app_opens"]].sum().reset_index()

eng_table["engagement_ratio"] = (
    eng_table["app_opens"] / eng_table["registered_users"].replace(0, float('nan'))
).round(2).fillna(0)

eng_table = eng_table.sort_values("engagement_ratio", ascending=False)

st.dataframe(eng_table, use_container_width=True, hide_index=True)
