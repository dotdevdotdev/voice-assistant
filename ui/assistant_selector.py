from PyQt6.QtWidgets import QWidget, QHBoxLayout, QComboBox, QPushButton
from PyQt6.QtCore import pyqtSignal
from event_bus import EventBus


class AssistantSelector(QWidget):
    assistant_selected = pyqtSignal(str)  # Emits selected assistant name

    def __init__(self):
        super().__init__()
        self.event_bus = EventBus.get_instance()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)

        # Assistant dropdown
        self.assistant_combo = QComboBox()
        self.assistant_combo.currentTextChanged.connect(self._handle_selection)

        # Add/Remove buttons
        self.add_button = QPushButton("Add")
        self.remove_button = QPushButton("Remove")
        self.remove_button.setEnabled(False)

        # Add widgets to layout
        layout.addWidget(self.assistant_combo)
        layout.addWidget(self.add_button)
        layout.addWidget(self.remove_button)

        # Connect button signals
        self.add_button.clicked.connect(self._handle_add)
        self.remove_button.clicked.connect(self._handle_remove)

    def add_assistant(self, name: str):
        """Add assistant to selector"""
        if self.assistant_combo.findText(name) == -1:
            self.assistant_combo.addItem(name)
            self.remove_button.setEnabled(True)

    def remove_assistant(self, name: str):
        """Remove assistant from selector"""
        index = self.assistant_combo.findText(name)
        if index != -1:
            self.assistant_combo.removeItem(index)
            if self.assistant_combo.count() == 0:
                self.remove_button.setEnabled(False)

    def _handle_selection(self, name: str):
        """Handle assistant selection"""
        if name:
            self.assistant_selected.emit(name)

    def _handle_add(self):
        """Handle add button click"""
        current = self.assistant_combo.currentText()
        if current:
            self.event_bus.va_state_changed.emit(current, True)

    def _handle_remove(self):
        """Handle remove button click"""
        current = self.assistant_combo.currentText()
        if current:
            self.event_bus.va_state_changed.emit(current, False)
