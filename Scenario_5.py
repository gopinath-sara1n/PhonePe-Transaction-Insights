import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(page_title="Insurance Engagement Analysis", layout="wide")

st.title("🛡 Insurance Engagement Analysis")

st.write("""
This dashboard analyzes insurance transactions across states and districts.
It helps identify demand patterns and potential growth areas for PhonePe's insurance services.
""")

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

conn = get_connection()

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

df_ins = pd.read_sql(insurance_query, conn)
df_district = pd.read_sql(district_query, conn)
df_user = pd.read_sql(user_query, conn)

# ---------------------------------------------------
# CREATE PERIOD
# ---------------------------------------------------

df_ins["period"] = df_ins["year"].astype(str) + "-Q" + df_ins["quarter"].astype(str)
df_district["period"] = df_district["year"].astype(str) + "-Q" + df_district["quarter"].astype(str)
df_user["period"] = df_user["year"].astype(str) + "-Q" + df_user["quarter"].astype(str)

# ---------------------------------------------------
# USER AGGREGATION
# ---------------------------------------------------

df_user_state = df_user.groupby(["state","period"])["registered_users"].sum().reset_index()

# ---------------------------------------------------
# MERGE DATA
# ---------------------------------------------------

df_merge = pd.merge(df_ins, df_user_state, on=["state","period"], how="left")

df_merge["avg_transaction_value"] = (
    df_merge["transcation_amount"] /
    df_merge["transcation_count"]
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

# ---------------------------------------------------
# SNAPSHOT PERIOD
# ---------------------------------------------------

if selected_period == "All":
    snapshot_period = df_merge["period"].max()
else:
    snapshot_period = selected_period

df_snapshot = df_filtered[df_filtered["period"] == snapshot_period]

st.info(f"Snapshot Period : {snapshot_period}")

# ---------------------------------------------------
# KPI METRICS
# ---------------------------------------------------

total_transactions = int(df_snapshot["transcation_count"].sum())
total_value = int(df_snapshot["transcation_amount"].sum())
avg_value = round(total_value / total_transactions,2)
total_users = int(df_snapshot["registered_users"].sum())

col1,col2,col3,col4 = st.columns(4)

col1.metric("Registered Users",f"{total_users:,}")
col2.metric("Insurance Transactions",f"{total_transactions:,}")
col3.metric("Insurance Value",f"{total_value:,}")
col4.metric("Avg Transaction Value",avg_value)

st.markdown("---")

# ---------------------------------------------------
# PERIOD GROWTH
# ---------------------------------------------------

st.subheader("Insurance Growth Over Time")

growth = df_merge.groupby("period")[[
"transcation_count",
"transcation_amount"
]].sum().reset_index()

growth["avg_value"] = growth["transcation_amount"] / growth["transcation_count"]

col1,col2 = st.columns(2)

with col1:
    fig1 = px.line(growth,x="period",y="transcation_count",markers=True,title="Transactions Growth")
    fig1.update_layout(template="plotly_dark",height=420)
    st.plotly_chart(fig1,use_container_width=True)

with col2:
    fig2 = px.line(growth,x="period",y="transcation_amount",markers=True,title="Value Growth")
    fig2.update_layout(template="plotly_dark",height=420)
    st.plotly_chart(fig2,use_container_width=True)

fig3 = px.line(growth,x="period",y="avg_value",markers=True,title="Average Value Growth")
fig3.update_layout(template="plotly_dark",height=420)

st.plotly_chart(fig3,use_container_width=True)

st.markdown("---")

# ---------------------------------------------------
# STATE ANALYSIS
# ---------------------------------------------------

st.subheader("State Insurance Engagement")

state_analysis = df_snapshot.groupby("state")[[
"transcation_count",
"transcation_amount"
]].sum().reset_index()

state_analysis["avg_value"] = (
    state_analysis["transcation_amount"] /
    state_analysis["transcation_count"]
)

col1,col2 = st.columns(2)

with col1:
    fig4 = px.bar(state_analysis.sort_values("transcation_count",ascending=False),
    x="state",y="transcation_count",title="Transactions by State")
    fig4.update_layout(template="plotly_dark",height=420)
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4,use_container_width=True)

