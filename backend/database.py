import re
import pyodbc
import pandas as pd
from config import DB_CONFIG

QUERY_TIMEOUT = 90   # seconds before a slow query is cancelled
ROW_LIMIT     = 5000 # hard cap — injected if Claude omits TOP


def get_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['username']};"
        f"PWD={DB_CONFIG['password']};"
        f"TrustServerCertificate=yes;"
        f"Connection Timeout=30;"
    )
    conn = pyodbc.connect(conn_str)
    conn.timeout = QUERY_TIMEOUT   # applies to every query on this connection
    return conn


def _enforce_row_limit(sql: str) -> str:
    """Inject TOP N after SELECT if the query has no TOP clause."""
    if not re.search(r'\bTOP\b', sql, re.IGNORECASE):
        sql = re.sub(r'\bSELECT\b', f'SELECT TOP {ROW_LIMIT}', sql,
                     count=1, flags=re.IGNORECASE)
    return sql


def run_query(sql: str) -> dict:
    """Execute SQL and return results as JSON-serializable dict."""
    try:
        sql = _enforce_row_limit(sql)
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