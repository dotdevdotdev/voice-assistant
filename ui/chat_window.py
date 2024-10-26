from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QScrollArea,
)
from PyQt6.QtCore import pyqtSignal, Qt
from .assistant_selector import AssistantSelector
from event_bus import EventBus
import logging


class ChatWindow(QMainWindow):
    # Signals
    closing = pyqtSignal()  # Emitted when window is closing
    send_message = pyqtSignal(str)  # Emitted when user sends a message
    send_ai_toggled = pyqtSignal(bool)  # AI processing toggle
    monitor_clipboard_toggled = pyqtSignal(bool)  # Clipboard monitoring toggle
    voice_input_toggled = pyqtSignal(bool)  # Voice input toggle

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.event_bus = EventBus.get_instance()

        # Setup UI
        self.setWindowTitle("AI Chat")
        self.setup_ui()

        # Connect event bus signals
        self._connect_event_bus()

    def setup_ui(self):
        """Initialize the UI components"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Assistant selector
        self.assistant_selector = AssistantSelector()
        layout.addWidget(self.assistant_selector)

        # Controls area
        controls_layout = QHBoxLayout()

        # Toggle buttons
        self.ai_toggle = QPushButton("AI Processing")
        self.ai_toggle.setCheckable(True)
        self.clipboard_toggle = QPushButton("Monitor Clipboard")
        self.clipboard_toggle.setCheckable(True)
        self.voice_toggle = QPushButton("Voice Input")
        self.voice_toggle.setCheckable(True)

        controls_layout.addWidget(self.ai_toggle)
        controls_layout.addWidget(self.clipboard_toggle)
        controls_layout.addWidget(self.voice_toggle)

        # Input area
        self.input_field = QTextEdit()
        self.input_field.setMaximumHeight(100)
        self.send_button = QPushButton("Send")

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)

        layout.addLayout(controls_layout)
        layout.addLayout(input_layout)

        # Connect UI signals
        self._connect_ui_signals()

    def _connect_ui_signals(self):
        """Connect all UI-related signals"""
        self.send_button.clicked.connect(self._handle_send)
        self.ai_toggle.toggled.connect(self._handle_ai_toggle)
        self.clipboard_toggle.toggled.connect(self._handle_clipboard_toggle)
        self.voice_toggle.toggled.connect(self._handle_voice_toggle)
        self.assistant_selector.assistant_selected.connect(
            self._handle_assistant_selected
        )

    def _connect_event_bus(self):
        """Connect to event bus signals"""
        self.event_bus.va_response_ready.connect(self.display_message)
        self.event_bus.va_state_changed.connect(self._handle_va_state_change)

    def _handle_send(self):
        """Handle send button click"""
        message = self.input_field.toPlainText().strip()
        if message:
            self.send_message.emit(message)
            self.input_field.clear()

    def _handle_ai_toggle(self, checked: bool):
        """Handle AI processing toggle"""
        self.send_ai_toggled.emit(checked)
        self.event_bus.ai_state_changed.emit(checked)

    def _handle_clipboard_toggle(self, checked: bool):
        """Handle clipboard monitoring toggle"""
        self.monitor_clipboard_toggled.emit(checked)
        self.event_bus.clipboard_state_changed.emit(checked)

    def _handle_voice_toggle(self, checked: bool):
        """Handle voice input toggle"""
        self.voice_input_toggled.emit(checked)
        self.event_bus.audio_state_changed.emit(checked)

    def _handle_assistant_selected(self, va_name: str):
        """Handle assistant selection"""
        # This will be handled by VAManager through the registry
        pass

    def _handle_va_state_change(self, va_name: str, is_active: bool):
        """Handle VA state changes"""
        if is_active:
            self.assistant_selector.add_assistant(va_name)
        else:
            self.assistant_selector.remove_assistant(va_name)

    def display_message(
        self, message: str, role: str = "assistant", va_name: str = None
    ):
        """Display a message in the chat window"""
        if role == "user":
            prefix = "You: "
        elif role == "assistant":
            prefix = f"{va_name}: " if va_name else "Assistant: "
        elif role == "clipboard":
            prefix = "Clipboard: "
        else:
            prefix = ""

        self.chat_display.append(f"{prefix}{message}")

    def add_participant(self, name: str):
        """Add a participant to the chat"""
        self.assistant_selector.add_assistant(name)

    def closeEvent(self, event):
        """Handle window close event"""
        self.closing.emit()
        super().closeEvent(event)
