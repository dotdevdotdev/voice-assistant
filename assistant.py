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
from utils import find_input_device_index, find_output_device_index


class Assistant:
    def __init__(self, name, voice_id=None, stability=None, similarity_boost=None):
        self.name = name
        self.voice_id = voice_id
        self.stability = stability
        self.similarity_boost = similarity_boost

        # Initialize other necessary attributes
        self.openai_client = None
        self.elevenlabs_client = None
        self.deepgram_client = None

    def configure(
        self,
        openai_api_key=None,
        elevenlabs_api_key=None,
        deepgram_api_key=None,
        app_settings=None,
    ):
        """Configure the assistant with API keys and settings after initialization"""
        if openai_api_key:
            openai.api_key = openai_api_key
            self.openai_client = openai.Client()

        if elevenlabs_api_key:
            # Initialize elevenlabs client properly
            from elevenlabs import set_api_key

            set_api_key(elevenlabs_api_key)
            self.elevenlabs_client = (
                True  # We don't need to store a client instance for elevenlabs
            )

        if deepgram_api_key:
            self.deepgram_client = DeepgramClient(deepgram_api_key)

        if app_settings:
            self.app_settings = app_settings
