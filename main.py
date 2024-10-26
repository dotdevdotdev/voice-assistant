import sys
import os
import yaml
import logging
import copy
import atexit
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread
from ui import MainWindow, ChatWindow
from va_manager import VAManager
from audio_manager import AudioManager
from event_bus import EventBus
from manager_registry import ManagerRegistry
# from dotenv import load_dotenv

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


def cleanup():
    logging.info("Performing cleanup tasks...")
    if hasattr(QApplication.instance(), "activeWindow"):
        main_window = QApplication.instance().activeWindow()
        if hasattr(main_window, "va_manager") and main_window.va_manager:
            try:
                main_window.va_manager.cleanup_current_va()
            except Exception as e:
                logging.error(f"Error during cleanup: {e}")
    logging.info("Cleanup completed.")


class Application:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Starting application initialization")

        # Initialize Qt Application
        self.logger.debug("Creating QApplication")
        self.app = QApplication(sys.argv)
        self.logger.debug("QApplication created")

        # Initialize singletons
        self.logger.debug("Initializing EventBus")
        self.event_bus = EventBus.get_instance()
        self.logger.debug("EventBus initialized")

        self.logger.debug("Initializing ManagerRegistry")
        self.registry = ManagerRegistry.get_instance()
        self.logger.debug("ManagerRegistry initialized")

        # Load configurations
        self.logger.debug("Loading configurations")
        self.app_settings = load_default_app_settings()
        self.va_configs = load_va_configs()
        self.logger.debug("Configurations loaded")

        # Initialize managers first - with defensive programming
        self.audio_manager = None
        try:
            self.logger.debug("Initializing AudioManager")
            self.audio_manager = AudioManager()
            self.logger.debug("AudioManager initialized successfully")
            # Give the event loop a chance to process
            QApplication.processEvents()
        except Exception as e:
            self.logger.error(f"Failed to initialize AudioManager: {e}", exc_info=True)
            raise RuntimeError("AudioManager initialization failed") from e

        # Small delay to ensure audio system is stable
        QThread.msleep(100)
        QApplication.processEvents()

        # Initialize UI after managers
        self.chat_window = None
        try:
            self.logger.debug("Creating ChatWindow")
            self.chat_window = ChatWindow()
            self.logger.debug("ChatWindow created successfully")
        except Exception as e:
            self.logger.error(f"Error creating ChatWindow: {e}", exc_info=True)
            if self.audio_manager:
                self.audio_manager.cleanup()
            raise RuntimeError("ChatWindow creation failed") from e

        # Initialize VA manager last
        self.va_manager = None
        try:
            self.logger.debug("Initializing VAManager")
            self.va_manager = VAManager(self.chat_window, self.va_configs)
            self.logger.debug("VAManager initialized successfully")
        except Exception as e:
            self.logger.error(f"Error initializing VAManager: {e}", exc_info=True)
            if self.audio_manager:
                self.audio_manager.cleanup()
            raise RuntimeError("VAManager initialization failed") from e

        # Register managers
        self.logger.debug("Registering managers")
        self.registry.audio_manager = self.audio_manager
        self.registry.va_manager = self.va_manager
        self.logger.debug("Managers registered")

        # Connect signals
        try:
            self.logger.debug("Connecting signals")
            self._connect_signals()
            self.logger.debug("Signals connected successfully")
        except Exception as e:
            self.logger.error(f"Error connecting signals: {e}", exc_info=True)
            self.cleanup()
            raise RuntimeError("Signal connection failed") from e

        # Register cleanup
        atexit.register(self.cleanup)

        # Show UI
        self.logger.debug("Showing ChatWindow")
        self.chat_window.show()
        self.logger.info("Application initialization complete")

    def _connect_signals(self):
        """Connect global application signals"""
        self.logger.debug("Connecting window close signal")
        self.chat_window.closing.connect(self.cleanup)

        self.logger.debug("Connecting voice input toggle")
        self.chat_window.voice_input_toggled.connect(
            self.audio_manager.set_listening_state
        )

    def cleanup(self):
        """Cleanup application resources"""
        self.logger.info("Cleaning up application resources...")
        self.audio_manager.cleanup()
        self.va_manager.cleanup()

    def run(self):
        """Run the application"""
        return self.app.exec()


def main():
    try:
        app = Application()
        sys.exit(app.run())
    except Exception as e:
        logging.critical("Fatal error during application startup", exc_info=True)
        sys.exit(1)


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

    main()
