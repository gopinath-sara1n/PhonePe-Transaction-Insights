import streamlit as st
import pandas as pd
import plotly.express as px
from db import read_sql, get_india_geojson

# Header
st.title("🗺️ PhonePe Pulse - India Transaction Dashboard")
st.markdown("Explore national and state-level payment trends, transaction volumes, and regional leaders across India.")

# --------------------------------------------------
# Sidebar Filters
# --------------------------------------------------
filter_query = """
SELECT DISTINCT year, quarter
FROM aggregated_transaction
ORDER BY year, quarter
"""

filter_df = read_sql(filter_query)

year_list = ["All"] + sorted(filter_df["year"].dropna().unique().tolist())
quarter_list = ["All"] + sorted(filter_df["quarter"].dropna().unique().tolist())

st.sidebar.markdown("### 🔍 Dashboard Filters")
selected_year = st.sidebar.selectbox("Select Year", year_list, index=0)
selected_quarter = st.sidebar.selectbox("Select Quarter", quarter_list, index=0)

# --------------------------------------------------
# Dynamic Filter Condition
# --------------------------------------------------
base_condition = "WHERE 1=1 "

if selected_year != "All":
    base_condition += f" AND year = {selected_year}"

if selected_quarter != "All":
    base_condition += f" AND quarter = {selected_quarter}"

# ==================================================
# KPI SECTION
# ==================================================
kpi_query = f"""
SELECT 
    SUM(transcation_amount) AS total_amount,
    SUM(transcation_count) AS total_transactions
FROM aggregated_transaction
{base_condition}
"""

kpi_df = read_sql(kpi_query)

if kpi_df.empty or pd.isna(kpi_df["total_amount"].iloc[0]):
    total_amount = 0
    total_transactions = 0
else:
    total_amount = float(kpi_df["total_amount"].iloc[0])
    total_transactions = int(kpi_df["total_transactions"].iloc[0])

avg_ticket_size = total_amount / total_transactions if total_transactions > 0 else 0

# Top State
top_state_query = f"""
SELECT state, SUM(transcation_amount) AS total
FROM aggregated_transaction
{base_condition}
GROUP BY state
ORDER BY total DESC
LIMIT 1
"""

top_state_df = read_sql(top_state_query)
top_state = top_state_df["state"].iloc[0] if not top_state_df.empty else "No Data"

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 Total Transaction Value",
        value=f"₹ {total_amount:,.0f}"
    )

with col2:
    st.metric(
        label="📊 Total Transaction Count",
        value=f"{total_transactions:,.0f}"
    )

with col3:
    st.metric(
        label="🏷️ Avg Ticket Size",
        value=f"₹ {avg_ticket_size:,.2f}"
    )

with col4:
    st.metric(
        label="🏆 Top Performing State",
        value=top_state
    )

st.divider()

# ==================================================
# MAP SECTION
# ==================================================
st.subheader("📍 State-wise Transaction Distribution")

query_map = f"""
SELECT state, SUM(transcation_amount) AS total_amount, SUM(transcation_count) AS total_count
FROM aggregated_transaction
{base_condition}
GROUP BY state
"""

df_map = read_sql(query_map)

if df_map.empty:
    st.warning("⚠️ No data available for selected Year / Quarter.")
else:
    geojson_data = get_india_geojson()
    fig_map = px.choropleth(
        df_map,
        geojson=geojson_data,
        featureidkey="properties.ST_NM",
        locations="state",
        color="total_amount",
        color_continuous_scale="Purples",
        hover_name="state",
        hover_data={"total_amount": ":,.0f", "total_count": ":,.0f"},
        labels={"total_amount": "Total Amount (₹)", "total_count": "Transactions"}
    )

    fig_map.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )

    fig_map.update_layout(
        template="plotly_dark",
        margin={"r": 0, "t": 20, "l": 0, "b": 0},
        coloraxis_colorbar=dict(
            title="Transaction Amount (₹)",
            tickprefix="₹ "
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)

# ==================================================
# TOP 10 STATES BAR CHART & SUMMARY
# ==================================================
col_chart, col_stats = st.columns([3, 2])

with col_chart:
    st.subheader("📊 Top 10 States by Transaction Value")
    top_10_states = df_map.sort_values("total_amount", ascending=False).head(10)
    fig_top_bar = px.bar(
        top_10_states,
        x="total_amount",
        y="state",
        orientation="h",
        color="total_amount",
        color_continuous_scale="Purples",
        labels={"total_amount": "Transaction Value (₹)", "state": "State"}
    )
    fig_top_bar.update_layout(
        template="plotly_dark",
        yaxis={'categoryorder': 'total ascending'},
        margin={"r": 10, "t": 20, "l": 10, "b": 10}
    )
    st.plotly_chart(fig_top_bar, use_container_width=True)

with col_stats:
    st.subheader("📈 Quick Filter Summary")
    st.write(f"- **Selected Year**: `{selected_year}`")
    st.write(f"- **Selected Quarter**: `{selected_quarter}`")
    st.write(f"- **Active States Count**: `{len(df_map)}`")
    if not df_map.empty:
        top_val = df_map['total_amount'].max()
        top_name = df_map.loc[df_map['total_amount'] == top_val, 'state'].iloc[0]
        st.write(f"- **Highest State Contribution**: `{top_name}` (₹ {top_val:,.0f})")

# ==================================================
# RAW DATA TABLE
# ==================================================
st.divider()
st.subheader("📋 Transaction Data Explorer")

query_table = f"""
SELECT 
    state,
    year,
    quarter,
    SUM(transcation_count) AS transaction_count,
    SUM(transcation_amount) AS transaction_amount
FROM aggregated_transaction
{base_condition}
GROUP BY state, year, quarter
ORDER BY transaction_amount DESC
"""

df_table = read_sql(query_table)

if not df_table.empty:
    display_df = df_table.copy()
    display_df["transaction_amount"] = display_df["transaction_amount"].apply(lambda x: f"₹ {x:,.0f}")
    display_df["transaction_count"] = display_df["transaction_count"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
