import sys
import os
import yaml
import pyautogui
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, QThread
from ui import MainWindow, ChatWindow
from assistant import Assistant
from assistant_manager import AssistantManager
from clipboard_listener import ClipboardListener
import argparse
import logging
import copy
import atexit
from pathlib import Path
from application import Application

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
            "input_device": "PD200X",
            "output_device": "Smart M70D",
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


def save_settings(settings, file_path):
    """Save settings to a YAML file."""
    try:
        with open(file_path, "w") as file:
            yaml.dump(settings, file, default_flow_style=False)
        logging.info(f"Settings saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving settings to {file_path}: {e}")


def load_va_configs():
    """Load all VA configuration files from the root directory"""
    va_configs = {}
    root_path = Path(".")
    for yaml_file in root_path.glob("va-*.yaml"):
        try:
            config = load_settings(str(yaml_file))
            va_name = yaml_file.stem.replace("va-", "")
            va_configs[va_name] = config
        except Exception as e:
            logging.error(f"Error loading VA config {yaml_file}: {e}")
    return va_configs


def create_assistant_manager(va_name, va_settings, chat_window):
    """Create a new assistant manager for the given VA configuration"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")

    # Add retry logic for assistant creation
    max_retries = 3
    retry_delay = 1  # seconds

    for attempt in range(max_retries):
        try:
            assistant = Assistant(
                openai_api_key,
                elevenlabs_api_key,
                deepgram_api_key,
                app_settings,
                va_settings,
            )
            break
        except Exception as e:
            if attempt < max_retries - 1:
                logging.warning(
                    f"Attempt {attempt + 1} failed to initialize audio devices: {e}"
                )
                time.sleep(retry_delay)
            else:
                logging.error(
                    f"Failed to initialize audio devices after {max_retries} attempts: {e}"
                )
                raise

    log_file_path = os.path.join(os.getcwd(), "data", "chat_history.json")
    assistant_manager = AssistantManager(
        assistant, log_file_path, va_name, va_settings["user"]["username"]
    )

    assistant_manager.update_chat_history.connect(chat_window.update_chat_history)
    assistant_manager.write_to_cursor.connect(lambda text: pyautogui.write(text))
    chat_window.send_message.connect(assistant_manager.process_user_input)
    assistant_manager.set_chat_window(chat_window)
    # Change this line to start with AI disabled
    assistant_manager.set_send_to_ai_active(False)

    return assistant_manager


def cleanup():
    logging.info("Performing cleanup tasks...")
    for manager in assistant_managers:
        try:
            manager.clipboard_thread.stop()
            manager.assistant.pyaudio.terminate()
        except Exception as e:
            logging.error(f"Error during cleanup for manager: {e}")
    logging.info("Cleanup completed.")


def main():
    global main_window, assistant_managers, app_settings

    # Handle app settings
    app_settings_path = Path("app-settings.yaml")
    default_app_settings = load_default_app_settings()

    if app_settings_path.exists():
        app_settings = load_settings(str(app_settings_path), default_app_settings)
    else:
        app_settings = default_app_settings
        save_settings(app_settings, app_settings_path)
        logging.info("Created default app-settings.yaml file")

    # Verify API keys
    required_keys = ["OPENAI_API_KEY", "ELEVENLABS_API_KEY", "DEEPGRAM_API_KEY"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    if missing_keys:
        logging.error(
            f"Error: Missing required environment variables: {', '.join(missing_keys)}"
        )
        sys.exit(1)

    # Create data directory
    data_dir = os.path.join(os.getcwd(), "data")
    os.makedirs(data_dir, exist_ok=True)

    # Initialize application
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.assistant_managers = []  # Add this line
    clipboard_listener = ClipboardListener()
    assistant_managers = main_window.assistant_managers  # Update the global reference

    # Create single chat window
    chat_window = ChatWindow(
        "Multi-Assistant Chat", os.path.join(data_dir, "chat_history.json")
    )
    main_window.setCentralWidget(chat_window)

    # Add a small delay before creating assistant managers
    QTimer.singleShot(1000, lambda: initialize_assistants(chat_window))

    main_window.show()
    atexit.register(cleanup)
    sys.exit(app.exec())


def initialize_assistants(chat_window):
    """Initialize assistant managers with a delay"""
    va_configs = load_va_configs()
    for va_name, va_settings in va_configs.items():
        try:
            assistant_manager = create_assistant_manager(
                va_name, va_settings, chat_window
            )
            assistant_managers.append(assistant_manager)
        except Exception as e:
            logging.error(f"Failed to create assistant manager for {va_name}: {e}")


if __name__ == "__main__":
    # Load app settings before running the application
    app_settings_path = Path("app-settings.yaml")
    default_app_settings = load_default_app_settings()

    if app_settings_path.exists():
        app_settings = load_settings(str(app_settings_path), default_app_settings)
    else:
        app_settings = default_app_settings
        save_settings(app_settings, app_settings_path)
        logging.info("Created default app-settings.yaml file")

    # Just call the main() function which already has the working QApplication setup
    main()
