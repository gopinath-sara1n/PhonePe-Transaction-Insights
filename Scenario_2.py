import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(page_title="PhonePe Device Analysis", page_icon="📱", layout="wide")

st.title("📱 Device Dominance & User Engagement Analysis")

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

def read_sql(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df_brand = read_sql("""
SELECT state,year,quarter,brand,count AS users
FROM aggregated_user
""")

df_map = read_sql("""
SELECT state,year,quarter,district_name,
registered_users,app_opens
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

df_brand = df_brand.sort_values(["state","brand","year","quarter"])

df_brand["previous_users"] = df_brand.groupby(["state","brand"])["users"].shift(1)

df_brand["growth"] = df_brand["users"] - df_brand["previous_users"]

df_brand["growth_percent"] = (df_brand["growth"] / df_brand["previous_users"]) * 100

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("Filters")

states = ["All"] + sorted(df_brand["state"].unique())
brands = ["All"] + sorted(df_brand["brand"].unique())
periods = ["All"] + sorted(df_brand["period"].unique())

selected_state = st.sidebar.selectbox("State", states)
selected_brand = st.sidebar.selectbox("Brand", brands)
selected_period = st.sidebar.selectbox("Period", periods)

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

df_latest = df_map[df_map["period"] == snapshot_period]
df_brand_latest = df_brand[df_brand["period"] == snapshot_period]

st.info(f"Snapshot Period : {snapshot_period}")

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

total_users = int(state_users["registered_users"].sum())

total_app_opens = int(df_map_cum["app_opens"].sum())

avg_growth = round(df_brand_cum["growth_percent"].mean(skipna=True),2)

state_opens = df_latest.groupby("state")["app_opens"].sum().reset_index()

eng = pd.merge(state_users,state_opens,on="state")

engagement_ratio = round((eng["app_opens"].sum()/eng["registered_users"].sum()),2)

# --------------------------------------------------
# KPI DISPLAY
# --------------------------------------------------

col1,col2,col3,col4 = st.columns(4)

col1.metric("Total Registered Users",f"{total_users:,}")
col2.metric("Total App Opens",f"{total_app_opens:,}")
col3.metric("Average Growth %",avg_growth)
col4.metric("Engagement Ratio",engagement_ratio)

st.divider()

# --------------------------------------------------
# BRAND DOMINANCE
# --------------------------------------------------

st.subheader("Device Brand Dominance")

brand_users = df_brand_latest.groupby("brand")["users"].sum().reset_index()

brand_users = brand_users.sort_values("users", ascending=False)

fig = px.bar(
    brand_users,
    x="brand",
    y="users",
    title="Users by Brand",
    category_orders={"brand": brand_users["brand"].tolist()}
)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# MARKET SHARE
# --------------------------------------------------

st.subheader("Device Market Share")

fig = px.pie(brand_users,names="brand",values="users",hole=0.4)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# DEVICE PREFERENCE BY STATE
# --------------------------------------------------

st.subheader("Device Preference by State")

state_device = df_brand_latest.groupby(["state","brand"])["users"].sum().reset_index()

state_device = state_device.sort_values("users", ascending=False)

fig = px.bar(
    state_device,
    x="state",
    y="users",
    color="brand"
)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# USER ENGAGEMENT BY STATE
# --------------------------------------------------

st.subheader("User Engagement Ratio by State")

eng["engagement_ratio"] = eng["app_opens"]/eng["registered_users"]

eng = eng.sort_values("engagement_ratio", ascending=False)

fig = px.bar(
    eng,
    x="state",
    y="engagement_ratio"
)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# DEVICE UTILIZATION
# --------------------------------------------------

st.subheader("Device Utilization")

util = df_brand_latest.groupby("brand").agg(
total_users=("users","sum"),
avg_growth=("growth","mean")
).reset_index()

util["avg_growth"]=util["avg_growth"].fillna(0)

fig = px.scatter(util,x="total_users",y="avg_growth",text="brand")

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# QUARTERLY DEVICE GROWTH
# --------------------------------------------------

st.subheader("Quarterly Device Growth")

trend = df_brand_cum.groupby(["brand","period"])["users"].sum().reset_index()

fig = px.line(trend,x="period",y="users",color="brand",markers=True)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# ENGAGEMENT RATIO GROWTH
# --------------------------------------------------

st.subheader("Engagement Ratio Growth")

eng_trend = df_map_cum.groupby("period")[["registered_users","app_opens"]].sum().reset_index()

eng_trend["engagement_ratio"] = eng_trend["app_opens"] / eng_trend["registered_users"]

fig = px.line(eng_trend,x="period",y="engagement_ratio",markers=True)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# REGISTERED USERS GROWTH
# --------------------------------------------------

st.subheader("Registered Users Growth")

fig = px.line(eng_trend,x="period",y="registered_users",markers=True)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# APP OPENS GROWTH
# --------------------------------------------------

st.subheader("App Opens Growth")

fig = px.line(eng_trend,x="period",y="app_opens",markers=True)

fig.update_layout(template="plotly_dark")

st.plotly_chart(fig,use_container_width=True)

# --------------------------------------------------
# RAW BRAND DATA
# --------------------------------------------------

st.subheader("📊 Raw Brand Dataset")

raw_brand_df = df_brand.copy()

if selected_state != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["state"] == selected_state]

if selected_brand != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["brand"] == selected_brand]

if selected_period != "All":
    raw_brand_df = raw_brand_df[raw_brand_df["period"] == selected_period]

raw_brand_df = raw_brand_df[
    ["state","period","brand","users","previous_users","growth","growth_percent"]
]

st.dataframe(
    raw_brand_df.sort_values(["period","state","brand"]),
    use_container_width=True
)

st.divider()

st.caption("PhonePe Device Dominance Dashboard")