import pyaudio
import wave
from typing import Optional, BinaryIO
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider, AudioConfig
import io
import struct
import traceback  # Add this import
import numpy as np


class PyAudioProvider(AudioInputProvider, AudioOutputProvider):
    def __init__(self):
        self._audio = pyaudio.PyAudio()
        self._stream = None
        self._playback_stream = None
        self._config = None
        self._recorded_frames = []
        self._output_device_id = None
        self._min_recording_length = 2.0  # Minimum recording length in seconds
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
            # Increase chunk size for more stable recording
            chunk = 2048  # Doubled from 1024

            print(f"Device: {device_info['name']}")
            print(f"Format: {sample_format}")
            print(f"Channels: {channels}")
            print(f"Rate: {fs}")
            print(f"Chunk: {chunk}")
            print(f"Min recording length: {self._min_recording_length}s")

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
            self._recorded_frames = []
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
            if data:
                # Amplify the audio data
                audio_data = np.frombuffer(data, dtype=np.int16)
                # Amplify by 5x (adjust this value as needed)
                audio_data = np.clip(audio_data * 5, -32768, 32767).astype(np.int16)
                data = audio_data.tobytes()
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

                # Calculate recording length
                total_samples = len(self._recorded_frames) * self._config["chunk"]
                recording_length = total_samples / self._config["rate"]
                print(f">>> Recording length: {recording_length:.2f}s")

                # Pad recording if too short
                if recording_length < self._min_recording_length:
                    samples_needed = int(
                        (self._min_recording_length * self._config["rate"])
                        - total_samples
                    )
                    if samples_needed > 0:
                        padding = np.zeros(samples_needed, dtype=np.int16).tobytes()
                        self._recorded_frames.append(padding)
                        print(f">>> Added {samples_needed} samples of padding")

                print(
                    f">>> Final recording length: {len(self._recorded_frames) * self._config['chunk'] / self._config['rate']:.2f}s"
                )

            except Exception as e:
                print(f"!!! Error stopping stream: {e}")
            finally:
                self._stream = None
        print(">>> Stream stopped")

    def set_output_device(self, device_id: int) -> None:
        """Set the output device ID for playback"""
        self._output_device_id = device_id
        print(f">>> Output device ID set to: {device_id}")

    def play_audio(self, audio_data: Optional[BinaryIO] = None) -> None:
        """Play audio from either a file or recorded frames"""
        print("\n=== Playing audio ===")

        try:
            # Debug output device info
            if self._output_device_id is not None:
                try:
                    device_info = self._audio.get_device_info_by_index(
                        self._output_device_id
                    )
                    print(f">>> Output device info:")
                    print(f"    Name: {device_info['name']}")
                    print(
                        f"    Max Output Channels: {device_info['maxOutputChannels']}"
                    )
                    print(
                        f"    Default Sample Rate: {device_info['defaultSampleRate']}"
                    )
                except Exception as e:
                    print(f"!!! Warning: Could not get complete device info: {e}")

            # Create WAV buffer for either input source
            wav_buffer = io.BytesIO()

            if audio_data is not None:
                # Using provided audio data (test sound)
                print(">>> Using provided audio data")
                wav_buffer.write(audio_data.read())
                wav_buffer.seek(0)
            elif self._recorded_frames and self._config:
                # Using recorded frames
                print(f">>> Using {len(self._recorded_frames)} recorded frames")
                with wave.open(wav_buffer, "wb") as wf:
                    wf.setnchannels(self._config["channels"])
                    wf.setsampwidth(self._audio.get_sample_size(self._config["format"]))
                    wf.setframerate(self._config["rate"])
                    wf.writeframes(b"".join(self._recorded_frames))
                wav_buffer.seek(0)
            else:
                print("!!! No audio data to play")
                return

            # Play the audio
            with wave.open(wav_buffer, "rb") as wf:
                print(f">>> WAV details:")
                print(f"    Channels: {wf.getnchannels()}")
                print(f"    Sample width: {wf.getsampwidth()}")
                print(f"    Frame rate: {wf.getframerate()}")
                print(f"    Frames: {wf.getnframes()}")

                # Create playback stream
                self._playback_stream = self._audio.open(
                    format=self._audio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                    output_device_index=self._output_device_id,
                    frames_per_buffer=1024,
                )

                # Read and play chunks
                chunk = 1024
                data = wf.readframes(chunk)
                total_bytes = 0

                while len(data) > 0:
                    self._playback_stream.write(data)
                    total_bytes += len(data)
                    data = wf.readframes(chunk)

                print(f">>> Played {total_bytes} bytes")

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
