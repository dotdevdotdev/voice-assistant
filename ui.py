from PyQt6.QtWidgets import QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget
from PyQt6.QtCore import pyqtSignal


class MainWindow(QMainWindow):
    start_listening = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.start_button = QPushButton("Start Listening")
        self.start_button.clicked.connect(self.on_start_button_clicked)
        layout.addWidget(self.start_button)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def on_start_button_clicked(self):
        self.start_listening.emit()

    def update_output(self, text):
        self.output_text.append(text)
