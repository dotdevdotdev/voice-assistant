import speech_recognition as sr
import openai
from openai import OpenAI
import requests
import json
import io
from pydub import AudioSegment
from pydub.playback import play as pydub_play

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
    def __init__(self, openai_api_key, elevenlabs_api_key, voice_id):
        self.recognizer = sr.Recognizer()
        openai.api_key = openai_api_key
        self.client = OpenAI()
        self.elevenlabs_api_key = elevenlabs_api_key
        self.voice_id = voice_id

    def listen(self):
        with sr.Microphone() as source:
            print("Listening...")
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
