import pandas as pd
import streamlit as st
import pymysql
import plotly.express as px

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="PhonePe Transaction Dynamics",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Decoding Transaction Dynamics on PhonePe")

# --------------------------------------------------
# Database Connection
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
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


# ==================================================
# 1️⃣ TOTAL TRANSACTION GROWTH
# ==================================================

query_total = """
SELECT year,
SUM(transcation_amount) AS total_amount,
SUM(transcation_count) AS total_count
FROM aggregated_transaction
GROUP BY year
ORDER BY year
"""

df_total = read_sql(query_total)

st.subheader("📈 Overall Transaction Growth")

col1, col2 = st.columns(2)

fig_count = px.line(
    df_total,
    x="year",
    y="total_count",
    markers=True,
    title="Transaction Count Growth"
)

fig_count.update_layout(template="plotly_dark")

fig_amount = px.line(
    df_total,
    x="year",
    y="total_amount",
    markers=True,
    title="Transaction Amount Growth"
)

fig_amount.update_layout(template="plotly_dark")

with col1:
    st.plotly_chart(fig_count, use_container_width=True)

with col2:
    st.plotly_chart(fig_amount, use_container_width=True)


# ==================================================
# 2️⃣ PAYMENT CATEGORY DISTRIBUTION
# ==================================================

query_category = """
SELECT transcation_type,
SUM(transcation_count) AS total_transactions,
SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
GROUP BY transcation_type
ORDER BY total_transactions DESC
"""

df_category = read_sql(query_category)

st.subheader("💳 Payment Category Distribution")

color_map = {
    "Peer-to-peer payments": "#636EFA",
    "Merchant payments": "#EF553B",
    "Recharge & bill payments": "#00CC96",
    "Financial Services": "#AB63FA",
    "Others": "#FFA15A"
}

col1, col2 = st.columns(2)

fig_cat_count = px.pie(
    df_category,
    names="transcation_type",
    values="total_transactions",
    hole=0.4,
    color="transcation_type",
    color_discrete_map=color_map,
    title="Transaction Count Distribution"
)

fig_cat_amount = px.pie(
    df_category,
    names="transcation_type",
    values="total_amount",
    hole=0.4,
    color="transcation_type",
    color_discrete_map=color_map,
    title="Transaction Amount Distribution"
)

fig_cat_count.update_layout(template="plotly_dark")
fig_cat_amount.update_layout(template="plotly_dark")

with col1:
    st.plotly_chart(fig_cat_count, use_container_width=True)

with col2:
    st.plotly_chart(fig_cat_amount, use_container_width=True)


# ==================================================
# 3️⃣ PAYMENT CATEGORY TRANSITION (MARKET SHARE)
# ==================================================

query_transition = """
SELECT transcation_type, year, quarter,
SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
GROUP BY transcation_type, year, quarter
ORDER BY year, quarter
"""

df_transition = read_sql(query_transition)

df_transition["year_quarter"] = (
    df_transition["year"].astype(str)
    + "-Q"
    + df_transition["quarter"].astype(str)
)

df_transition["quarter_total"] = df_transition.groupby(
    "year_quarter"
)["total_amount"].transform("sum")

df_transition["share_pct"] = (
    df_transition["total_amount"] / df_transition["quarter_total"]
) * 100

st.subheader("📊 Payment Category Market Share Transition")

fig_transition = px.area(
    df_transition,
    x="year_quarter",
    y="share_pct",
    color="transcation_type"
)

fig_transition.update_layout(
    template="plotly_dark",
    yaxis_title="Market Share (%)"
)

fig_transition.update_yaxes(ticksuffix="%")

st.plotly_chart(fig_transition, use_container_width=True)


# ==================================================
# 4️⃣ STATE TRANSACTION HEATMAP
# ==================================================

query_state = """
SELECT state,
SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
GROUP BY state
"""

df_state_map = read_sql(query_state)

st.subheader("🗺 State-wise Transaction Distribution")

fig_map = px.choropleth(
    df_state_map,
    geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
    featureidkey="properties.ST_NM",
    locations="state",
    color="total_amount",
    color_continuous_scale="Viridis",
    hover_data={"total_amount":":,.0f"}
)

fig_map.update_geos(
    fitbounds="locations",
    visible=False,
    bgcolor="rgba(0,0,0,0)"
)

fig_map.update_layout(
    template="plotly_dark",
    coloraxis_colorbar=dict(
        title="Transaction Amount",
        tickprefix="₹"
    )
)

st.plotly_chart(fig_map, use_container_width=True)

