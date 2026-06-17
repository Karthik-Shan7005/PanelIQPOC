import asyncio
import anthropic
from config import ANTHROPIC_API_KEY
from schema_context import SCHEMA_CONTEXT
from sql_validator import validate_sql
from database import run_query
from result_formatter import SUMMARY_PROMPT, clean_results, recommend_chart

client       = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

def _strip_code_fences(text: str) -> str:
    """Remove markdown code fences Claude sometimes adds despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop opening fence line (```sql or ```)
        lines = lines[1:]
        # drop closing fence line if present
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text

def generate_sql(question: str) -> str:
    """
    Send question to Claude with schema context.
    Returns generated SQL string.
    """
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SCHEMA_CONTEXT,
        messages=[{"role": "user", "content": question}]
    )
    return _strip_code_fences(response.content[0].text)

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


# ── Streaming pipeline ────────────────────────────────────────────────────────

async def process_question_stream(question: str):
    """Async generator that yields SSE event dicts as the pipeline progresses."""

    # Step 1: Stream SQL generation token by token
    sql_chunks = []
    try:
        async with async_client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SCHEMA_CONTEXT,
            messages=[{"role": "user", "content": question}],
        ) as stream:
            async for token in stream.text_stream:
                sql_chunks.append(token)
                yield {"type": "sql_chunk", "content": token}
    except Exception as e:
        yield {"type": "error", "content": f"Failed to generate SQL: {e}"}
        return

    sql = _strip_code_fences("".join(sql_chunks))
    yield {"type": "sql_done", "content": sql}

    # Step 2: Validate
    validation = validate_sql(sql)
    if not validation["valid"]:
        yield {"type": "error", "content": f"SQL validation failed: {validation['reason']}"}
        return

    # Step 3: Execute query in thread pool (pyodbc is sync)
    yield {"type": "status", "content": "Querying KpiReports database…"}
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, run_query, sql)
    except Exception as e:
        yield {"type": "error", "content": str(e)}
        return

    if not result["success"]:
        yield {"type": "error", "content": result["error"]}
        return

    result = clean_results(result)
    yield {"type": "data", "content": {
        "columns": result["columns"],
        "rows":    result["rows"],
        "row_count": result["row_count"],
    }}

    # Step 4: Stream analyst summary
    if result["row_count"] == 0:
        yield {"type": "summary_done", "content": {
            "summary": "No data found for this query. Try adjusting the date range or filters.",
            "followup": "Can you show me data for a different time period?",
        }}
        yield {"type": "chart", "content": recommend_chart(result["columns"], 0)}
        yield {"type": "done"}
        return

    yield {"type": "status", "content": "Analysing results…"}

    preview = result["rows"][:20]
    result_text = (
        f"Columns: {result['columns']}\nTotal rows: {result['row_count']}\nData:\n"
        + "".join(f"  {row}\n" for row in preview)
    )

    summary_raw = []
    try:
        async with async_client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=300,
            system=SUMMARY_PROMPT,
            messages=[{"role": "user", "content":
                       f"Question asked: {question}\n\nResults:\n{result_text}"}],
        ) as stream:
            async for token in stream.text_stream:
                summary_raw.append(token)
                yield {"type": "summary_chunk", "content": token}
    except Exception:
        pass

    # Parse SUMMARY / FOLLOWUP lines
    full = "".join(summary_raw)
    summary, followup = "", ""
    for line in full.split("\n"):
        if line.startswith("SUMMARY:"):
            summary = line[len("SUMMARY:"):].strip()
        elif line.startswith("FOLLOWUP:"):
            followup = line[len("FOLLOWUP:"):].strip()

    yield {"type": "summary_done", "content": {
        "summary":  summary or full,
        "followup": followup or "Would you like to filter this data further?",
    }}
    yield {"type": "chart", "content": recommend_chart(result["columns"], result["row_count"])}
    yield {"type": "done"}