from typing import AsyncIterator, Optional, List
import os
import asyncio
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)
from core.interfaces.speech import SpeechToTextProvider
from core.events import EventBus, Event, EventType


class DeepgramProvider(SpeechToTextProvider):
    def __init__(self, api_key: Optional[str] = None):
        print("\n=== Initializing Deepgram Provider ===")
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key not provided")

        self.client = DeepgramClient(self.api_key)
        self._event_bus = EventBus.get_instance()
        self._config = None
        self._connection = None
        self._transcription_queue = asyncio.Queue()
        self._running = False

    def configure(self, config: dict):
        """Configure the provider with settings"""
        self._config = config
        print(f"Configured Deepgram with: {config}")

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        print("\n>>> Starting Deepgram transcription stream")
        try:
            self._running = True
            options = {
                "model": "nova-2",
                "smart_format": True,
                "language": "en",
                "encoding": "linear16",
                "channels": 1,
                "sample_rate": 16000,
            }

            if self._config:
                options.update(self._config)
                print(f"Using configured sample rate: {options['sample_rate']}")

            print(f"Using Deepgram options: {options}")

            # Create live transcription connection
            dg_connection = self.client.listen.live.v("1")
            print(">>> Created Deepgram connection")

            # Define handlers before starting connection
            async def handle_transcript(data):
                try:
                    if not self._running:
                        return

                    if hasattr(data, "channel") and hasattr(
                        data.channel, "alternatives"
                    ):
                        transcript = data.channel.alternatives[0].transcript
                        if transcript and transcript.strip():
                            print(f">>> Deepgram transcription: '{transcript}'")
                            self._transcription_queue.put_nowait(transcript)
                except Exception as e:
                    print(f"!!! Error handling transcript: {e}")
                    print(f"Raw transcript data: {data}")

            async def handle_error(error):
                print(f"!!! Deepgram error: {error}")
                if self._running:
                    self._transcription_queue.put_nowait(None)  # Signal error

            async def handle_close():
                print(">>> Deepgram connection closed")
                self._running = False

            # Register event handlers
            dg_connection.on(LiveTranscriptionEvents.TRANSCRIPT, handle_transcript)
            dg_connection.on(LiveTranscriptionEvents.ERROR, handle_error)
            dg_connection.on(LiveTranscriptionEvents.CLOSE, handle_close)

            # Start the connection with options
            connection = await dg_connection.start(options)
            print(">>> Started Deepgram connection with options")

            # Process audio chunks and yield transcriptions
            try:
                async for chunk in audio_stream:
                    if not self._running:
                        break

                    if connection and connection.is_connected():
                        await connection.send(chunk)
                        try:
                            text = await asyncio.wait_for(
                                self._transcription_queue.get(), timeout=0.1
                            )
                            if text is not None:  # None signals an error
                                yield text
                        except asyncio.TimeoutError:
                            continue
                    else:
                        print("!!! Deepgram connection not ready")
                        break

            except Exception as e:
                print(f"!!! Error in audio processing loop: {e}")
            finally:
                self._running = False
                if connection and connection.is_connected():
                    try:
                        await connection.finish()
                    except Exception as e:
                        print(f"!!! Error closing connection: {e}")

        except Exception as e:
            print(f"!!! Error in Deepgram transcription: {e}")
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
        finally:
            self._running = False
            # Clear the queue
            while not self._transcription_queue.empty():
                try:
                    self._transcription_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

    async def transcribe_file(self, audio_file: bytes) -> str:
        print("\n>>> Starting Deepgram file transcription")
        try:
            # Create options for file transcription
            options = {
                "model": "nova-2",
                "smart_format": True,
                "language": "en",
            }

            if self._config:
                options.update(self._config)

            # Use the PrerecordedOptions for file transcription
            response = await self.client.transcription.prerecorded.v("1").transcribe(
                {"buffer": audio_file}, options
            )

            text = response["results"]["channels"][0]["alternatives"][0]["transcript"]
            print(f">>> Transcribed text: '{text}'")
            return text

        except Exception as e:
            print(f"!!! Error in file transcription: {e}")
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    def __del__(self):
        """Cleanup when the provider is destroyed"""
        self._running = False
