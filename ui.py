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
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon
import pyperclip
import pyautogui


class MainWindow(QMainWindow):
    start_listening = pyqtSignal()
    stop_listening = pyqtSignal()
    send_to_ai = pyqtSignal(str)
    start_clipboard_monitoring = pyqtSignal()
    stop_clipboard_monitoring = pyqtSignal()
    send_ai_toggle = pyqtSignal(bool)

    def __init__(self, theme_settings):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 800, 600)
        self.apply_theme(theme_settings)

        self.setup_fonts()
        layout = QVBoxLayout()

        self.status_label = QLabel("Listening...")
        self.status_label.setFont(self.label_font)
        layout.addWidget(self.status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(self.text_font)
        layout.addWidget(self.output_text)

        dictation_layout = QHBoxLayout()
        dictation_label = QLabel("Dictation Area")
        dictation_label.setFont(self.label_font)
        dictation_layout.addWidget(dictation_label)

        self.copy_clipboard_button = QPushButton()
        copy_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton)
        self.copy_clipboard_button.setIcon(copy_icon)
        self.copy_clipboard_button.setFixedSize(30, 30)
        self.copy_clipboard_button.setToolTip("Copy to Clipboard")
        self.copy_clipboard_button.clicked.connect(self.on_copy_to_clipboard)
        dictation_layout.addWidget(self.copy_clipboard_button)

        layout.addLayout(dictation_layout)

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

        self.clipboard_monitor_toggle = self.create_toggle_button("Monitor Clipboard")
        self.clipboard_monitor_toggle.clicked.connect(self.on_clipboard_monitor_toggle)
        button_layout.addWidget(self.clipboard_monitor_toggle)

        layout.addLayout(button_layout)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.send_to_ai_active = False
        self.output_to_cursor_active = False

    def apply_theme(self, theme_settings):
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme_settings['background_color']};
                color: {theme_settings['text_color']};
            }}
            QTextEdit {{
                background-color: {theme_settings['background_color']};
                border: 1px solid {theme_settings['accent_color']};
                border-radius: 5px;
            }}
            QPushButton {{
                background-color: {theme_settings['background_color']};
                color: {theme_settings['text_color']};
                border: 2px solid {theme_settings['accent_color']};
                border-radius: 5px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {theme_settings['accent_color']};
                color: {theme_settings['background_color']};
            }}
            QLabel {{
                color: {theme_settings['text_color']};
            }}
        """)

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

    def update_chat_history(self, chat_history):
        self.dictation_area.setPlainText(chat_history)
        self.output_text.setPlainText(chat_history)
        # Scroll to the bottom of both text areas
        self.dictation_area.verticalScrollBar().setValue(
            self.dictation_area.verticalScrollBar().maximum()
        )
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )

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

    def on_clipboard_monitor_toggle(self):
        self.clipboard_monitor_active = self.clipboard_monitor_toggle.isChecked()
        if self.clipboard_monitor_active:
            self.start_clipboard_monitoring.emit()
        else:
            self.stop_clipboard_monitoring.emit()

    def on_copy_to_clipboard(self):
        text = self.dictation_area.toPlainText().strip()
        if text:
            pyperclip.copy(text)

    def closeEvent(self, event):
        self.stop_listening.emit()
        event.accept()
