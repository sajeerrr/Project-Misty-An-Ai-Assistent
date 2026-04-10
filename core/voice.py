import os
import re
import threading
import time
import winsound
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

try:
    import pygame
except ImportError:
    pygame = None

try:
    import sounddevice as sd
except ImportError:
    sd = None

try:
    import scipy.io.wavfile as wavfile
except ImportError:
    wavfile = None

try:
    import torch
except ImportError:
    torch = None

try:
    import whisper
except ImportError:
    whisper = None

try:
    from TTS.api import TTS
except ImportError:
    TTS = None

try:
    from playsound import playsound
except ImportError:
    playsound = None

from config import (
    OUTPUT_AUDIO_FILE,
    RECORD_SECONDS,
    SAMPLE_RATE,
    SILENCE_THRESHOLD,
    SPEAKER_WAV,
    TTS_LANGUAGE,
    TTS_MODEL,
    USE_GPU,
    VOICE_ENABLED,
    WAKE_WORD,
    WHISPER_MODEL_SIZE,
    get_logger,
)


logger = get_logger("voice")

_whisper_model = None
_tts_model = None
_voice_thread = None
_voice_stop_event = threading.Event()
_voice_status = "Voice mode off"
_voice_lock = threading.Lock()


def _set_status(status):
    global _voice_status
    _voice_status = status


def get_voice_status():
    return _voice_status


def get_voice_status_display():
    status = get_voice_status()
    lowered_status = status.lower()

    if "processing" in lowered_status or "thinking" in lowered_status or "speaking" in lowered_status:
        return f"🟡 {status}"

    if "listening for wake word" in lowered_status:
        return f"🔴 {status}"

    return f"🟢 {status}"


def is_voice_mode_running():
    return _voice_thread is not None and _voice_thread.is_alive()


def _get_device():
    if USE_GPU and torch is not None and torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _split_text_for_tts(text, max_length=200):
    cleaned_text = text.strip()
    if not cleaned_text:
        return []

    if len(cleaned_text) <= max_length:
        return [cleaned_text]

    parts = re.split(r"(?<=[.!?])\s+", cleaned_text)
    chunks = []
    current_chunk = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        candidate = f"{current_chunk} {part}".strip()
        if current_chunk and len(candidate) > max_length:
            chunks.append(current_chunk)
            current_chunk = part
        else:
            current_chunk = candidate

    if current_chunk:
        chunks.append(current_chunk)

    return chunks or [cleaned_text]


