import sys
import os
import yaml
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from ui import MainWindow, ChatWindow
from assistant import Assistant
import pyautogui
import asyncio
import threading
import argparse
import pyperclip
import datetime
import json
import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
        "user": {"username": "default_user"},
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


class AIChatHistory:
    def __init__(self, log_file_path, va_name, username):
        self.history = []
        self.log_file_path = log_file_path
        self.va_name = va_name
        self.username = username
        self.load_history()

    def add_entry(self, entry_type, content):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "type": entry_type,
            "content": content,
            "va_name": self.va_name,
            "username": self.username,
        }
        self.history.append(entry)
        self.save_history()

    def get_history(self):
        return "\n".join(
            [
                f"[{entry['timestamp']}] {entry['username']} to {entry['va_name']} - {entry['type']}: {entry['content']}"
                for entry in self.history
            ]
        )

    def load_history(self):
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as f:
                self.history = json.load(f)

    def save_history(self):
        with open(self.log_file_path, "w") as f:
            json.dump(self.history, f, indent=2)


class AssistantThread(QThread):
    update_chat_history = pyqtSignal(str)
    write_to_cursor = pyqtSignal(str)

    def __init__(self, assistant, log_file_path, va_name, username):
        super().__init__()
        self.assistant = assistant
        self.loop = asyncio.new_event_loop()
        self.send_to_ai_active = False
        self.output_to_cursor_active = False
        self.last_processed_input = ""
        self.last_processed_response = ""
        self.multi_threaded = False
        self.monitor_clipboard = False
        self.chat_history = AIChatHistory(log_file_path, va_name, username)

        # Emit the initial chat history
        initial_history = self.chat_history.get_history()
        logging.debug(f"Initial chat history: {initial_history}")
        self.update_chat_history.emit(initial_history)

    def set_chat_window(self, chat_window):
        self.chat_window = chat_window

    def run(self):
        asyncio.set_event_loop(self.loop)
        while True:
            user_input = self.loop.run_until_complete(self.assistant.listen())
            if (
                user_input
                and user_input != self.last_processed_input
                and user_input != self.last_processed_response
            ):
                self.chat_history.add_entry("User", user_input)
                self.update_chat_history.emit(self.chat_history.get_history())
                self.last_processed_input = user_input

                if self.output_to_cursor_active:
                    pyautogui.write(user_input)

                if self.send_to_ai_active:

                    def process_and_speak():
                        response_text, cached_audio = self.assistant.process(user_input)
                        self.chat_history.add_entry("Assistant", response_text)
                        self.update_chat_history.emit(self.chat_history.get_history())

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
            self.chat_history.add_entry("Clipboard", content)
            self.update_chat_history.emit(self.chat_history.get_history())
            self.assistant.speak(content)
        else:
            print("Clipboard monitoring is not active")  # Debug print

    def process_user_input(self, user_input):
        self.chat_history.add_entry("User", user_input)
        self.update_chat_history.emit(self.chat_history.get_history())
        self.last_processed_input = user_input

        if self.output_to_cursor_active:
            self.write_to_cursor.emit(
                user_input
            )  # Emit signal instead of directly writing

        if self.send_to_ai_active:

            def process_and_speak():
                response_text, cached_audio = self.assistant.process(user_input)
                self.chat_history.add_entry("Assistant", response_text)
                self.update_chat_history.emit(self.chat_history.get_history())

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


def create_new_chat(va_name):
    log_file_path = os.path.join(os.getcwd(), "data", f"chat_history_{va_name}.json")
    chat_window = ChatWindow(va_name, log_file_path)
    main_window.add_chat_window(chat_window)

    # Get the necessary API keys and settings
    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    # Ensure settings is accessible here (you might need to make it global or pass it as an argument)
    openai_settings = settings["openai"]
    elevenlabs_settings = settings["elevenlabs"]

    assistant = Assistant(
        openai_api_key,
        elevenlabs_api_key,
        deepgram_api_key,
        openai_settings,
        elevenlabs_settings,
    )

    assistants.append(assistant)


def main():
    global main_window, assistants, settings  # Add settings to global variables
    parser = argparse.ArgumentParser(
        description="Run the AI assistant with custom settings."
    )
    parser.add_argument("--settings", help="Path to the custom settings YAML file")
    args = parser.parse_args()

    settings = load_settings(args.settings)

    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    if not openai_api_key or not elevenlabs_api_key:
        print(
            "Error: OPENAI_API_KEY and ELEVENLABS_API_KEY must be set as environment variables."
        )
        sys.exit(1)

    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    # Use VA name and username from settings for log file and audio cache
    va_name = settings.get("va_name", "default")
    username = settings["user"]["username"]
    log_file_path = os.path.join(data_dir, f"chat_history_{va_name}_{username}.json")
    audio_cache_dir = os.path.join(data_dir, "audio_cache", va_name, username)
    os.makedirs(audio_cache_dir, exist_ok=True)

    # Create the assistant object
    assistant = Assistant(
        openai_api_key,
        elevenlabs_api_key,
        deepgram_api_key,
        settings["openai"],
        settings["elevenlabs"],
    )

    app = QApplication(sys.argv)
    main_window = MainWindow()

    clipboard_listener = ClipboardListenerThread()

    assistants = []

    main_window.show()

    main_window.new_chat_window.connect(create_new_chat)
    create_new_chat("VA_0")

    clipboard_listener.clipboard_changed.connect(
        lambda content: [
            thread.process_clipboard_content(content) for thread in assistants
        ]
    )

    clipboard_listener.start()
    app.aboutToQuit.connect(clipboard_listener.stop)
    logging.debug("Starting Qt event loop")
    sys.exit(app.exec())


if __name__ == "__main__":
    logging.debug("Starting main function")
    main()
