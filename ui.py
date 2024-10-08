from PyQt6.QtWidgets import (
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal


class MainWindow(QMainWindow):
    start_listening = pyqtSignal()
    stop_listening = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.status_label = QLabel("Listening...")
        layout.addWidget(self.status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def update_output(self, text):
        self.output_text.append(text)

    def closeEvent(self, event):
        self.stop_listening.emit()
        event.accept()
