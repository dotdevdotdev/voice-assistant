from PyQt6.QtCore import QThread, QTimer


class ClipboardThread(QThread):
    def __init__(self, clipboard_listener):
        super().__init__()
        self.clipboard_listener = clipboard_listener
        self.running = False

    def run(self):
        self.running = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.clipboard_listener.check_clipboard)
        self.timer.start(1000)  # Check every second
        self.exec()  # Start Qt event loop

    def stop(self):
        self.running = False
        self.timer.stop()
        self.quit()
        self.wait()
