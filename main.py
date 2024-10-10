import sys
import os
import yaml
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from ui import MainWindow
from assistant import Assistant
import pyperclip
import pyautogui
import asyncio


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


def load_settings():
    default_settings = load_default_settings()
    try:
        with open("va-settings.yaml", "r") as file:
            user_settings = yaml.safe_load(file)
            # Merge user settings with default settings
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
                    response = self.assistant.process(user_input)
                    self.update_response.emit(response)

                    if response:
                        self.last_processed_response = response
                        self.assistant.speak(response)

    def stop(self):
        self.running = False

    def start_clipboard_monitoring(self):
        self.monitor_clipboard = True

    def stop_clipboard_monitoring(self):
        self.monitor_clipboard = False

    def process_and_speak_ai_response(self, text):
        response = self.assistant.process(text)
        self.output.emit(f"AI: {response}")
        self.assistant.speak(response)

    def set_send_to_ai_active(self, active):  # Add this method
        self.send_to_ai_active = active
        if not active:
            self.last_processed_input = ""  # Reset when toggled off

    def set_output_to_cursor_active(self, active):
        self.output_to_cursor_active = active


def main():
    settings = load_settings()

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
    assistant_thread = AssistantThread(assistant)  # Remove the window parameter

    assistant_thread.update_dictation.connect(window.update_dictation)
    assistant_thread.update_response.connect(window.update_output)

    # Change this line to connect to the button's clicked signal
    window.send_ai_toggle.clicked.connect(
        lambda checked: assistant_thread.set_send_to_ai_active(checked)
    )

    window.output_cursor_toggle.clicked.connect(
        lambda checked: assistant_thread.set_output_to_cursor_active(checked)
    )

    # def process_and_speak_ai_response(text):
    #     if window.send_to_ai_active:
    #         response = assistant.process(text)
    #         window.update_output(f"2AI: {response}")
    #         assistant.speak(response)

    # window.send_to_ai.connect(process_and_speak_ai_response)
    # window.stop_listening.connect(assistant_thread.stop)

    window.start_clipboard_monitoring.connect(
        assistant_thread.start_clipboard_monitoring
    )
    window.stop_clipboard_monitoring.connect(assistant_thread.stop_clipboard_monitoring)

    window.show()
    assistant_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
