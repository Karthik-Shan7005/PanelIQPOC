import anthropic
from config import ANTHROPIC_API_KEY
from schema_context import SCHEMA_CONTEXT
from database import run_query

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def generate_sql(question: str) -> str:
    """Generate SQL from natural language question"""
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        system=SCHEMA_CONTEXT,
        messages=[{"role": "user", "content": question}]
    )
    return response.content[0].text.strip()

def ask(question: str):
    """Full pipeline: question → SQL → execute → results"""
    print(f"\n{'='*60}")
    print(f"❓ Question: {question}")
    print(f"{'='*60}")

    # Step 1: Generate SQL
    print("🔄 Generating SQL...")
    sql = generate_sql(question)
    print(f"📝 SQL:\n{sql}")

    # Step 2: Execute SQL
    print(f"\n🔄 Executing against database...")
    result = run_query(sql)

    if result["success"]:
        print(f"✅ Success! {result['row_count']} rows returned")
        print(f"📊 Columns: {result['columns']}")
        print(f"📋 Results:")
        for row in result["rows"][:10]:  # Show max 10 rows
            print(f"   {row}")
        if result["row_count"] > 10:
            print(f"   ... and {result['row_count'] - 10} more rows")
    else:
        print(f"❌ Query failed: {result['error']}")

    return result

# Test all 4 questions against real database
ask("Show me completes by market for last 6 months")
ask("Give me invites, clicks and completes for March 2026")
ask("What is the screenout breakdown by status group this year?")
ask("Which markets have the highest incidence rate in Q1 2026?")

print("\n" + "="*60)
print("Full Pipeline Test Complete!")
print("="*60)
