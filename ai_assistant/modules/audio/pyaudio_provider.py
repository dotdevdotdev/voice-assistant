import pyaudio
import wave
from typing import Optional, BinaryIO
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider, AudioConfig
import io
import struct


class PyAudioProvider(AudioInputProvider, AudioOutputProvider):
    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._playback_stream = None
        self._config = None
        self._recorded_frames = []
        print(">>> PyAudio initialized")

    def start_stream(self, config: AudioConfig) -> None:
        """Start recording audio stream"""
        print("\n=== Starting audio stream ===")

        try:
            if self._stream is not None:
                self.stop_stream()

            # Get device info
            device_info = self._audio.get_device_info_by_index(config.device_id)
            sample_format = pyaudio.paInt16
            channels = 1
            fs = int(device_info["defaultSampleRate"])
            chunk = 1024

            print(f"Device: {device_info['name']}")
            print(f"Format: {sample_format}")
            print(f"Channels: {channels}")
            print(f"Rate: {fs}")
            print(f"Chunk: {chunk}")

            self._stream = self._audio.open(
                format=sample_format,
                channels=channels,
                rate=fs,
                frames_per_buffer=chunk,
                input=True,
                input_device_index=config.device_id,
            )

            self._config = {
                "format": sample_format,
                "channels": channels,
                "rate": fs,
                "chunk": chunk,
            }
            self._recorded_frames = []  # Clear any previous recording
            print(">>> Stream opened successfully")

        except Exception as e:
            print(f"!!! Error starting stream: {e}")
            if self._stream:
                self.stop_stream()
            raise

    def read_chunk(self) -> bytes:
        """Read a chunk of audio data"""
        if not self._stream:
            raise RuntimeError("Stream not started")

        try:
            data = self._stream.read(self._config["chunk"], exception_on_overflow=False)
            if data:  # Only append if we got data
                self._recorded_frames.append(data)
            return data
        except Exception as e:
            print(f"!!! Error reading chunk: {e}")
            raise

    def stop_stream(self) -> None:
        """Stop the audio stream"""
        print("\n=== Stopping audio stream ===")
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
                print(f">>> Recorded {len(self._recorded_frames)} frames")
            except Exception as e:
                print(f"!!! Error stopping stream: {e}")
            finally:
                self._stream = None
        print(">>> Stream stopped")

    def play_audio(self, audio_data: Optional[BinaryIO] = None) -> None:
        """Play recorded audio"""
        print("\n=== Playing recorded audio ===")

        if not self._recorded_frames:
            print("!!! No recorded audio to play")
            return

        try:
            print(f">>> Playing {len(self._recorded_frames)} frames")

            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(self._config["channels"])
                wf.setsampwidth(self._audio.get_sample_size(self._config["format"]))
                wf.setframerate(self._config["rate"])
                wf.writeframes(b"".join(self._recorded_frames))

            # Rewind buffer for reading
            wav_buffer.seek(0)

            # Create playback stream
            with wave.open(wav_buffer, "rb") as wf:
                print(f">>> WAV details:")
                print(f"    Channels: {wf.getnchannels()}")
                print(f"    Sample width: {wf.getsampwidth()}")
                print(f"    Frame rate: {wf.getframerate()}")
                print(f"    Frames: {wf.getnframes()}")

                self._playback_stream = self._audio.open(
                    format=self._audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=self._config.get("output_device_id"),
                )

                # Read data in chunks and play
                chunk = 1024
                data = wf.readframes(chunk)

                while len(data) > 0:
                    self._playback_stream.write(data)
                    data = wf.readframes(chunk)

                self.stop_playback()

            print(">>> Playback completed")

        except Exception as e:
            print(f"!!! Error during playback: {e}")
            print(f"!!! Traceback: {traceback.format_exc()}")
            self.stop_playback()
            raise

    def stop_playback(self) -> None:
        """Stop current audio playback"""
        if self._playback_stream:
            try:
                self._playback_stream.stop_stream()
                self._playback_stream.close()
            except Exception as e:
                print(f"!!! Error stopping playback: {e}")
            finally:
                self._playback_stream = None

    def save_recording(self, filename: str) -> None:
        """Save the recorded audio to a WAV file"""
        if not self._recorded_frames:
            print("!!! No recorded audio to save")
            return

        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self._config["channels"])
                wf.setsampwidth(self._audio.get_sample_size(self._config["format"]))
                wf.setframerate(self._config["rate"])
                wf.writeframes(b"".join(self._recorded_frames))
            print(f">>> Recording saved to {filename}")
        except Exception as e:
            print(f"!!! Error saving recording: {e}")
            raise

    def get_devices(self) -> list[dict]:
        """Get available input and output devices"""
        input_devices = []
        output_devices = []
        try:
            info = self._audio.get_host_api_info_by_index(0)
            numdevices = info.get("deviceCount")

            for i in range(0, numdevices):
                device_info = self._audio.get_device_info_by_host_api_device_index(0, i)
                device = {
                    "id": i,
                    "name": device_info["name"],
                    "sample_rate": int(device_info["defaultSampleRate"]),
                }

                if device_info.get("maxInputChannels") > 0:
                    input_devices.append(device)
                if device_info.get("maxOutputChannels") > 0:
                    output_devices.append(device)

            if input_devices:
                print(f">>> Found {len(input_devices)} input devices")
            if output_devices:
                print(f">>> Found {len(output_devices)} output devices")

        except Exception as e:
            print(f"!!! Error enumerating devices: {e}")
        return {"input": input_devices, "output": output_devices}

    def __del__(self):
        """Cleanup resources"""
        try:
            if self._stream:
                self.stop_stream()
            if self._playback_stream:
                self.stop_playback()
            if self._audio:
                self._audio.terminate()
        except Exception as e:
            print(f"!!! Error during cleanup: {e}")
