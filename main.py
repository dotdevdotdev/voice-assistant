import sys
import os
import yaml
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from ui import MainWindow, ChatWindow
from assistant import Assistant
from assistant_manager import AssistantManager
from clipboard_listener import ClipboardListener
import argparse
import logging
import copy

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def load_default_va_settings():
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
            "voice_settings": {
                "stability": 0.49,
                "similarity_boost": 0.49,
                "style_exaggeration": 0.49,
                "speaker_boost": True,
            },
        },
        "user": {"username": "default_user"},
    }


def load_default_app_settings():
    return {
        "app": {
            "theme": {
                "background_color": "#000000",
                "text_color": "#39FF14",
                "accent_color": "#39FF14",
            },
            "input_device": "(hw:4,0)",
            "output_device": "(hw:0,8)",
        },
    }


def load_settings(settings_file=None, default_settings=load_default_va_settings()):
    result = copy.deepcopy(default_settings)

    if settings_file:
        try:
            with open(settings_file, "r") as file:
                user_settings = yaml.safe_load(file)
                # Merge user settings with default settings
                result.update(user_settings)
                return result
        except FileNotFoundError:
            logging.warning(
                f"Warning: {settings_file} not found. Using default settings."
            )
            return result
        except yaml.YAMLError as e:
            logging.error(f"Error parsing {settings_file}: {e}")
            logging.info("Using default settings.")
            return result
    else:
        return result


def create_new_chat(va_name):
    log_file_path = os.path.join(os.getcwd(), "data", f"chat_history_{va_name}.json")
    chat_window = ChatWindow(va_name, log_file_path)
    main_window.add_chat_window(chat_window)

    # Get the necessary API keys and settings
    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    assistant = Assistant(
        openai_api_key,
        elevenlabs_api_key,
        deepgram_api_key,
        app_settings,
        va_settings,
    )

    assistant_manager = AssistantManager(
        assistant, log_file_path, va_name, va_settings["user"]["username"]
    )
    assistant_manager.update_chat_history.connect(chat_window.update_chat_history)
    assistant_manager.write_to_cursor.connect(lambda text: pyautogui.write(text))

    chat_window.send_message.connect(assistant_manager.process_user_input)
    assistant_manager.set_chat_window(chat_window)

    # Start voice listening by default
    assistant_manager.set_send_to_ai_active(True)

    return assistant_manager


def main():
    global main_window, assistant_managers, app_settings, va_settings
    parser = argparse.ArgumentParser(
        description="Run the AI assistant with custom settings."
    )
    parser.add_argument("--settings", help="Path to the custom settings YAML file")
    args = parser.parse_args()

    app_settings = load_settings("app-settings.yaml", load_default_app_settings())
    va_settings = load_settings(args.settings, load_default_va_settings())

    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    if not openai_api_key or not elevenlabs_api_key or not deepgram_api_key:
        logging.error(
            "Error: OPENAI_API_KEY, ELEVENLABS_API_KEY, and DEEPGRAM_API_KEY must be set as environment variables."
        )
        sys.exit(1)

    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    app = QApplication(sys.argv)
    main_window = MainWindow()

    clipboard_listener = ClipboardListener()

    assistant_managers = []

    main_window.show()

    main_window.new_chat_window.connect(
        lambda va_name: assistant_managers.append(create_new_chat(va_name))
    )
    create_new_chat("Default_AI")

    clipboard_listener.clipboard_changed.connect(
        lambda content: [
            manager.process_clipboard_content(content) for manager in assistant_managers
        ]
    )

    app.aboutToQuit.connect(
        lambda: [manager.clipboard_thread.stop() for manager in assistant_managers]
    )
    app.aboutToQuit.connect(
        lambda: [
            manager.assistant.pyaudio.terminate() for manager in assistant_managers
        ]
    )

    sys.exit(app.exec())


if __name__ == "__main__":
    logging.debug("Starting main function")
    main()
