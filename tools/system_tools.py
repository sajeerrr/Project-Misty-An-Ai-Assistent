import subprocess
import time
import ctypes
import random
from urllib.parse import quote_plus

try:
    import pyautogui
except ImportError:
    pyautogui = None

from config.settings import DANGEROUS_COMMANDS


VK_MEDIA_NEXT_TRACK = 0xB0
VK_MEDIA_PREV_TRACK = 0xB1
VK_MEDIA_PLAY_PAUSE = 0xB3
VK_RETURN = 0x0D
VK_TAB = 0x09
VK_DOWN = 0x28

RANDOM_SPOTIFY_QUERIES = [
    "top hits",
    "feel good songs",
    "lofi beats",
    "pop mix",
    "chill playlist",
]

SPOTIFY_BACKGROUND_PLAYLISTS = [
    ("Today's Top Hits", "37i9dQZF1DXcBWIGoYBM5M"),
    ("Chill Hits", "37i9dQZF1DX4WYpdgoIcn6"),
]

RANDOM_YOUTUBE_QUERIES = [
    "funny video",
    "travel vlog",
    "science documentary short",
    "gaming highlights",
    "music mix",
]

RANDOM_YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=jNQXAC9IVRw",
    "https://www.youtube.com/watch?v=ysz5S6PUM-U",
    "https://www.youtube.com/watch?v=aqz-KE-bpKQ",
    "https://www.youtube.com/watch?v=ScMzIvxBSi4",
]

SW_MINIMIZE = 6
SW_RESTORE = 9


def _require_pyautogui():
    if pyautogui is None:
        return "pyautogui is not installed"
    return None


def _open_target(target, minimized=False):
    window_flag = "/min " if minimized else ""
    subprocess.Popen(f'start "" {window_flag}"{target}"', shell=True)


def _press_virtual_key(key_code):
    try:
        ctypes.windll.user32.keybd_event(key_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(key_code, 0, 2, 0)
        return True
    except Exception:
        return False


def _minimize_windows_with_title(title_fragment):
    title_fragment = title_fragment.lower()
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        window_title = buffer.value.lower()

        if title_fragment in window_title:
            user32.ShowWindow(hwnd, SW_MINIMIZE)

        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)


def _find_window_by_title(title_fragment):
    title_fragment = title_fragment.lower()
    user32 = ctypes.windll.user32
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    found_hwnd = []

    def callback(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True

        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buffer, length + 1)
        if title_fragment in buffer.value.lower():
            found_hwnd.append(hwnd)
            return False

        return True

    user32.EnumWindows(EnumWindowsProc(callback), 0)
    return found_hwnd[0] if found_hwnd else 0


def _activate_window_by_title(title_fragment):
    hwnd = _find_window_by_title(title_fragment)
    if not hwnd:
        return False

    try:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.4)
        return True
    except Exception:
        return False


def _press_key_sequence(key_codes, delay=0.25):
    for key_code in key_codes:
        _press_virtual_key(key_code)
        time.sleep(delay)


def _spotify_is_running():
    try:
        result = subprocess.run(
            "tasklist /FI \"IMAGENAME eq Spotify.exe\" /FO CSV /NH",
            shell=True,
            capture_output=True,
            text=True,
        )
        return "Spotify.exe" in result.stdout
    except Exception:
        return False


def _ensure_spotify_running(background=False):
    target = "Spotify.exe" if _spotify_is_running() else "spotify:"
    _open_target(target, minimized=background)
    time.sleep(2)
    if background:
        _minimize_windows_with_title("spotify")


def _start_random_spotify_playlist_background():
    playlist_name, playlist_id = random.choice(SPOTIFY_BACKGROUND_PLAYLISTS)
    _ensure_spotify_running(background=True)
    _open_target(f"spotify:playlist:{playlist_id}", minimized=True)
    time.sleep(2)
    _press_virtual_key(VK_MEDIA_PLAY_PAUSE)
    time.sleep(0.5)

    # Jump a few tracks forward so repeat requests feel less predictable.
    skip_count = random.randint(0, 3)
    for _ in range(skip_count):
        _press_virtual_key(VK_MEDIA_NEXT_TRACK)
        time.sleep(0.35)

    _minimize_windows_with_title("spotify")
    return f"Started a background song from Spotify playlist '{playlist_name}'"


# ------------------ BASIC COMMAND ------------------