def _play_audio_file(audio_file_path):
    if pygame is not None:
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(audio_file_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            return
        except Exception as exc:
            logger.warning("pygame playback failed: %s", exc)

    if playsound is not None:
        try:
            playsound(audio_file_path)
            return
        except Exception as exc:
            logger.warning("playsound playback failed: %s", exc)

    os.system(f'start /min wmplayer "{audio_file_path}"')


def _save_audio_array(audio_file_path, audio_array):
    if wavfile is None or np is None:
        raise RuntimeError("scipy and numpy are required to save audio")

    clipped_audio = np.clip(audio_array, -1.0, 1.0)
    int_audio = (clipped_audio * 32767).astype(np.int16)
    wavfile.write(audio_file_path, SAMPLE_RATE, int_audio)


def _calculate_rms(audio_data):
    if np is None:
        return 0.0
    return float(np.sqrt(np.mean(np.square(audio_data))))


def load_models():
    global _whisper_model, _tts_model

    with _voice_lock:
        if _whisper_model is None:
            if whisper is None:
                raise RuntimeError("Whisper is not installed. Run: pip install openai-whisper")

            device = _get_device()
            print(f"Loading Whisper {WHISPER_MODEL_SIZE} on {device}...")
            _whisper_model = whisper.load_model(WHISPER_MODEL_SIZE, device=device)
            print("Whisper loaded successfully.")
            logger.info("Loaded Whisper model on %s", device)

        if _tts_model is None:
            if TTS is None:
                raise RuntimeError("Coqui TTS is not installed. Run: pip install coqui-tts")

            device = _get_device()
            print(f"Loading Coqui TTS model on {device}...")
            _tts_model = TTS(TTS_MODEL)
            if device == "cuda":
                _tts_model = _tts_model.to(device)
            print("Coqui TTS loaded successfully.")
            logger.info("Loaded Coqui TTS model on %s", device)

    return _whisper_model, _tts_model


def record_audio():
    if sd is None or np is None:
        print("Microphone recording libraries are not installed.")
        return None

    try:
        _set_status("Listening...")
        print("Listening...")
        recording = sd.rec(
            int(RECORD_SECONDS * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        print("Processing...")
        _set_status("Processing...")
        audio_data = recording.flatten()

        if _calculate_rms(audio_data) < SILENCE_THRESHOLD:
            logger.info("Skipped silent audio sample")
            return None

        return audio_data
    except Exception as exc:
        logger.exception("Audio recording failed")
        print(f"Microphone error: {exc}")
        return None
    finally:
        _set_status("Idle")


def speech_to_text(audio_data):
    if audio_data is None:
        return ""

    try:
        whisper_model, _ = load_models()
        device = _get_device()
        result = whisper_model.transcribe(audio_data, fp16=(device == "cuda"))
        text = result.get("text", "").strip()
        print(f"Heard: {text}")
        logger.info("Transcribed speech: %s", text)
        return text
    except Exception as exc:
        logger.exception("Speech to text failed")
        print(f"Speech recognition error: {exc}")
        return ""


def text_to_speech(text):
    cleaned_text = text.strip()
    if not cleaned_text:
        return

    try:
        _, tts_model = load_models()
        audio_chunks = _split_text_for_tts(cleaned_text)

        for chunk in audio_chunks:
            output_path = Path(OUTPUT_AUDIO_FILE)
            if output_path.exists():
                output_path.unlink()

            tts_kwargs = {
                "text": chunk,
                "file_path": str(output_path),
                "language": TTS_LANGUAGE,
            }
            if SPEAKER_WAV:
                tts_kwargs["speaker_wav"] = SPEAKER_WAV

            _set_status("Speaking...")
            tts_model.tts_to_file(**tts_kwargs)
            _play_audio_file(str(output_path))

            if output_path.exists():
                output_path.unlink()
    except Exception as exc:
        logger.exception("Text to speech failed")
        print(f"Text to speech error: {exc}")
    finally:
        _set_status("Idle")


def listen_once():
    audio_data = record_audio()
    if audio_data is None:
        return ""
    return speech_to_text(audio_data)


def _beep():
    try:
        winsound.Beep(1000, 200)
    except Exception:
        pass


def listen_for_wake_word():
    dot_counter = 0
    wake_word = WAKE_WORD.lower()
    _set_status("Listening for wake word...")

    while not _voice_stop_event.is_set():
        text = listen_once().lower().strip()
        dot_counter += 1

        if dot_counter % 3 == 0:
            print(".")

        if wake_word and wake_word in text:
            _beep()
            logger.info("Wake word detected")
            return True

    return False


def voice_mode_loop(agent_chat_function):
    if not VOICE_ENABLED:
        print("Voice mode is disabled in config.")
        return

    load_models()
    _voice_stop_event.clear()
    _set_status("Listening for wake word...")

    while not _voice_stop_event.is_set():
        if not listen_for_wake_word():
            break

        if _voice_stop_event.is_set():
            break

        text_to_speech("Yes, how can I help?")
        command = listen_once().strip()

        if not command:
            continue

        if command.lower() == "stop voice mode":
            stop_voice_mode()
            break

        _set_status("Thinking...")
        reply = agent_chat_function(command)
        text_to_speech(reply)

    _set_status("Voice mode off")


def start_voice_mode_background(agent_chat_function):
    global _voice_thread

    if is_voice_mode_running():
        return _voice_thread

    _voice_stop_event.clear()
    _voice_thread = threading.Thread(
        target=voice_mode_loop,
        args=(agent_chat_function,),
        daemon=True,
        name="voice-mode-thread",
    )
    _voice_thread.start()
    logger.info("Voice mode thread started")
    return _voice_thread


def start_voice_mode_command(agent_chat_function):
    if is_voice_mode_running():
        return "Voice mode is already running."

    start_voice_mode_background(agent_chat_function)
    return "Voice mode started."


def stop_voice_mode():
    _voice_stop_event.set()
    _set_status("Voice mode stopped")
    print("Voice mode stopped")
    logger.info("Voice mode stopped")


def stop_voice_mode_command():
    if not is_voice_mode_running():
        return "Voice mode is already off."

    stop_voice_mode()
    return "Voice mode stopped."


def test_microphone():
    audio_data = record_audio()
    if audio_data is None:
        print("No sound detected.")
        return False

    print("Microphone working!")
    return True


def test_speaker():
    text_to_speech("Hello, I am your AI assistant. Voice is working correctly.")


def get_available_microphones():
    if sd is None:
        print("sounddevice is not installed.")
        return []

    microphones = []
    try:
        devices = sd.query_devices()
        for index, device in enumerate(devices):
            if device.get("max_input_channels", 0) > 0:
                label = f"{index}: {device['name']}"
                microphones.append(label)
                print(label)
    except Exception as exc:
        print(f"Could not list microphones: {exc}")
    return microphones


if __name__ == "__main__":
    print("Voice module self-test")
    get_available_microphones()
    print("Testing microphone...")
    test_microphone()
