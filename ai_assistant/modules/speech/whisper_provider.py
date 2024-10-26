import whisper  # This will now correctly import openai-whisper
from typing import AsyncIterator, Optional
import numpy as np
from core.interfaces.speech import SpeechToTextProvider
from core.events import EventBus, Event, EventType


class WhisperProvider(SpeechToTextProvider):
    def __init__(self, model_name: str = "base"):
        self.model = whisper.load_model(model_name)
        self._event_bus = EventBus.get_instance()
        self._buffer = bytearray()
        self._min_audio_len = 750  # minimum ms of audio before processing

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        async for chunk in audio_stream:
            self._buffer.extend(chunk)

            # Convert buffer to float32 numpy array
            audio_data = np.frombuffer(self._buffer, dtype=np.float32)

            # Process if we have enough audio data
            if len(audio_data) >= self.model.dims.n_audio_ctx:
                result = self.model.transcribe(audio_data)
                if result["text"].strip():
                    yield result["text"]
                # Keep a small overlap for context
                overlap = int(0.5 * self.model.dims.n_audio_ctx)
                self._buffer = self._buffer[-overlap:]

    async def transcribe_file(self, audio_file: bytes) -> str:
        # Convert bytes to numpy array
        audio_data = np.frombuffer(audio_file, dtype=np.float32)
        result = self.model.transcribe(audio_data)
        return result["text"]
