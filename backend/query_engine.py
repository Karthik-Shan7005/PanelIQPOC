import anthropic
from config import ANTHROPIC_API_KEY
from schema_context import SCHEMA_CONTEXT
from sql_validator import validate_sql
from database import run_query
from result_formatter import clean_results, generate_summary, recommend_chart

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_sql(question: str) -> str:
    """
    Send question to Claude with schema context.
    Returns generated SQL string.
    """
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SCHEMA_CONTEXT,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text.strip()

def process_question(question: str) -> dict:
    """
    Full pipeline:
    1. Generate SQL from question
    2. Validate SQL for safety
    3. Execute SQL on database
    4. Clean and format results
    5. Generate AI summary
    6. Recommend chart type
    Returns complete response dict for frontend.
    """

    response = {
        "success": False,
        "question": question,
        "sql": "",
        "columns": [],
        "rows": [],
        "row_count": 0,
        "summary": "",
        "followup": "",
        "chart_type": "table",
        "error": ""
    }

    try:
        # Step 1: Generate SQL
        print(f"[QueryEngine] Generating SQL for: {question}")
        sql = generate_sql(question)
        response["sql"] = sql
        print(f"[QueryEngine] SQL generated: {sql[:100]}...")

        # Step 2: Validate SQL
        print(f"[QueryEngine] Validating SQL...")
        validation = validate_sql(sql)
        if not validation["valid"]:
            response["error"] = f"SQL validation failed: {validation['reason']}"
            response["summary"] = "I couldn't generate a safe query for that question. Please try rephrasing."
            print(f"[QueryEngine] Validation failed: {validation['reason']}")
            return response

        # Step 3: Execute SQL
        print(f"[QueryEngine] Executing SQL...")
        result = run_query(sql)

        if not result["success"]:
            response["error"] = result["error"]
            response["summary"] = "The query ran into an error. Please try rephrasing your question."
            print(f"[QueryEngine] Execution failed: {result['error']}")
            return response

        # Step 4: Clean results
        result = clean_results(result)
        response["columns"] = result["columns"]
        response["rows"] = result["rows"]
        response["row_count"] = result["row_count"]
        response["success"] = True

        # Step 5: Generate summary
        print(f"[QueryEngine] Generating summary...")
        summary_result = generate_summary(question, result)
        response["summary"] = summary_result["summary"]
        response["followup"] = summary_result["followup"]

        # Step 6: Recommend chart type
        response["chart_type"] = recommend_chart(result["columns"], result["row_count"])

        print(f"[QueryEngine] Complete! {result['row_count']} rows, chart: {response['chart_type']}")

    except Exception as e:
        response["error"] = str(e)
        response["summary"] = "An unexpected error occurred. Please try again."
        print(f"[QueryEngine] Unexpected error: {e}")

    return response