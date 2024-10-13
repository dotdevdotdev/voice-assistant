from PyQt5.QtCore import QThread


class ClipboardThread(QThread):
    def __init__(self, clipboard_listener):
        super().__init__()
        self.clipboard_listener = clipboard_listener

    def run(self):
        while self.clipboard_listener.running:
            QThread.msleep(100)

    def stop(self):
        self.clipboard_listener.stop()
        self.wait()
