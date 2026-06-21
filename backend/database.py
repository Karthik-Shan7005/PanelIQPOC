import re
import decimal
import pyodbc
import pandas as pd
from config import DB_CONFIG

ROW_LIMIT = 5000  # hard cap — injected if Claude omits TOP


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
    return pyodbc.connect(conn_str)


def _enforce_row_limit(sql: str) -> str:
    """Inject TOP N after SELECT if the query has no TOP or OFFSET clause."""
    has_top    = re.search(r'\bTOP\b',    sql, re.IGNORECASE)
    has_offset = re.search(r'\bOFFSET\b', sql, re.IGNORECASE)
    if has_offset:
        # TOP and OFFSET cannot coexist in SQL Server — strip the OFFSET/FETCH clause
        # and replace with TOP N so we still cap results.
        sql = re.sub(
            r'\bORDER\s+BY\b(.+?)\bOFFSET\b.+$', r'ORDER BY\1',
            sql, flags=re.IGNORECASE | re.DOTALL
        )
        if not re.search(r'\bTOP\b', sql, re.IGNORECASE):
            sql = re.sub(r'\bSELECT\b', f'SELECT TOP {ROW_LIMIT}', sql,
                         count=1, flags=re.IGNORECASE)
    elif not has_top:
        sql = re.sub(r'\bSELECT\b', f'SELECT TOP {ROW_LIMIT}', sql,
                     count=1, flags=re.IGNORECASE)
    return sql


def run_query(sql: str) -> dict:
    """Execute SQL and return results as JSON-serializable dict."""
    conn = None
    try:
        sql = _enforce_row_limit(sql)
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description]
        # Convert non-JSON-serializable types at source (Decimal, datetime, etc.)
        rows = [
            [float(v) if isinstance(v, decimal.Decimal)
             else v.isoformat() if hasattr(v, 'isoformat') and not isinstance(v, str)
             else v
             for v in row]
            for row in cursor.fetchall()
        ]
        conn.close()
        conn = None

        df = pd.DataFrame(rows, columns=columns)
        df = df.fillna("N/A")

        # Convert datetime/timestamp columns to strings so they're JSON-serializable
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime('%Y-%m-%d').where(df[col].notna(), "N/A")
            elif df[col].dtype == object:
                df[col] = df[col].apply(
                    lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
                    if hasattr(v, 'strftime') else v
                )

        return {
            "success": True,
            "columns": list(df.columns),
            "rows": df.values.tolist(),
            "row_count": len(df)
        }

    except Exception as e:
        err_str = str(e)
        if 'HYT00' in err_str or 'timeout' in err_str.lower():
            msg = (
                "The query took too long to run. "
                "Try narrowing the date range (e.g. a single month instead of all-time) "
                "or filtering by a specific market."
            )
        else:
            msg = err_str
        return {
            "success": False,
            "error": msg,
            "columns": [],
            "rows": [],
            "row_count": 0
        }
    finally:
        if conn:
            conn.close()