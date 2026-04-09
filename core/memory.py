import os

MEMORY_FILE = "data/memory.txt"


def save_memory(text):
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
        return "Memory saved"
    except Exception as e:
        return str(e)


def read_memory():
    try:
        if not os.path.exists(MEMORY_FILE):
            return "No memory yet"

        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return str(e)