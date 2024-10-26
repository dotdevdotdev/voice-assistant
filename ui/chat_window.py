from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QListWidget,
    QSplitter,
)
from PyQt6.QtCore import pyqtSignal, Qt
from .assistant_selector import AssistantSelector
from .styles import NEON_GREEN, NEON_BLUE, DARK_BG


class ChatWindow(QWidget):
    send_message = pyqtSignal(str)
    output_to_cursor_toggled = pyqtSignal(bool)
    send_ai_toggled = pyqtSignal(bool)
    monitor_clipboard_toggled = pyqtSignal(bool)

    def __init__(self, title, log_file_path):
        super().__init__()
        self.title = title
        self.log_file_path = log_file_path
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Assistant selector at the top - minimal height
        selector_container = QWidget()
        selector_container.setFixedHeight(60)  # Fixed height for the selector
        selector_layout = QVBoxLayout(selector_container)
        selector_layout.setContentsMargins(0, 0, 0, 0)

        self.assistant_selector = AssistantSelector()
        selector_layout.addWidget(self.assistant_selector)
        main_layout.addWidget(selector_container)

        # Create chat area with participants list - this will expand to fill space
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)

        # Participants list and chat display in splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Participants list on the left side of chat
        self.participants_list = QListWidget()
        self.participants_list.setMaximumWidth(150)
        self.participants_list.setStyleSheet(f"""
            QListWidget {{
                border: 2px solid {NEON_GREEN};
                border-radius: 4px;
                padding: 5px;
            }}
            QListWidget::item {{
                color: {NEON_GREEN};
                padding: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {NEON_GREEN};
                color: {DARK_BG};
            }}
        """)

        # Chat display area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        splitter.addWidget(self.participants_list)
        splitter.addWidget(self.chat_display)
        chat_layout.addWidget(splitter)

        # Add the chat container with a stretch factor
        main_layout.addWidget(chat_container, stretch=1)

        # Input area at the bottom - minimal height
        input_container = QWidget()
        input_container.setFixedHeight(40)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.message_input = QLineEdit()
        self.message_input.returnPressed.connect(self.send_message_clicked)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message_clicked)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        main_layout.addWidget(input_container)

        # Control buttons - minimal height
        controls_container = QWidget()
        controls_container.setFixedHeight(40)
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.toggle_cursor_button = QPushButton("Toggle Cursor Output")
        self.toggle_cursor_button.setCheckable(True)
        self.toggle_ai_button = QPushButton("Toggle AI")
        self.toggle_ai_button.setCheckable(True)
        self.toggle_clipboard_button = QPushButton("Toggle Clipboard")
        self.toggle_clipboard_button.setCheckable(True)

        controls_layout.addWidget(self.toggle_cursor_button)
        controls_layout.addWidget(self.toggle_ai_button)
        controls_layout.addWidget(self.toggle_clipboard_button)

        main_layout.addWidget(controls_container)

        self.setLayout(main_layout)

        # Connect signals
        self.toggle_cursor_button.toggled.connect(self.output_to_cursor_toggled)
        self.toggle_ai_button.toggled.connect(self.send_ai_toggled)
        self.toggle_clipboard_button.toggled.connect(self.monitor_clipboard_toggled)

    def send_message_clicked(self):
        message = self.message_input.text().strip()
        if message:
            self.send_message.emit(message)
            self.message_input.clear()

    def update_chat_history(self, history):
        self.chat_display.setHtml(history)
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def add_participant(self, name):
        self.participants_list.addItem(name)

    def remove_participant(self, name):
        items = self.participants_list.findItems(name, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.participants_list.takeItem(self.participants_list.row(item))
