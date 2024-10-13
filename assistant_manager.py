from PyQt5.QtCore import QObject, pyqtSignal, QMetaObject, Qt, Q_ARG
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
        self.logger = logging.getLogger(__name__)
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
        self.logger.debug(f"Initial chat history: {initial_history}")
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
        self.logger.info(f"Send to AI active: {active}")
        if active:
            self.start_voice_listening()
        else:
            self.stop_voice_listening()

    def emit_voice_input(self, voice_input):
        self.voice_input_received.emit(voice_input)

    def start_voice_listening(self):
        if not self.voice_listening_active:
            self.voice_listening_active = True
            self.voice_thread = threading.Thread(target=self.voice_listening_loop)
            self.voice_thread.daemon = True  # Set the thread as daemon
            self.voice_thread.start()
            self.logger.info("Voice listening thread started")

    def stop_voice_listening(self):
        if self.voice_listening_active:
            self.voice_listening_active = False
            if self.voice_thread and self.voice_thread.is_alive():
                self.voice_thread.join(timeout=5)
            self.voice_thread = None
            self.logger.info("Voice listening stopped")

    def voice_listening_loop(self):
        while self.voice_listening_active:
            try:
                voice_input = self.assistant.listen()
                if voice_input:
                    self.process_user_input(voice_input)
            except Exception as e:
                self.logger.error(f"Error in voice listening: {e}")
            time.sleep(0.1)  # Small delay to prevent tight looping

    def set_output_to_cursor_active(self, active):
        self.output_to_cursor_active = active
        self.logger.info(f"Output to cursor active: {active}")

    def process_user_input(self, user_input):
        self.chat_history.add_entry("User", user_input)
        self.update_chat_history.emit(self.chat_history.get_history())
        self.last_processed_input = user_input

        if self.output_to_cursor_active:
            self.write_to_cursor.emit(user_input)

        if self.send_to_ai_active:
            self.logger.info("Sending to AI")
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
            self.logger.info("Not sending to AI (inactive)")

    def process_clipboard_content(self, content):
        self.logger.info(f"Processing clipboard content: {content}")
        if self.monitor_clipboard:
            self.logger.info("Clipboard monitoring is active")
            self.chat_history.add_entry("Clipboard", content)
            self.update_chat_history.emit(self.chat_history.get_history())
            self.assistant.speak(content)
        else:
            self.logger.info("Clipboard monitoring is not active")

    def set_monitor_clipboard_active(self, active):
        self.monitor_clipboard = active
        if active:
            self.clipboard_thread.start()
        else:
            self.clipboard_thread.stop()
