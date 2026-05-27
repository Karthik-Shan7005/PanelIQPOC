import pyodbc
import pandas as pd
from config import DB_CONFIG

def get_connection():
    """Create and return a SQL Server connection"""
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )
    return pyodbc.connect(conn_str)

def run_query(sql: str) -> dict:
    """Execute SQL and return results as JSON-serializable dict"""
    try:
        conn = get_connection()
        df = pd.read_sql(sql, conn)
        conn.close()

        # Replace NaN/None with "N/A" for clean JSON output
        df = df.fillna("N/A")

        return {
            "success": True,
            "columns": list(df.columns),
            "rows": df.values.tolist(),
            "row_count": len(df)
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0
        }