import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SUMMARY_PROMPT = """
You are PanelIQ, an expert market research panel analyst.
You have just run a query and received results from a panel database.
Your job is to:
1. Write a concise 2-3 sentence analyst-style summary of the results
2. Highlight the most important finding
3. Flag anything that looks unusual or needs attention
4. Recommend 1 follow-up question the user might want to ask next

Rules:
- Be specific — use actual numbers from the results
- Be concise — maximum 4 sentences total
- Sound like a senior analyst, not a robot
- If numbers are large, format them (e.g. 378,230 not 378230)
- End with: "Follow-up: <suggested next question>"

Return your response in this exact format:
SUMMARY: <your 2-3 sentence analysis>
FOLLOWUP: <one suggested follow-up question>
"""

def format_number(val):
    """Format numbers for display"""
    if isinstance(val, float):
        if val == int(val):
            return f"{int(val):,}"
        return f"{val:,.1f}"
    if isinstance(val, int):
        return f"{val:,}"
    return val

def clean_results(result: dict) -> dict:
    """Clean and format raw query results"""
    if not result["success"]:
        return result

    # Format numbers in rows
    cleaned_rows = []
    for row in result["rows"]:
        cleaned_row = [format_number(val) if isinstance(val, (int, float)) else val for val in row]
        cleaned_rows.append(cleaned_row)

    result["rows"] = cleaned_rows
    return result

def generate_summary(question: str, result: dict) -> dict:
    """
    Generate analyst-style summary and follow-up suggestion.
    Returns dict with 'summary' and 'followup' keys.
    """
    if not result["success"] or result["row_count"] == 0:
        return {
            "summary": "No data found for this query. Try adjusting the date range or filters.",
            "followup": "Can you show me data for a different time period?"
        }

    # Prepare result preview for Claude (max 20 rows to save tokens)
    preview_rows = result["rows"][:20]
    result_text = f"Columns: {result['columns']}\n"
    result_text += f"Total rows: {result['row_count']}\n"
    result_text += "Data:\n"
    for row in preview_rows:
        result_text += f"  {row}\n"
    if result["row_count"] > 20:
        result_text += f"  ... and {result['row_count'] - 20} more rows\n"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            system=SUMMARY_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Question asked: {question}\n\nResults:\n{result_text}"
            }]
        )

        text = response.content[0].text.strip()

        # Parse summary and followup
        summary = ""
        followup = ""

        for line in text.split('\n'):
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('FOLLOWUP:'):
                followup = line.replace('FOLLOWUP:', '').strip()

        return {
            "summary": summary or text,
            "followup": followup or "Would you like to see this broken down further?"
        }

    except Exception as e:
        return {
            "summary": f"Query returned {result['row_count']} rows successfully.",
            "followup": "Would you like to filter this data further?"
        }

def recommend_chart(columns: list, row_count: int) -> str:
    """
    Recommend the best chart type based on the data structure.
    Returns chart type string.
    """
    col_lower = [c.lower() for c in columns]

    # Single row results — metric cards, no chart
    if row_count == 1:
        return "metric_cards"

    # Has a date/month/year column — line chart
    date_keywords = ['month', 'date', 'year', 'week', 'quarter', 'period']
    if any(kw in col for col in col_lower for kw in date_keywords):
        return "line_chart"

    # Has market/country/status/vendor — bar chart
    category_keywords = ['market', 'country', 'status', 'vendor', 'panel',
                        'group', 'region', 'type', 'category']
    if any(kw in col for col in col_lower for kw in category_keywords):
        if row_count <= 10:
            return "bar_chart"
        return "bar_chart_scrollable"

    # Percentage breakdown — pie chart
    pct_keywords = ['percentage', 'pct', '%', 'share', 'rate']
    if any(kw in col for col in col_lower for kw in pct_keywords):
        if row_count <= 8:
            return "pie_chart"

    # Default — table
    return "table"