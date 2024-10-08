import speech_recognition as sr
import openai
from openai import OpenAI
import requests
import json
import io
from pydub import AudioSegment
from pydub.playback import play as pydub_play
import logging

CHUNK_SIZE = 1024
url = "https://api.elevenlabs.io/v1/text-to-speech/<voice-id>"

headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": "<xi-api-key>",
}

data = {
    "text": "Your text here",
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
}

response = requests.post(url, json=data, headers=headers)
with open("output.mp3", "wb") as f:
    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
        if chunk:
            f.write(chunk)


class Assistant:
    def __init__(
        self, openai_api_key, elevenlabs_api_key, voice_id, realtime_mode=False
    ):
        self.recognizer = sr.Recognizer()
        openai.api_key = openai_api_key
        self.client = OpenAI()
        self.elevenlabs_api_key = elevenlabs_api_key
        self.voice_id = voice_id
        self.realtime_mode = realtime_mode
        self.device_found = False

        # Configure logging
        logging.basicConfig(level=logging.WARNING)
        logging.getLogger("speech_recognition").setLevel(logging.ERROR)

    def listen(self):
        with sr.Microphone() as source:
            if not self.device_found:
                print("Listening...")
                self.device_found = True
                logging.info(f"Connected to microphone: {source.device_index}")
            audio = self.recognizer.listen(source)

        try:
            text = self.recognizer.recognize_google(audio)
            return text
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand that."
        except sr.RequestError:
            return "Sorry, there was an error with the speech recognition service."

    def process(self, user_input):
        # This function should return a response, but it might be returning None
        # Let's add a basic implementation
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input},
            ],
        )
        return response.choices[0].message.content

    def speak(self, text):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_api_key,
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
        }

        response = requests.post(url, json=data, headers=headers)

        if response.status_code == 200:
            audio = io.BytesIO(response.content)
            sound = AudioSegment.from_mp3(audio)
            pydub_play(sound)
        else:
            print(
                f"Error: Unable to generate speech. Status code: {response.status_code}"
            )

    def process_message(self, message, realtime_mode=None):
        # Use the realtime_mode from the request if provided, otherwise use the default
        use_realtime = (
            realtime_mode if realtime_mode is not None else self.realtime_mode
        )

        if use_realtime:
            return self.process_realtime(message)
        else:
            return self.process_normal(message)

    def process_normal(self, message):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
        )
        return response.choices[0].message["content"]

    def process_realtime(self, message):
        response = ""
        for chunk in openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": message},
            ],
            stream=True,
        ):
            if chunk.choices[0].delta.get("content"):
                response += chunk.choices[0].delta.content
        return response
