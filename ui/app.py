import streamlit as st

from config import UI_ICON, UI_MODEL_LABEL, UI_STATUS, UI_TITLE
from core.agent import chat
from core.memory import load_conversation, load_memory_store
from core.voice import (
    get_voice_status_display,
    get_voice_status,
    is_voice_mode_running,
    listen_once,
    start_voice_mode_background,
    stop_voice_mode,
)


def main():
    st.set_page_config(page_title=UI_TITLE, page_icon=UI_ICON, layout="wide")
    st.title(UI_TITLE)
    st.caption(f"{UI_MODEL_LABEL} | {UI_STATUS}")

    if "messages" not in st.session_state:
        stored_messages = []
        for item in load_conversation():
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                stored_messages.append(
                    {
                        "role": role,
                        "content": content,
                        "timestamp": item.get("timestamp", ""),
                        "tool_name": item.get("tool_name", ""),
                    }
                )
        st.session_state.messages = stored_messages

    if "voice_draft" not in st.session_state:
        st.session_state.voice_draft = ""

    with st.sidebar:
        st.subheader("Voice")
        st.markdown(get_voice_status_display())

        if is_voice_mode_running():
            if st.button("Stop Voice Mode"):
                stop_voice_mode()
                st.rerun()
        else:
            if st.button("Start Voice Mode"):
                try:
                    start_voice_mode_background(chat)
                    st.success("Voice mode started.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Voice mode could not start: {exc}")

        if st.button("Speak Once"):
            try:
                st.session_state.voice_draft = listen_once()
                st.rerun()
            except Exception as exc:
                st.error(f"Voice capture failed: {exc}")

        if st.session_state.voice_draft:
            st.text_area("Voice Draft", key="voice_draft", height=120)
            if st.button("Send Voice Draft"):
                voice_prompt = st.session_state.voice_draft.strip()
                if voice_prompt:
                    st.session_state.pending_voice_prompt = voice_prompt
                    st.session_state.voice_draft = ""
                    st.rerun()

        st.subheader("Memory")
        memories = load_memory_store()
        if memories:
            for key, value in memories.items():
                st.write(f"**{key}:** {value}")
        else:
            st.caption("No saved memories yet.")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("timestamp"):
                st.caption(message["timestamp"])
            st.write(message["content"])
            if message.get("tool_name"):
                st.caption(f"Tool: {message['tool_name']}")

    prompt = st.chat_input("Ask Misty to search, fetch pages, manage files, or remember things")

    if st.session_state.get("pending_voice_prompt"):
        prompt = st.session_state.pop("pending_voice_prompt")

    if prompt:
        user_message = {"role": "user", "content": prompt}
        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.write(prompt)

        response = chat(prompt, verbose=False)
        assistant_message = {"role": "assistant", "content": response}
        st.session_state.messages.append(assistant_message)

        with st.chat_message("assistant"):
            st.write(response)


if __name__ == "__main__":
    main()
