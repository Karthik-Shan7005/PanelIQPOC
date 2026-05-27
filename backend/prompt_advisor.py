import anthropic
import json
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

ADVISOR_PROMPT = """
You are a prompt advisor for PanelIQ — a market research panel analytics tool.

The tool can answer questions about:
- Panel Engagement: Completes, Invites, Clicks, Click Rate, Conversion Rate, IR%
- Market Performance: Country-wise breakdowns, top/bottom markets
- Project Analysis: Project health, target vs achieved, GID level rollups
- Status Analysis: Screenouts, Drop Outs, Quota Full, Quality Rejects, Fraud blocks
- Time Analysis: Monthly trends, quarterly comparisons, year-on-year
- Panel Source: Internal TPS vs External, device type, browser analysis

Given the user's partial or complete question, suggest 3 improved or related
questions that are specific, time-bound, and will return useful insights.

Rules:
- Keep each suggestion under 12 words
- Make them specific — include time periods, market names, metrics
- Vary suggestions — cover different angles of the same topic
- Return ONLY a valid JSON array of 3 strings, nothing else
- No markdown, no explanation, just the JSON array

Example input: "india"
Example output: ["Show completes for India in last 3 months", "Compare India vs USA conversion rates in Q1 2026", "What is India screenout breakdown this year?"]

Example input: "completes"
Example output: ["Show completes by market for last 6 months", "Which market had highest completes in March 2026?", "Compare monthly completes trend for 2025 vs 2026"]
"""

def get_suggestions(partial_question: str) -> list:
    """
    Returns 3 prompt suggestions based on what user is typing.
    Called on every keystroke with debouncing on frontend.
    """
    # Don't suggest for very short inputs
    if not partial_question or len(partial_question.strip()) < 3:
        return get_default_suggestions()

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=ADVISOR_PROMPT,
            messages=[{
                "role": "user",
                "content": partial_question.strip()
            }]
        )

        text = response.content[0].text.strip()

        # Clean any markdown if present
        text = text.replace('```json', '').replace('```', '').strip()

        suggestions = json.loads(text)

        # Ensure we always return exactly 3 suggestions
        if isinstance(suggestions, list) and len(suggestions) >= 3:
            return suggestions[:3]

        return get_default_suggestions()

    except Exception:
        return get_default_suggestions()

def get_default_suggestions() -> list:
    """Returns default suggestions when input is too short or API fails"""
    return [
        "Show me completes by market for last 6 months",
        "Give me invites, clicks and completes for March 2026",
        "What is the screenout breakdown by status group this year?"
    ]