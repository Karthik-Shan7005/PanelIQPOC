import anthropic
from config import ANTHROPIC_API_KEY
from schema_context import SCHEMA_CONTEXT

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def test_sql_generation(question: str):
    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"{'='*60}")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SCHEMA_CONTEXT,
        messages=[{"role": "user", "content": question}]
    )

    sql = response.content[0].text.strip()
    print(f"Generated SQL:\n{sql}")
    return sql

# Test questions
questions = [
    "Show me completes by market for last 6 months",
    "Give me invites, clicks and completes for March 2026",
    "What is the screenout breakdown by status group this year?",
    "Which markets have the highest incidence rate in Q1 2026?",
]

for q in questions:
    test_sql_generation(q)

print("\n" + "="*60)
print("Claude SQL Generation Test Complete!")
print("="*60)
