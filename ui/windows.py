# Copy all contents from ui.py into this file
from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QCheckBox,
    QComboBox,
    QStyle,
    QScrollArea,
    QFrame,
    QSizePolicy,
    QLineEdit,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
import pyperclip
import pyautogui
import logging
import json
import os
from .assistant_selector import AssistantSelector  # Note the relative import


# Rest of the contents from ui.py...
# (Copy everything else from ui.py, keeping the same class definitions)


class ChatWindow(QWidget):
    send_message = pyqtSignal(str)
    output_to_cursor_toggled = pyqtSignal(bool)
    monitor_clipboard_toggled = pyqtSignal(bool)
    send_ai_toggled = pyqtSignal(bool)  # New signal

    def __init__(self, title, log_file_path):
        super().__init__()
        self.layout = QVBoxLayout()
        self.log_file_path = log_file_path  # Add this line

        # Add participants list
        self.participants_label = QLabel("Participants: (You)")
        self.layout.addWidget(self.participants_label)

        # Add assistant selector
        self.assistant_selector = AssistantSelector()
        self.layout.addWidget(self.assistant_selector)

        # Chat history display (rename chat_display to chat_history)
        self.chat_history = QTextEdit()  # Changed from chat_display
        self.chat_history.setReadOnly(True)
        self.layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(50)
        self.send_button = QPushButton("Send")
        self.ai_toggle = QPushButton("AI")
        self.ai_toggle.setCheckable(True)
        self.ai_toggle.setChecked(False)

        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.ai_toggle)

        self.layout.addLayout(input_layout)
        self.setLayout(self.layout)

        # Connect signals
        self.send_button.clicked.connect(self.send_message_clicked)
        self.message_input.textChanged.connect(self.handle_input)
        self.ai_toggle.clicked.connect(self.on_send_ai_toggled)  # Add this line

        self.participants = ["(You)"]

    def add_participant(self, name):
        if name not in self.participants:
            self.participants.append(name)
            self.update_participants_label()

    def update_participants_label(self):
        self.participants_label.setText("Participants: " + ", ".join(self.participants))

    def on_output_cursor_toggled(self, checked):
        self.output_to_cursor_toggled.emit(checked)

    def on_monitor_clipboard_toggled(self, checked):
        self.monitor_clipboard_toggled.emit(checked)

    def on_send_ai_toggled(self, checked):
        self.send_ai_toggled.emit(checked)
        logging.info(f"Send to AI toggled: {checked}")

    def send_message_clicked(self):
        message = self.message_input.toPlainText().strip()
        if message:
            logging.info(f"Sending message: {message}")
            self.send_message.emit(message)
            self.message_input.clear()

    def update_chat_history(self, message, role="user", va_name=None):
        # Check if we can access the main window and assistant managers
        main_window = self.parent()
        if hasattr(main_window, "assistant_managers"):
            is_active = any(
                manager.send_to_ai_active for manager in main_window.assistant_managers
            )
        else:
            # Default to inactive if we can't access assistant managers yet
            is_active = False

        message_widget = QWidget()
        layout = QHBoxLayout()
        message_widget.setLayout(layout)

        text_label = QLabel(message)
        text_label.setWordWrap(True)
        text_label.setStyleSheet(
            f"""
            background-color: {'#2b2b2b' if not is_active and role == 'user' else '#1e1e1e' if role == 'user' else '#2b5b2b'};
            color: {'#808080' if not is_active and role == 'user' else '#ffffff'};
            border-radius: 10px;
            padding: 8px;
            """
        )

        cursor = self.chat_history.textCursor()

        # Fix the undefined align_right variable
        align_right = role == "user"

        block_format = cursor.blockFormat()
        if align_right:
            block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_format)

        frame_color = "#39FF14" if align_right else "#00BFFF"
        message_class = "user" if align_right else "assistant"
        frame_html = f"""
        <div style="
        ">
            <div style="
                color: {frame_color};
                margin: 10px 0px 5px 0px;
            " class="{message_class}">{message}</div>
        </div>
        """

        cursor.insertHtml(frame_html)
        cursor.insertBlock()
        self.chat_history.setTextCursor(cursor)

    def add_message(self, message, align_right=False):
        cursor = self.chat_history.textCursor()

        block_format = cursor.blockFormat()
        if align_right:
            block_format.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            block_format.setAlignment(Qt.AlignmentFlag.AlignLeft)
        cursor.setBlockFormat(block_format)

        frame_color = "#39FF14" if align_right else "#00BFFF"
        message_class = "user" if align_right else "assistant"
        frame_html = f"""
        <div style="
        ">
            <div style="
                color: {frame_color};
                margin: 10px 0px 5px 0px;
            " class="{message_class}">{message}</div>
        </div>
        """

        cursor.insertHtml(frame_html)
        cursor.insertBlock()
        self.chat_history.setTextCursor(cursor)

    def load_chat_history(self):
        if os.path.exists(self.log_file_path):
            with open(self.log_file_path, "r") as f:
                history = json.load(f)
            self.update_chat_history(
                "\n".join([f"{entry['type']}: {entry['content']}" for entry in history])
            )

    def handle_input(self):
        # This method is called when text changes in the input field
        # For now, we'll just use it to handle Enter key presses
        if self.message_input.document().size().height() > 50:
            # If text is too long, prevent new lines
            text = self.message_input.toPlainText()
            text = text.replace("\n", "")
            self.message_input.setPlainText(text)
            self.message_input.moveCursor(self.message_input.textCursor().End)


class MainWindow(QMainWindow):
    new_chat_window = pyqtSignal(str, str)  # Add log_file_path to the signal

    def __init__(self):
        super().__init__()
        self.chat_windows = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AI Assistant Chat")
        self.resize(800, 600)

        # Apply theme settings if available
        if hasattr(self, "app_settings") and "theme" in self.app_settings["app"]:
            self.apply_theme(self.app_settings["app"]["theme"])

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet("""
            background-color: #000000;
            color: #39FF14;
            font-family: 'Courier New', monospace;
        """)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # New chat button
        new_chat_button = QPushButton("New Chat")
        new_chat_button.clicked.connect(self.create_new_chat)
        new_chat_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: #39FF14;
                border: 2px solid #39FF14;
                border-radius: 20px;
                padding: 10px 20px;
                font-family: 'Courier New', monospace;
                font-size: 16px;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #39FF14;
                color: #000000;
            }
        """)
        layout.addWidget(new_chat_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Scroll area for chat windows
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #000000;
            }
        """)
        layout.addWidget(scroll_area)

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(20)
        scroll_area.setWidget(self.chat_container)

    def create_new_chat(self):
        va_name = f"VA_{len(self.chat_windows)}"
        log_file_path = os.path.join(
            os.getcwd(), "data", f"chat_history_{va_name}.json"
        )
        self.new_chat_window.emit(va_name, log_file_path)

    def add_chat_window(self, chat_window):
        self.chat_windows.append(chat_window)
        self.chat_layout.addWidget(chat_window)
