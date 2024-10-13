import openai
import speech_recognition as sr
import logging
import requests
import io
import os
from pydub import AudioSegment
from pydub.playback import play as pydub_play
import pydub  # Add this line to import pydub module
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
import sounddevice as sd
import soundfile as sf
import platform
import sys
import numpy as np


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

        self.pyaudio = pyaudio.PyAudio()
        self.input_device_index = self.find_input_device(self.pyaudio)
        # self.pyaudio.terminate()

        # Log system information
        self.log_system_info()

    def log_system_info(self):
        self.logger.info(f"Python version: {sys.version}")
        self.logger.info(f"Platform: {platform.platform()}")
        self.logger.info(f"PyAudio version: {pyaudio.__version__}")

        # Handle pydub version
        try:
            pydub_version = pydub.__version__
        except AttributeError:
            pydub_version = "Unknown"
        self.logger.info(f"Pydub version: {pydub_version}")

        self.logger.info(f"Sounddevice version: {sd.__version__}")
        self.logger.info(f"SoundFile version: {sf.__version__}")

        # Log audio devices
        self.logger.info("Audio Input devices:")
        for i in range(self.pyaudio.get_device_count()):
            dev_info = self.pyaudio.get_device_info_by_index(i)
            if dev_info["maxInputChannels"] > 0:
                self.logger.info(f"  Device {i}: {dev_info['name']}")

        self.logger.info("Audio Output devices:")
        for i in range(self.pyaudio.get_device_count()):
            dev_info = self.pyaudio.get_device_info_by_index(i)
            if dev_info["maxOutputChannels"] > 0:
                self.logger.info(f"  Device {i}: {dev_info['name']}")

    def listen(self):
        recognizer = sr.Recognizer()

        with sr.Microphone(device_index=self.input_device_index) as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.1)
            try:
                self.logger.info("Listening...")
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                if audio:
                    text = self.transcribe(audio)
                    if text:
                        self.logger.info(f"You said: {text}")
                        return text

                self.logger.info("No speech detected")
                return None
            except sr.WaitTimeoutError:
                self.logger.debug("Listening timed out - no speech detected")
                return None
            except Exception as e:
                self.logger.error(f"Error in listening: {e}")
                return None

    def find_input_device(self, p, preferred_device_name="(hw:4,0)"):
        if preferred_device_name:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if preferred_device_name.lower() in dev["name"].lower():
                    self.logger.info(f"Found input device: {dev['name']}")
                    return i

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxInputChannels"] > 0:
                self.logger.info(f"Found input device: {dev['name']}")
                return i
        return None

    def find_output_device(self, p, preferred_device_name="(hw:0,8)"):
        if preferred_device_name:
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if preferred_device_name.lower() in dev["name"].lower():
                    self.logger.info(f"Found output device: {dev['name']}")
                    return i

        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if dev["maxOutputChannels"] > 0:
                self.logger.info(f"Found output device: {dev['name']}")
                return i
        return None

    def transcribe(self, audio_data):
        return self.transcribe_with_deepgram(audio_data)

    def transcribe_with_deepgram(self, audio_data):
        try:
            # Configure Deepgram options for audio analysis
            options = PrerecordedOptions(
                smart_format=True,
                model="nova-2",
                language="en-US",
            )

            # Prepare the audio payload
            payload = {
                "buffer": audio_data.get_wav_data(),
            }

            # Call the transcribe_file method with the audio payload and options
            response = self.deepgram.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )

            # Extract the transcript from the response
            transcript = response.results.channels[0].alternatives[0].transcript

            return transcript
        except Exception as e:
            self.logger.error(f"Error transcribing with Deepgram: {str(e)}")
            if "Unexpected 'content'" in str(e):
                self.logger.info(
                    "The audio data format is not what Deepgram expected. Make sure you're sending raw audio data."
                )
            elif "402" in str(e):
                self.logger.info(
                    "Insufficient credits. Please check your Deepgram account balance."
                )
            elif "429" in str(e):
                self.logger.info(
                    "Rate limit exceeded. Please try again later or implement a backoff strategy."
                )
            else:
                self.logger.info(
                    "An unexpected error occurred. Please check your API key and request format."
                )
            return "Sorry, there was an error with the speech recognition service."

    def process(self, user_input, chat_history):
        # Prepare the messages for the API call
        messages = [{"role": "system", "content": self.system_prompt}]

        # Add the last few messages from the chat history for context
        max_history = 5  # Adjust this number as needed
        for entry in chat_history[-max_history:]:
            role = "assistant" if entry["type"] == "Assistant" else "user"
            messages.append({"role": role, "content": entry["content"]})

        # Add the current user input
        messages.append({"role": "user", "content": user_input})

        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=messages,
        )
        response_text = response.choices[0].message.content

        # Generate audio for the response
        sound = self.generate_audio(response_text)

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
            silence = AudioSegment.silent(duration=350)
            sound = silence + sound

            return sound
        else:
            self.logger.error(
                f"Error: Unable to generate speech. Status code: {response.status_code}"
            )
            self.logger.error(f"Response content: {response.content}")
            return None

    def play_audio(self, audio_data):
        try:
            if isinstance(audio_data, str):
                audio_segment = AudioSegment.from_wav(audio_data)
            elif isinstance(audio_data, AudioSegment):
                audio_segment = audio_data
            else:
                raise ValueError(
                    "Invalid audio_data type. Expected str or AudioSegment."
                )

            timestamp = int(time.time())
            filename = f"audio_{timestamp}.wav"
            filepath = os.path.join(self.save_path, filename)

            audio_segment.export(filepath, format="wav")

            data, samplerate = sf.read(filepath)
            sd.play(data, samplerate)
            sd.wait()

            os.remove(filepath)

        except Exception as e:
            self.logger.error(f"Unexpected error in play_audio: {str(e)}")
            self.logger.exception("Stack trace:")

    def speak(self, text):
        sound = self.generate_audio(text)

        if sound:
            self.play_audio(sound)
