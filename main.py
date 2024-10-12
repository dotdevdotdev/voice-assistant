import sys
import os
import yaml
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from ui import MainWindow
from assistant import Assistant
import pyautogui
import asyncio
import threading
import argparse
import pyperclip


def load_default_settings():
    DEFAULT_SYSTEM_PROMPT = """
You're a clever, slightly sarcastic AI assistant. Keep it real, keep it short.

## Key traits:
- Conversational: Talk like a real person, not a textbook
- Concise: One or two sentences max, usually
- Witty: Throw in jokes when it fits, but don't force it
- Slightly sarcastic: A little sass is good, but don't be mean
- Direct: Skip the fluff, get to the point

## Don'ts:
- No "certainly," "definitely," or other filler words
- Don't apologize or say sorry
- Avoid being overly polite or formal

## Do:
- Use casual language
- Be helpful and informative, but in a chill way
- If you can make a clever quip in a few words, go for it
- Ask for clarification if needed, but keep it brief

Remember, you're having a chat, not giving a lecture. Keep it snappy, fun, and real."
"""
    return {
        "openai": {
            "model": "gpt-4o-mini",
            "system_prompt": DEFAULT_SYSTEM_PROMPT,
        },
        "elevenlabs": {
            "model_id": "eleven_turbo_v2_5",
            "voice_id": "Crm8VULvkVs5ZBDa1Ixm",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        },
        "app": {
            "theme": {
                "background_color": "#000000",
                "text_color": "#39FF14",
                "accent_color": "#39FF14",
            }
        },
    }


def load_settings(settings_file=None):
    default_settings = load_default_settings()
    if settings_file:
        try:
            with open(settings_file, "r") as file:
                user_settings = yaml.safe_load(file)
                # Merge user settings with default settings
                settings = default_settings.copy()
                settings.update(user_settings)
                return settings
        except FileNotFoundError:
            print(f"Warning: {settings_file} not found. Using default settings.")
            return default_settings
        except yaml.YAMLError as e:
            print(f"Error parsing {settings_file}: {e}")
            print("Using default settings.")
            return default_settings
    else:
        # Try to load va-settings.yaml if no custom file is specified
        try:
            with open("va-settings.yaml", "r") as file:
                user_settings = yaml.safe_load(file)
                settings = default_settings.copy()
                settings.update(user_settings)
                return settings
        except FileNotFoundError:
            print("Warning: va-settings.yaml not found. Using default settings.")
            return default_settings
        except yaml.YAMLError as e:
            print(f"Error parsing va-settings.yaml: {e}")
            print("Using default settings.")
            return default_settings


class ClipboardListenerThread(QThread):
    clipboard_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.last_text = ""

    def run(self):
        while self.running:
            try:
                text = pyperclip.paste()
                if text != self.last_text:
                    print(f"Clipboard changed: {text}")  # Debug print
                    self.last_text = text
                    self.clipboard_changed.emit(text)
            except Exception as e:
                print(f"Error reading clipboard: {e}")
            self.msleep(100)  # Check every 100ms

    def stop(self):
        self.running = False
        print("Clipboard listener stopped")  # Debug print


class AssistantThread(QThread):
    update_dictation = pyqtSignal(str)
    update_response = pyqtSignal(str)

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant
        self.loop = asyncio.new_event_loop()
        self.send_to_ai_active = False
        self.output_to_cursor_active = False
        self.last_processed_input = ""
        self.last_processed_response = ""
        self.multi_threaded = False
        self.monitor_clipboard = False

    def run(self):
        asyncio.set_event_loop(self.loop)
        while True:
            user_input = self.loop.run_until_complete(self.assistant.listen())
            if (
                user_input
                and user_input != self.last_processed_input
                and user_input != self.last_processed_response
            ):
                self.update_dictation.emit(user_input)
                self.last_processed_input = user_input

                if self.output_to_cursor_active:
                    pyautogui.write(user_input)

                if self.send_to_ai_active:

                    def process_and_speak():
                        response_text, cached_audio = self.assistant.process(user_input)
                        self.update_response.emit(response_text)

                        if response_text:
                            self.last_processed_response = response_text
                            if cached_audio:
                                self.assistant.play_audio(cached_audio)
                            else:
                                self.assistant.speak(response_text)

                    if self.multi_threaded:
                        threading.Thread(target=process_and_speak).start()
                    else:
                        process_and_speak()

    def set_send_to_ai_active(self, active):
        self.send_to_ai_active = active
        if not active:
            self.last_processed_input = ""

    def set_output_to_cursor_active(self, active):
        self.output_to_cursor_active = active

    def process_clipboard_content(self, content):
        print(f"Processing clipboard content: {content}")  # Debug print
        if self.monitor_clipboard:
            print("Clipboard monitoring is active")  # Debug print
            self.update_response.emit(f"Clipboard: {content}")
            self.assistant.speak(content)
        else:
            print("Clipboard monitoring is not active")  # Debug print


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI assistant with custom settings."
    )
    parser.add_argument("--settings", help="Path to the custom settings YAML file")
    args = parser.parse_args()

    settings = load_settings(args.settings)

    app = QApplication(sys.argv)
    window = MainWindow(settings["app"]["theme"])

    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    if not openai_api_key or not elevenlabs_api_key:
        print(
            "Error: OPENAI_API_KEY and ELEVENLABS_API_KEY must be set as environment variables."
        )
        sys.exit(1)

    assistant = Assistant(
        openai_api_key,
        elevenlabs_api_key,
        deepgram_api_key,
        settings["openai"],
        settings["elevenlabs"],
    )
    assistant_thread = AssistantThread(assistant)
    clipboard_listener = ClipboardListenerThread()

    assistant_thread.update_dictation.connect(window.update_dictation)
    assistant_thread.update_response.connect(window.update_output)
    clipboard_listener.clipboard_changed.connect(
        assistant_thread.process_clipboard_content
    )

    window.send_ai_toggle.clicked.connect(
        lambda checked: assistant_thread.set_send_to_ai_active(checked)
    )

    window.output_cursor_toggle.clicked.connect(
        lambda checked: assistant_thread.set_output_to_cursor_active(checked)
    )

    window.start_clipboard_monitoring.connect(
        lambda: setattr(assistant_thread, "monitor_clipboard", True)
    )
    window.stop_clipboard_monitoring.connect(
        lambda: setattr(assistant_thread, "monitor_clipboard", False)
    )

    window.show()
    assistant_thread.start()
    clipboard_listener.start()

    app.aboutToQuit.connect(clipboard_listener.stop)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
