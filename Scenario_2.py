import streamlit as st
import pandas as pd
import plotly.express as px
from db import read_sql

st.title("📱 Device Dominance & User Engagement Analysis")
st.markdown("Analyze brand preference, mobile OS adoption patterns, and active user engagement metrics across Indian states.")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------
df_brand = read_sql("""
SELECT state, year, quarter, brand, count AS users
FROM aggregated_user
""")

df_map = read_sql("""
SELECT state, year, quarter, district_name,
registered_users, app_opens
FROM map_user
""")

# --------------------------------------------------
# CREATE PERIOD
# --------------------------------------------------
df_brand["period"] = df_brand["year"].astype(str) + "-Q" + df_brand["quarter"].astype(str)
df_map["period"] = df_map["year"].astype(str) + "-Q" + df_map["quarter"].astype(str)

# --------------------------------------------------
# DATA PREPARATION
# --------------------------------------------------
df_brand = df_brand.sort_values(["state", "brand", "year", "quarter"])
df_brand["previous_users"] = df_brand.groupby(["state", "brand"])["users"].shift(1)
df_brand["growth"] = df_brand["users"] - df_brand["previous_users"]
df_brand["growth_percent"] = (df_brand["growth"] / df_brand["previous_users"]) * 100

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------
st.sidebar.markdown("### 🔍 Device Filters")

states = ["All"] + sorted(df_brand["state"].dropna().unique().tolist())
brands = ["All"] + sorted(df_brand["brand"].dropna().unique().tolist())
periods = ["All"] + sorted(df_brand["period"].dropna().unique().tolist())

selected_state = st.sidebar.selectbox("Select State", states)
selected_brand = st.sidebar.selectbox("Select Brand", brands)
selected_period = st.sidebar.selectbox("Select Period", periods)

# --------------------------------------------------
# FILTER DATA
# --------------------------------------------------
df_brand_f = df_brand.copy()
df_map_f = df_map.copy()

if selected_state != "All":
    df_brand_f = df_brand_f[df_brand_f["state"] == selected_state]
    df_map_f = df_map_f[df_map_f["state"] == selected_state]

if selected_brand != "All":
    df_brand_f = df_brand_f[df_brand_f["brand"] == selected_brand]

# --------------------------------------------------
# SNAPSHOT PERIOD
# --------------------------------------------------
if selected_period == "All":
    snapshot_period = df_map["period"].max()
else:
    snapshot_period = selected_period

df_latest = df_map_f[df_map_f["period"] == snapshot_period]
df_brand_latest = df_brand_f[df_brand_f["period"] == snapshot_period]

st.info(f"📌 Showing Metrics for Snapshot Period: **{snapshot_period}**")

# --------------------------------------------------
# CUMULATIVE DATA
# --------------------------------------------------
if selected_period == "All":
    df_map_cum = df_map_f.copy()
    df_brand_cum = df_brand_f.copy()
else:
    df_map_cum = df_map_f[df_map_f["period"] <= selected_period]
    df_brand_cum = df_brand_f[df_brand_f["period"] <= selected_period]

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------
state_users = df_latest.groupby("state")["registered_users"].sum().reset_index()
total_users = int(state_users["registered_users"].sum()) if not state_users.empty else 0
total_app_opens = int(df_map_cum["app_opens"].sum()) if not df_map_cum.empty else 0
avg_growth = round(float(df_brand_cum["growth_percent"].mean(skipna=True)), 2) if not df_brand_cum.empty else 0.0

state_opens = df_latest.groupby("state")["app_opens"].sum().reset_index()
eng = pd.merge(state_users, state_opens, on="state")
total_reg = eng["registered_users"].sum() if not eng.empty else 0
engagement_ratio = round(float(eng["app_opens"].sum() / total_reg), 2) if total_reg > 0 else 0.0

