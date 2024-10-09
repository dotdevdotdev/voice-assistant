from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
    QHBoxLayout,
    QCheckBox,
)
from PyQt6.QtCore import pyqtSignal
import pyperclip
import pyautogui


class MainWindow(QMainWindow):
    start_listening = pyqtSignal()
    stop_listening = pyqtSignal()
    send_to_ai = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        self.status_label = QLabel("Listening...")
        layout.addWidget(self.status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        # Add dictation area
        self.dictation_area = QTextEdit()
        self.dictation_area.setPlaceholderText("Type or dictate here...")
        layout.addWidget(self.dictation_area)

        # Add auto-send checkbox
        self.auto_send_checkbox = QCheckBox("Send to AI automatically")
        layout.addWidget(self.auto_send_checkbox)

        # Add buttons
        button_layout = QHBoxLayout()

        self.send_ai_button = QPushButton("Send to AI")
        self.send_ai_button.clicked.connect(self.on_send_to_ai)
        button_layout.addWidget(self.send_ai_button)

        self.output_cursor_button = QPushButton("Output to Cursor")
        self.output_cursor_button.clicked.connect(self.on_output_to_cursor)
        button_layout.addWidget(self.output_cursor_button)

        self.copy_clipboard_button = QPushButton("Copy to Clipboard")
        self.copy_clipboard_button.clicked.connect(self.on_copy_to_clipboard)
        button_layout.addWidget(self.copy_clipboard_button)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_output(self, text):
        self.output_text.append(text)

    def on_send_to_ai(self):
        text = self.dictation_area.toPlainText().strip()
        if text:
            self.send_to_ai.emit(text)
            self.dictation_area.clear()  # Clear the dictation area after sending

    def on_output_to_cursor(self):
        text = self.dictation_area.toPlainText().strip()
        if text:
            pyautogui.write(text)

    def on_copy_to_clipboard(self):
        text = self.dictation_area.toPlainText().strip()
        if text:
            pyperclip.copy(text)

    def closeEvent(self, event):
        self.stop_listening.emit()
        event.accept()

    def should_auto_send(self):
        return self.auto_send_checkbox.isChecked()
