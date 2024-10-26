from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    """Central event bus for inter-manager communication"""

    # Audio related signals
    audio_transcription = pyqtSignal(str)  # Emits transcribed text
    audio_state_changed = pyqtSignal(bool)  # Emits when audio recording starts/stops

    # VA related signals
    va_response_ready = pyqtSignal(str, str)  # (response_text, va_name)
    va_state_changed = pyqtSignal(str, bool)  # (va_name, is_active)

    # Global state signals
    ai_state_changed = pyqtSignal(bool)
    clipboard_state_changed = pyqtSignal(bool)

    _instance = None

    @staticmethod
    def get_instance():
        """Singleton accessor"""
        if EventBus._instance is None:
            EventBus._instance = EventBus()
        return EventBus._instance