def run_command(cmd):
    if any(d in cmd.lower() for d in DANGEROUS_COMMANDS):
        return "Blocked dangerous command"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout or result.stderr
        return output.strip() or "Command completed"
    except Exception as e:
        return str(e)


def open_app(name):
    try:
        _open_target(name)
        time.sleep(2)
        return f"Opened: {name}"
    except Exception as e:
        return str(e)


def open_spotify():
    try:
        _ensure_spotify_running(background=False)
        return "Opened Spotify"
    except Exception as e:
        return str(e)


def play_spotify(query):
    if not query:
        was_running = _spotify_is_running()
        _ensure_spotify_running(background=True)
        time.sleep(1)

        if was_running and _press_virtual_key(VK_MEDIA_PLAY_PAUSE):
            _minimize_windows_with_title("spotify")
            return "Tried to resume your recently played song in Spotify"

        return _start_random_spotify_playlist_background()

    try:
        encoded_query = quote_plus(query)
        _ensure_spotify_running(background=False)
        _open_target(f"spotify:search:{encoded_query}", minimized=False)
        time.sleep(2.5)

        if _activate_window_by_title("spotify"):
            # Search pages usually need a confirm, then focus on results, then open the first match.
            _press_key_sequence([VK_RETURN, VK_TAB, VK_RETURN], delay=0.35)
            time.sleep(1)

            # If the result page opens without audio, this nudges playback to start.
            _press_virtual_key(VK_MEDIA_PLAY_PAUSE)
            time.sleep(0.3)
            _minimize_windows_with_title("spotify")
            return f"Tried to play '{query}' on Spotify"

        _minimize_windows_with_title("spotify")
        return f"Opened Spotify search for '{query}', but could not focus the Spotify window to start playback"
    except Exception as e:
        return str(e)


def media_play_pause():
    if _press_virtual_key(VK_MEDIA_PLAY_PAUSE):
        _minimize_windows_with_title("spotify")
        return "Toggled media play/pause"
    return "Could not send play/pause media key"


def next_track():
    if _press_virtual_key(VK_MEDIA_NEXT_TRACK):
        _minimize_windows_with_title("spotify")
        return "Skipped to the next track"
    return "Could not send next track media key"


def previous_track():
    if _press_virtual_key(VK_MEDIA_PREV_TRACK):
        _minimize_windows_with_title("spotify")
        return "Went back to the previous track"
    return "Could not send previous track media key"


# ------------------ KEYBOARD CONTROL ------------------

def type_text(text):
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    pyautogui.write(text)
    return "Typed"


def press_key(key):
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    pyautogui.press(key)
    return f"Pressed {key}"


def save_file():
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    pyautogui.hotkey('ctrl', 's')
    time.sleep(1)
    pyautogui.press('enter')
    return "Saved"


# ------------------ FULL AUTO SEARCH ------------------

def auto_search(query):
    if not query:
        return "Missing search query"

    url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    _open_target(url)
    return f"Searched: {query}"


# ------------------ CLICK FIRST RESULT ------------------

def click_first_result():
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    time.sleep(2)

    # Move slightly down where first result usually is
    pyautogui.moveTo(500, 400)
    pyautogui.click()

    return "Clicked first result"


# ------------------ YOUTUBE AUTO PLAY ------------------

def play_youtube(video):
    chosen_query = video.strip() if video else random.choice(RANDOM_YOUTUBE_QUERIES)
    missing_dependency = _require_pyautogui()

    if missing_dependency and not video:
        random_url = random.choice(RANDOM_YOUTUBE_URLS)
        _open_target(random_url)
        return "Opened and played a random YouTube video"

    if missing_dependency:
        return missing_dependency

    url = f"https://www.youtube.com/results?search_query={quote_plus(chosen_query)}"
    _open_target(url)
    time.sleep(3)

    # Try to open the first result and start playback.
    pyautogui.press("tab")
    time.sleep(0.2)
    pyautogui.press("enter")
    time.sleep(1)
    pyautogui.moveTo(500, 400)
    pyautogui.click()

    if video:
        return f"Tried to play '{video}' on YouTube"
    return f"Tried to play a random YouTube video using '{chosen_query}'"


# ------------------ SCROLL ------------------

def scroll_down():
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    pyautogui.scroll(-500)
    return "Scrolled down"


def scroll_up():
    missing_dependency = _require_pyautogui()
    if missing_dependency:
        return missing_dependency
    pyautogui.scroll(500)
    return "Scrolled up"
