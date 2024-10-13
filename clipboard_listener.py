from PyQt5.QtCore import QObject, pyqtSignal, QTimer
import pyperclip


class ClipboardListener(QObject):
    clipboard_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True
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
                print(f"Error reading clipboard: {e}")

    def stop(self):
        self.running = False
        self.timer.stop()
