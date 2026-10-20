import os
import json
import sqlite3
import pandas as pd
import streamlit as st

DB_FILE = os.path.join(os.path.dirname(__file__), "phonepe.db")
GEOJSON_FILE = os.path.join(os.path.dirname(__file__), "india_states.geojson")
GEOJSON_URL = "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"

def is_mysql_configured() -> bool:
    """Check if MySQL configuration is available in st.secrets or environment variables."""
    try:
        if "mysql" in st.secrets:
            return True
    except Exception:
        pass
    return bool(os.getenv("MYSQL_HOST") and os.getenv("MYSQL_USER") and os.getenv("MYSQL_DATABASE"))

def get_connection():
    """
    Returns a database connection.
    Prioritizes MySQL if configured in st.secrets or environment variables,
    otherwise seamlessly falls back to the embedded SQLite database (phonepe.db).
    """
    if is_mysql_configured():
        import pymysql
        try:
            if "mysql" in st.secrets:
                cfg = st.secrets["mysql"]
                return pymysql.connect(
                    host=cfg.get("host", "localhost"),
                    user=cfg.get("user", "root"),
                    password=cfg.get("password", ""),
                    database=cfg.get("database", "phonepe"),
                    port=int(cfg.get("port", 3306))
                )
            else:
                return pymysql.connect(
                    host=os.getenv("MYSQL_HOST", "localhost"),
                    user=os.getenv("MYSQL_USER", "root"),
                    password=os.getenv("MYSQL_PASSWORD", ""),
                    database=os.getenv("MYSQL_DATABASE", "phonepe"),
                    port=int(os.getenv("MYSQL_PORT", 3306))
                )
        except Exception as e:
            st.sidebar.warning(f"MySQL connection failed ({e}). Falling back to embedded SQLite.")

    # SQLite fallback (ideal for Streamlit Cloud and zero-config local run)
    if os.path.exists(DB_FILE):
        return sqlite3.connect(DB_FILE)
    else:
        raise FileNotFoundError(f"Database file not found at {DB_FILE}. Please ensure phonepe.db exists.")

@st.cache_data(ttl=3600, show_spinner=False)
def read_sql(query: str) -> pd.DataFrame:
    """
    Executes a SQL query and returns a pandas DataFrame with automatic caching.
    Standardizes column names to lowercase for cross-database consistency.
    """
    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn)
        df.columns = [c.lower() for c in df.columns]
        return df
    finally:
        conn.close()

@st.cache_data(ttl=86400, show_spinner=False)
def get_india_geojson():
    """Load India States GeoJSON from local file or remote fallback."""
    if os.path.exists(GEOJSON_FILE):
        try:
            with open(GEOJSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return GEOJSON_URL

def get_database_info() -> str:
    """Returns a short description of the active database backend."""
    if is_mysql_configured():
        return "MySQL (Cloud / Custom)"
    return "SQLite (Embedded, Zero-Config)"
