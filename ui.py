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


class ChatWindow(QWidget):
    send_message = pyqtSignal(str)
    output_to_cursor_toggled = pyqtSignal(bool)
    monitor_clipboard_toggled = pyqtSignal(bool)
    send_ai_toggled = pyqtSignal(bool)  # New signal

    def __init__(self, va_name, log_file_path):
        super().__init__()
        self.va_name = va_name
        self.log_file_path = log_file_path
        self.init_ui()
        self.load_chat_history()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Chat history area
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("""
            font-family: monospace;
            font-size: 18px;
            font-weight: bold;
            color: #000000;
        """)
        layout.addWidget(self.chat_history)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(15)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                background-color: #000000;
                color: #FFFFFF;
                border: 2px solid #39FF14;
                border-radius: 20px;
                padding: 10px 15px;
                font-family: monospace;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #000000;
                color: #39FF14;
                border: 2px solid #39FF14;
                border-radius: 20px;
                padding: 10px 20px;
                font-family: monospace;
                font-size: 18px;
                font-weight: bold;
                min-width: 100px;
                transition: background-color 0.3s ease-out, color 0.3s ease-out, transform 0.3s ease-out;
                transform: scale(1);
            }
            QPushButton:checked {
                background-color: #39FF14;
                color: #000000;
            }
            QPushButton:hover {
                background-color: #39FF14;
                color: #000000;
            }
        """)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(15)
        self.send_ai_toggle = QPushButton("Send to AI")
        self.output_cursor_toggle = QPushButton("Output to Cursor")
        self.monitor_clipboard_toggle = QPushButton("Monitor Clipboard")

        for button in [
            self.send_ai_toggle,
            self.output_cursor_toggle,
            self.monitor_clipboard_toggle,
        ]:
            button.setCheckable(True)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #000000;
                    color: #39FF14;
                    border: 2px solid #39FF14;
                    border-radius: 20px;
                    padding: 10px 20px;
                    font-family: monospace;
                    font-size: 18px;
                    font-weight: bold;
                    min-width: 100px;
                    transition: background-color 0.3s ease-out, color 0.3s ease-out, transform 0.3s ease-out;
                    transform: scale(1);
                }
                QPushButton:checked {
                    background-color: #39FF14;
                    color: #000000;
                }
                QPushButton:hover {
                    background-color: #39FF14;
                    color: #000000;
                }
            """)
            toolbar_layout.addWidget(button)

        self.send_ai_toggle.setChecked(True)
        layout.addLayout(toolbar_layout)

        self.setLayout(layout)

        # Connect signals
        self.send_button.clicked.connect(self.send_message_action)
        self.input_field.returnPressed.connect(self.send_message_action)
        self.output_cursor_toggle.toggled.connect(self.on_output_cursor_toggled)
        self.monitor_clipboard_toggle.toggled.connect(self.on_monitor_clipboard_toggled)
        self.send_ai_toggle.toggled.connect(self.on_send_ai_toggled)

    def on_output_cursor_toggled(self, checked):
        self.output_to_cursor_toggled.emit(checked)

    def on_monitor_clipboard_toggled(self, checked):
        self.monitor_clipboard_toggled.emit(checked)

    def on_send_ai_toggled(self, checked):
        self.send_ai_toggled.emit(checked)
        logging.info(f"Send to AI toggled: {checked}")

    def send_message_action(self):
        message = self.input_field.text().strip()
        if message:
            logging.info(f"Sending message: {message}")
            self.send_message.emit(message)
            self.input_field.clear()

    def update_chat_history(self, history):
        logging.debug(f"Updating chat history for {self.va_name}")
        logging.debug(f"Received history: {history}")
        self.chat_history.clear()
        messages = history.split("\n")
        for message in messages:
            if "User" in message:
                self.add_message(message.split("User: ", 1)[1], align_right=True)
            elif "Assistant" in message:
                self.add_message(message.split("Assistant: ", 1)[1], align_right=False)
            else:
                self.chat_history.append(message)

        # Scroll to the bottom of the chat history
        scrollbar = self.chat_history.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        logging.debug("Chat history updated and scrolled to bottom")

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


class MainWindow(QMainWindow):
    new_chat_window = pyqtSignal(str, str)  # Add log_file_path to the signal

    def __init__(self):
        super().__init__()
        self.chat_windows = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setGeometry(100, 100, 800, 600)

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
