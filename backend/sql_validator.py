import re

# Keywords that should never appear in generated SQL
FORBIDDEN_KEYWORDS = [
    'insert', 'update', 'delete', 'drop', 'truncate',
    'exec', 'execute', 'alter', 'create', 'merge',
    'xp_', 'sp_', 'openrowset', 'opendatasource'
]

def validate_sql(sql: str) -> dict:
    """
    Validates generated SQL for safety before execution.
    Returns dict with 'valid' boolean and 'reason' string.
    """
    if not sql or not sql.strip():
        return {
            "valid": False,
            "reason": "Empty SQL query received."
        }

    sql_clean = sql.strip()
    sql_lower = sql_clean.lower()

    # Rule 1: Must start with SELECT
    if not sql_lower.startswith('select'):
        return {
            "valid": False,
            "reason": "Only SELECT queries are permitted. Query must start with SELECT."
        }

    # Rule 2: No forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, sql_lower):
            return {
                "valid": False,
                "reason": f"Forbidden keyword detected: '{keyword}'. Only read operations are allowed."
            }

    # Rule 3: Must reference at least one of our approved views
    approved_views = [
        'kpisurveydata',
        'kpireportprojectdata',
        'kpisurveydataexternal'
    ]
    if not any(view in sql_lower for view in approved_views):
        return {
            "valid": False,
            "reason": "Query must reference at least one approved view."
        }

    # Rule 4: Must contain global exclusion filter
    if "engagement surveys" not in sql_lower:
        return {
            "valid": False,
            "reason": "Query missing required global exclusion filter for 'Engagement Surveys - Research'."
        }

    return {
        "valid": True,
        "reason": "OK"
    }