with col2:
    fig5 = px.bar(state_analysis.sort_values("transcation_amount",ascending=False),
    x="state",y="transcation_amount",title="Value by State")
    fig5.update_layout(template="plotly_dark",height=420)
    fig5.update_xaxes(tickangle=45)
    st.plotly_chart(fig5,use_container_width=True)

fig6 = px.bar(state_analysis.sort_values("avg_value",ascending=False),
x="state",y="avg_value",title="Average Policy Value by State")

fig6.update_layout(template="plotly_dark",height=420)
fig6.update_xaxes(tickangle=45)

st.plotly_chart(fig6,use_container_width=True)

st.markdown("---")

# ---------------------------------------------------
# DISTRICT ANALYSIS
# ---------------------------------------------------

st.subheader("Top Insurance Districts")

district_merge = pd.merge(
df_district,
df_user,
on=["state","district_name","year","quarter"],
how="left"
)

district_merge["period"] = (
district_merge["year"].astype(str)+"-Q"+district_merge["quarter"].astype(str)
)

district_snapshot = district_merge[district_merge["period"] == snapshot_period]

district_snapshot["avg_value"] = (
district_snapshot["total_amount"] /
district_snapshot["total_count"]
)

col1,col2 = st.columns(2)

with col1:
    top_count = district_snapshot.sort_values("total_count",ascending=False).head(10)

    fig7 = px.bar(top_count,x="district_name",y="total_count",title="Top Districts by Transactions")
    fig7.update_layout(template="plotly_dark",height=420)
    fig7.update_xaxes(tickangle=45)
    st.plotly_chart(fig7,use_container_width=True)

with col2:
    top_value = district_snapshot.sort_values("total_amount",ascending=False).head(10)

    fig8 = px.bar(top_value,x="district_name",y="total_amount",title="Top Districts by Value")
    fig8.update_layout(template="plotly_dark",height=420)
    fig8.update_xaxes(tickangle=45)
    st.plotly_chart(fig8,use_container_width=True)

top_avg = district_snapshot.sort_values("avg_value",ascending=False).head(10)

fig9 = px.bar(top_avg,x="district_name",y="avg_value",title="Top Districts by Avg Policy Value")
fig9.update_layout(template="plotly_dark",height=420)
fig9.update_xaxes(tickangle=45)

st.plotly_chart(fig9,use_container_width=True)

st.markdown("---")

# ---------------------------------------------------
# OPPORTUNITY BUBBLE CHART
# ---------------------------------------------------

st.subheader("Insurance Growth Opportunity")

fig10 = px.scatter(
    df_snapshot,
    x="registered_users",
    y="transcation_count",
    size="transcation_amount",
    color="avg_transaction_value",
    hover_name="state",
    color_continuous_scale="viridis",
    title="Users vs Insurance Transactions"
)

fig10.update_layout(template="plotly_dark",height=520)

st.plotly_chart(fig10,use_container_width=True)

st.info("""
States with large user bases but fewer insurance transactions
represent strong growth opportunities.
""")

st.markdown("---")

# ---------------------------------------------------
# RAW TABLE
# ---------------------------------------------------

st.subheader("Insurance Engagement Table")

district_table = district_snapshot.copy()

district_table["avg_transaction_value"] = (
district_table["total_amount"] /
district_table["total_count"]
)

table = district_table[[
"state",
"district_name",
"period",
"registered_users",
"total_count",
"total_amount",
"avg_transaction_value"
]]

table["avg_transaction_value"] = table["avg_transaction_value"].round(2)

st.dataframe(table,use_container_width=True)

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")
st.caption("PhonePe Insurance Engagement Dashboard")