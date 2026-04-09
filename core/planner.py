import ollama
from config.settings import MODEL


def create_plan(user_input):
    prompt = f"""
You are an AI planner.

Break the user's request into clear steps.

User request:
{user_input}

Return steps like:
1. step one
2. step two
3. step three

Only return steps. No explanation.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]