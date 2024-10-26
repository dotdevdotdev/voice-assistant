from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import threading
import time
import logging
import os
from typing import Dict, Optional
from clipboard_listener import ClipboardListener
from clipboard_thread import ClipboardThread
from assistant import Assistant
from event_bus import EventBus


class VAManager(QObject):
    """Manages multiple virtual assistants and their interactions"""

    assistant_error = pyqtSignal(str, str)  # (error_msg, va_name)
    assistant_status_changed = pyqtSignal(str, bool)  # (va_name, is_active)

    def __init__(self, chat_window, va_configs):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.chat_window = chat_window
        self.va_configs = va_configs
        self.event_bus = EventBus.get_instance()

        # Core state
        self.active_assistants: Dict[str, Assistant] = {}

        # Global feature flags
        self.global_ai_active = False
        self.global_clipboard_active = False

        # Initialize global components
        self.clipboard_listener = ClipboardListener()
        self.clipboard_thread = ClipboardThread(self.clipboard_listener)
        self.clipboard_listener.clipboard_changed.connect(
            self.process_clipboard_content
        )

        # Connect signals
        self._connect_signals()

    def _connect_signals(self):
        """Connect all signals"""
        # Chat window signals
        self.chat_window.send_ai_toggled.connect(self.set_global_ai_active)
        self.chat_window.monitor_clipboard_toggled.connect(
            self.set_global_clipboard_active
        )
        self.chat_window.send_message.connect(self.process_user_input)

        # Event bus signals
        self.event_bus.audio_transcription.connect(self.process_transcription)
        self.event_bus.ai_state_changed.connect(self.set_global_ai_active)

    def request_add_assistant(self, va_name: str) -> bool:
        # First checks if "andrea" exists in va_configs
        if va_name not in self.va_configs:
            self.logger.error(f"No configuration found for assistant: {va_name}")
            return False

        # Then checks if "andrea" is already active
        if va_name in self.active_assistants:
            self.logger.warning(f"Assistant {va_name} is already active in chat")
            return False

        # If checks pass, calls add_assistant("andrea")
        try:
            success = self.add_assistant(va_name)
            if success:
                # Emits signal to notify UI that andrea is now active
                self.assistant_status_changed.emit(va_name, True)
            return success
        except Exception as e:
            self.logger.error(f"Failed to add assistant {va_name}: {e}")
            self.assistant_error.emit(str(e), va_name)
            return False

    def add_assistant(self, va_name: str) -> bool:
        """Add a new assistant"""
        try:
            if va_name in self.active_assistants:
                return True

            # Get config for this VA
            config = self.va_configs.get(va_name, {})

            # Create new assistant
            assistant = Assistant(
                name=va_name,
                voice_id=config.get("elevenlabs", {}).get("voice_id"),
                stability=config.get("elevenlabs", {})
                .get("voice_settings", {})
                .get("stability"),
                similarity_boost=config.get("elevenlabs", {})
                .get("voice_settings", {})
                .get("similarity_boost"),
            )

            # Configure the assistant
            assistant.configure(config)

            # Add to active assistants
            self.active_assistants[va_name] = assistant
            self.assistant_status_changed.emit(va_name, True)
            return True

        except Exception as e:
            self.logger.error(f"Error adding assistant {va_name}: {e}")
            self.assistant_error.emit(str(e), va_name)
            return False

    def remove_assistant(self, va_name: str):
        """Remove an assistant"""
        if va_name in self.active_assistants:
            try:
                # Cleanup assistant resources if needed
                assistant = self.active_assistants[va_name]
                del self.active_assistants[va_name]
                self.assistant_status_changed.emit(va_name, False)
            except Exception as e:
                self.logger.error(f"Error removing assistant {va_name}: {e}")
                self.assistant_error.emit(str(e), va_name)

    def process_user_input(self, user_input: str):
        """Process user input for all active assistants"""
        if not user_input.strip():
            return

        # Display user message
        self.chat_window.display_message(user_input, role="user")

        # Process with each active assistant if AI is enabled
        if self.global_ai_active:
            for va_name, assistant in self.active_assistants.items():
                self.process_with_assistant(user_input, va_name, assistant)

    def process_with_assistant(
        self, user_input: str, va_name: str, assistant: Assistant
    ):
        """Process input with a specific assistant"""
        try:
            response_text, audio = assistant.process(user_input)
            self.chat_window.display_message(
                response_text, role="assistant", va_name=va_name
            )

            if audio:
                audio.export(f"response_{va_name}.mp3", format="mp3")

        except Exception as e:
            self.logger.error(f"Error processing with {va_name}: {e}")
            self.assistant_error.emit(str(e), va_name)

    @pyqtSlot(str)
    def process_clipboard_content(self, content: str):
        """Process clipboard content with all active assistants"""
        if self.global_clipboard_active:
            self.chat_window.display_message(content, role="clipboard")
            for assistant in self.active_assistants.values():
                try:
                    assistant.speak(content)
                except Exception as e:
                    self.logger.error(f"Error processing clipboard: {e}")

    @pyqtSlot(str, str)
    def handle_assistant_error(self, error_msg: str, va_name: str):
        """Handle errors from assistants"""
        self.logger.error(f"Assistant {va_name} error: {error_msg}")
        # Attempt to restart the assistant or remove if necessary
        if va_name in self.active_assistants:
            try:
                self.remove_assistant(va_name)
                self.add_assistant(va_name)  # Attempt to restart
            except Exception as e:
                self.logger.error(f"Could not restart assistant {va_name}: {e}")

    def set_global_ai_active(self, active: bool):
        """Toggle global AI processing"""
        self.global_ai_active = active

    def set_global_clipboard_active(self, active: bool):
        """Toggle global clipboard monitoring"""
        self.global_clipboard_active = active
        if active:
            self.clipboard_thread.start()
        else:
            self.clipboard_thread.stop()

    def cleanup(self):
        """Cleanup all assistants and resources"""
        for va_name in list(self.active_assistants.keys()):
            self.remove_assistant(va_name)
        self.clipboard_thread.stop()

    @pyqtSlot(str)
    def process_transcription(self, text: str):
        """Process transcribed text from AudioManager"""
        if self.global_ai_active:
            for va_name, assistant in self.active_assistants.items():
                self.process_with_assistant(text, va_name, assistant)

    def handle_transcription(self, text):
        """Determine if text needs assistant processing"""
        if self._is_command(text):
            # Process with assistants
            self.process_with_assistants(text)
        else:
            # Just add to chat
            self.add_dictation_to_chat(text)
