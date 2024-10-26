from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
import pyaudio
import wave
import threading
import logging
from deepgram import DeepgramClient
from event_bus import EventBus
from pydub import AudioSegment
import io
import time
from utils import find_input_device_index, find_output_device_index
import os
from threading import Lock


class AudioManager(QObject):
    """Manages audio capture and transcription"""

    error_occurred = pyqtSignal(str)

    def __init__(self):
        try:
            super().__init__()
            self.logger = logging.getLogger(__name__)
            self.logger.info("Initializing AudioManager")

            # Thread safety
            self._lock = Lock()
            self._state_lock = Lock()

            # Get EventBus instance with error handling
            try:
                self.event_bus = EventBus.get_instance()
                self.logger.debug("Got EventBus instance")
            except Exception as e:
                self.logger.error("Failed to get EventBus instance")
                raise RuntimeError("EventBus initialization failed") from e

            # Initialize state variables first
            self._initialize_state()

            # Initialize PyAudio with error handling
            try:
                self.audio = pyaudio.PyAudio()
                self.logger.debug("PyAudio initialized")
            except Exception as e:
                self.logger.error("Failed to initialize PyAudio")
                raise RuntimeError("PyAudio initialization failed") from e

            # Set up audio configuration
            self._initialize_audio_config()

            # Initialize Deepgram with validation
            self._initialize_deepgram()

            # Connect signals with error handling
            self._connect_signals()

            self.logger.info("AudioManager initialization complete")

        except Exception as e:
            self.logger.error(f"Failed to initialize AudioManager: {e}", exc_info=True)
            self.cleanup()
            raise

    def _initialize_state(self):
        """Initialize state variables with thread safety"""
        with self._state_lock:
            self.is_listening = False
            self.is_playing = False
            self.stream = None
            self.listening_thread = None
        self.logger.debug("State initialized")

    def _initialize_audio_config(self):
        """Initialize audio configuration with device validation"""
        try:
            # Basic audio configuration with fallback rates
            self.chunk = 1024
            self.format = pyaudio.paFloat32
            self.channels = 1

            # List of sample rates to try, in order of preference
            sample_rates = [16000, 44100, 48000, 8000]
            self.rate = None

            # Find and validate devices
            self.input_device_index = find_input_device_index(self.audio)
            if self.input_device_index is None:
                self.logger.error("No valid input device found")
                raise RuntimeError("No valid input device available")

            # Test sample rates on the selected device
            device_info = self.audio.get_device_info_by_index(self.input_device_index)
            self.logger.debug(f"Testing device: {device_info['name']}")

            for rate in sample_rates:
                try:
                    # Test if the rate is supported
                    test_stream = self.audio.open(
                        format=self.format,
                        channels=self.channels,
                        rate=rate,
                        input=True,
                        input_device_index=self.input_device_index,
                        frames_per_buffer=self.chunk,
                        start=False,
                    )
                    test_stream.close()
                    self.rate = rate
                    self.logger.info(f"Using sample rate: {rate}Hz")
                    break
                except Exception as e:
                    self.logger.debug(f"Sample rate {rate}Hz not supported: {e}")
                    continue

            if self.rate is None:
                raise RuntimeError("No supported sample rate found")

            # Find output device
            self.output_device_index = find_output_device_index(self.audio)
            if self.output_device_index is None:
                self.logger.warning("No preferred output device found, using default")

            self.logger.debug(
                f"Audio config initialized with input device {self.input_device_index} "
                f"at {self.rate}Hz"
            )

        except Exception as e:
            self.logger.error("Failed to initialize audio configuration")
            raise RuntimeError("Audio configuration failed") from e

    def _initialize_deepgram(self):
        """Initialize Deepgram client with API key validation"""
        try:
            api_key = os.getenv("DEEPGRAM_API_KEY")
            if not api_key:
                raise ValueError("DEEPGRAM_API_KEY not found in environment")

            self.deepgram = DeepgramClient(api_key)
            self.logger.debug("Deepgram client initialized")

        except Exception as e:
            self.logger.error("Failed to initialize Deepgram client")
            raise RuntimeError("Deepgram initialization failed") from e

    def _connect_signals(self):
        """Connect event signals with error handling"""
        try:
            self.event_bus.audio_state_changed.connect(self.set_listening_state)
            self.logger.debug("Signals connected")
        except Exception as e:
            self.logger.error("Failed to connect signals")
            raise RuntimeError("Signal connection failed") from e

    def _listening_loop(self):
        """Audio capture and transcription loop with error handling"""
        self.logger.debug("Starting listening loop")

        while self.is_listening:
            if self.is_playing:
                time.sleep(0.1)
                continue

            try:
                with self._lock:
                    if not self.stream or not self.is_listening:
                        break

                    frames = []
                    silence_threshold = 0.01
                    silence_frames = 0
                    max_silence_frames = int(self.rate / self.chunk * 1)

                    while self.is_listening and not self.is_playing:
                        try:
                            data = self.stream.read(
                                self.chunk, exception_on_overflow=False
                            )
                            frames.append(data)

                            if max(abs(float(b)) for b in data) < silence_threshold:
                                silence_frames += 1
                            else:
                                silence_frames = 0

                            if silence_frames >= max_silence_frames and frames:
                                self._process_audio_frames(frames)
                                frames = []
                                silence_frames = 0

                        except IOError as e:
                            self.logger.error(f"IO Error in audio capture: {e}")
                            break

            except Exception as e:
                self.logger.error(f"Error in listening loop: {e}", exc_info=True)
                self.error_occurred.emit(f"Audio capture error: {str(e)}")
                break

        self.logger.debug("Listening loop ended")

    def _process_audio_frames(self, frames):
        """Process captured audio frames with error handling"""
        try:
            audio_data = b"".join(frames)

            payload = {"buffer": audio_data}
            options = {
                "smart_format": True,
                "model": "nova-2",
                "language": "en-US",
            }

            response = self.deepgram.listen.rest.v("1").transcribe_file(
                payload, options
            )
            transcript = response.to_json()["results"]["channels"][0]["alternatives"][
                0
            ]["transcript"]

            if transcript.strip():
                self.logger.debug(f"Emitting transcription: {transcript}")
                self.event_bus.audio_transcription.emit(transcript)

        except Exception as e:
            self.logger.error(f"Error processing audio: {e}", exc_info=True)
            self.error_occurred.emit(f"Audio processing error: {str(e)}")

    @pyqtSlot(bool)
    def set_listening_state(self, should_listen: bool):
        """Handle requests to change listening state with thread safety"""
        with self._state_lock:
            if should_listen:
                self.start_listening()
            else:
                self.stop_listening()

    def start_listening(self):
        """Start audio capture with error handling"""
        with self._state_lock:
            if self.is_listening:
                return

            try:
                self.stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=self.input_device_index,
                    frames_per_buffer=self.chunk,
                )

                self.is_listening = True
                self.listening_thread = threading.Thread(
                    target=self._listening_loop, daemon=True
                )
                self.listening_thread.start()

                self.event_bus.audio_state_changed.emit(True)
                self.logger.info("Audio capture started")

            except Exception as e:
                self.logger.error(f"Failed to start audio capture: {e}")
                self.error_occurred.emit(str(e))
                self.is_listening = False
                if self.stream:
                    self.stream.close()
                    self.stream = None

    def stop_listening(self):
        """Stop audio capture with thread safety"""
        with self._state_lock:
            if not self.is_listening:
                return

            self.is_listening = False
            self.event_bus.audio_state_changed.emit(False)

            if self.stream:
                try:
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = None
                except Exception as e:
                    self.logger.error(f"Error closing audio stream: {e}")

            if self.listening_thread:
                self.listening_thread.join(timeout=1)
                self.listening_thread = None

    def cleanup(self):
        """Cleanup resources with error handling"""
        self.logger.info("Cleaning up AudioManager resources")
        try:
            self.stop_listening()
            if self.audio:
                self.audio.terminate()
                self.audio = None
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def play_audio(self, audio_segment):
        """Play audio data with error handling and thread safety"""
        with self._state_lock:
            if self.is_playing:
                self.logger.debug("Already playing audio, skipping")
                return False

            try:
                self.logger.debug("Starting audio playback")
                self.is_playing = True

                raw_data = audio_segment.raw_data

                out_stream = self.audio.open(
                    format=self.audio.get_format_from_width(audio_segment.sample_width),
                    channels=audio_segment.channels,
                    rate=audio_segment.frame_rate,
                    output=True,
                    output_device_index=self.output_device_index,
                )

                chunk_size = 1024
                offset = 0
                while offset < len(raw_data):
                    if not self.is_playing:
                        break
                    chunk = raw_data[offset : offset + chunk_size]
                    out_stream.write(chunk)
                    offset += chunk_size

                out_stream.stop_stream()
                out_stream.close()
                return True

            except Exception as e:
                self.logger.error(f"Error playing audio: {e}", exc_info=True)
                self.error_occurred.emit(f"Audio playback error: {str(e)}")
                return False
            finally:
                self.is_playing = False
                self.logger.debug("Audio playback complete")