# ==================================================
# 5️⃣ STATE VS PAYMENT CATEGORY (STACKED BAR)
# ==================================================

query_heat = """
SELECT state, transcation_type,
SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
GROUP BY state, transcation_type
"""

df_heat = read_sql(query_heat)

# Sort states by total transaction value
state_order = (
    df_heat.groupby("state")["total_amount"]
    .sum()
    .sort_values(ascending=False)
    .index
)

df_heat["state"] = pd.Categorical(
    df_heat["state"],
    categories=state_order,
    ordered=True
)

df_heat = df_heat.sort_values("state")

st.subheader("🔥 State vs Payment Category Distribution")

fig_bar = px.bar(
    df_heat,
    y="state",
    x="total_amount",
    color="transcation_type",
    orientation="h",
    title="Payment Category Distribution Across States",
)

fig_bar.update_layout(
    template="plotly_dark",
    height=max(700, len(state_order) * 25),
    xaxis_title="Transaction Amount",
    yaxis_title="State",
    legend_title="Payment Type"
)

st.plotly_chart(fig_bar, use_container_width=True)


# ==================================================
# 6️⃣ STATE GROWTH ANALYSIS (QoQ)
# ==================================================

query_state_growth = """
SELECT state, year, quarter,
SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
GROUP BY state, year, quarter
ORDER BY state, year, quarter
"""

df_state = read_sql(query_state_growth)

df_state = df_state.sort_values(["state","year","quarter"])

df_state["prev_amount"] = df_state.groupby("state")["total_amount"].shift(1)

df_state["growth_pct"] = (
    (df_state["total_amount"] - df_state["prev_amount"])
    / df_state["prev_amount"]
) * 100

df_growth = df_state.groupby("state")["growth_pct"].mean().reset_index()

df_growth["growth_pct"] = df_growth["growth_pct"].round(2)

# Sort descending
df_growth_sorted = df_growth.sort_values("growth_pct", ascending=False)

top_growing = df_growth_sorted.head(5)
least_growing = df_growth_sorted.tail(5).sort_values("growth_pct")

st.subheader("🚀 State Growth Analysis")

col1, col2 = st.columns(2)

# -----------------------------
# TOP GROWING
# -----------------------------

with col1:

    st.markdown("### Top Growing States")

    st.dataframe(top_growing, hide_index=True)

    fig_top = px.bar(
        top_growing,
        x="state",
        y="growth_pct",
        color="growth_pct",
        title="Top 5 Growing States"
    )

    fig_top.update_layout(template="plotly_dark")

    st.plotly_chart(fig_top, use_container_width=True)


# -----------------------------
# LEAST GROWING
# -----------------------------

with col2:

    st.markdown("### Least Growing States")

    st.dataframe(least_growing, hide_index=True)

    fig_low = px.bar(
        least_growing,
        x="state",
        y="growth_pct",
        color="growth_pct",
        title="Least Growing States"
    )

    fig_low.update_layout(template="plotly_dark")

    st.plotly_chart(fig_low, use_container_width=True)

# ==================================================
# 7️⃣ TREND VALIDATION
# ==================================================

df_state["year_quarter"] = (
    df_state["year"].astype(str)
    + "-Q"
    + df_state["quarter"].astype(str)
)

top_states = top_growing["state"].tolist()
least_states = least_growing["state"].tolist()

df_top_plot = df_state[df_state["state"].isin(top_states)]
df_least_plot = df_state[df_state["state"].isin(least_states)]

st.subheader("📈 Trend for Top Growing States")

fig_top_trend = px.line(
    df_top_plot,
    x="year_quarter",
    y="total_amount",
    color="state",
    markers=True
)

fig_top_trend.update_layout(template="plotly_dark")

st.plotly_chart(fig_top_trend, use_container_width=True)


st.subheader("📉 Trend for Least Growing States")

fig_low_trend = px.line(
    df_least_plot,
    x="year_quarter",
    y="total_amount",
    color="state",
    markers=True
)

fig_low_trend.update_layout(template="plotly_dark")

st.plotly_chart(fig_low_trend, use_container_width=True)

# ==================================================
# 8 RAW GROWTH DATA
# ==================================================

st.subheader("📋 State Growth Percentage (All States)")

df_growth_sorted["growth_pct"] = df_growth_sorted["growth_pct"].round(2)
df_growth_sorted["growth_pct"] = df_growth_sorted["growth_pct"].map("{:.2f}%".format)
st.dataframe(
    df_growth_sorted,
    use_container_width=True,
    hide_index=True
)