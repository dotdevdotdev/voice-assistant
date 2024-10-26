import sys
import os
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from config.settings import AppConfig
from utils.registry import ProviderRegistry
from core.events import EventBus, EventType, Event
from ui.chat_window import ChatWindow
from ui.styles import AppTheme
from modules.audio import create_audio_provider
from modules.speech import create_speech_provider
from modules.assistant import create_assistant_provider
from modules.clipboard import create_clipboard_provider
from core.interfaces.audio import AudioInputProvider
from core.interfaces.speech import SpeechToTextProvider
from core.interfaces.assistant import AssistantProvider
from core.interfaces.clipboard import ClipboardProvider


class Application:
    CONFIG_PATH = os.path.join("config", "app-settings.yaml")

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.event_bus = EventBus.get_instance()
        self.registry = ProviderRegistry.get_instance()

        # Set up asyncio integration first
        self._setup_asyncio()

        self.config = AppConfig.load(self.CONFIG_PATH)
        self._setup_event_handling()

    def _setup_event_handling(self):
        self.event_bus.subscribe(EventType.ERROR, self._handle_error)

    async def _handle_error(self, event: Event):
        # TODO: Implement proper error handling/display
        print(f"Error occurred: {event.error}", file=sys.stderr)

    def _setup_providers(self):
        """Initialize and register all providers"""
        try:
            # Audio provider
            audio_provider = create_audio_provider(self.config.audio.provider_type)
            self.registry.register_provider(
                AudioInputProvider, audio_provider, self.config.audio.config
            )

            # Speech provider
            speech_provider = create_speech_provider(self.config.speech.provider_type)
            self.registry.register_provider(
                SpeechToTextProvider, speech_provider, self.config.speech.config
            )

            # Assistant provider
            assistant_provider = create_assistant_provider(
                self.config.assistant.provider_type
            )
            self.registry.register_provider(
                AssistantProvider, assistant_provider, self.config.assistant.config
            )

            # Clipboard provider
            clipboard_provider = create_clipboard_provider(
                self.config.clipboard.provider_type
            )
            self.registry.register_provider(ClipboardProvider, clipboard_provider)

        except Exception as e:
            # Use the event loop directly instead of create_task
            self.loop.call_soon(
                lambda: self.loop.create_task(
                    self.event_bus.emit(Event(EventType.ERROR, error=e))
                )
            )
            raise

    def _setup_style(self):
        """Apply application styling"""
        theme = AppTheme(dark_mode=True)  # TODO: Get from config
        self.app.setPalette(theme.get_palette())
        self.app.setStyleSheet(theme.get_stylesheet())

    def run(self):
        """Start the application"""
        try:
            self._setup_providers()
            self._setup_style()

            # Create and show main window
            self.main_window = ChatWindow()
            self.main_window.show()

            # Start the application
            return self.app.exec()

        except Exception as e:
            print(f"Failed to start application: {e}", file=sys.stderr)
            return 1

    def _setup_asyncio(self):
        """Set up asyncio event loop integration with Qt"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Create a timer to process asyncio events
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_asyncio_events)
        self.async_timer.start(10)  # 10ms interval

    def _process_asyncio_events(self):
        """Process pending asyncio events"""
        try:
            self.loop.stop()
            self.loop.run_forever()
        except Exception as e:
            print(f"Error processing async events: {e}", file=sys.stderr)
