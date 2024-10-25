from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import sys
from typing import Optional

from audio_manager import AudioManager
from assistant import Assistant
from ui import MainWindow


class Application(QApplication):
    def __init__(self, argv: list):
        super().__init__(argv)

        # Initialize core components
        self.audio_manager: Optional[AudioManager] = None
        self.assistant: Optional[Assistant] = None
        self.main_window: Optional[MainWindow] = None

        # Setup timer for cleanup
        self.exit_timer = QTimer()
        self.exit_timer.timeout.connect(self.cleanup)

        self.initialize()

    def initialize(self) -> None:
        """Initialize all application components"""
        try:
            # Initialize core services
            self.audio_manager = AudioManager()
            self.assistant = Assistant()

            # Initialize and show main window
            self.main_window = MainWindow(self.audio_manager, self.assistant)
            self.main_window.show()

            # Connect cleanup to application aboutToQuit signal
            self.aboutToQuit.connect(self.cleanup)

        except Exception as e:
            print(f"Failed to initialize application: {str(e)}")
            self.quit()

    def cleanup(self) -> None:
        """Cleanup resources before application exit"""
        if self.audio_manager:
            self.audio_manager.cleanup()

        if self.assistant:
            self.assistant.cleanup()

        if self.main_window:
            self.main_window.cleanup()

    @staticmethod
    def run() -> int:
        """Create and run the application"""
        app = Application(sys.argv)
        return app.exec()
