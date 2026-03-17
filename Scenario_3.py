import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="Insurance Penetration Analysis", layout="wide")

st.title("🛡 Insurance Penetration & Growth Potential Analysis")

st.write(
"""
This dashboard analyzes PhonePe insurance adoption across states,
tracks growth trends, and identifies untapped markets for expansion.
"""
)

# ---------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------

def get_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Qwerty@123",
        database="phonepe"
    )

def read_sql(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------

df_ins = read_sql("""
SELECT state,year,quarter,
transcation_count,transcation_amount
FROM aggregated_insurance
""")

df_district = read_sql("""
SELECT state,year,quarter,
district_name,total_count,total_amount
FROM map_insurance
""")

df_user = read_sql("""
SELECT state,year,quarter,
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
["state","period"]
)["registered_users"].sum().reset_index()


# ---------------------------------------------------
# MERGE INSURANCE + USERS
# ---------------------------------------------------

df_merge = pd.merge(
df_ins,
df_user_state,
on=["state","period"],
how="left"
)

df_merge["penetration_ratio"] = (
df_merge["transcation_count"] /
df_merge["registered_users"]
)


# ---------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------

st.sidebar.header("Filters")

states = ["All"] + sorted(df_merge["state"].unique())
periods = ["All"] + sorted(df_merge["period"].unique())

selected_state = st.sidebar.selectbox("State", states)
selected_period = st.sidebar.selectbox("Period", periods)

df_filtered = df_merge.copy()

if selected_state != "All":
    df_filtered = df_filtered[df_filtered["state"] == selected_state]

if selected_period != "All":
    df_filtered = df_filtered[df_filtered["period"] == selected_period]


# ---------------------------------------------------
# KPI METRICS
# ---------------------------------------------------

total_transactions = int(df_filtered["transcation_count"].sum())

total_value = int(df_filtered["transcation_amount"].sum())

avg_policy_value = round(total_value / total_transactions,2)

latest_users = int(df_filtered["registered_users"].sum())

penetration_ratio = round(total_transactions / latest_users,4)

col1,col2,col3,col4 = st.columns(4)

col1.metric("Total Insurance Transactions", f"{total_transactions:,}")
col2.metric("Total Insurance Value", f"{total_value:,}")
col3.metric("Average Policy Value", avg_policy_value)
col4.metric("Insurance Penetration", penetration_ratio)

st.divider()


# ---------------------------------------------------
# INSURANCE VALUE GROWTH
# ---------------------------------------------------

st.subheader("Insurance Transaction Value Growth")

growth = df_merge.groupby("period")[
"transcation_amount"
].sum().reset_index()

fig1 = px.line(
growth,
x="period",
y="transcation_amount",
markers=True,
title="Insurance Transaction Value Over Time"
)

fig1.update_layout(template="plotly_dark")

st.plotly_chart(fig1,use_container_width=True)


# ---------------------------------------------------
# INSURANCE PENETRATION GROWTH
# ---------------------------------------------------

st.subheader("Insurance Penetration Growth Over Time")

penetration_trend = df_merge.groupby("period").agg(
insurance_txn=("transcation_count","sum"),
users=("registered_users","sum")
).reset_index()

penetration_trend["penetration_ratio"] = (
penetration_trend["insurance_txn"] /
penetration_trend["users"]
)

fig_pen = px.line(
penetration_trend,
x="period",
y="penetration_ratio",
markers=True,
title="Insurance Penetration Growth"
)

fig_pen.update_layout(template="plotly_dark")

fig_pen.update_yaxes(tickformat=".2%")

st.plotly_chart(fig_pen,use_container_width=True)


# ---------------------------------------------------
# STATE INSURANCE ADOPTION
# ---------------------------------------------------

st.subheader("State-wise Insurance Adoption")

state_ins = df_filtered.groupby("state")[
"transcation_amount"
].sum().reset_index()

state_ins = state_ins.sort_values(
"transcation_amount",ascending=False
)

fig2 = px.bar(
state_ins,
x="state",
y="transcation_amount",
title="Insurance Value by State"
)

fig2.update_layout(template="plotly_dark")

st.plotly_chart(fig2,use_container_width=True)


# ---------------------------------------------------
# PENETRATION BY STATE
# ---------------------------------------------------

st.subheader("Insurance Penetration by State")

penetration = df_merge.groupby("state").agg(
insurance_txn=("transcation_count","sum"),
users=("registered_users","max")
).reset_index()

penetration["penetration_ratio"] = (
penetration["insurance_txn"] /
penetration["users"]
)

penetration = penetration.sort_values(
"penetration_ratio",ascending=False
)

fig3 = px.bar(
penetration,
x="state",
y="penetration_ratio",
title="Insurance Penetration Ratio by State"
)

fig3.update_layout(template="plotly_dark")

fig3.update_yaxes(tickformat=".2%")

st.plotly_chart(fig3,use_container_width=True)

st.subheader("Insurance Penetration Ratio by State Dataset")

st.dataframe(
    penetration,
    use_container_width=True
)


# ---------------------------------------------------
# MARKET OPPORTUNITY ANALYSIS
# ---------------------------------------------------

st.subheader("Insurance Market Opportunity Analysis")

fig4 = px.scatter(
penetration,
x="users",
y="insurance_txn",
text="state",
title="Insurance Opportunity Matrix (Users vs Policies)"
)

fig4.update_layout(template="plotly_dark")

st.plotly_chart(fig4,use_container_width=True)

st.info(
"""
States with **high user base but low insurance transactions**
represent strong opportunities for insurance expansion.
"""
)


# ---------------------------------------------------
# TOP INSURANCE DISTRICTS
# ---------------------------------------------------

st.subheader("Top Insurance Districts")

district_top = df_district.groupby(
"district_name"
)["total_amount"].sum().reset_index()

district_top = district_top.sort_values(
"total_amount",ascending=False
).head(10)

fig5 = px.bar(
district_top,
x="district_name",
y="total_amount",
title="Top 10 Districts by Insurance Value"
)

fig5.update_layout(template="plotly_dark")

st.plotly_chart(fig5,use_container_width=True)


# ---------------------------------------------------
# RAW DATA TABLE
# ---------------------------------------------------

st.subheader("Raw Insurance Dataset")

st.dataframe(
df_filtered.sort_values(
["period","state"]
),
use_container_width=True
)


# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")

st.caption("PhonePe Insurance Insights Dashboard")