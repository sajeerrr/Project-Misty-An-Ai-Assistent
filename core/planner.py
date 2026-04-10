import re

from core.memory import load_conversation


def _memory_key_from_text(text):
    cleaned_text = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    if not cleaned_text:
        return "note"
    if cleaned_text.startswith("my_"):
        return cleaned_text
    return f"my_{cleaned_text}"


def _get_recent_tool_context():
    history = load_conversation()
    for item in reversed(history):
        tool_name = (item.get("tool_name") or "").strip()
        if tool_name:
            return tool_name
    return ""


def create_plan(user_input):
    raw_input = user_input.strip()
    user_input = raw_input.lower()
    recent_tool_name = _get_recent_tool_context()

    plan = []

    if not user_input:
        return plan

    if "open first result" in user_input or "click first result" in user_input:
        plan.append("click_first_result:")

    elif user_input in {"open spotify", "launch spotify", "start spotify"}:
        plan.append("open_spotify:")

    elif user_input in {
        "play a song",
        "play song",
        "play some music",
        "play music",
        "play any song",
        "play a random song",
        "play random song",
    }:
        plan.append("play_spotify:")

    elif user_input in {
        "play a video",
        "play video",
        "play any video",
        "play random video",
        "play a random video",
    }:
        plan.append("play_youtube:")

    elif any(phrase in user_input for phrase in {"pause spotify", "pause music", "resume spotify", "resume music", "play/pause spotify"}):
        plan.append("media_play_pause:")

    elif user_input in {
        "turn on voice mode",
        "start voice mode",
        "enable voice mode",
        "voice mode on",
    }:
        plan.append("start_voice_mode:")

    elif user_input in {
        "turn off voice mode",
        "stop voice mode",
        "disable voice mode",
        "voice mode off",
    }:
        plan.append("stop_voice_mode:")

    elif user_input in {"voice status", "show voice status", "is voice mode on"}:
        plan.append("get_voice_status:")

    elif user_input in {"listen once", "speak once", "hear me once"}:
        plan.append("listen_once:")

    elif any(
        phrase in user_input
        for phrase in {
            "next song",
            "next track",
            "skip song",
            "skip track",
            "play another song",
            "play next song",
            "another song",
        }
    ):
        plan.append("next_track:")

    elif any(phrase in user_input for phrase in {"previous song", "previous track", "last song", "go back song"}):
        plan.append("previous_track:")

    elif user_input in {"another one", "one more", "same again", "do that again"}:
        if recent_tool_name in {"play_spotify", "next_track", "previous_track", "media_play_pause"}:
            plan.append("next_track:")
        elif recent_tool_name == "play_youtube":
            plan.append("play_youtube:")

    elif user_input in {"play it", "continue it", "continue"}:
        if recent_tool_name in {"play_spotify", "next_track", "previous_track", "media_play_pause"}:
            plan.append("media_play_pause:")
        elif recent_tool_name == "play_youtube":
            plan.append("play_youtube:")

    elif "spotify" in user_input and user_input.startswith("play "):
        query = (
            raw_input.replace("play", "", 1)
            .replace("on spotify", "")
            .replace("in spotify", "")
            .replace("spotify", "")
            .strip()
        )
        plan.append(f"play_spotify:{query}")

    elif "spotify" in user_input and "music" in user_input:
        plan.append("open_spotify:")

    elif user_input.startswith("play ") and any(word in user_input for word in {"song", "music"}):
        query = (
            raw_input.replace("play", "", 1)
            .replace("song", "")
            .replace("music", "")
            .strip()
        )
        plan.append(f"play_spotify:{query}")

    elif recent_tool_name in {"play_spotify", "next_track", "previous_track", "media_play_pause"} and user_input.startswith("play "):
        query = raw_input.replace("play", "", 1).strip()
        if not query or query in {"another", "again"}:
            plan.append("next_track:")
        else:
            plan.append(f"play_spotify:{query}")

    elif user_input.startswith("play ") and "video" in user_input:
        query = (
            raw_input.replace("play", "", 1)
            .replace("video", "")
            .strip()
        )
        plan.append(f"play_youtube:{query}")

    elif "scroll down" in user_input:
        plan.append("scroll_down:")

    elif "scroll up" in user_input:
        plan.append("scroll_up:")

    elif user_input.startswith("search the web for "):
        query = raw_input[19:].strip()
        plan.append(f"search_web:{query}")

    elif user_input.startswith("search web for "):
        query = raw_input[15:].strip()
        plan.append(f"search_web:{query}")

    elif user_input.startswith("search images for "):
        query = raw_input[18:].strip()
        plan.append(f"search_images:{query}")

    elif user_input.startswith("search "):
        query = raw_input[7:].strip()
        plan.append(f"auto_search:{query}")

    elif user_input.startswith("open url "):
        plan.append(f"open_url:{raw_input[9:].strip()}")

    elif user_input.startswith("open http://") or user_input.startswith("open https://"):
        plan.append(f"open_url:{raw_input[5:].strip()}")

    elif user_input.startswith("fetch page "):
        plan.append(f"fetch_page:{raw_input[11:].strip()}")

    elif user_input.startswith("download the file from this url:"):
        url = raw_input.split(":", 1)[1].strip()
        plan.append(f"download_file:{url}|downloaded_file")

    elif user_input.startswith("weather in "):
        plan.append(f"get_weather:{raw_input[11:].strip()}")

    elif "weather" in user_input and " in " in user_input:
        plan.append(f"get_weather:{raw_input.rsplit(' in ', 1)[1].strip()}")

    elif user_input.startswith("get me the latest news about "):
        plan.append(f"get_news:{raw_input[29:].strip()}")

    elif user_input.startswith("latest news about "):
        plan.append(f"get_news:{raw_input[18:].strip()}")

    elif user_input in {"is my internet working", "check internet", "internet status"}:
        plan.append("check_internet:")

    elif user_input in {"what is my public ip", "public ip", "what is my ip address"}:
        plan.append("get_public_ip:")

    elif user_input.startswith("play ") or "youtube" in user_input:
        query = (
            raw_input.replace("play", "", 1)
            .replace("on youtube", "")
            .replace("in youtube", "")
            .replace("youtube", "")
            .strip()
        )
        plan.append(f"play_youtube:{query}")

    elif user_input.startswith("open "):
        app = raw_input[5:].strip()
        plan.append(f"open_app:{app}")

    elif user_input in {"show file path", "show current directory", "current directory", "pwd"}:
        plan.append("get_current_directory:")

    elif user_input in {"show files", "list files"}:
        plan.append("list_files:.")

    elif user_input.startswith("type "):
        text = raw_input[5:].strip()
        plan.append(f"type_text:{text}")

    elif user_input.startswith("press "):
        key = raw_input[6:].strip()
        plan.append(f"press_key:{key}")

    elif user_input == "save file":
        plan.append("save_file:")

    elif user_input.startswith("run "):
        command = raw_input[4:].strip()
        plan.append(f"run_command:{command}")

    elif user_input.startswith("read file "):
        path = raw_input[10:].strip()
        plan.append(f"read_file:{path}")

    elif user_input.startswith("remember that "):
        fact = raw_input[14:].strip()
        if " is " in fact:
            key_text, value = fact.split(" is ", 1)
        elif ":" in fact:
            key_text, value = fact.split(":", 1)
        else:
            key_text, value = "note", fact
        plan.append(f"save_memory:{_memory_key_from_text(key_text)}|{value.strip()}")

    elif user_input in {"what do you remember", "show me everything you remember", "show memories"}:
        plan.append("list_memories:")

    elif user_input.startswith("forget "):
        key_text = raw_input[7:].strip()
        plan.append(f"delete_memory:{_memory_key_from_text(key_text)}")

    elif user_input.startswith("what is my "):
        plan.append(f"get_memory:{_memory_key_from_text(raw_input[11:].strip())}")

    elif user_input.startswith("who am i"):
        plan.append("get_memory:my_name")

    return plan
