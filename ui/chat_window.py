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

    def __init__(self, title):
        super().__init__()
        self.title = title
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
        self.chat_display.setAcceptRichText(True)
        self.chat_display.setStyleSheet(f"""
            QTextEdit {{
                background-color: {DARK_BG};
                border: 2px solid {NEON_GREEN};
                border-radius: 4px;
                padding: 10px;
            }}
        """)

        # Initialize with a simple HTML structure
        self.chat_display.setHtml('<div id="chat-container"></div>')

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

        # Add test button for debugging
        self.test_button = QPushButton("Test Messages")
        self.test_button.clicked.connect(self.test_messages)
        controls_layout.addWidget(self.test_button)

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
            print(f"ChatWindow: Sending message: {message}")
            # Remove the receivers check since it's not available in PyQt6
            self.send_message.emit(message)
            self.message_input.clear()
            # Add immediate test display
            print("ChatWindow: Testing direct message display")
            self.display_message(message, role="user")

    def display_message(self, message, role="user", va_name=None):
        # Set text color
        text_color = NEON_GREEN if role == "user" else NEON_BLUE

        # Create message HTML
        message_html = f"""
            <div style="
                display: inline-block;
                max-width: 70%;
                padding: 12px;
                border: 2px solid {text_color};
                border-radius: 10px;
                color: {text_color};
                background-color: {DARK_BG};
                font-size: 14pt;
            ">
                <div style="line-height: 1.4;">
                    {message}
                </div>
                <div style="
                    font-size: 11pt;
                    color: #666;
                    margin-top: 5px;
                    text-align: {'right' if role == 'user' else 'left'};
                ">
                    {va_name if va_name and not role == 'user' else 'You'}
                </div>
            </div>
        """

        # Get current content
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        # Insert a line break if there's already content
        if not self.chat_display.toPlainText().strip() == "":
            cursor.insertHtml("<br /><br />")

        # Insert the new message
        cursor.insertHtml(message_html)

        # Scroll to the bottom
        self.chat_display.verticalScrollBar().setValue(
            self.chat_display.verticalScrollBar().maximum()
        )

    def add_participant(self, name):
        self.participants_list.addItem(name)

    def remove_participant(self, name):
        items = self.participants_list.findItems(name, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.participants_list.takeItem(self.participants_list.row(item))

    def test_messages(self):
        """Debug function to test message display"""
        print("Testing message display...")

        # Test user message
        self.display_message("This is a test user message", role="user")

        # Test assistant message
        self.display_message(
            "This is a test assistant response",
            role="assistant",
            va_name="Test Assistant",
        )
