from typing import AsyncIterator, Optional
import os
from deepgram import DeepgramClient, DeepgramClientOptions
from core.interfaces.speech import SpeechToTextProvider
from core.events import EventBus, Event, EventType


class DeepgramProvider(SpeechToTextProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key not provided")

        options = DeepgramClientOptions(api_key=self.api_key)
        self.client = DeepgramClient(options)
        self._event_bus = EventBus.get_instance()

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        try:
            # Create live transcription socket
            socket = await self.client.transcription.live(
                {"smart_format": True, "model": "nova", "language": "en-US"}
            )

            # Handle incoming transcripts
            @socket.on(socket.EVENT_TRANSCRIPT)
            async def handle_transcript(transcript):
                if transcript.is_final:
                    text = transcript.channel.alternatives[0].transcript
                    if text.strip():
                        yield text

            # Send audio data
            async for chunk in audio_stream:
                if socket.is_ready():
                    await socket.send(chunk)
                else:
                    break

            # Close socket when done
            await socket.finish()

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    async def transcribe_file(self, audio_file: bytes) -> str:
        try:
            response = await self.client.transcription.prerecorded(
                {
                    "buffer": audio_file,
                },
                {"smart_format": True, "model": "nova", "language": "en-US"},
            )

            return response["results"]["channels"][0]["alternatives"][0]["transcript"]

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
