import json
from datetime import datetime

from config import HISTORY_FILE, MAX_HISTORY, MEMORY_FILE, get_logger, read_json, write_json


logger = get_logger("memory")


def load_memory_store():
    return read_json(MEMORY_FILE, {})


def save_memory(key, value):
    memories = load_memory_store()
    memories[key] = value
    try:
        write_json(MEMORY_FILE, memories)
        logger.info("Saved memory: %s", key)
        return f"Saved memory '{key}'."
    except OSError as exc:
        logger.warning("Could not save memory '%s': %s", key, exc)
        return f"Could not save memory '{key}': {exc}"


def get_memory(key):
    memories = load_memory_store()
    if key not in memories:
        return f"No memory saved for '{key}'."
    return str(memories[key])


def list_memories():
    memories = load_memory_store()
    if not memories:
        return "No saved memories yet."
    return json.dumps(memories, indent=2)


def delete_memory(key):
    memories = load_memory_store()
    if key not in memories:
        return f"No memory saved for '{key}'."

    del memories[key]
    try:
        write_json(MEMORY_FILE, memories)
        logger.info("Deleted memory: %s", key)
        return f"Deleted memory '{key}'."
    except OSError as exc:
        logger.warning("Could not delete memory '%s': %s", key, exc)
        return f"Could not delete memory '{key}': {exc}"


def load_conversation():
    return read_json(HISTORY_FILE, [])


def save_conversation(messages):
    trimmed_messages = messages[-MAX_HISTORY:]
    try:
        write_json(HISTORY_FILE, trimmed_messages)
        logger.info("Saved conversation history with %s messages", len(trimmed_messages))
        return "Conversation history saved."
    except OSError as exc:
        logger.warning("Could not save conversation history: %s", exc)
        return f"Could not save conversation history: {exc}"


def append_conversation(role, content, tool_name="", tool_input=""):
    history = load_conversation()
    history.append(
        {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "content": content,
            "tool_name": tool_name,
            "tool_input": tool_input,
        }
    )
    return save_conversation(history)


def clear_history():
    try:
        write_json(HISTORY_FILE, [])
        logger.info("Cleared conversation history")
        return "Conversation history cleared."
    except OSError as exc:
        logger.warning("Could not clear conversation history: %s", exc)
        return f"Could not clear conversation history: {exc}"
