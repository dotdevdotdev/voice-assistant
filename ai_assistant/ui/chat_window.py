from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QSettings
from .components.message_view import MessageView
from .components.input_area import InputArea
from .components.assistant_selector import AssistantSelector
from .components.audio_controls import AudioControls
from core.interfaces.assistant import Message
from utils.registry import ProviderRegistry
from core.events import EventBus, Event, EventType


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._event_bus = EventBus.get_instance()
        self._settings = QSettings("AIAssistant", "Chat")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(800, 600)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section with assistant selector and audio controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        self.assistant_selector = AssistantSelector()
        self.assistant_selector.model_changed.connect(self._on_model_changed)

        self.audio_controls = AudioControls()
        self.audio_controls.recording_started.connect(self._on_recording_started)
        self.audio_controls.recording_stopped.connect(self._on_recording_stopped)

        top_layout.addWidget(self.assistant_selector)
        top_layout.addWidget(self.audio_controls)

        # Message view
        self.message_view = MessageView()

        # Input area
        self.input_area = InputArea()
        self.input_area.message_submitted.connect(self._on_message_submitted)
        self.input_area.recording_toggled.connect(
            self.audio_controls.record_button.setChecked
        )

        # Add widgets to splitter
        splitter.addWidget(top_widget)
        splitter.addWidget(self.message_view)
        splitter.addWidget(self.input_area)

        # Set stretch factors
        splitter.setStretchFactor(0, 0)  # Top section - fixed
        splitter.setStretchFactor(1, 1)  # Message view - stretches
        splitter.setStretchFactor(2, 0)  # Input area - fixed

        layout.addWidget(splitter)

    async def _on_message_submitted(self, text: str):
        # Add user message to view
        user_message = Message("user", text)
        self.message_view.add_message(user_message)

        # Get assistant response
        try:
            assistant = ProviderRegistry.get_instance().get_provider(AssistantProvider)
            messages = self.message_view.get_messages()

            # Create assistant message placeholder
            assistant_message = Message("assistant", "")
            self.message_view.add_message(assistant_message)

            full_response = ""
            async for chunk in assistant.send_message(messages):
                full_response += chunk
                assistant_message.content = full_response
                # Need to implement message update mechanism

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))

    def _on_model_changed(self, model: str, config: dict):
        # Update the assistant configuration
        pass

    def _on_recording_started(self):
        self.input_area.setEnabled(False)

    def _on_recording_stopped(self):
        self.input_area.setEnabled(True)

    def load_settings(self):
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_settings(self):
        self._settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
