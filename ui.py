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
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette
import pyperclip
import pyautogui


class ChatWindow(QWidget):
    send_message = pyqtSignal(str)

    def __init__(self, va_name):
        super().__init__()
        self.va_name = va_name
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Set the background color to black
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        self.setPalette(palette)

        # Chat area
        self.chat_area = QScrollArea()
        self.chat_area.setStyleSheet(
            "background-color: #000000; border: 1px solid #39FF14;"
        )
        self.chat_widget = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_area.setWidget(self.chat_widget)
        self.chat_area.setWidgetResizable(True)
        layout.addWidget(self.chat_area)

        # Input area
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setFixedHeight(50)
        self.message_input.setStyleSheet(
            "background-color: #000000; color: #39FF14; border: 1px solid #39FF14;"
        )
        self.send_button = QPushButton("Send")
        self.send_button.setStyleSheet(
            "background-color: #000000; color: #39FF14; border: 1px solid #39FF14;"
        )
        self.send_button.clicked.connect(self.send_message_clicked)
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)
        layout.addLayout(input_layout)

        # Control buttons
        control_layout = QHBoxLayout()
        self.send_ai_toggle = QPushButton("Send to AI")
        self.send_ai_toggle.setCheckable(True)
        self.output_cursor_toggle = QPushButton("Output to Cursor")
        self.output_cursor_toggle.setCheckable(True)
        self.monitor_clipboard_toggle = QPushButton("Monitor Clipboard")
        self.monitor_clipboard_toggle.setCheckable(True)

        for button in [
            self.send_ai_toggle,
            self.output_cursor_toggle,
            self.monitor_clipboard_toggle,
        ]:
            button.setStyleSheet("""
                QPushButton {
                    background-color: #000000;
                    color: #39FF14;
                    border: 1px solid #39FF14;
                }
                QPushButton:checked {
                    background-color: #39FF14;
                    color: #000000;
                }
            """)

        control_layout.addWidget(self.send_ai_toggle)
        control_layout.addWidget(self.output_cursor_toggle)
        control_layout.addWidget(self.monitor_clipboard_toggle)
        layout.addLayout(control_layout)

        self.setLayout(layout)

    def send_message_clicked(self):
        message = self.message_input.toPlainText()
        if message:
            self.send_message.emit(message)
            self.message_input.clear()
            self.add_message(message, is_user=True)

    def add_message(self, message, is_user=False):
        message_widget = QLabel(message)
        message_widget.setWordWrap(True)

        if is_user:
            message_widget.setStyleSheet(
                "background-color: #000000; color: #39FF14; border: 1px solid #39FF14; border-radius: 10px; padding: 10px; margin: 5px;"
            )
            message_widget.setAlignment(Qt.AlignmentFlag.AlignLeft)
        else:
            message_widget.setStyleSheet(
                "background-color: #000000; color: #00BFFF; border: 1px solid #00BFFF; border-radius: 10px; padding: 10px; margin: 5px;"
            )
            message_widget.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.chat_layout.addWidget(message_widget)

        # Ensure the latest message is visible
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )

    def update_chat_history(self, history):
        # Clear existing messages
        for i in reversed(range(self.chat_layout.count())):
            self.chat_layout.itemAt(i).widget().setParent(None)

        # Add new messages
        for entry in history.split("\n"):
            parts = entry.split(" - ", 1)
            if len(parts) == 2:
                metadata, content = parts
                is_user = "User" in metadata
                self.add_message(content, is_user)

        # Scroll to the bottom
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )


class MainWindow(QMainWindow):
    new_chat_window = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multi-Chat AI Assistant")
        self.setGeometry(100, 100, 800, 600)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)

        # Set the background color to black
        central_widget.setAutoFillBackground(True)
        palette = central_widget.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#000000"))
        central_widget.setPalette(palette)

        # Chat windows area
        self.chat_area = QScrollArea()
        self.chat_area.setStyleSheet(
            "background-color: #000000; border: 1px solid #39FF14;"
        )
        self.chat_widget = QWidget()
        self.chat_layout = QHBoxLayout(self.chat_widget)
        self.chat_area.setWidget(self.chat_widget)
        self.chat_area.setWidgetResizable(True)
        main_layout.addWidget(self.chat_area)

        # New chat button
        new_chat_button = QPushButton("New Chat")
        new_chat_button.setStyleSheet(
            "background-color: #000000; color: #39FF14; border: 1px solid #39FF14;"
        )
        new_chat_button.clicked.connect(self.create_new_chat)
        main_layout.addWidget(new_chat_button)

        self.setCentralWidget(central_widget)

    def create_new_chat(self):
        va_name = f"VA_{len(self.chat_layout)}"  # Simple naming scheme
        self.new_chat_window.emit(va_name)

    def add_chat_window(self, chat_window):
        self.chat_layout.addWidget(chat_window)
