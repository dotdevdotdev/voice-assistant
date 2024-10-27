from typing import AsyncIterator, Optional
import os
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents
from core.interfaces.speech import SpeechToTextProvider
from core.events import EventBus, Event, EventType


class DeepgramProvider(SpeechToTextProvider):
    def __init__(self, api_key: Optional[str] = None):
        print("\n=== Initializing Deepgram Provider ===")
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key not provided")

        options = DeepgramClientOptions(api_key=self.api_key)
        self.client = DeepgramClient(options)
        self._event_bus = EventBus.get_instance()
        self._transcription_queue = None

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        print("\n>>> Starting Deepgram transcription stream")
        try:
            # Configure live transcription options
            options = {
                "smart_format": True,
                "model": "nova-2",
                "language": "en",
                "encoding": "linear16",  # For raw PCM audio
                "channels": 1,
                "sample_rate": 16000,
            }

            # Create live transcription connection
            connection = await self.client.transcription.live(options)
            print(">>> Deepgram connection established")

            @connection.on(LiveTranscriptionEvents.TRANSCRIPT)
            async def handle_transcript(transcript):
                if transcript.is_final:
                    text = transcript.channel.alternatives[0].transcript
                    if text.strip():
                        print(f">>> Deepgram transcription: '{text}'")
                        yield text

            @connection.on(LiveTranscriptionEvents.ERROR)
            async def handle_error(error):
                print(f"!!! Deepgram error: {error}")
                await self._event_bus.emit(
                    Event(EventType.ERROR, error=Exception(f"Deepgram error: {error}"))
                )

            # Process incoming audio chunks
            print(">>> Starting audio processing loop")
            async for chunk in audio_stream:
                if connection.is_ready():
                    try:
                        await connection.send(chunk)
                    except Exception as e:
                        print(f"!!! Error sending chunk to Deepgram: {e}")
                        break
                else:
                    print("!!! Deepgram connection not ready")
                    break

            # Clean up
            print(">>> Closing Deepgram connection")
            await connection.finish()

        except Exception as e:
            print(f"!!! Error in Deepgram transcription: {e}")
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    async def transcribe_file(self, audio_file: bytes) -> str:
        print("\n>>> Starting Deepgram file transcription")
        try:
            options = {
                "smart_format": True,
                "model": "nova-2",
                "language": "en",
            }

            response = await self.client.transcription.prerecorded(
                {"buffer": audio_file}, options
            )

            text = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            print(f">>> Transcribed text: '{text}'")
            return text

        except Exception as e:
            print(f"!!! Error in file transcription: {e}")
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
