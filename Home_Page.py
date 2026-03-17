import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px

# --------------------------------------------------
# Page Config
# --------------------------------------------------

st.set_page_config(
    page_title="PhonePe Transaction Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("🗺️ Phonepe - India Transaction Heatmap")

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

selected_year = st.sidebar.selectbox("Select Year", year_list)
selected_quarter = st.sidebar.selectbox("Select Quarter", quarter_list)

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

if kpi_df.empty:
    total_amount = 0
    total_transactions = 0
else:
    total_amount = kpi_df["total_amount"].fillna(0).iloc[0]
    total_transactions = kpi_df["total_transactions"].fillna(0).iloc[0]


# --------------------------------------------------
# Top State
# --------------------------------------------------

top_state_query = f"""
SELECT state, SUM(transcation_amount) AS total
FROM aggregated_transaction
{base_condition}
GROUP BY state
ORDER BY total DESC
LIMIT 1
"""

top_state_df = read_sql(top_state_query)

if top_state_df.empty:
    top_state = "No Data"
else:
    top_state = top_state_df["state"].iloc[0]


# --------------------------------------------------
# KPI Cards
# --------------------------------------------------

col1, col2, col3 = st.columns(3)

col1.metric(
    "💰 Total Transaction Amount",
    f"₹ {total_amount:,.0f}"
)

col2.metric(
    "📊 Total Transactions",
    f"{total_transactions:,.0f}"
)

col3.metric(
    "🏆 Top Performing State",
    top_state
)

st.markdown("---")


# ==================================================
# MAP SECTION
# ==================================================

query_map = f"""
SELECT state, SUM(transcation_amount) AS total_amount
FROM aggregated_transaction
{base_condition}
GROUP BY state
"""

df_map = read_sql(query_map)

if df_map.empty:

    st.warning("⚠ No data available for selected Year / Quarter")

else:

    fig_map = px.choropleth(
        df_map,
        geojson="https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson",
        featureidkey="properties.ST_NM",
        locations="state",
        color="total_amount",
        color_continuous_scale="Blues",
        title="State-wise Transaction Amount",
        hover_data={"total_amount":":,.0f"}
    )

    fig_map.update_geos(
        fitbounds="locations",
        visible=False,
        bgcolor="rgba(0,0,0,0)"
    )

    fig_map.update_layout(
        template="plotly_dark",
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title="Transaction Amount",
            tickprefix="₹"
        )
    )

    st.plotly_chart(fig_map, use_container_width=True)


# ==================================================
# RAW DATA TABLE
# ==================================================

st.markdown("---")

st.subheader("📋 Transaction Data Table")

query_table = f"""
SELECT 
state,
year,

SUM(transcation_count) AS transaction_count,
SUM(transcation_amount) AS transaction_amount
FROM aggregated_transaction
{base_condition}
GROUP BY state, year 
ORDER BY transaction_amount DESC
"""

df_table = read_sql(query_table)

if df_table.empty:

    st.warning("⚠ No data available")

else:

    df_table["transaction_amount"] = df_table["transaction_amount"].apply(lambda x: f"₹ {x:,.0f}")
    df_table["transaction_count"] = df_table["transaction_count"].apply(lambda x: f"{x:,.0f}")

    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True
    )