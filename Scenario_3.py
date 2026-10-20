import streamlit as st
import pandas as pd
import plotly.express as px
from db import read_sql

st.title("🛡️ Insurance Penetration & Growth Potential Analysis")
st.markdown("Analyze PhonePe insurance adoption across states, track policy growth trends, and identify untapped markets for financial inclusion.")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------
df_ins = read_sql("""
SELECT state, year, quarter,
transcation_count, transcation_amount
FROM aggregated_insurance
""")

df_district = read_sql("""
SELECT state, year, quarter,
district_name, total_count, total_amount
FROM map_insurance
""")

df_user = read_sql("""
SELECT state, year, quarter,
registered_users
FROM map_user
""")

# ---------------------------------------------------
# CREATE PERIOD COLUMN
# ---------------------------------------------------
df_ins["period"] = df_ins["year"].astype(str) + "-Q" + df_ins["quarter"].astype(str)
df_district["period"] = df_district["year"].astype(str) + "-Q" + df_district["quarter"].astype(str)
df_user["period"] = df_user["year"].astype(str) + "-Q" + df_user["quarter"].astype(str)

# ---------------------------------------------------
# AGGREGATE USERS (DISTRICT → STATE)
# ---------------------------------------------------
df_user_state = df_user.groupby(
    ["state", "period"]
)["registered_users"].sum().reset_index()

# ---------------------------------------------------
# MERGE INSURANCE + USERS
# ---------------------------------------------------
df_merge = pd.merge(
    df_ins,
    df_user_state,
    on=["state", "period"],
    how="left"
)

df_merge["penetration_ratio"] = (
    df_merge["transcation_count"] / df_merge["registered_users"].replace(0, float('nan'))
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

if selected_period != "All":
    df_filtered = df_filtered[df_filtered["period"] == selected_period]

# ---------------------------------------------------
# KPI METRICS
# ---------------------------------------------------
total_transactions = int(df_filtered["transcation_count"].sum()) if not df_filtered.empty else 0
total_value = float(df_filtered["transcation_amount"].sum()) if not df_filtered.empty else 0.0
avg_policy_value = round(total_value / total_transactions, 2) if total_transactions > 0 else 0.0
latest_users = int(df_filtered["registered_users"].sum()) if not df_filtered.empty else 0
penetration_ratio = round(total_transactions / latest_users, 4) if latest_users > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)

col1.metric("🛡️ Total Insurance Txns", f"{total_transactions:,}")
col2.metric("💰 Total Insurance Value", f"₹ {total_value:,.0f}")
col3.metric("🏷️ Avg Policy Value", f"₹ {avg_policy_value:,.2f}")
col4.metric("📈 Insurance Penetration", f"{penetration_ratio:.2%}")

st.divider()

# ---------------------------------------------------
# INSURANCE VALUE & PENETRATION GROWTH
# ---------------------------------------------------
col_g1, col_g2 = st.columns(2)

growth = df_merge.groupby("period")["transcation_amount"].sum().reset_index()

with col_g1:
    st.subheader("📈 Insurance Transaction Value Growth")
    fig1 = px.line(
        growth,
        x="period",
        y="transcation_amount",
        markers=True,
        title="Insurance Transaction Value Over Time",
        labels={"transcation_amount": "Total Amount (₹)", "period": "Quarter"}
    )
    fig1.update_layout(template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

penetration_trend = df_merge.groupby("period").agg(
    insurance_txn=("transcation_count", "sum"),
    users=("registered_users", "sum")
).reset_index()

penetration_trend["penetration_ratio"] = (
    penetration_trend["insurance_txn"] / penetration_trend["users"].replace(0, float('nan'))
).fillna(0)

with col_g2:
    st.subheader("📊 Insurance Penetration Trend")
    fig_pen = px.line(
        penetration_trend,
        x="period",
        y="penetration_ratio",
        markers=True,
        title="Insurance Penetration Growth (Policies / User)",
        labels={"penetration_ratio": "Penetration Ratio", "period": "Quarter"}
    )
    fig_pen.update_layout(template="plotly_dark")
    fig_pen.update_yaxes(tickformat=".2%")
    st.plotly_chart(fig_pen, use_container_width=True)

# ---------------------------------------------------
# STATE INSURANCE ADOPTION & PENETRATION
# ---------------------------------------------------
col_s1, col_s2 = st.columns(2)

state_ins = df_filtered.groupby("state")["transcation_amount"].sum().reset_index()
state_ins = state_ins.sort_values("transcation_amount", ascending=False).head(15)

with col_s1:
    st.subheader("🏆 Insurance Value by State (Top 15)")
    fig2 = px.bar(
        state_ins,
        x="state",
        y="transcation_amount",
        color="transcation_amount",
        color_continuous_scale="Purples",
        title="Top States by Insurance Premium Value",
        labels={"transcation_amount": "Transaction Value (₹)", "state": "State"}
    )
    fig2.update_layout(template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

penetration = df_merge.groupby("state").agg(
    insurance_txn=("transcation_count", "sum"),
    users=("registered_users", "max")
).reset_index()

penetration["penetration_ratio"] = (
    penetration["insurance_txn"] / penetration["users"].replace(0, float('nan'))
).fillna(0)
penetration_top = penetration.sort_values("penetration_ratio", ascending=False).head(15)

with col_s2:
    st.subheader("🎯 Highest Insurance Penetration by State")
    fig3 = px.bar(
        penetration_top,
        x="state",
        y="penetration_ratio",
        color="penetration_ratio",
        color_continuous_scale="Purples",
        title="Top States by Insurance Penetration Ratio",
        labels={"penetration_ratio": "Penetration Ratio", "state": "State"}
    )
    fig3.update_layout(template="plotly_dark")
    fig3.update_yaxes(tickformat=".2%")
    st.plotly_chart(fig3, use_container_width=True)

# ---------------------------------------------------
# MARKET OPPORTUNITY ANALYSIS
# ---------------------------------------------------
st.subheader("🚀 Insurance Market Opportunity Matrix")
fig4 = px.scatter(
    penetration,
    x="users",
    y="insurance_txn",
    text="state",
    color="penetration_ratio",
    color_continuous_scale="Purples",
    title="Opportunity Matrix: Registered Users vs Insurance Policies Bought",
    labels={"users": "Registered Users", "insurance_txn": "Insurance Policies Bought", "penetration_ratio": "Penetration"}
)
fig4.update_layout(template="plotly_dark", height=500)
st.plotly_chart(fig4, use_container_width=True)

st.info("💡 **Insight**: States in the bottom-right (high user base, relatively low insurance volume) represent prime targets for targeted insurance campaigns.")

# ---------------------------------------------------
# TOP INSURANCE DISTRICTS
# ---------------------------------------------------
st.subheader("📍 Top 10 Insurance Districts in India")

district_top = df_district.groupby("district_name")["total_amount"].sum().reset_index()
district_top = district_top.sort_values("total_amount", ascending=False).head(10)

fig5 = px.bar(
    district_top,
    x="district_name",
    y="total_amount",
    color="total_amount",
    color_continuous_scale="Purples",
    title="Top 10 Districts by Insurance Value (All-Time)",
    labels={"total_amount": "Total Premium Amount (₹)", "district_name": "District"}
)
fig5.update_layout(template="plotly_dark")
st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------
# RAW DATA TABLE
# ---------------------------------------------------
st.subheader("📋 Insurance Dataset Explorer")
st.dataframe(
    df_filtered.sort_values(["period", "state"]),
    use_container_width=True,
    hide_index=True
)
