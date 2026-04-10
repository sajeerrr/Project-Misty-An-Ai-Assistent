import time
import re

try:
    import requests
except ImportError:
    requests = None

from config import MAX_HISTORY, MAX_TOKENS, MODEL_NAME, OLLAMA_URL, TEMPERATURE, get_logger
from core.memory import (
    append_conversation,
    clear_history,
    delete_memory,
    get_memory,
    list_memories,
    load_conversation,
    save_memory,
)
from core.planner import create_plan
from core.voice import (
    get_voice_status,
    listen_once,
    start_voice_mode_command,
    stop_voice_mode_command,
)
from tools.file_tools import (
    append_file,
    copy_file,
    delete_file,
    get_current_directory,
    get_file_info,
    list_files,
    move_file,
    read_excel,
    read_file,
    read_pdf,
    read_word,
    rename_file,
    search_file,
    write_file,
    zip_folder,
)
from tools.system_tools import (
    auto_search,
    click_first_result,
    media_play_pause,
    next_track,
    open_app,
    open_spotify,
    play_spotify,
    play_youtube,
    press_key,
    previous_track,
    run_command,
    save_file,
    scroll_down,
    scroll_up,
    type_text,
)
from tools.web_tools import (
    check_internet,
    download_file,
    fetch_page,
    get_news,
    get_public_ip,
    get_weather,
    open_url,
    search_images,
    search_web,
)


logger = get_logger("agent")

SYSTEM_PROMPT = """
You are a helpful personal AI assistant running locally on the user's Windows PC.

You have access to these tools:

FILE TOOLS:
- read_file(path)
- write_file(path|content)
- append_file(path|content)
- delete_file(path)
- copy_file(src|dst)
- move_file(src|dst)
- rename_file(old|new)
- list_files(folder)
- search_file(folder|name)
- get_file_info(path)
- read_pdf(path)
- read_word(path)
- read_excel(path)
- zip_folder(folder|output_zip_path)

SYSTEM TOOLS:
- run_command(cmd)
- open_app(name)
- open_spotify()
- play_spotify(song_or_playlist_or_blank_for_recent_music)
- media_play_pause()
- next_track()
- previous_track()
- auto_search(query)
- click_first_result()
- play_youtube(video_or_blank_for_random_video)
- type_text(text)
- press_key(key)
- save_file()
- scroll_down()
- scroll_up()
- get_current_directory()

WEB TOOLS:
- search_web(query)
- search_images(query)
- open_url(url)
- fetch_page(url)
- get_weather(city)
- get_news(topic)
- download_file(url|path)
- check_internet()
- get_public_ip()

MEMORY TOOLS:
- save_memory(key|value)
- get_memory(key)
- list_memories()
- delete_memory(key)
- clear_history()

VOICE TOOLS:
- start_voice_mode()
- stop_voice_mode()
- listen_once()
- get_voice_status()

Rules:
1. When you need a tool, reply only in this exact format:
TOOL: tool_name
INPUT: input_value
2. For tools with no input, leave INPUT blank.
3. If no tool is needed, reply naturally.
4. Never delete files, send dangerous commands, or shut down the PC without clear user confirmation.
5. After you receive a tool result, answer the user naturally and mention what happened.
6. For action requests like open, play, search, read, run, type, press, or fetch, do not claim success unless you called a tool first.
7. If the user says "play a song" or "play music" without naming one, use play_spotify with blank input so it resumes recent music or starts something random.
8. If the user says "play a video" without naming one, use play_youtube with blank input so it starts a random YouTube video.
9. If the user says "play another song" or asks for the next song, use next_track instead of reopening Spotify.
10. Only bring an app window to the front if the user explicitly asks to open, show, or focus it. For music playback, prefer background behavior.
11. Use recent conversation history to understand the user's short follow-up phrases and usual style, especially for media commands.
12. If the user asks to turn on voice mode, use start_voice_mode. If the user asks to turn it off, use stop_voice_mode.
"""


def _parse_pair_input(raw_input, tool_name):
    if "|" not in raw_input:
        return None, f"{tool_name} expects 'value1|value2'"
    left, right = raw_input.split("|", 1)
    return (left.strip(), right.strip()), None


