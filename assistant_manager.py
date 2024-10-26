from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt
import threading
import time
import logging
from clipboard_listener import ClipboardListener
from clipboard_thread import ClipboardThread


class AssistantManager(QObject):
    update_chat_history = pyqtSignal(str)
    write_to_cursor = pyqtSignal(str)
    voice_input_received = pyqtSignal(str)

    def __init__(
        self, assistant=None, va_name=None, username=None, elevenlabs_api_key=None
    ):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.elevenlabs_api_key = elevenlabs_api_key
        self.assistants = {}

        # Initialize manager-specific attributes
        self.assistant = assistant
        self.va_name = va_name
        self.username = username
        self.send_to_ai_active = True
        self.output_to_cursor_active = False
        self.monitor_clipboard = False
        self.chat_window = None
        print(f"AssistantManager initialized for {va_name}")  # Debug print

        # Initialize other components as needed
        self.clipboard_listener = ClipboardListener()
        self.clipboard_thread = ClipboardThread(self.clipboard_listener)
        self.clipboard_listener.clipboard_changed.connect(
            self.process_clipboard_content
        )
        self.voice_listening_active = False
        self.voice_thread = None

    def create_assistant(
        self, name, voice_id=None, stability=None, similarity_boost=None
    ):
        try:
            # Create assistant without passing the API key
            assistant = Assistant(
                name=name,
                voice_id=voice_id,
                stability=stability,
                similarity_boost=similarity_boost,
            )
            self.assistants[name] = assistant
            return assistant
        except Exception as e:
            logging.error(f"Failed to create assistant manager for {name}: {str(e)}")
            raise

    def set_chat_window(self, chat_window):
        print(f"Setting chat window for {self.va_name}")  # Debug print
        self.chat_window = chat_window

        try:
            # Connect signals
            self.chat_window.output_to_cursor_toggled.connect(
                self.set_output_to_cursor_active
            )
            self.chat_window.send_ai_toggled.connect(self.set_send_to_ai_active)
            self.chat_window.monitor_clipboard_toggled.connect(
                self.set_monitor_clipboard_active
            )
            self.chat_window.send_message.connect(self.process_user_input)
            self.voice_input_received.connect(self.process_user_input)
            print("Chat window signals connected successfully")  # Debug print
        except Exception as e:
            print(f"Error connecting signals: {e}")

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
            self.voice_thread.daemon = True
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
            time.sleep(0.1)

    def set_output_to_cursor_active(self, active):
        self.output_to_cursor_active = active
        self.logger.info(f"Output to cursor active: {active}")

    def process_user_input(self, user_input):
        print(f"AssistantManager: Processing user input: {user_input}")
        if not user_input.strip():
            return

        if self.chat_window is None:
            print("AssistantManager: Error - chat_window is None!")
            return

        try:
            # Always display user message
            print("AssistantManager: Attempting to display user message")
            self.chat_window.display_message(user_input, role="user")
            print("AssistantManager: Successfully displayed user message")

            # Only process with AI if enabled
            if self.send_to_ai_active:
                print("AssistantManager: AI is active, processing with assistant")
                try:
                    response_text, audio = self.assistant.process(user_input)
                    print(f"AssistantManager: Got response: {response_text}")

                    # Display AI response
                    self.chat_window.display_message(
                        response_text, role="assistant", va_name=self.va_name
                    )

                    # Handle audio if present
                    if audio:
                        audio.export("response.mp3", format="mp3")

                except Exception as e:
                    print(f"AssistantManager: Error processing with AI: {e}")
                    error_msg = "Sorry, I encountered an error processing your message."
                    self.chat_window.display_message(
                        error_msg, role="assistant", va_name=self.va_name
                    )
        except Exception as e:
            print(f"AssistantManager: Error in process_user_input: {e}")

    def process_clipboard_content(self, content):
        self.logger.info(f"Processing clipboard content: {content}")
        if self.monitor_clipboard:
            self.logger.info("Clipboard monitoring is active")
            self.chat_window.display_message(
                content, role="clipboard"
            )  # Updated method name
            self.assistant.speak(content)
        else:
            self.logger.info("Clipboard monitoring is not active")

    def set_monitor_clipboard_active(self, active):
        self.monitor_clipboard = active
        if active:
            self.clipboard_thread.start()
        else:
            self.clipboard_thread.stop()
