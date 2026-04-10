import json
import logging
import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCREENSHOT_DIR = Path(os.path.expanduser("~/Desktop/screenshots"))
SCREENSHOT_FOLDER = SCREENSHOT_DIR

MODEL_NAME = "llama3"
OLLAMA_URL = "http://localhost:11434"
MAX_TOKENS = 2048
TEMPERATURE = 0.7

MEMORY_FILE = DATA_DIR / "memory.json"
HISTORY_FILE = DATA_DIR / "conversation_history.json"
TASKS_FILE = DATA_DIR / "tasks.json"
ACTION_LOG_FILE = DATA_DIR / "agent_actions.log"
MAX_HISTORY = 20

VOICE_ENABLED = True
VOICE_RATE = 175
VOICE_VOLUME = 0.9
WAKE_WORD = "hey agent"
WHISPER_MODEL_SIZE = "small"
SAMPLE_RATE = 16000
RECORD_SECONDS = 6
SILENCE_THRESHOLD = 0.01
TTS_MODEL = "tts_models/multilingual/multi-dataset/xtts_v2"
TTS_LANGUAGE = "en"
SPEAKER_WAV = None
USE_GPU = True
OUTPUT_AUDIO_FILE = str(BASE_DIR / "temp_speech.wav")

EMAIL_ADDRESS = os.getenv("AGENT_EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("AGENT_EMAIL_PASSWORD", "")
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
IMAP_SERVER = "imap.gmail.com"

UI_TITLE = "My AI Agent"
UI_ICON = "M"
UI_MODEL_LABEL = "Llama 3"
UI_STATUS = "Offline and local"
UI_THEME = "dark"

HOTKEY = "ctrl+shift+space"

BLOCKED_COMMAND_FRAGMENTS = [
    "rm -rf",
    "format",
    "del /f /s",
    "shutdown /s",
    "shutdown /r",
]


def ensure_app_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    if not MEMORY_FILE.exists():
        MEMORY_FILE.write_text("{}", encoding="utf-8")

    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text("[]", encoding="utf-8")

    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]", encoding="utf-8")

    if not ACTION_LOG_FILE.exists():
        ACTION_LOG_FILE.write_text("", encoding="utf-8")


def read_json(path, default_value):
    ensure_app_files()
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_value


def write_json(path, data):
    ensure_app_files()
    Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")


def get_logger(name):
    ensure_app_files()
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    try:
        handler = logging.FileHandler(ACTION_LOG_FILE, encoding="utf-8")
    except OSError:
        # Keep startup working even if the log file location is unavailable.
        handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


ensure_app_files()


__all__ = [
    "ACTION_LOG_FILE",
    "BASE_DIR",
    "BLOCKED_COMMAND_FRAGMENTS",
    "DATA_DIR",
    "EMAIL_ADDRESS",
    "EMAIL_PASSWORD",
    "HISTORY_FILE",
    "HOTKEY",
    "IMAP_SERVER",
    "MAX_HISTORY",
    "MAX_TOKENS",
    "MEMORY_FILE",
    "MODEL_NAME",
    "OLLAMA_URL",
    "SCREENSHOT_DIR",
    "SCREENSHOT_FOLDER",
    "SMTP_PORT",
    "SMTP_SERVER",
    "TASKS_FILE",
    "TEMPERATURE",
    "UI_ICON",
    "UI_MODEL_LABEL",
    "UI_STATUS",
    "UI_THEME",
    "UI_TITLE",
    "OUTPUT_AUDIO_FILE",
    "RECORD_SECONDS",
    "SAMPLE_RATE",
    "SILENCE_THRESHOLD",
    "SPEAKER_WAV",
    "TTS_LANGUAGE",
    "TTS_MODEL",
    "USE_GPU",
    "VOICE_ENABLED",
    "VOICE_RATE",
    "VOICE_VOLUME",
    "WAKE_WORD",
    "WHISPER_MODEL_SIZE",
    "ensure_app_files",
    "get_logger",
    "read_json",
    "write_json",
]