def _run_pair_tool(raw_input, tool_name, tool_function):
    values, error_message = _parse_pair_input(raw_input, tool_name)
    if error_message:
        return error_message
    return tool_function(*values)


def _read_memory_from_input(raw_input):
    key = raw_input.strip()
    if not key:
        return "get_memory expects a memory key"
    return get_memory(key)


def _save_memory_from_input(raw_input):
    values, error_message = _parse_pair_input(raw_input, "save_memory")
    if error_message:
        return error_message
    return save_memory(*values)


def _no_input(tool_fn):
    return lambda _raw_input="": tool_fn()


def _start_voice_mode_from_agent(_raw_input=""):
    return start_voice_mode_command(chat)


def _listen_once_from_agent(_raw_input=""):
    captured_text = listen_once().strip()
    if not captured_text:
        return "I could not hear anything."
    return captured_text


TOOL_MAP = {
    "append_file": lambda raw_input: _run_pair_tool(raw_input, "append_file", append_file),
    "auto_search": auto_search,
    "check_internet": _no_input(check_internet),
    "clear_history": _no_input(clear_history),
    "click_first_result": _no_input(click_first_result),
    "copy_file": lambda raw_input: _run_pair_tool(raw_input, "copy_file", copy_file),
    "delete_file": delete_file,
    "delete_memory": delete_memory,
    "download_file": lambda raw_input: _run_pair_tool(raw_input, "download_file", download_file),
    "fetch_page": fetch_page,
    "get_current_directory": _no_input(get_current_directory),
    "get_file_info": get_file_info,
    "get_memory": _read_memory_from_input,
    "get_news": get_news,
    "get_public_ip": _no_input(get_public_ip),
    "get_weather": get_weather,
    "get_voice_status": _no_input(get_voice_status),
    "list_files": list_files,
    "list_memories": _no_input(list_memories),
    "listen_once": _listen_once_from_agent,
    "media_play_pause": _no_input(media_play_pause),
    "move_file": lambda raw_input: _run_pair_tool(raw_input, "move_file", move_file),
    "next_track": _no_input(next_track),
    "open_app": open_app,
    "open_spotify": _no_input(open_spotify),
    "open_url": open_url,
    "play_spotify": play_spotify,
    "play_youtube": play_youtube,
    "press_key": press_key,
    "previous_track": _no_input(previous_track),
    "read_excel": read_excel,
    "read_file": read_file,
    "read_pdf": read_pdf,
    "read_word": read_word,
    "rename_file": lambda raw_input: _run_pair_tool(raw_input, "rename_file", rename_file),
    "run_command": run_command,
    "save_file": _no_input(save_file),
    "save_memory": _save_memory_from_input,
    "scroll_down": _no_input(scroll_down),
    "scroll_up": _no_input(scroll_up),
    "search_file": lambda raw_input: _run_pair_tool(raw_input, "search_file", search_file),
    "search_images": search_images,
    "search_web": search_web,
    "start_voice_mode": _start_voice_mode_from_agent,
    "stop_voice_mode": _no_input(stop_voice_mode_command),
    "type_text": type_text,
    "write_file": lambda raw_input: _run_pair_tool(raw_input, "write_file", write_file),
    "zip_folder": lambda raw_input: _run_pair_tool(raw_input, "zip_folder", zip_folder),
}


def _parse_step(step):
    tool, raw_input = step.split(":", 1) if ":" in step else (step, "")
    return tool.strip(), raw_input.strip()


def _run_tool(tool, raw_input):
    action = TOOL_MAP.get(tool)
    if action is None:
        return f"Unknown tool: {tool}"

    try:
        result = action(raw_input)
        logger.info("Ran tool '%s' with input '%s'", tool, raw_input)
        return result
    except Exception as exc:
        logger.exception("Tool '%s' failed", tool)
        return f"{tool} failed: {exc}"


