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
        self.running = True

    def run(self):
        while self.running:
            user_input = self.assistant.listen()
            if user_input and user_input != "Sorry, I couldn't understand that.":
                self.output.emit(f"You said: {user_input}")

                response = self.assistant.process(user_input)
                self.output.emit(f"Assistant: {response}")

                self.assistant.speak(response)

    def stop(self):
        self.running = False


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "default")

    if not openai_api_key or not elevenlabs_api_key:
        print(
            "Error: Missing API keys. Please set OPENAI_API_KEY and ELEVENLABS_API_KEY environment variables."
        )
        sys.exit(1)

    if voice_id == "default":
        print("Warning: ELEVENLABS_VOICE_ID not set. Using default voice.")

    assistant = Assistant(openai_api_key, elevenlabs_api_key, voice_id)
    thread = AssistantThread(assistant)

    thread.output.connect(window.update_output)
    window.start_listening.connect(thread.start)
    window.stop_listening.connect(thread.stop)

    thread.start()  # Start the thread immediately

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