# --------------------------------------------------
# KPI DISPLAY
# --------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("👥 Registered Users", f"{total_users:,}")
col2.metric("📲 Total App Opens", f"{total_app_opens:,}")
col3.metric("📈 Avg Growth %", f"{avg_growth}%")
col4.metric("⚡ Engagement Ratio", engagement_ratio)

st.divider()

# --------------------------------------------------
# BRAND DOMINANCE & MARKET SHARE
# --------------------------------------------------
col_b1, col_b2 = st.columns(2)

brand_users = df_brand_latest.groupby("brand")["users"].sum().reset_index()
brand_users = brand_users.sort_values("users", ascending=False)

with col_b1:
    st.subheader("📊 Users by Brand")
    if not brand_users.empty:
        fig_brand_bar = px.bar(
            brand_users,
            x="brand",
            y="users",
            title="Active Users by Smartphone Brand",
            color="users",
            color_continuous_scale="Purples",
            category_orders={"brand": brand_users["brand"].tolist()},
            labels={"users": "Registered Users", "brand": "Brand"}
        )
        fig_brand_bar.update_layout(template="plotly_dark")
        st.plotly_chart(fig_brand_bar, use_container_width=True)

with col_b2:
    st.subheader("🥧 Brand Market Share")
    if not brand_users.empty:
        fig_pie = px.pie(
            brand_users,
            names="brand",
            values="users",
            hole=0.4,
            title="Brand Market Share (%)"
        )
        fig_pie.update_layout(template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)

# --------------------------------------------------
# DEVICE PREFERENCE BY STATE
# --------------------------------------------------
st.subheader("🗺️ Device Preference Across States")
state_device = df_brand_latest.groupby(["state", "brand"])["users"].sum().reset_index()
state_device = state_device.sort_values("users", ascending=False)

if not state_device.empty:
    fig_state_brand = px.bar(
        state_device,
        x="state",
        y="users",
        color="brand",
        title="Brand Preference Breakdown by State",
        labels={"users": "Users", "state": "State"}
    )
    fig_state_brand.update_layout(template="plotly_dark")
    st.plotly_chart(fig_state_brand, use_container_width=True)

# --------------------------------------------------
# USER ENGAGEMENT BY STATE
# --------------------------------------------------
st.subheader("⚡ User Engagement Ratio by State")
if not eng.empty:
    eng["engagement_ratio"] = eng["app_opens"] / eng["registered_users"]
    eng = eng.sort_values("engagement_ratio", ascending=False)

    fig_eng = px.bar(
        eng,
        x="state",
        y="engagement_ratio",
        color="engagement_ratio",
        color_continuous_scale="Purples",
        title="App Opens per Registered User by State",
        labels={"engagement_ratio": "Engagement Ratio", "state": "State"}
    )
    fig_eng.update_layout(template="plotly_dark")
    st.plotly_chart(fig_eng, use_container_width=True)

# --------------------------------------------------
# QUARTERLY DEVICE GROWTH
# --------------------------------------------------
st.subheader("📈 Quarterly Device Growth Trends")
trend = df_brand_cum.groupby(["brand", "period"])["users"].sum().reset_index()

if not trend.empty:
    fig_trend = px.line(
        trend,
        x="period",
        y="users",
        color="brand",
        markers=True,
        title="Quarterly User Growth by Device Brand",
        labels={"users": "Users", "period": "Quarter"}
    )
    fig_trend.update_layout(template="plotly_dark")
    st.plotly_chart(fig_trend, use_container_width=True)

# --------------------------------------------------
# RAW BRAND DATA
# --------------------------------------------------
st.subheader("📋 Raw Brand Dataset")
raw_brand_df = df_brand.copy()

if selected_state != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["state"] == selected_state]

if selected_brand != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["brand"] == selected_brand]

if selected_period != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["period"] == selected_period]

raw_brand_df = raw_brand_df[
    ["state", "period", "brand", "users", "previous_users", "growth", "growth_percent"]
]

st.dataframe(
    raw_brand_df.sort_values(["period", "state", "brand"]),
    use_container_width=True,
    hide_index=True
)
