from PyQt5.QtCore import QObject, pyqtSignal
import threading
import time
import logging
from chat_history import AIChatHistory
from clipboard_listener import ClipboardListener
from clipboard_thread import ClipboardThread


class AssistantManager(QObject):
    update_chat_history = pyqtSignal(str)
    write_to_cursor = pyqtSignal(str)
    voice_input_received = pyqtSignal(str)

    def __init__(self, assistant, log_file_path, va_name, username):
        super().__init__()
        self.assistant = assistant
        self.send_to_ai_active = True
        self.output_to_cursor_active = False
        self.last_processed_input = ""
        self.last_processed_response = ""
        self.monitor_clipboard = False
        self.chat_history = AIChatHistory(log_file_path, va_name, username)
        self.clipboard_listener = ClipboardListener()
        self.clipboard_thread = ClipboardThread(self.clipboard_listener)
        self.clipboard_listener.clipboard_changed.connect(
            self.process_clipboard_content
        )
        self.voice_listening_active = False
        self.voice_thread = None

        # Emit the initial chat history
        initial_history = self.chat_history.get_history()
        logging.debug(f"Initial chat history: {initial_history}")
        self.update_chat_history.emit(initial_history)

    def set_chat_window(self, chat_window):
        self.chat_window = chat_window
        self.chat_window.output_to_cursor_toggled.connect(
            self.set_output_to_cursor_active
        )
        self.chat_window.send_ai_toggled.connect(self.set_send_to_ai_active)
        self.chat_window.monitor_clipboard_toggled.connect(
            self.set_monitor_clipboard_active
        )
        self.chat_window.send_message.connect(self.process_user_input)
        self.voice_input_received.connect(self.process_user_input)

    def set_send_to_ai_active(self, active):
        self.send_to_ai_active = active
        print(f"Send to AI active: {active}")  # Debug print
        if active:
            self.start_voice_listening()
        else:
            self.stop_voice_listening()

    def start_voice_listening(self):
        if not self.voice_listening_active:
            self.voice_listening_active = True
            self.voice_thread = threading.Thread(target=self.voice_listening_loop)
            self.voice_thread.daemon = True  # Set the thread as daemon
            self.voice_thread.start()
            print("Voice listening started")  # Debug print

    def stop_voice_listening(self):
        if self.voice_listening_active:
            self.voice_listening_active = False
            if self.voice_thread and self.voice_thread.is_alive():
                self.voice_thread.join(timeout=5)
            self.voice_thread = None
            print("Voice listening stopped")  # Debug print

    def voice_listening_loop(self):
        while self.voice_listening_active:
            try:
                voice_input = self.assistant.listen(timeout=10)
                if voice_input:
                    print(f"Voice input received: {voice_input}")
                    self.voice_input_received.emit(voice_input)
                else:
                    print("No voice input detected, continuing to listen...")
            except Exception as e:
                print(f"Error in voice listening: {e}")
            time.sleep(0.1)  # Small delay to prevent tight looping

    def set_output_to_cursor_active(self, active):
        self.output_to_cursor_active = active
        print(f"Output to cursor active: {active}")  # Debug print

    def process_user_input(self, user_input):
        print(f"Processing user input: {user_input}")  # Debug print
        self.chat_history.add_entry("User", user_input)
        self.update_chat_history.emit(self.chat_history.get_history())
        self.last_processed_input = user_input

        if self.output_to_cursor_active:
            self.write_to_cursor.emit(user_input)

        if self.send_to_ai_active:
            print("Sending to AI")  # Debug print
            # Only send the new user input to the AI
            response_text, sound = self.assistant.process(
                user_input, self.chat_history.history
            )
            self.chat_history.add_entry("Assistant", response_text)
            self.update_chat_history.emit(self.chat_history.get_history())

            if response_text:
                self.last_processed_response = response_text
                if sound:
                    self.assistant.play_audio(sound)
                else:
                    self.assistant.speak(response_text)
        else:
            print("Not sending to AI (inactive)")  # Debug print

    def process_clipboard_content(self, content):
        print(f"Processing clipboard content: {content}")  # Debug print
        if self.monitor_clipboard:
            print("Clipboard monitoring is active")  # Debug print
            self.chat_history.add_entry("Clipboard", content)
            self.update_chat_history.emit(self.chat_history.get_history())
            self.assistant.speak(content)
        else:
            print("Clipboard monitoring is not active")  # Debug print

    def set_monitor_clipboard_active(self, active):
        self.monitor_clipboard = active
        if active:
            self.clipboard_thread.start()
        else:
            self.clipboard_thread.stop()
