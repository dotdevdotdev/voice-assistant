import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from ui import MainWindow
from assistant import Assistant


class AssistantThread(QThread):
    output = pyqtSignal(str)

    def __init__(self, assistant):
        super().__init__()
        self.assistant = assistant

    def run(self):
        user_input = self.assistant.listen()
        self.output.emit(f"You said: {user_input}")

        response = self.assistant.process(user_input)
        self.output.emit(f"Assistant: {response}")

        self.assistant.speak(response)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    assistant = Assistant(openai_api_key)
    thread = AssistantThread(assistant)

    thread.output.connect(window.update_output)
    window.start_listening.connect(thread.start)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
