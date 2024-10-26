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
    def __init__(self, openai_api_key, name=None):
        self.openai_api_key = openai_api_key
        self.name = name
        # ... rest of initialization ...
