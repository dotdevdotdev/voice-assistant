from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import pyperclip
import logging


class ClipboardListener(QObject):
    clipboard_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
        self.logger = logging.getLogger(__name__)
        self.last_text = ""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_clipboard)
        self.timer.start(100)  # Check every 100ms

    def check_clipboard(self):
        if self.running:
            try:
                text = pyperclip.paste()
                if text != self.last_text:
                    self.last_text = text
                    self.clipboard_changed.emit(text)
            except Exception as e:
                self.logger.error(f"Error reading clipboard: {e}")

    def stop(self):
        self.running = False
        self.timer.stop()
