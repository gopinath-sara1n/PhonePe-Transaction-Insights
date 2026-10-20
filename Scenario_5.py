import streamlit as st
import pandas as pd
import plotly.express as px
from db import read_sql

st.title("💼 Insurance Engagement & Opportunity Deep-Dive")
st.markdown("Examine insurance transaction distribution, average policy values, district-level performance, and market penetration headroom.")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
insurance_query = """
SELECT state, year, quarter, transcation_count, transcation_amount
FROM aggregated_insurance
"""

district_query = """
SELECT state, year, quarter, district_name, total_count, total_amount
FROM map_insurance
"""

user_query = """
SELECT state, year, quarter, district_name, registered_users
FROM map_user
"""

df_ins = read_sql(insurance_query)
df_district = read_sql(district_query)
df_user = read_sql(user_query)

# ---------------------------------------------------
# CREATE PERIOD
# ---------------------------------------------------
df_ins["period"] = df_ins["year"].astype(str) + "-Q" + df_ins["quarter"].astype(str)
df_district["period"] = df_district["year"].astype(str) + "-Q" + df_district["quarter"].astype(str)
df_user["period"] = df_user["year"].astype(str) + "-Q" + df_user["quarter"].astype(str)

# ---------------------------------------------------
# USER AGGREGATION
# ---------------------------------------------------
df_user_state = df_user.groupby(["state", "period"])["registered_users"].sum().reset_index()

# ---------------------------------------------------
# MERGE DATA
# ---------------------------------------------------
df_merge = pd.merge(df_ins, df_user_state, on=["state", "period"], how="left")

df_merge["avg_transaction_value"] = (
    df_merge["transcation_amount"] / df_merge["transcation_count"].replace(0, float('nan'))
).fillna(0)

# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------
st.sidebar.markdown("### 🔍 Insurance Filters")

states = ["All"] + sorted(df_merge["state"].dropna().unique().tolist())
periods = ["All"] + sorted(df_merge["period"].dropna().unique().tolist())

selected_state = st.sidebar.selectbox("Select State", states)
selected_period = st.sidebar.selectbox("Select Period", periods)

df_filtered = df_merge.copy()

if selected_state != "All":
    df_filtered = df_filtered[df_filtered["state"] == selected_state]

# ---------------------------------------------------
# SNAPSHOT PERIOD
# ---------------------------------------------------
if selected_period == "All":
    snapshot_period = df_merge["period"].max()
else:
    snapshot_period = selected_period

df_snapshot = df_filtered[df_filtered["period"] == snapshot_period]

st.info(f"📌 Showing Metrics for Snapshot Period: **{snapshot_period}**")

# ---------------------------------------------------
# KPI METRICS
# ---------------------------------------------------
total_transactions = int(df_snapshot["transcation_count"].sum()) if not df_snapshot.empty else 0
total_value = float(df_snapshot["transcation_amount"].sum()) if not df_snapshot.empty else 0.0
avg_value = round(total_value / total_transactions, 2) if total_transactions > 0 else 0.0
total_users = int(df_snapshot["registered_users"].sum()) if not df_snapshot.empty else 0

col1, col2, col3, col4 = st.columns(4)

col1.metric("👥 Registered Users", f"{total_users:,}")
col2.metric("🛡️ Insurance Policies", f"{total_transactions:,}")
col3.metric("💰 Total Insurance Value", f"₹ {total_value:,.0f}")
col4.metric("🏷️ Avg Policy Value", f"₹ {avg_value:,.2f}")

st.divider()

# ---------------------------------------------------
# PERIOD GROWTH
# ---------------------------------------------------
st.subheader("📈 Insurance Growth Trends Over Time")