def _extract_tool_call(reply):
    tool_name = ""
    raw_input = ""

    tool_match = re.search(r"TOOL:\s*(.+?)(?=\s+INPUT:|$)", reply, re.IGNORECASE | re.DOTALL)
    input_match = re.search(r"INPUT:\s*(.*)", reply, re.IGNORECASE | re.DOTALL)

    if tool_match:
        tool_name = tool_match.group(1).strip()
    if input_match:
        raw_input = input_match.group(1).strip()

    if tool_name and tool_name not in TOOL_MAP and raw_input in TOOL_MAP:
        return raw_input, ""

    if tool_name:
        return tool_name, raw_input
    return "", ""


def _build_messages(user_message):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for message in load_conversation()[-MAX_HISTORY:]:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _call_ollama(messages):
    if requests is None:
        return "", "requests is not installed"

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE,
                    "num_predict": MAX_TOKENS,
                },
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload.get("message", {}).get("content", "")
        if not content:
            return "", "Ollama returned an empty response"
        return content.strip(), ""
    except Exception as exc:
        return "", str(exc)


def _chat_with_ollama(user_message, verbose=False):
    messages = _build_messages(user_message)
    last_tool_name = ""
    last_tool_input = ""
    fallback_plan = create_plan(user_message)

    for _ in range(3):
        reply, error_message = _call_ollama(messages)
        if error_message:
            logger.warning("Ollama chat failed: %s", error_message)
            return "", "", ""

        if verbose:
            print(f"Model -> {reply}")

        tool_name, raw_input = _extract_tool_call(reply)
        if not tool_name:
            if not last_tool_name and fallback_plan:
                logger.warning("Model skipped tool call for actionable request: %s", user_message)
                return "", "", ""
            return reply, last_tool_name, last_tool_input

        if tool_name not in TOOL_MAP:
            if not last_tool_name and fallback_plan:
                logger.warning("Model returned invalid tool '%s' for request: %s", tool_name, user_message)
                return "", "", ""
            return reply, last_tool_name, last_tool_input

        last_tool_name = tool_name
        last_tool_input = raw_input
        tool_result = _run_tool(tool_name, raw_input)

        if verbose:
            display_input = raw_input if raw_input else "no input"
            print(f"Running: {tool_name} ({display_input})")
            print(f"{tool_name} -> {tool_result}")

        messages.append({"role": "assistant", "content": reply})
        messages.append(
            {
                "role": "user",
                "content": (
                    f"Tool result for {tool_name}:\n{tool_result}\n\n"
                    "Please answer the user naturally now. "
                    "Only call another tool if it is truly needed."
                ),
            }
        )

    return "I hit the tool-call limit while handling that request.", last_tool_name, last_tool_input


def _fallback_chat(user_message, verbose=False):
    plan = create_plan(user_message)
    if not plan:
        return "I couldn't map that request to a tool, and Ollama is unavailable right now.", "", ""

    last_result = "Done"
    last_tool_name = ""
    last_tool_input = ""

    if verbose:
        print("\nFallback plan:")
        for step in plan:
            print(f"- {step}")

    for step in plan:
        tool_name, raw_input = _parse_step(step)
        last_tool_name = tool_name
        last_tool_input = raw_input

        if verbose:
            display_input = raw_input if raw_input else "no input"
            print(f"Running: {tool_name} ({display_input})")

        if tool_name == "press_key":
            time.sleep(0.5)

        last_result = _run_tool(tool_name, raw_input)

        if verbose:
            print(f"{tool_name} -> {last_result}")

        time.sleep(0.5)

    return str(last_result), last_tool_name, last_tool_input


def chat(user_message, verbose=False):
    reply, tool_name, tool_input = _chat_with_ollama(user_message, verbose=verbose)
    if not reply:
        reply, tool_name, tool_input = _fallback_chat(user_message, verbose=verbose)

    append_conversation("user", user_message)
    append_conversation("assistant", reply, tool_name=tool_name, tool_input=tool_input)
    return reply


def handle_tool(reply):
    tool_name, raw_input = _extract_tool_call(reply)
    if not tool_name:
        return "No tool specified"
    return _run_tool(tool_name, raw_input)
