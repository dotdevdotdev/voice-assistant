import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from ui import MainWindow
from assistant import Assistant
import pyperclip
import pyautogui


class AssistantThread(QThread):
    output = pyqtSignal(str)
    update_dictation = pyqtSignal(str)

    def __init__(self, assistant, window):
        super().__init__()
        self.assistant = assistant
        self.window = window
        self.running = True

    def run(self):
        while self.running:
            user_input = self.assistant.listen()
            if user_input and user_input != "Sorry, I couldn't understand that.":
                self.output.emit(f"You said: {user_input}")
                self.update_dictation.emit(user_input)

    def stop(self):
        self.running = False


def main():
    app = QApplication(sys.argv)
    window = MainWindow()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID")

    assistant = Assistant(openai_api_key, elevenlabs_api_key, voice_id)
    assistant_thread = AssistantThread(assistant, window)

    assistant_thread.output.connect(window.update_output)
    assistant_thread.update_dictation.connect(window.update_dictation)

    def process_and_speak_ai_response(text):
        if window.send_to_ai_active:
            response = assistant.process(text)
            window.update_output(f"AI: {response}")
            assistant.speak(response)

    window.send_to_ai.connect(process_and_speak_ai_response)
    window.stop_listening.connect(assistant_thread.stop)

    window.show()
    assistant_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
