import pyaudio
import wave
from io import BytesIO
from typing import Optional
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider, AudioConfig
from core.events import EventBus, Event, EventType


class PyAudioProvider(AudioInputProvider, AudioOutputProvider):
    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._stream: Optional[pyaudio.Stream] = None
        self._config: Optional[AudioConfig] = None
        self._event_bus = EventBus.get_instance()
        self._playback_stream: Optional[pyaudio.Stream] = None
        self._buffer_size = None

    def start_stream(self, config: AudioConfig) -> None:
        if self._stream is not None:
            self.stop_stream()

        print(f"Starting audio stream with config: {config}")

        # Use larger chunk size for the actual stream
        self._buffer_size = config.chunk_size * 4
        self._config = config

        print(f"Using buffer size: {self._buffer_size}")

        try:
            self._stream = self._audio.open(
                format=pyaudio.paFloat32,
                channels=config.channels,
                rate=config.sample_rate,
                input=True,
                input_device_index=config.device_id,
                frames_per_buffer=self._buffer_size,
                stream_callback=None,  # Ensure blocking mode
            )
            print("Audio stream opened successfully")
        except Exception as e:
            print(f"Error opening audio stream: {e}")
            raise

    def read_chunk(self) -> bytes:
        if not self._stream:
            raise RuntimeError("Audio stream not started")
        try:
            data = self._stream.read(self._buffer_size, exception_on_overflow=False)
            return data
        except Exception as e:
            print(f"Error reading audio chunk: {e}")
            raise

    def stop_stream(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

    def get_devices(self) -> list[dict]:
        devices = []
        for i in range(self._audio.get_device_count()):
            device_info = self._audio.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:  # Only input devices
                devices.append(
                    {
                        "id": i,
                        "name": device_info["name"],
                        "channels": device_info["maxInputChannels"],
                        "sample_rate": int(device_info["defaultSampleRate"]),
                    }
                )
        return devices

    def play_audio(self, audio_data: BytesIO) -> None:
        if self._playback_stream is not None:
            self.stop_playback()

        # Convert audio data to wave
        with wave.Wave_read(audio_data) as wf:
            self._playback_stream = self._audio.open(
                format=self._audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
            )

            # Read data in chunks
            chunk_size = 1024
            data = wf.readframes(chunk_size)
            while data:
                self._playback_stream.write(data)
                data = wf.readframes(chunk_size)

    def stop_playback(self) -> None:
        if self._playback_stream:
            self._playback_stream.stop_stream()
            self._playback_stream.close()
            self._playback_stream = None

    def __del__(self):
        self.stop_stream()
        self.stop_playback()
        self._audio.terminate()
