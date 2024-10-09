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
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont
import pyperclip
import pyautogui


class MainWindow(QMainWindow):
    start_listening = pyqtSignal()
    stop_listening = pyqtSignal()
    send_to_ai = pyqtSignal(str)
    speak_response = pyqtSignal(str)  # New signal for speaking responses

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 800, 600)  # Increased window size

        self.setup_fonts()
        layout = QVBoxLayout()

        self.status_label = QLabel("Listening...")
        self.status_label.setFont(self.label_font)
        layout.addWidget(self.status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(self.text_font)
        layout.addWidget(self.output_text)

        self.dictation_area = QTextEdit()
        self.dictation_area.setPlaceholderText("Transcribed text will appear here...")
        self.dictation_area.setFont(self.text_font)
        layout.addWidget(self.dictation_area)

        button_layout = QHBoxLayout()

        self.send_ai_toggle = self.create_toggle_button("Send to AI")
        self.send_ai_toggle.clicked.connect(self.on_send_ai_toggle)
        button_layout.addWidget(self.send_ai_toggle)

        self.output_cursor_toggle = self.create_toggle_button("Output to Cursor")
        self.output_cursor_toggle.clicked.connect(self.on_output_cursor_toggle)
        button_layout.addWidget(self.output_cursor_toggle)

        self.copy_clipboard_button = QPushButton("Copy to Clipboard")
        self.copy_clipboard_button.clicked.connect(self.on_copy_to_clipboard)
        self.copy_clipboard_button.setFont(self.button_font)
        button_layout.addWidget(self.copy_clipboard_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.send_to_ai_active = False
        self.output_to_cursor_active = False

    def setup_fonts(self):
        self.label_font = QFont()
        self.label_font.setPointSize(16)

        self.text_font = QFont()
        self.text_font.setPointSize(14)

        self.button_font = QFont()
        self.button_font.setPointSize(14)
        self.button_font.setBold(True)

    def create_toggle_button(self, text):
        button = QPushButton(text)
        button.setCheckable(True)
        button.setFont(self.button_font)
        button.setStyleSheet("""
            QPushButton {
                background-color: black;
                color: #39FF14;
                border: 2px solid #39FF14;
                border-radius: 5px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #39FF14;
                color: black;
                border: 2px solid black;
            }
        """)
        return button

    def update_output(self, text):
        self.output_text.append(text)
        if self.send_to_ai_active and text.startswith("AI:"):
            self.speak_response.emit(text[4:])  # Emit signal to speak AI response

    def update_dictation(self, text):
        self.dictation_area.setPlainText(text)
        if self.send_to_ai_active:
            self.send_to_ai.emit(text)
        if self.output_to_cursor_active:
            pyautogui.write(text)

    def on_send_ai_toggle(self):
        self.send_to_ai_active = self.send_ai_toggle.isChecked()
        if self.send_to_ai_active:
            self.output_cursor_toggle.setChecked(False)
            self.output_to_cursor_active = False

    def on_output_cursor_toggle(self):
        self.output_to_cursor_active = self.output_cursor_toggle.isChecked()
        if self.output_to_cursor_active:
            self.send_ai_toggle.setChecked(False)
            self.send_to_ai_active = False

    def on_copy_to_clipboard(self):
        text = self.dictation_area.toPlainText().strip()
        if text:
            pyperclip.copy(text)

    def closeEvent(self, event):
        self.stop_listening.emit()
        event.accept()
