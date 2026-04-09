import ollama
from config.settings import MODEL
from tools.system_tools import run_command, open_app
from tools.file_tools import read_file, write_file
from tools.web_tools import search_web
from core.memory import save_memory, read_memory

conversation_history = []

SYSTEM_PROMPT = """
You are Misty, a smart local AI assistant.

You can:
- Control the PC
- Read/write files
- Search web
- Remember things

TOOLS:
run_command, open_app, read_file, write_file, search_web, save_memory, read_memory

RULES:
1. Use tools only when needed
2. Store important user info using save_memory
3. Recall info using read_memory
4. Never run dangerous commands

FORMAT:
TOOL: tool_name
INPUT: input_here
"""


def chat(user_message):
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    response = ollama.chat(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                 + conversation_history
    )

    reply = response["message"]["content"]

    if reply.startswith("TOOL:"):
        result = handle_tool(reply)

        conversation_history.append({"role": "assistant", "content": reply})
        conversation_history.append({"role": "user", "content": f"Tool result: {result}"})

        final = ollama.chat(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}]
                     + conversation_history
        )

        reply = final["message"]["content"]

    conversation_history.append({
        "role": "assistant",
        "content": reply
    })

    return reply


def handle_tool(reply):
    lines = reply.split("\n")
    tool = lines[0].replace("TOOL:", "").strip()
    inp = lines[1].replace("INPUT:", "").strip() if len(lines) > 1 else ""

    tools = {
        "run_command": run_command,
        "open_app": open_app,
        "read_file": read_file,
        "write_file": lambda x: write_file(*x.split("|", 1)),
        "search_web": search_web,
        "save_memory": save_memory,
        "read_memory": lambda x: read_memory(),
    }

    if tool in tools:
        return tools[tool](inp)

    return "Unknown tool"