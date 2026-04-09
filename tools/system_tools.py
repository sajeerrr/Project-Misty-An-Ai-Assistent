import subprocess
from config.settings import DANGEROUS_COMMANDS
import pyautogui
import time
import subprocess


def run_command(cmd):
    if any(d in cmd.lower() for d in DANGEROUS_COMMANDS):
        return "❌ Blocked dangerous command"

    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True
        )
        return result.stdout or result.stderr
    except Exception as e:
        return str(e)


def open_app(name):
    try:
        subprocess.Popen(f"start {name}", shell=True)

        time.sleep(4)  # 🔥 increase delay

        return "App opened"
    except Exception as e:
        return str(e)


def type_text(text):
    try:
        print("Typing started...")

        time.sleep(2)

        # 🔥 Click center of screen (Notepad area)
        screen_width, screen_height = pyautogui.size()
        pyautogui.click(screen_width // 2, screen_height // 2)

        time.sleep(1)

        pyautogui.write(text, interval=0.05)

        print("Typing done")
        return "Typed text"

    except Exception as e:
        return str(e)


def save_file():
    try:
        pyautogui.hotkey('ctrl', 's')
        time.sleep(1)
        pyautogui.press('enter')
        return "File saved"
    except Exception as e:
        return str(e)