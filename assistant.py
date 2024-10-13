import openai
import speech_recognition as sr
import logging
import requests
import io
import os
from pydub import AudioSegment
from pydub.playback import play as pydub_play
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
    FileSource,
)
import time
import pyaudio
import wave
import json
import hashlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError


class Assistant:
    def __init__(
        self,
        openai_api_key,
        elevenlabs_api_key,
        deepgram_api_key,
        openai_settings,
        elevenlabs_settings,
        realtime_mode=False,
        save_path="~/projects/voice-assistant/data/",
    ):
        # Configure logging first
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        # Now we can use self.logger
        self.logger.debug(f"Current working directory: {os.getcwd()}")

        # Set up save_path
        self.save_path = os.path.expanduser(save_path)
        os.makedirs(self.save_path, exist_ok=True)
        self.logger.debug(f"Save path for .wav files: {self.save_path}")

        self.recognizer = sr.Recognizer()

        self.openai_api_key = openai_api_key
        self.elevenlabs_api_key = elevenlabs_api_key
        self.deepgram_api_key = deepgram_api_key

        self.deepgram = DeepgramClient(deepgram_api_key)

        openai.api_key = openai_api_key
        self.client = openai.OpenAI()

        self.openai_model = openai_settings["model"]
        self.system_prompt = openai_settings["system_prompt"]

        self.elevenlabs_model_id = elevenlabs_settings["model_id"]
        self.voice_id = elevenlabs_settings["voice_id"]
        self.elevenlabs_voice_settings = elevenlabs_settings["voice_settings"]
        self.realtime_mode = realtime_mode
        self.device_found = False

        # Set up cache directory and metadata file
        self.cache_dir = os.path.join(self.save_path, "audio_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_metadata_file = os.path.join(self.cache_dir, "metadata.json")
        self.load_cache_metadata()

    def load_cache_metadata(self):
        if os.path.exists(self.cache_metadata_file):
            with open(self.cache_metadata_file, "r") as f:
                self.cache_metadata = json.load(f)
        else:
            self.cache_metadata = {}

    def save_cache_metadata(self):
        with open(self.cache_metadata_file, "w") as f:
            json.dump(self.cache_metadata, f, indent=2)

    def get_cache_key(self, prompt):
        return hashlib.md5(prompt.encode()).hexdigest()

    def get_cached_response(self, prompt):
        cache_key = self.get_cache_key(prompt)
        if cache_key in self.cache_metadata:
            audio_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
            if os.path.exists(audio_path):
                self.logger.debug(f"Using cached response for prompt: {prompt[:30]}...")
                return self.cache_metadata[cache_key][
                    "response_text"
                ], AudioSegment.from_wav(audio_path)
        return None, None

    def cache_response(self, prompt, response_text, audio_segment):
        cache_key = self.get_cache_key(prompt)
        audio_path = os.path.join(self.cache_dir, f"{cache_key}.wav")
        audio_segment.export(audio_path, format="wav")
        self.cache_metadata[cache_key] = {
            "prompt": prompt,
            "response_text": response_text,
            "timestamp": int(time.time()),
            "file_path": audio_path,
        }
        self.save_cache_metadata()
        self.logger.debug(f"Cached response for prompt: {prompt[:30]}...")

    def listen(self, timeout=None):
        recognizer = sr.Recognizer()

        # Set up PyAudio with a specific device index
        p = pyaudio.PyAudio()
        device_index = self.find_input_device(p)
        p.terminate()

        with sr.Microphone(device_index=device_index) as source:
            print("Listening...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            try:
                print("Waiting for speech...")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)

                print("Speech detected, transcribing...")
                text = self.transcribe_with_deepgram(audio)
                if text:
                    print(f"Transcribed: {text}")
                    return text
                else:
                    print("No speech detected")
                    return None
            except sr.WaitTimeoutError:
                print("Listening timed out - no speech detected")
                return None
            except Exception as e:
                print(f"Error in listening: {e}")
                return None

    def find_input_device(self, p):
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0:
                print(f"Found input device: {dev['name']}")
                return i
        return None

    def transcribe_with_deepgram(self, audio_data):
        try:
            # Configure Deepgram options for audio analysis
            options = PrerecordedOptions(
                smart_format=True,
                model="nova-2",
                language="en-US",
            )

            # Prepare the audio payload
            payload: FileSource = {
                "buffer": audio_data,
            }

            # Call the transcribe_file method with the audio payload and options
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )

            # Extract the transcript from the response
            transcript = response.results.channels[0].alternatives[0].transcript
            print(f"You said: {transcript}")
            return transcript
        except Exception as e:
            print(f"Error transcribing with Deepgram: {str(e)}")
            return "Sorry, there was an error with the speech recognition service."

    def process(self, user_input):
        cached_response, cached_audio = self.get_cached_response(user_input)
        if cached_response:
            self.logger.debug("Using cached response")
            return cached_response, cached_audio

        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ],
        )
        response_text = response.choices[0].message.content

        # Generate audio for the response
        sound = self.generate_audio(response_text)

        # Cache the response
        if sound:
            self.cache_response(user_input, response_text, sound)

        return response_text, sound

    def generate_audio(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }

        data = {
            "text": text,
            "model_id": self.elevenlabs_model_id,
            "voice_settings": self.elevenlabs_voice_settings,
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            audio = io.BytesIO(response.content)
            sound = AudioSegment.from_mp3(audio)

            # Add a small silence at the beginning
            silence = AudioSegment.silent(duration=100)  # 100ms of silence
            sound = silence + sound

            return sound
        else:
            self.logger.error(
                f"Error: Unable to generate speech. Status code: {response.status_code}"
            )
            self.logger.error(f"Response content: {response.content}")
            return None

    def play_audio(self, audio_data):
        if isinstance(audio_data, str):
            # If audio_data is a string, assume it's a file path
            audio_segment = AudioSegment.from_wav(audio_data)
        elif isinstance(audio_data, AudioSegment):
            audio_segment = audio_data
        else:
            raise ValueError("Invalid audio_data type. Expected str or AudioSegment.")

        # Generate a unique filename using timestamp
        timestamp = int(time.time())
        filename = f"audio_{timestamp}.wav"
        filepath = os.path.join(self.save_path, filename)

        # Export the audio segment to a temporary WAV file
        audio_segment.export(filepath, format="wav")
        self.logger.debug(f"Saved audio file: {filepath}")

        # Open the WAV file
        wf = wave.open(filepath, "rb")

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        # Open stream
        stream = p.open(
            format=p.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
        )

        # Read data
        data = wf.readframes(1024)

        # Play stream
        while len(data) > 0:
            stream.write(data)
            data = wf.readframes(1024)

        # Stop stream
        stream.stop_stream()
        stream.close()

        # Close PyAudio
        p.terminate()

        # Remove the temporary file
        os.remove(filepath)

    def speak(self, text):
        start_time = time.time()
        self.logger.debug(f"Starting speak method for text: {text[:30]}...")

        # Check if we have a cached version of this audio
        cached_response, cached_audio = self.get_cached_response(text)
        if cached_audio:
            self.logger.debug("Using cached audio")
            self.logger.debug("Starting audio playback")
            playback_start = time.time()
            self.play_audio(cached_audio)
            self.logger.debug(
                f"Audio playback completed in {time.time() - playback_start:.2f} seconds"
            )
            return

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }

        data = {
            "text": text,
            "model_id": self.elevenlabs_model_id,
            "voice_settings": self.elevenlabs_voice_settings,
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            self.logger.debug(
                f"Received audio response in {time.time() - start_time:.2f} seconds"
            )
            audio = io.BytesIO(response.content)
            sound = AudioSegment.from_mp3(audio)

            # Add a small silence at the beginning
            silence = AudioSegment.silent(duration=100)  # 100ms of silence
            sound = silence + sound

            self.logger.debug("Starting audio playback")
            playback_start = time.time()
            self.play_audio(sound)
            self.logger.debug(
                f"Audio playback completed in {time.time() - playback_start:.2f} seconds"
            )

            # Cache the response
            self.cache_response(
                text, text, sound
            )  # We're using the input text as both prompt and response
        else:
            self.logger.error(
                f"Error: Unable to generate speech. Status code: {response.status_code}"
            )
            self.logger.error(f"Response content: {response.content}")
