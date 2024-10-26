import openai
import speech_recognition as sr
import logging
import requests
import io
import os
from pydub import AudioSegment
from pydub.playback import play as pydub_play
import pydub
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
from utils import find_input_device_index, find_output_device_index
import asyncio
from speech_recognition_handler import transcribe_audio
from PyQt6.QtCore import QObject, pyqtSignal
import elevenlabs  # Change this import


# Make Assistant inherit from QObject to enable signals
class Assistant(QObject):
    # Add a signal for transcribed text
    transcription_ready = pyqtSignal(str)

    def __init__(
        self,
        name="Claude",
        voice_id=None,
        stability=None,
        similarity_boost=None,
        model="gpt-3.5-turbo",
    ):
        super().__init__()  # Initialize QObject
        self.name = name
        self.voice_id = voice_id
        self.stability = stability
        self.similarity_boost = similarity_boost
        self.logger = logging.getLogger(__name__)
        # Initialize the OpenAI client with environment variable only
        self.openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        self.pyaudio = pyaudio.PyAudio()
        self.stream = None

    def configure(
        self,
        app_settings=None,
    ):
        """Configure the assistant with settings after initialization"""
        # Remove API key parameters since they're handled via env vars
        if app_settings:
            self.app_settings = app_settings

        # Set up clients using environment variables
        if os.getenv("ELEVENLABS_API_KEY"):
            elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))
            self.elevenlabs_configured = True

        if os.getenv("DEEPGRAM_API_KEY"):
            self.deepgram_client = DeepgramClient(os.getenv("DEEPGRAM_API_KEY"))

    def listen(self):
        """Listen for voice input and return transcribed text"""
        try:
            # Create microphone instance
            with sr.Microphone() as source:
                print(f"Assistant {self.name}: Listening...")
                # Adjust for ambient noise
                self.recognizer.adjust_for_ambient_noise(source)
                # Listen for audio input
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                try:
                    # Try using Deepgram first (assuming credentials are set)
                    text = asyncio.run(transcribe_audio(audio))
                    print(f"Assistant {self.name}: Transcribed: {text}")
                    # Emit the signal instead of returning
                    self.transcription_ready.emit(text)
                    return text
                except Exception as e:
                    self.logger.error(
                        f"Deepgram transcription failed, falling back to Google: {e}"
                    )
                    # Fallback to Google Speech Recognition
                    text = self.recognizer.recognize_google(audio)
                    print(f"Assistant {self.name}: Transcribed (Google): {text}")
                    # Emit the signal instead of returning
                    self.transcription_ready.emit(text)
                    return text

        except sr.WaitTimeoutError:
            self.logger.warning("No speech detected within timeout period")
            return None
        except sr.RequestError as e:
            self.logger.error(f"Could not request results; {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in listen(): {e}")
            return None

    async def _get_ai_response(self, user_input):
        """Get response from OpenAI API"""
        try:
            messages = [{"role": "user", "content": user_input}]
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Error getting AI response: {e}")
            raise

    async def _generate_voice(self, text):
        """Generate voice response using ElevenLabs"""
        try:
            if hasattr(self, "elevenlabs_configured"):
                audio = elevenlabs.generate(
                    text=text, voice=self.voice_id, model="eleven_monolingual_v1"
                )
                return audio
        except Exception as e:
            self.logger.error(f"Error generating voice: {e}")
            return None
        return None

    def process(self, user_input):
        """Process user input and return response text and optional audio"""
        try:
            # Get AI response
            response_text = asyncio.run(self._get_ai_response(user_input))

            # Generate voice if configured
            audio = None
            if hasattr(self, "elevenlabs_configured"):
                audio = asyncio.run(self._generate_voice(response_text))

            return response_text, audio

        except Exception as e:
            self.logger.error(f"Error in process(): {e}")
            raise

    def speak(self, text):
        """Convert text to speech and play it"""
        try:
            if hasattr(self, "elevenlabs_configured"):
                audio = asyncio.run(self._generate_voice(text))
                if audio:
                    # Convert audio bytes to AudioSegment
                    audio_segment = AudioSegment.from_file(
                        io.BytesIO(audio), format="mp3"
                    )
                    # Play the audio
                    pydub_play(audio_segment)
        except Exception as e:
            self.logger.error(f"Error in speak(): {e}")