growth = df_filtered.groupby("period")[["transcation_count", "transcation_amount"]].sum().reset_index()
growth["avg_value"] = (
    growth["transcation_amount"] / growth["transcation_count"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    fig1 = px.line(
        growth,
        x="period",
        y="transcation_count",
        markers=True,
        title="Insurance Transactions Growth",
        labels={"transcation_count": "Transactions", "period": "Quarter"}
    )
    fig1.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = px.line(
        growth,
        x="period",
        y="transcation_amount",
        markers=True,
        title="Insurance Value Growth (₹)",
        labels={"transcation_amount": "Total Value (₹)", "period": "Quarter"}
    )
    fig2.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig2, use_container_width=True)

fig3 = px.line(
    growth,
    x="period",
    y="avg_value",
    markers=True,
    title="Average Policy Ticket Size Growth (₹)",
    labels={"avg_value": "Avg Value (₹)", "period": "Quarter"}
)
fig3.update_layout(template="plotly_dark", height=380)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---------------------------------------------------
# STATE ANALYSIS
# ---------------------------------------------------
st.subheader("🗺️ State-Level Insurance Distribution")

state_analysis = df_snapshot.groupby("state")[["transcation_count", "transcation_amount"]].sum().reset_index()
state_analysis["avg_value"] = (
    state_analysis["transcation_amount"] / state_analysis["transcation_count"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    fig4 = px.bar(
        state_analysis.sort_values("transcation_count", ascending=False).head(15),
        x="state",
        y="transcation_count",
        color="transcation_count",
        color_continuous_scale="Purples",
        title="Top 15 States by Insurance Policies",
        labels={"transcation_count": "Transactions", "state": "State"}
    )
    fig4.update_layout(template="plotly_dark", height=420)
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4, use_container_width=True)

with col2:
    fig5 = px.bar(
        state_analysis.sort_values("transcation_amount", ascending=False).head(15),
        x="state",
        y="transcation_amount",
        color="transcation_amount",
        color_continuous_scale="Purples",
        title="Top 15 States by Insurance Value (₹)",
        labels={"transcation_amount": "Total Amount (₹)", "state": "State"}
    )
    fig5.update_layout(template="plotly_dark", height=420)
    fig5.update_xaxes(tickangle=45)
    st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------
# DISTRICT ANALYSIS
# ---------------------------------------------------
st.subheader("📍 District Performance")

district_merge = pd.merge(
    df_district,
    df_user,
    on=["state", "district_name", "year", "quarter"],
    how="left"
)
district_merge["period"] = (
    district_merge["year"].astype(str) + "-Q" + district_merge["quarter"].astype(str)
)

district_snapshot = district_merge[district_merge["period"] == snapshot_period].copy()
district_snapshot["avg_value"] = (
    district_snapshot["total_amount"] / district_snapshot["total_count"].replace(0, float('nan'))
).fillna(0)

col1, col2 = st.columns(2)

with col1:
    top_count = district_snapshot.sort_values("total_count", ascending=False).head(10)
    fig7 = px.bar(
        top_count,
        x="district_name",
        y="total_count",
        color="total_count",
        color_continuous_scale="Purples",
        title="Top 10 Districts by Policy Count",
        labels={"total_count": "Policy Count", "district_name": "District"}
    )
    fig7.update_layout(template="plotly_dark", height=420)
    fig7.update_xaxes(tickangle=45)
    st.plotly_chart(fig7, use_container_width=True)

with col2:
    top_value = district_snapshot.sort_values("total_amount", ascending=False).head(10)
    fig8 = px.bar(
        top_value,
        x="district_name",
        y="total_amount",
        color="total_amount",
        color_continuous_scale="Purples",
        title="Top 10 Districts by Insurance Value (₹)",
        labels={"total_amount": "Total Amount (₹)", "district_name": "District"}
    )
    fig8.update_layout(template="plotly_dark", height=420)
    fig8.update_xaxes(tickangle=45)
    st.plotly_chart(fig8, use_container_width=True)

# ---------------------------------------------------
# OPPORTUNITY BUBBLE CHART
# ---------------------------------------------------
st.subheader("🎯 Registered Users vs Insurance Transactions")

fig10 = px.scatter(
    df_snapshot,
    x="registered_users",
    y="transcation_count",
    size="transcation_amount",
    color="avg_transaction_value",
    hover_name="state",
    color_continuous_scale="Purples",
    title="State Opportunity Plot: Users vs Policies Bought (Bubble size = Total ₹)",
    labels={
        "registered_users": "Registered Users",
        "transcation_count": "Insurance Policies",
        "avg_transaction_value": "Avg Policy (₹)"
    }
)
fig10.update_layout(template="plotly_dark", height=520)
st.plotly_chart(fig10, use_container_width=True)

# ---------------------------------------------------
# RAW TABLE
# ---------------------------------------------------
st.subheader("📋 Insurance Engagement Data Explorer")

district_table = district_snapshot.copy()
district_table["avg_transaction_value"] = (
    district_table["total_amount"] / district_table["total_count"].replace(0, float('nan'))
).round(2).fillna(0)

table = district_table[[
    "state",
    "district_name",
    "period",
    "registered_users",
    "total_count",
    "total_amount",
    "avg_transaction_value"
]]

st.dataframe(table, use_container_width=True, hide_index=True)
