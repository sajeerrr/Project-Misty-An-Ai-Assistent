import ollama
from config.settings import MODEL
from tools.system_tools import run_command, open_app
from tools.file_tools import read_file, write_file
from tools.web_tools import search_web
from core.memory import save_memory, read_memory
from core.planner import create_plan
from tools.file_tools import get_current_directory, list_files

conversation_history = []

SYSTEM_PROMPT = """
You are Misty, a local AI assistant.

IMPORTANT RULES:

1. You ONLY execute ONE step at a time
2. You ONLY use tools when clearly needed
3. NEVER invent UI actions like "File > Save"
4. ONLY use real commands or file paths

VALID EXAMPLES:

✔ open notepad → TOOL: open_app INPUT: notepad  
✔ create file → TOOL: write_file INPUT: path|content  

For write_file:
INPUT must be: filepath|content
Example:
TOOL: write_file
INPUT: test.txt|hello world

INVALID EXAMPLES:

❌ "click file menu"
❌ "File > Save"
❌ "press button"

TOOLS:
run_command, open_app, read_file, write_file, search_web, save_memory, read_memory

FORMAT (STRICT):
TOOL: tool_name
INPUT: input_here

You can:
- get current folder path using get_current_directory
- list files using list_files

Examples:

User: show file path  
→ TOOL: get_current_directory  
INPUT:

User: show files  
→ TOOL: list_files  
INPUT: .

Otherwise reply normally.
"""


def chat(user_message):
    # Step 1: create simple plan (no LLM if you followed fix)
    plan = create_plan(user_message)

    print("\n🧠 Plan:\n", plan)

    # Step 2: ask AI to execute ONLY first step
    prompt = f"""
User request: {user_message}

Execute the FIRST step only.
Use tools if needed.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    reply = response["message"]["content"]

    # Step 3: tool execution
    if reply.startswith("TOOL:"):
        result = handle_tool(reply)
        return f"✅ Executed:\n{result}"

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
        "get_current_directory": lambda x: get_current_directory(),
        "list_files": list_files,
    }

    if tool in tools:
        return tools[tool](inp)

    return "Unknown tool"