import ollama
from config.settings import MODEL


def create_plan(user_input):
    if "notepad" in user_input.lower():
        return [
        "open_app:notepad",
        "type_text:hello world"
    ]
    return []